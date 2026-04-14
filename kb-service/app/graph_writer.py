import os
import hashlib
from datetime import datetime, timezone

from neo4j import GraphDatabase

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "test")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
_schema_initialized = False

BEHAVIOR_WEIGHTS = {
    "VIEWED": 1.0,
    "ADDED_TO_CART": 3.0,
    "PURCHASED": 5.0,
    "SEARCHED": 2.0,
}


def _normalize_behavior_type(event_type):
    value = str(event_type or "").upper().strip()
    if value in BEHAVIOR_WEIGHTS:
        return value
    raise ValueError(f"Unsupported behavior type: {event_type}")


def _normalize_timestamp(value=None):
    if not value:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return str(value)


def _day_bucket(timestamp_text):
    normalized = _normalize_timestamp(timestamp_text)
    return normalized[:10]


def _behavior_event_id(customer_id, event_type, target_key, timestamp_text):
    raw = f"{int(customer_id)}|{str(event_type).upper()}|{target_key}|{_normalize_timestamp(timestamp_text)}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:40]


def _ensure_graph_schema():
    global _schema_initialized
    if _schema_initialized:
        return
    with driver.session() as session:
        session.run("CREATE CONSTRAINT customer_id_unique IF NOT EXISTS FOR (n:Customer) REQUIRE n.id IS UNIQUE")
        session.run("CREATE CONSTRAINT product_id_unique IF NOT EXISTS FOR (n:Product) REQUIRE n.id IS UNIQUE")
        session.run("CREATE CONSTRAINT category_id_unique IF NOT EXISTS FOR (n:Category) REQUIRE n.id IS UNIQUE")
        session.run("CREATE CONSTRAINT order_id_unique IF NOT EXISTS FOR (n:Order) REQUIRE n.id IS UNIQUE")
        session.run("CREATE CONSTRAINT attribute_id_unique IF NOT EXISTS FOR (n:Attribute) REQUIRE n.id IS UNIQUE")
        session.run("CREATE CONSTRAINT brand_name_unique IF NOT EXISTS FOR (n:Brand) REQUIRE n.name IS UNIQUE")
        session.run("CREATE CONSTRAINT searchterm_query_unique IF NOT EXISTS FOR (n:SearchTerm) REQUIRE n.query IS UNIQUE")
        session.run("CREATE CONSTRAINT day_date_unique IF NOT EXISTS FOR (n:Day) REQUIRE n.date IS UNIQUE")
        session.run("CREATE CONSTRAINT behavior_event_id_unique IF NOT EXISTS FOR (n:BehaviorEvent) REQUIRE n.id IS UNIQUE")
    _schema_initialized = True


def _normalize_gender(value=None):
    text = str(value or "").strip().lower()
    aliases = {
        "male": "men",
        "man": "men",
        "female": "women",
        "woman": "women",
        "boy": "kids",
        "girl": "kids",
    }
    return aliases.get(text, text)


def _price_range_from_value(base_price, explicit_price_range=None):
    explicit = str(explicit_price_range or "").strip().lower()
    if explicit:
        return explicit

    try:
        price = float(base_price or 0)
    except (TypeError, ValueError):
        return ""

    # Supports both small-unit and VND-like price scales.
    if price <= 0:
        return ""
    if price < 1000:
        if price < 200:
            return "budget"
        if price < 800:
            return "mid"
        return "premium"

    if price < 5_000_000:
        return "budget"
    if price < 20_000_000:
        return "mid"
    return "premium"


def upsert_product(
    tx,
    product_id,
    name,
    category_id=None,
    brand=None,
    category_name=None,
    base_price=0,
    price_range="",
    gender="",
    attributes=None,
):
    brand_name = str(brand or "").strip()
    attributes = attributes if isinstance(attributes, list) else []
    tx.run(
        """
        MERGE (p:Product {id: $product_id})
        SET p.name = $name,
            p.brand = $brand,
            p.category_name = $category_name,
            p.base_price = $base_price,
            p.price_range = $price_range,
            p.gender = $gender
        WITH p
        OPTIONAL MATCH (c:Category {id: $category_id})
        FOREACH (_ IN CASE WHEN c IS NULL THEN [] ELSE [1] END |
            MERGE (p)-[:PRODUCT_IN_CATEGORY]->(c)
        )
        WITH p
        FOREACH (_ IN CASE WHEN $brand_name = '' THEN [] ELSE [1] END |
            MERGE (b:Brand {name: $brand_name})
            MERGE (p)-[:PRODUCT_OF_BRAND]->(b)
        )
        """,
        product_id=product_id,
        name=name,
        brand=brand,
        brand_name=brand_name,
        category_id=category_id,
        category_name=category_name,
        base_price=float(base_price or 0),
        price_range=price_range,
        gender=gender,
    )
    for attr in attributes:
        attr_id = attr.get("attribute_id")
        if attr_id is None:
            continue
        try:
            attr_id = int(attr_id)
        except (TypeError, ValueError):
            continue

        tx.run(
            """
            MERGE (p:Product {id: $product_id})
            MERGE (a:Attribute {id: $attribute_id})
            SET a.name = $attribute_name,
                a.data_type = $data_type,
                a.unit = $unit
            MERGE (p)-[r:PRODUCT_HAS_ATTRIBUTE]->(a)
            SET r.value = $attribute_value,
                r.updated_at = $updated_at
            """,
            product_id=product_id,
            attribute_id=attr_id,
            attribute_name=str(attr.get("name") or f"attribute-{attr_id}"),
            data_type=str(attr.get("data_type") or ""),
            unit=str(attr.get("unit") or ""),
            attribute_value=str(attr.get("value") or ""),
            updated_at=_normalize_timestamp(attr.get("updated_at")),
        )


def upsert_category(tx, category_id, name):
    tx.run(
        """
        MERGE (c:Category {id: $category_id})
        SET c.name = $name
        """,
        category_id=category_id,
        name=name,
    )


def upsert_customer(tx, customer_id, name):
    tx.run(
        """
        MERGE (u:Customer {id: $customer_id})
        SET u.name = $name
        """,
        customer_id=customer_id,
        name=name,
    )


def create_or_update_interaction(
    tx,
    event_type,
    customer_id,
    product_id,
    product_name=None,
    timestamp=None,
    rating=None,
):
    rel_type = _normalize_behavior_type(event_type)
    query = f"""
        MERGE (u:Customer {{id: $customer_id}})
        MERGE (p:Product {{id: $product_id}})
        ON CREATE SET p.name = coalesce($product_name, 'Unknown Product')
        ON MATCH SET p.name = coalesce(p.name, $product_name, 'Unknown Product')
        MERGE (u)-[r:{rel_type}]->(p)
        SET r.timestamp = $timestamp,
            r.weight = $weight,
            r.rating = $rating

        MERGE (e:BehaviorEvent {{id: $event_id}})
        SET e.event_type = $event_type,
            e.timestamp = $timestamp,
            e.weight = $weight,
            e.rating = $rating
        MERGE (u)-[:PERFORMED]->(e)
        MERGE (e)-[:ON_PRODUCT]->(p)

        MERGE (d:Day {{date: $day_bucket}})
        MERGE (e)-[:IN_DAY]->(d)
    """
    timestamp_text = _normalize_timestamp(timestamp)
    tx.run(
        query,
        customer_id=customer_id,
        product_id=product_id,
        product_name=product_name,
        timestamp=timestamp_text,
        weight=float(BEHAVIOR_WEIGHTS[rel_type]),
        rating=float(rating) if rating is not None else None,
        event_type=rel_type,
        event_id=_behavior_event_id(customer_id, rel_type, f"product:{product_id}", timestamp_text),
        day_bucket=_day_bucket(timestamp_text),
    )


def create_search_event(tx, customer_id, query_text, timestamp=None):
    normalized_query = str(query_text or "").strip().lower()
    timestamp_text = _normalize_timestamp(timestamp)
    tx.run(
        """
        MERGE (u:Customer {id: $customer_id})
        MERGE (s:SearchTerm {query: toLower($query_text)})
        MERGE (u)-[r:SEARCHED]->(s)
        SET r.timestamp = $timestamp,
            r.weight = $weight

        MERGE (e:BehaviorEvent {id: $event_id})
        SET e.event_type = 'SEARCHED',
            e.timestamp = $timestamp,
            e.weight = $weight,
            e.query = $query_text
        MERGE (u)-[:PERFORMED]->(e)
        MERGE (e)-[:ON_SEARCH_TERM]->(s)

        MERGE (d:Day {date: $day_bucket})
        MERGE (e)-[:IN_DAY]->(d)
        """,
        customer_id=customer_id,
        query_text=normalized_query,
        timestamp=timestamp_text,
        weight=float(BEHAVIOR_WEIGHTS["SEARCHED"]),
        event_id=_behavior_event_id(customer_id, "SEARCHED", f"query:{normalized_query}", timestamp_text),
        day_bucket=_day_bucket(timestamp_text),
    )


def create_purchase(tx, customer_id, product_id, product_name=None, timestamp=None, rating=None):
    create_or_update_interaction(
        tx,
        event_type="PURCHASED",
        customer_id=customer_id,
        product_id=product_id,
        product_name=product_name,
        timestamp=timestamp,
        rating=rating,
    )


def close():
    driver.close()


def sync_product(product):
    _ensure_graph_schema()
    print(f"[Neo4j] sync_product: {product}")
    price_range = _price_range_from_value(
        base_price=product.get("base_price"),
        explicit_price_range=product.get("price_range"),
    )
    gender = _normalize_gender(product.get("gender"))
    with driver.session() as session:
        session.execute_write(
            upsert_product,
            product_id=product["external_id"],
            name=product["name"],
            category_id=product.get("category_external_id"),
            brand=product.get("brand"),
            category_name=product.get("category_name"),
            base_price=product.get("base_price"),
            price_range=price_range,
            gender=gender,
            attributes=product.get("attributes") or [],
        )


def sync_category(category):
    _ensure_graph_schema()
    print(f"[Neo4j] sync_category: {category}")
    with driver.session() as session:
        session.execute_write(
            upsert_category,
            category_id=category["external_id"],
            name=category["name"],
        )


def sync_customer(customer):
    _ensure_graph_schema()
    print(f"[Neo4j] sync_customer: {customer}")
    with driver.session() as session:
        session.execute_write(
            upsert_customer,
            customer_id=customer["external_id"],
            name=customer["name"],
        )


def _upsert_order_graph(
    tx,
    order_id,
    customer_id,
    timestamp=None,
    total_amount=None,
    payment_method=None,
    order_status=None,
):
    timestamp_text = _normalize_timestamp(timestamp)
    tx.run(
        """
        MERGE (u:Customer {id: $customer_id})
        MERGE (o:Order {id: $order_id})
        SET o.timestamp = $timestamp,
            o.total_amount = $total_amount,
            o.payment_method = $payment_method,
            o.order_status = $order_status
        MERGE (u)-[:PLACED_ORDER]->(o)

        MERGE (d:Day {date: $day_bucket})
        MERGE (o)-[:IN_DAY]->(d)
        """,
        order_id=int(order_id),
        customer_id=int(customer_id),
        timestamp=timestamp_text,
        total_amount=float(total_amount) if total_amount not in (None, "") else None,
        payment_method=str(payment_method or ""),
        order_status=str(order_status or ""),
        day_bucket=_day_bucket(timestamp_text),
    )


def _link_order_item(
    tx,
    order_id,
    customer_id,
    product_id,
    product_name=None,
    timestamp=None,
    rating=None,
    quantity=None,
    unit_price=None,
    line_total=None,
):
    timestamp_text = _normalize_timestamp(timestamp)
    tx.run(
        """
        MERGE (o:Order {id: $order_id})
        MERGE (p:Product {id: $product_id})
        ON CREATE SET p.name = coalesce($product_name, 'Unknown Product')
        ON MATCH SET p.name = coalesce(p.name, $product_name, 'Unknown Product')
        MERGE (o)-[item:ORDER_CONTAINS]->(p)
        SET item.quantity = $quantity,
            item.unit_price = $unit_price,
            item.line_total = $line_total,
            item.timestamp = $timestamp
        """,
        order_id=int(order_id),
        product_id=int(product_id),
        product_name=product_name,
        quantity=int(quantity) if quantity not in (None, "") else 1,
        unit_price=float(unit_price) if unit_price not in (None, "") else None,
        line_total=float(line_total) if line_total not in (None, "") else None,
        timestamp=timestamp_text,
    )

    create_or_update_interaction(
        tx,
        event_type="PURCHASED",
        customer_id=customer_id,
        product_id=product_id,
        product_name=product_name,
        timestamp=timestamp_text,
        rating=rating,
    )


def sync_order(order):
    _ensure_graph_schema()
    print(f"[Neo4j] sync_order: {order}")
    order_id = order.get("order_id")
    if order_id is None:
        raw_ts = _normalize_timestamp(order.get("timestamp"))
        order_id = int(hashlib.sha1(f"{order.get('customer_id')}|{raw_ts}".encode("utf-8")).hexdigest()[:12], 16)

    with driver.session() as session:
        session.execute_write(
            _upsert_order_graph,
            order_id=int(order_id),
            customer_id=int(order["customer_id"]),
            timestamp=order.get("timestamp"),
            total_amount=order.get("total_amount"),
            payment_method=order.get("payment_method"),
            order_status=order.get("order_status"),
        )
        for product in order["products"]:
            session.execute_write(
                _link_order_item,
                order_id=int(order_id),
                customer_id=order["customer_id"],
                product_id=product["id"],
                product_name=product.get("name"),
                timestamp=product.get("timestamp") or order.get("timestamp"),
                rating=product.get("rating") or order.get("rating"),
                quantity=product.get("quantity"),
                unit_price=product.get("unit_price"),
                line_total=product.get("line_total"),
            )


def sync_user_behavior(event):
    _ensure_graph_schema()
    print(f"[Neo4j] sync_user_behavior: {event}")
    customer_id = int(event["customer_id"])
    event_type = _normalize_behavior_type(event.get("event_type"))
    timestamp = event.get("timestamp")
    rating = event.get("rating")
    with driver.session() as session:
        if event_type == "SEARCHED" and event.get("query"):
            session.execute_write(
                create_search_event,
                customer_id=customer_id,
                query_text=event.get("query"),
                timestamp=timestamp,
            )
            return

        if event.get("product_id") is None:
            raise ValueError("product_id is required for this event type")

        session.execute_write(
            create_or_update_interaction,
            event_type=event_type,
            customer_id=customer_id,
            product_id=int(event.get("product_id")),
            product_name=event.get("product_name"),
            timestamp=timestamp,
            rating=rating,
        )


def _build_product_filter_clause():
    return """
      AND ($price_range IS NULL OR $price_range = '' OR rec.price_range = $price_range)
      AND (
        $gender IS NULL OR $gender = '' OR
        rec.gender = $gender OR
        rec.gender = 'unisex' OR
        rec.gender IS NULL OR
        rec.gender = ''
      )
    """


def _run_ranked_product_query(query, params):
    _ensure_graph_schema()
    with driver.session() as session:
        result = session.run(query, **params)
        return [record.data() for record in result]


def _merge_ranked_results(*ranked_lists):
    merged = {}
    for ranked in ranked_lists:
        for row in ranked:
            product_id = row.get("product_id")
            if product_id is None:
                continue
            score = float(row.get("score") or 0)
            existing = merged.get(product_id)
            if not existing:
                merged[product_id] = {
                    "product_id": product_id,
                    "name": row.get("name"),
                    "brand": row.get("brand"),
                    "gender": row.get("gender"),
                    "price_range": row.get("price_range"),
                    "score": score,
                }
            else:
                existing["score"] += score
    values = list(merged.values())
    values.sort(key=lambda item: item.get("score", 0), reverse=True)
    for item in values:
        item["score"] = round(float(item["score"]), 4)
    return values


def _scale_ranked_scores(ranked, factor):
    scaled = []
    for row in ranked:
        copied = dict(row)
        copied["score"] = float(copied.get("score") or 0.0) * float(factor)
        scaled.append(copied)
    return scaled


# Recommendation: products in the same category.
def recommend_same_category(product_id, limit=10, price_range=None, gender=None):
    query = (
        """
    MATCH (p:Product {id: $product_id})-[:PRODUCT_IN_CATEGORY]->(c:Category)<-[:PRODUCT_IN_CATEGORY]-(rec:Product)
    WHERE rec.id <> $product_id
    """
        + _build_product_filter_clause()
        + """
    RETURN rec.id AS product_id,
           rec.name AS name,
           rec.brand AS brand,
           rec.gender AS gender,
           rec.price_range AS price_range,
           1.0 AS score
    LIMIT $limit
    """
    )
    return _run_ranked_product_query(
        query,
        {
            "product_id": int(product_id),
            "limit": max(1, int(limit)),
            "price_range": str(price_range or "").lower(),
            "gender": _normalize_gender(gender),
        },
    )


# Recommendation: products co-interacted by other users.
def recommend_also_bought(product_id, limit=10, price_range=None, gender=None):
    behavior_query = (
        """
    MATCH (p:Product {id: $product_id})<-[seed_rel:VIEWED|ADDED_TO_CART|PURCHASED]-(u:Customer)-[candidate_rel:VIEWED|ADDED_TO_CART|PURCHASED]->(rec:Product)
    WHERE rec.id <> $product_id
    """
        + _build_product_filter_clause()
        + """
    RETURN rec.id AS product_id,
           rec.name AS name,
           rec.brand AS brand,
           rec.gender AS gender,
           rec.price_range AS price_range,
           sum(
             coalesce(seed_rel.weight, CASE type(seed_rel)
               WHEN 'PURCHASED' THEN 5.0
               WHEN 'ADDED_TO_CART' THEN 3.0
               ELSE 1.0
             END) *
             coalesce(candidate_rel.weight, CASE type(candidate_rel)
               WHEN 'PURCHASED' THEN 5.0
               WHEN 'ADDED_TO_CART' THEN 3.0
               ELSE 1.0
             END) *
             exp(-toFloat(duration.inDays(datetime(coalesce(candidate_rel.timestamp, datetime().toString())), datetime()).days) / 180.0) *
             (1.0 + coalesce(candidate_rel.rating, 0.0) / 5.0)
           ) AS score
    ORDER BY score DESC
    LIMIT $limit
    """
    )
    order_query = (
        """
    MATCH (seed:Product {id: $product_id})<-[seed_item:ORDER_CONTAINS]-(o:Order)-[item:ORDER_CONTAINS]->(rec:Product)
    WHERE rec.id <> $product_id
    """
        + _build_product_filter_clause()
        + """
    RETURN rec.id AS product_id,
           rec.name AS name,
           rec.brand AS brand,
           rec.gender AS gender,
           rec.price_range AS price_range,
           sum(
             coalesce(seed_item.quantity, 1.0) *
             coalesce(item.quantity, 1.0) *
             exp(-toFloat(duration.inDays(datetime(coalesce(item.timestamp, o.timestamp, datetime().toString())), datetime()).days) / 180.0)
           ) AS score
    ORDER BY score DESC
    LIMIT $limit
    """
    )
    attribute_query = (
        """
    MATCH (seed:Product {id: $product_id})-[seed_attr:PRODUCT_HAS_ATTRIBUTE]->(a:Attribute)<-[rec_attr:PRODUCT_HAS_ATTRIBUTE]-(rec:Product)
    WHERE rec.id <> $product_id
    """
        + _build_product_filter_clause()
        + """
    RETURN rec.id AS product_id,
           rec.name AS name,
           rec.brand AS brand,
           rec.gender AS gender,
           rec.price_range AS price_range,
           sum(
             CASE
               WHEN coalesce(seed_attr.value, '') <> ''
                    AND toLower(seed_attr.value) = toLower(coalesce(rec_attr.value, ''))
               THEN 2.0
               ELSE 1.0
             END
           ) AS score
    ORDER BY score DESC
    LIMIT $limit
    """
    )

    params = {
        "product_id": int(product_id),
        "limit": max(1, int(limit)),
        "price_range": str(price_range or "").lower(),
        "gender": _normalize_gender(gender),
    }

    behavior_ranked = _run_ranked_product_query(behavior_query, params)
    order_ranked = _run_ranked_product_query(order_query, params)
    attribute_ranked = _run_ranked_product_query(attribute_query, params)

    merged = _merge_ranked_results(
        _scale_ranked_scores(behavior_ranked, 0.60),
        _scale_ranked_scores(order_ranked, 0.25),
        _scale_ranked_scores(attribute_ranked, 0.15),
    )
    return merged[: params["limit"]]


def recommend_top_products(limit=10, price_range=None, gender=None):
    behavior_query = """
    MATCH (u:Customer)-[r:VIEWED|ADDED_TO_CART|PURCHASED]->(p:Product)
    WHERE 1 = 1
      AND ($price_range IS NULL OR $price_range = '' OR p.price_range = $price_range)
      AND (
        $gender IS NULL OR $gender = '' OR
        p.gender = $gender OR
        p.gender = 'unisex' OR
        p.gender IS NULL OR
        p.gender = ''
      )
    RETURN p.id AS product_id,
           p.name AS name,
           p.brand AS brand,
           p.gender AS gender,
           p.price_range AS price_range,
           sum(
             coalesce(r.weight, CASE type(r)
               WHEN 'PURCHASED' THEN 5.0
               WHEN 'ADDED_TO_CART' THEN 3.0
               ELSE 1.0
             END) *
             exp(-toFloat(duration.inDays(datetime(coalesce(r.timestamp, datetime().toString())), datetime()).days) / 180.0) *
             (1.0 + coalesce(r.rating, 0.0) / 5.0)
           ) AS score
    ORDER BY score DESC
    LIMIT $limit
    """

    order_query = """
    MATCH (o:Order)-[item:ORDER_CONTAINS]->(p:Product)
    WHERE 1 = 1
      AND ($price_range IS NULL OR $price_range = '' OR p.price_range = $price_range)
      AND (
        $gender IS NULL OR $gender = '' OR
        p.gender = $gender OR
        p.gender = 'unisex' OR
        p.gender IS NULL OR
        p.gender = ''
      )
    RETURN p.id AS product_id,
           p.name AS name,
           p.brand AS brand,
           p.gender AS gender,
           p.price_range AS price_range,
           sum(
             coalesce(item.quantity, 1.0) *
             exp(-toFloat(duration.inDays(datetime(coalesce(item.timestamp, o.timestamp, datetime().toString())), datetime()).days) / 180.0)
           ) AS score
    ORDER BY score DESC
    LIMIT $limit
    """

    params = {
        "limit": max(1, int(limit)),
        "price_range": str(price_range or "").lower(),
        "gender": _normalize_gender(gender),
    }

    behavior_ranked = _run_ranked_product_query(behavior_query, params)
    order_ranked = _run_ranked_product_query(order_query, params)

    merged = _merge_ranked_results(
        _scale_ranked_scores(behavior_ranked, 0.70),
        _scale_ranked_scores(order_ranked, 0.30),
    )
    return merged[: params["limit"]]


def recommend_personalized(customer_id, limit=10, price_range=None, gender=None):
        behavior_query = (
                """
        MATCH (u:Customer {id: $customer_id})-[seed_rel:VIEWED|ADDED_TO_CART|PURCHASED]->(seed:Product)
        MATCH (seed)<-[peer_seed_rel:VIEWED|ADDED_TO_CART|PURCHASED]-(peer:Customer)-[candidate_rel:VIEWED|ADDED_TO_CART|PURCHASED]->(rec:Product)
        WHERE rec.id <> seed.id
            AND NOT EXISTS { MATCH (u)-[:PURCHASED]->(rec) }
        """
                + _build_product_filter_clause()
                + """
        RETURN rec.id AS product_id,
                     rec.name AS name,
                     rec.brand AS brand,
                     rec.gender AS gender,
                     rec.price_range AS price_range,
                     sum(
                         coalesce(seed_rel.weight, CASE type(seed_rel)
                             WHEN 'PURCHASED' THEN 5.0
                             WHEN 'ADDED_TO_CART' THEN 3.0
                             ELSE 1.0
                         END) *
                         coalesce(candidate_rel.weight, CASE type(candidate_rel)
                             WHEN 'PURCHASED' THEN 5.0
                             WHEN 'ADDED_TO_CART' THEN 3.0
                             ELSE 1.0
                         END) *
                         exp(-toFloat(duration.inDays(datetime(coalesce(candidate_rel.timestamp, datetime().toString())), datetime()).days) / 120.0) *
                         (1.0 + coalesce(candidate_rel.rating, 0.0) / 5.0)
                     ) AS score
        ORDER BY score DESC
        LIMIT $limit
        """
        )

        search_query = """
        MATCH (u:Customer {id: $customer_id})-[s:SEARCHED]->(term:SearchTerm)
        MATCH (rec:Product)
        WHERE toLower(
                        coalesce(rec.name, '') + ' ' +
                        coalesce(rec.brand, '') + ' ' +
                        coalesce(rec.category_name, '')
                    ) CONTAINS toLower(term.query)
            AND NOT EXISTS { MATCH (u)-[:PURCHASED]->(rec) }
            AND ($price_range IS NULL OR $price_range = '' OR rec.price_range = $price_range)
            AND (
                $gender IS NULL OR $gender = '' OR
                rec.gender = $gender OR
                rec.gender = 'unisex' OR
                rec.gender IS NULL OR
                rec.gender = ''
            )
        RETURN rec.id AS product_id,
                     rec.name AS name,
                     rec.brand AS brand,
                     rec.gender AS gender,
                     rec.price_range AS price_range,
                     sum(
                         coalesce(s.weight, 2.0) *
                         exp(-toFloat(duration.inDays(datetime(coalesce(s.timestamp, datetime().toString())), datetime()).days) / 30.0)
                     ) AS score
        ORDER BY score DESC
        LIMIT $limit
        """

        order_query = (
                """
        MATCH (u:Customer {id: $customer_id})-[:PLACED_ORDER]->(:Order)-[:ORDER_CONTAINS]->(seed:Product)
        MATCH (seed)<-[seed_item:ORDER_CONTAINS]-(o:Order)-[item:ORDER_CONTAINS]->(rec:Product)
        WHERE rec.id <> seed.id
            AND NOT EXISTS { MATCH (u)-[:PURCHASED]->(rec) }
        """
                + _build_product_filter_clause()
                + """
        RETURN rec.id AS product_id,
                     rec.name AS name,
                     rec.brand AS brand,
                     rec.gender AS gender,
                     rec.price_range AS price_range,
                     sum(
                         coalesce(seed_item.quantity, 1.0) *
                         coalesce(item.quantity, 1.0) *
                         exp(-toFloat(duration.inDays(datetime(coalesce(item.timestamp, o.timestamp, datetime().toString())), datetime()).days) / 120.0)
                     ) AS score
        ORDER BY score DESC
        LIMIT $limit
        """
        )

        attribute_query = (
                """
        MATCH (u:Customer {id: $customer_id})-[seed_rel:VIEWED|ADDED_TO_CART|PURCHASED]->(seed:Product)-[seed_attr:PRODUCT_HAS_ATTRIBUTE]->(a:Attribute)
        MATCH (rec:Product)-[rec_attr:PRODUCT_HAS_ATTRIBUTE]->(a)
        WHERE rec.id <> seed.id
            AND NOT EXISTS { MATCH (u)-[:PURCHASED]->(rec) }
        """
                + _build_product_filter_clause()
                + """
        RETURN rec.id AS product_id,
                     rec.name AS name,
                     rec.brand AS brand,
                     rec.gender AS gender,
                     rec.price_range AS price_range,
                     sum(
                         coalesce(seed_rel.weight, CASE type(seed_rel)
                             WHEN 'PURCHASED' THEN 5.0
                             WHEN 'ADDED_TO_CART' THEN 3.0
                             ELSE 1.0
                         END) *
                         CASE
                             WHEN coalesce(seed_attr.value, '') <> ''
                                        AND toLower(seed_attr.value) = toLower(coalesce(rec_attr.value, ''))
                             THEN 2.0
                             ELSE 1.0
                         END *
                         exp(-toFloat(duration.inDays(datetime(coalesce(seed_rel.timestamp, datetime().toString())), datetime()).days) / 150.0)
                     ) AS score
        ORDER BY score DESC
        LIMIT $limit
        """
        )

        params = {
                "customer_id": int(customer_id),
                "limit": max(1, int(limit)),
                "price_range": str(price_range or "").lower(),
                "gender": _normalize_gender(gender),
        }

        behavior_ranked = _run_ranked_product_query(behavior_query, params)
        search_ranked = _run_ranked_product_query(search_query, params)
        order_ranked = _run_ranked_product_query(order_query, params)
        attribute_ranked = _run_ranked_product_query(attribute_query, params)

        merged = _merge_ranked_results(
                _scale_ranked_scores(behavior_ranked, 0.45),
                _scale_ranked_scores(search_ranked, 0.20),
                _scale_ranked_scores(order_ranked, 0.25),
                _scale_ranked_scores(attribute_ranked, 0.10),
        )
        if merged:
                return merged[: params["limit"]]

        # Cold-start fallback if user has no personal signal.
        return recommend_top_products(
                limit=params["limit"],
                price_range=params["price_range"],
                gender=params["gender"],
        )
