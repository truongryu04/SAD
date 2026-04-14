import json
import math
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Dict, List

from django.conf import settings


def _fetch_json(url: str, timeout: int = 20) -> Dict:
    req = urllib.request.Request(url=url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
            return json.loads(raw or "{}")
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return {}


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class ProductRecommenderService:
    def __init__(
        self,
        customer_service_url: str,
        product_service_url: str,
        laptop_service_url: str,
        mobile_service_url: str,
        decay_days: int = 30,
    ) -> None:
        self.customer_service_url = customer_service_url.rstrip("/")
        self.product_service_url = product_service_url.rstrip("/")
        self.laptop_service_url = laptop_service_url.rstrip("/")
        self.mobile_service_url = mobile_service_url.rstrip("/")
        self.decay_days = decay_days

    def _category_to_item_type(self, category_id) -> str:
        try:
            cid = int(category_id)
        except (TypeError, ValueError):
            return "mobile"
        return "laptop" if cid in {2, 9, 10} else "mobile"

    def _activity_score(self, activity: Dict) -> float:
        action = str(activity.get("action") or "").upper()
        quantity = int(activity.get("quantity") or 0)
        rating_score = int(activity.get("rating_score") or 0)

        if action == "VIEW_PRODUCT":
            base = 1.0
        elif action == "ADD_TO_CART":
            base = 4.0 + 0.5 * max(quantity, 1)
        elif action == "RATE_PRODUCT":
            base = 2.0 + max(rating_score, 0)
        else:
            base = 1.0

        created_at = _parse_iso_datetime(activity.get("created_at"))
        if created_at is None:
            return base

        now = datetime.now(timezone.utc)
        days_ago = max((now - created_at).total_seconds() / 86400.0, 0.0)
        time_weight = math.exp(-days_ago / float(self.decay_days)) if self.decay_days > 0 else 1.0
        return base * time_weight

    def _load_activities(self, customer_id: int | None, limit: int = 2000) -> List[Dict]:
        params = {"limit": str(limit)}
        if customer_id is not None:
            params["customer_id"] = str(customer_id)

        query = urllib.parse.urlencode(params)
        url = f"{self.customer_service_url}/customer/activities/?{query}"
        payload = _fetch_json(url)
        data = payload.get("data")
        return data if isinstance(data, list) else []

    def _load_products(self) -> Dict[str, Dict]:
        products: Dict[str, Dict] = {}

        payload = _fetch_json(f"{self.product_service_url}/api/products/")
        rows = payload if isinstance(payload, list) else payload.get("data") or payload.get("results") or []
        for item in rows if isinstance(rows, list) else []:
            item_id = item.get("id")
            if item_id is None:
                continue
            item_type = self._category_to_item_type(item.get("category_id"))
            key = f"{item_type}:{item_id}"
            products[key] = {
                "item_type": item_type,
                "item_id": item_id,
                "name": item.get("name", "Unknown"),
                "brand": item.get("brand", "Unknown"),
                "price": item.get("base_price", 0),
                "stock": 1 if str(item.get("status") or "").upper() == "ACTIVE" else 0,
            }

        if products:
            return products

        laptops = _fetch_json(f"{self.laptop_service_url}/laptops/").get("data", [])
        for item in laptops if isinstance(laptops, list) else []:
            item_id = item.get("id")
            if item_id is None:
                continue
            key = f"laptop:{item_id}"
            products[key] = {
                "item_type": "laptop",
                "item_id": item_id,
                "name": item.get("name", "Unknown"),
                "brand": item.get("brand", "Unknown"),
                "price": item.get("price", 0),
                "stock": item.get("stock", 0),
            }

        mobiles = _fetch_json(f"{self.mobile_service_url}/mobiles/").get("data", [])
        for item in mobiles if isinstance(mobiles, list) else []:
            item_id = item.get("id")
            if item_id is None:
                continue
            key = f"mobile:{item_id}"
            products[key] = {
                "item_type": "mobile",
                "item_id": item_id,
                "name": item.get("name", "Unknown"),
                "brand": item.get("brand", "Unknown"),
                "price": item.get("price", 0),
                "stock": item.get("stock", 0),
            }

        return products

    def recommend(self, customer_id: int, limit: int = 20) -> List[Dict]:
        user_activities = self._load_activities(customer_id=customer_id, limit=3000)
        all_activities = self._load_activities(customer_id=None, limit=5000)
        catalog = self._load_products()

        # Personal preference by concrete product and product type.
        user_item_score: Dict[str, float] = {}
        type_preference: Dict[str, float] = {"laptop": 0.0, "mobile": 0.0}
        for act in user_activities:
            item_type = str(act.get("item_type") or "").lower()
            item_id = act.get("item_id")
            if item_type in {"laptop", "mobile"} and item_id is not None:
                key = f"{item_type}:{item_id}"
                activity_score = self._activity_score(act)
                user_item_score[key] = user_item_score.get(key, 0.0) + activity_score
                type_preference[item_type] += activity_score

        # Global trend from all users.
        global_item_score: Dict[str, float] = {}
        for act in all_activities:
            item_type = str(act.get("item_type") or "").lower()
            item_id = act.get("item_id")
            if item_type not in {"laptop", "mobile"} or item_id is None:
                continue
            key = f"{item_type}:{item_id}"
            global_item_score[key] = global_item_score.get(key, 0.0) + self._activity_score(act)

        scored: List[Dict] = []
        for key, product in catalog.items():
            item_type = product["item_type"]

            # Keep already interacted products in the candidate list.
            # Recommendation is driven by 3 behaviors: view, add-to-cart, rate.
            score = (
                0.6 * user_item_score.get(key, 0.0)
                + 0.25 * global_item_score.get(key, 0.0)
                + 0.15 * type_preference.get(item_type, 0.0)
            )

            if score <= 0:
                score = 0.01

            scored.append(
                {
                    **product,
                    "score": round(score, 4),
                    "reason": "ranked_by_user_activity",
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[: max(1, limit)]

    def recommend_graph(self, customer_id: int, limit: int = 20) -> List[Dict]:
        final_limit = max(1, limit)
        candidate_limit = min(max(final_limit * 3, 30), 200)

        graph = KBGraphRecommender(getattr(settings, "KB_SERVICE_URL", "http://kb-service:8010"))
        graph_ranked = graph.recommend_personalized(customer_id=customer_id, limit=candidate_limit)
        source_reason = "graph_personalized"
        if not graph_ranked:
            graph_ranked = graph.recommend_top_products(limit=candidate_limit)
            source_reason = "graph_top_fallback"

        catalog = self._load_products()
        by_product_id: Dict[int, Dict] = {}
        for product in catalog.values():
            item_id = product.get("item_id")
            if isinstance(item_id, int):
                by_product_id[item_id] = product

        output: List[Dict] = []
        for idx, row in enumerate(graph_ranked, start=1):
            pid = row.get("product_id")
            if pid is None:
                continue
            try:
                product_id = int(pid)
            except (TypeError, ValueError):
                continue

            catalog_product = by_product_id.get(product_id)
            if catalog_product:
                product = {
                    "item_type": catalog_product.get("item_type", "mobile"),
                    "item_id": product_id,
                    "name": catalog_product.get("name", row.get("name") or "Unknown"),
                    "brand": catalog_product.get("brand", row.get("brand") or "Unknown"),
                    "price": catalog_product.get("price", 0),
                    "stock": catalog_product.get("stock", 0),
                }
            else:
                product = {
                    "item_type": "mobile",
                    "item_id": product_id,
                    "name": row.get("name") or "Unknown",
                    "brand": row.get("brand") or "Unknown",
                    "price": 0,
                    "stock": 1,
                }

            score_value = row.get("score")
            if score_value is None:
                score_value = 1.0 / float(idx)

            output.append(
                {
                    **product,
                    "score": round(float(score_value), 6),
                    "reason": source_reason,
                }
            )

        return output[:final_limit]

    def recommend_hybrid(self, customer_id: int, limit: int = 20) -> List[Dict]:
        final_limit = max(1, limit)
        candidate_limit = min(max(final_limit * 3, 30), 200)

        activity_ranked = self.recommend(customer_id=customer_id, limit=candidate_limit)

        graph = KBGraphRecommender(getattr(settings, "KB_SERVICE_URL", "http://kb-service:8010"))
        graph_ranked = graph.recommend_personalized(customer_id=customer_id, limit=candidate_limit)
        if not graph_ranked:
            graph_ranked = graph.recommend_top_products(limit=candidate_limit)

        catalog = self._load_products()
        by_product_id: Dict[int, Dict] = {}
        for product in catalog.values():
            item_id = product.get("item_id")
            if isinstance(item_id, int):
                by_product_id[item_id] = product

        merged: Dict[int, Dict] = {}

        for item in activity_ranked:
            item_id = item.get("item_id")
            if item_id is None:
                continue
            merged[int(item_id)] = {
                "item_type": item.get("item_type", "mobile"),
                "item_id": int(item_id),
                "name": item.get("name", "Unknown"),
                "brand": item.get("brand", "Unknown"),
                "price": item.get("price", 0),
                "stock": item.get("stock", 0),
            }

        for row in graph_ranked:
            pid = row.get("product_id")
            if pid is None:
                continue
            try:
                product_id = int(pid)
            except (TypeError, ValueError):
                continue

            existing = merged.get(product_id)
            if existing:
                continue

            catalog_product = by_product_id.get(product_id)
            if catalog_product:
                merged[product_id] = {
                    "item_type": catalog_product.get("item_type", "mobile"),
                    "item_id": product_id,
                    "name": catalog_product.get("name", row.get("name") or "Unknown"),
                    "brand": catalog_product.get("brand", row.get("brand") or "Unknown"),
                    "price": catalog_product.get("price", 0),
                    "stock": catalog_product.get("stock", 0),
                }
            else:
                merged[product_id] = {
                    "item_type": "mobile",
                    "item_id": product_id,
                    "name": row.get("name") or "Unknown",
                    "brand": row.get("brand") or "Unknown",
                    "price": 0,
                    "stock": 1,
                }

        rank_score: Dict[int, float] = {}
        fusion_k = 60.0
        activity_weight = 0.65
        graph_weight = 0.35

        for idx, item in enumerate(activity_ranked, start=1):
            item_id = item.get("item_id")
            if item_id is None:
                continue
            rank_score[int(item_id)] = rank_score.get(int(item_id), 0.0) + activity_weight / (fusion_k + idx)

        for idx, row in enumerate(graph_ranked, start=1):
            pid = row.get("product_id")
            if pid is None:
                continue
            try:
                product_id = int(pid)
            except (TypeError, ValueError):
                continue
            rank_score[product_id] = rank_score.get(product_id, 0.0) + graph_weight / (fusion_k + idx)

        if not rank_score:
            return activity_ranked[:final_limit]

        output: List[Dict] = []
        for product_id, score in sorted(rank_score.items(), key=lambda kv: kv[1], reverse=True):
            product = merged.get(product_id)
            if not product:
                continue
            output.append(
                {
                    **product,
                    "score": round(float(score), 6),
                    "reason": "hybrid_activity_graph",
                }
            )

        return output[:final_limit]

    def recommend_from_graph(self, product_id: int, mode: str = "same_category", limit: int = 10):
        kb_url = getattr(settings, "KB_SERVICE_URL", "http://kb-service:8010")
        graph = KBGraphRecommender(kb_url)
        if mode == "same_category":
            return graph.recommend_same_category(product_id, limit)
        elif mode == "also_bought":
            return graph.recommend_also_bought(product_id, limit)
        elif mode == "top":
            return graph.recommend_top_products(limit)
        else:
            return []


class KBGraphRecommender:
    def __init__(self, kb_service_url: str):
        self.kb_service_url = kb_service_url.rstrip("/")

    def _safe_recommend_get(self, url: str, timeout: int = 10):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8") or "{}")
                data = payload.get("recommendations", [])
                return data if isinstance(data, list) else []
        except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError, TimeoutError, ValueError):
            return []

    def recommend_same_category(self, product_id: int, limit: int = 10):
        url = f"{self.kb_service_url}/api/kb/recommend/?product_id={product_id}&mode=same_category&limit={limit}"
        return self._safe_recommend_get(url)

    def recommend_also_bought(self, product_id: int, limit: int = 10):
        url = f"{self.kb_service_url}/api/kb/recommend/?product_id={product_id}&mode=also_bought&limit={limit}"
        return self._safe_recommend_get(url)

    def recommend_personalized(self, customer_id: int, limit: int = 10):
        url = f"{self.kb_service_url}/api/kb/recommend/?customer_id={customer_id}&mode=personalized&limit={limit}"
        return self._safe_recommend_get(url)

    def recommend_top_products(self, limit: int = 10):
        url = f"{self.kb_service_url}/api/kb/recommend/top/?limit={limit}"
        return self._safe_recommend_get(url)
