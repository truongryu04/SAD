import json
import math
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Dict, List


def _fetch_json(url: str, timeout: int = 20) -> Dict:
    req = urllib.request.Request(url=url, headers={"Accept": "application/json"}, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")
        return json.loads(raw or "{}")


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
        laptop_service_url: str,
        mobile_service_url: str,
        decay_days: int = 30,
    ) -> None:
        self.customer_service_url = customer_service_url.rstrip("/")
        self.laptop_service_url = laptop_service_url.rstrip("/")
        self.mobile_service_url = mobile_service_url.rstrip("/")
        self.decay_days = decay_days

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
