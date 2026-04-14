import json
import urllib.error
import urllib.request

from django.conf import settings
from django.utils import timezone


from .models import KBCategory, KBInventory, KBProduct, KBSyncCheckpoint
from .graph_writer import sync_category, sync_product, sync_customer, sync_order


def _pick_first(row, keys, default=""):
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return default


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _derive_price_range(base_price, explicit_price_range=""):
    explicit = str(explicit_price_range or "").strip().lower()
    if explicit:
        return explicit

    price = _safe_float(base_price, 0.0)
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


def _fetch_json(url, timeout=20):
    request = urllib.request.Request(url=url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw_body = response.read().decode("utf-8")
        payload = json.loads(raw_body or "[]")
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and isinstance(payload.get("data"), list):
            return payload["data"]
        return []


def _set_checkpoint(source_name, count=0, error_message=""):
    checkpoint, _ = KBSyncCheckpoint.objects.get_or_create(source_name=source_name)
    checkpoint.records_synced = int(count)
    checkpoint.last_error = error_message
    checkpoint.last_success_at = timezone.now() if not error_message else checkpoint.last_success_at
    checkpoint.save(update_fields=["records_synced", "last_error", "last_success_at", "updated_at"])


def _sync_categories():
    print("[COLLECTOR] _sync_categories called")
    endpoint = f"{settings.CATEGORY_SERVICE_URL.rstrip('/')}/api/categories/"
    rows = _fetch_json(endpoint)
    count = 0
    for row in rows:
        external_id = row.get("id")
        if external_id is None:
            continue
        KBCategory.objects.update_or_create(
            external_id=int(external_id),
            defaults={
                "name": str(row.get("name") or ""),
                "description": str(row.get("description") or ""),
                "raw_payload": row,
            },
        )
        # Ghi vào Neo4j
        sync_category({
            "external_id": int(external_id),
            "name": str(row.get("name") or "")
        })
        count += 1
    return count


def _sync_products():
    print("[COLLECTOR] _sync_products called")
    endpoint = f"{settings.PRODUCT_SERVICE_URL.rstrip('/')}/api/products/"
    attribute_endpoint = f"{settings.ATTRIBUTE_SERVICE_URL.rstrip('/')}/api/attributes/"
    product_attribute_endpoint = f"{settings.ATTRIBUTE_SERVICE_URL.rstrip('/')}/api/product-attribute-values/"

    rows = _fetch_json(endpoint)
    attribute_rows = _fetch_json(attribute_endpoint)
    product_attribute_rows = _fetch_json(product_attribute_endpoint)

    attribute_map = {}
    for attr in attribute_rows:
        attr_id = attr.get("id")
        if attr_id is None:
            continue
        try:
            attribute_map[int(attr_id)] = {
                "name": str(attr.get("name") or f"attribute-{attr_id}"),
                "data_type": str(attr.get("data_type") or ""),
                "unit": str(attr.get("unit") or ""),
            }
        except (TypeError, ValueError):
            continue

    product_attribute_map = {}
    for pav in product_attribute_rows:
        product_id = pav.get("product_id")
        attribute_id = pav.get("attribute_id")
        if product_id is None or attribute_id is None:
            continue
        try:
            product_id = int(product_id)
            attribute_id = int(attribute_id)
        except (TypeError, ValueError):
            continue

        attr_meta = attribute_map.get(attribute_id, {})
        product_attribute_map.setdefault(product_id, []).append(
            {
                "attribute_id": attribute_id,
                "name": attr_meta.get("name", f"attribute-{attribute_id}"),
                "data_type": attr_meta.get("data_type", ""),
                "unit": attr_meta.get("unit", ""),
                "value": str(pav.get("value") or ""),
            }
        )

    category_map = {item.external_id: item.name for item in KBCategory.objects.all()}
    count = 0

    for row in rows:
        external_id = row.get("id")
        if external_id is None:
            continue
        category_id = row.get("category_id")
        category_name = category_map.get(int(category_id), "") if category_id is not None else ""
        name = str(row.get("name") or "")
        description = str(row.get("description") or "")
        brand = str(row.get("brand") or "")
        status = str(row.get("status") or "")
        base_price = row.get("base_price") or 0
        gender = str(_pick_first(row, ["gender", "target_gender", "audience"], "")).strip().lower()
        price_range = _derive_price_range(base_price, explicit_price_range=row.get("price_range") or "")

        normalized_text = " ".join(
            token for token in [
                name,
                description,
                brand,
                category_name,
                str(base_price),
                status,
            ]
            if token
        ).lower()

        KBProduct.objects.update_or_create(
            external_id=int(external_id),
            defaults={
                "name": name,
                "description": description,
                "brand": brand,
                "category_external_id": int(category_id) if category_id is not None else None,
                "category_name": category_name,
                "base_price": base_price,
                "status": status,
                "normalized_text": normalized_text,
                "raw_payload": row,
            },
        )
        # Ghi vào Neo4j
        sync_product({
            "external_id": int(external_id),
            "name": name,
            "category_external_id": int(category_id) if category_id is not None else None,
            "category_name": category_name,
            "brand": brand,
            "base_price": base_price,
            "price_range": price_range,
            "gender": gender,
            "attributes": product_attribute_map.get(int(external_id), []),
        })
        count += 1
    return count


def _sync_inventories():
    print("[COLLECTOR] _sync_inventories called")
    endpoint = f"{settings.INVENTORY_SERVICE_URL.rstrip('/')}/api/inventories/"
    rows = _fetch_json(endpoint)
    count = 0

    for row in rows:
        external_id = row.get("id")
        if external_id is None:
            continue

        KBInventory.objects.update_or_create(
            external_id=int(external_id),
            defaults={
                "variant_id": int(row.get("variant_id") or 0),
                "quantity": int(row.get("quantity") or 0),
                "reserved_quantity": int(row.get("reserved_quantity") or 0),
                "raw_payload": row,
            },
        )
        count += 1
    return count


def _sync_customers():
    print("[COLLECTOR] _sync_customers called")
    endpoint = f"{settings.CUSTOMER_SERVICE_URL.rstrip('/')}/customer/accounts/"
    rows = _fetch_json(endpoint)
    count = 0

    for row in rows:
        external_id = row.get("id")
        if external_id is None:
            continue

        sync_customer(
            {
                "external_id": int(external_id),
                "name": str(row.get("full_name") or row.get("username") or f"customer-{external_id}"),
            }
        )
        count += 1

    return count


def _extract_order_products(order_row):
    products = []
    order_timestamp = _pick_first(order_row, ["created_at", "ordered_at", "order_date", "timestamp", "updated_at"], "")
    order_rating = order_row.get("rating")
    for item in order_row.get("items") or []:
        candidate = item.get("product_id")
        if candidate is None:
            candidate = item.get("item_id")
        if candidate is None:
            continue
        try:
            products.append(
                {
                    "id": int(candidate),
                    "name": str(item.get("item_name") or ""),
                    "rating": _safe_float(item.get("rating") if item.get("rating") is not None else order_rating, None),
                    "timestamp": _pick_first(item, ["created_at", "ordered_at", "timestamp"], order_timestamp),
                    "quantity": int(item.get("quantity") or 1),
                    "unit_price": _safe_float(item.get("unit_price"), None),
                    "line_total": _safe_float(item.get("line_total"), None),
                }
            )
        except (TypeError, ValueError):
            continue
    return products


def _sync_orders():
    print("[COLLECTOR] _sync_orders called")
    endpoint = f"{settings.ORDER_SERVICE_URL.rstrip('/')}/orders/"
    rows = _fetch_json(endpoint)
    count = 0

    for row in rows:
        customer_id = row.get("customer_id")
        if customer_id is None:
            continue

        products = _extract_order_products(row)
        if not products:
            continue

        sync_order(
            {
                "order_id": int(row.get("id")),
                "customer_id": int(customer_id),
                "timestamp": _pick_first(row, ["created_at", "ordered_at", "order_date", "timestamp", "updated_at"], ""),
                "total_amount": row.get("total_amount"),
                "payment_method": row.get("payment_method"),
                "order_status": row.get("order_status"),
                "products": products,
            }
        )
        count += 1

    return count


def run_phase1_collection():
    result = {
        "categories": 0,
        "products": 0,
        "inventories": 0,
        "customers": 0,
        "orders": 0,
        "errors": {},
    }

    tasks = [
        ("categories", _sync_categories),
        ("products", _sync_products),
        ("inventories", _sync_inventories),
        ("customers", _sync_customers),
        ("orders", _sync_orders),
    ]

    for source_name, fn in tasks:
        try:
            count = fn()
            result[source_name] = count
            _set_checkpoint(source_name, count=count)
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, ValueError) as exc:
            message = str(exc)
            result["errors"][source_name] = message
            _set_checkpoint(source_name, count=0, error_message=message)

    return result
