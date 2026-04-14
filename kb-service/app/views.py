from rest_framework.response import Response
from rest_framework.views import APIView

from .collector import run_phase1_collection

from .models import KBCategory, KBInventory, KBProduct, KBSyncCheckpoint
from .graph_writer import (
    recommend_same_category,
    recommend_also_bought,
    recommend_top_products,
    recommend_personalized,
    sync_user_behavior,
)

# API: /api/kb/recommend/
from rest_framework.decorators import api_view

@api_view(["GET"])
def KBRecommendView(request):
    product_id = request.GET.get("product_id")
    customer_id = request.GET.get("customer_id")
    mode = request.GET.get("mode", "same_category")
    price_range = (request.GET.get("price_range") or "").strip().lower()
    gender = (request.GET.get("gender") or "").strip().lower()
    limit = int(request.GET.get("limit", 10))
    if mode in ("same_category", "also_bought") and not product_id:
        return Response({"error": "product_id is required"}, status=400)
    if mode == "same_category":
        data = recommend_same_category(
            int(product_id),
            limit=limit,
            price_range=price_range,
            gender=gender,
        )
    elif mode == "also_bought":
        data = recommend_also_bought(
            int(product_id),
            limit=limit,
            price_range=price_range,
            gender=gender,
        )
    elif mode == "personalized":
        if not customer_id:
            return Response({"error": "customer_id is required for personalized mode"}, status=400)
        data = recommend_personalized(
            int(customer_id),
            limit=limit,
            price_range=price_range,
            gender=gender,
        )
    else:
        return Response({"error": "mode not supported"}, status=400)
    return Response({"recommendations": data})

@api_view(["GET"])
def KBRecommendTopView(request):
    price_range = (request.GET.get("price_range") or "").strip().lower()
    gender = (request.GET.get("gender") or "").strip().lower()
    limit = int(request.GET.get("limit", 10))
    data = recommend_top_products(limit=limit, price_range=price_range, gender=gender)
    return Response({"recommendations": data})


@api_view(["POST"])
def KBBehaviorEventView(request):
    payload = request.data if isinstance(request.data, dict) else {}
    events = payload.get("events") if isinstance(payload.get("events"), list) else [payload]

    accepted = 0
    errors = []
    for idx, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append({"index": idx, "error": "event must be an object"})
            continue
        if event.get("customer_id") is None:
            errors.append({"index": idx, "error": "customer_id is required"})
            continue
        if not event.get("event_type"):
            errors.append({"index": idx, "error": "event_type is required"})
            continue
        try:
            sync_user_behavior(event)
            accepted += 1
        except (TypeError, ValueError) as exc:
            errors.append({"index": idx, "error": str(exc)})

    status_code = 200 if not errors else (207 if accepted else 400)
    return Response(
        {
            "accepted": accepted,
            "errors": errors,
        },
        status=status_code,
    )

def _tokenize(text):
    return [token for token in str(text or "").lower().split() if token]


class KBHealthView(APIView):
    def get(self, request):
        return Response(
            {
                "status": "ok",
                "counts": {
                    "products": KBProduct.objects.count(),
                    "categories": KBCategory.objects.count(),
                    "inventories": KBInventory.objects.count(),
                    "checkpoints": KBSyncCheckpoint.objects.count(),
                },
            }
        )


class KBCollectView(APIView):
    def post(self, request):
        result = run_phase1_collection()
        return Response(
            {
                "message": "Phase 1 collection completed.",
                "result": result,
            }
        )


class KBSemanticSearchView(APIView):
    def post(self, request):
        query = (request.data.get("query") or "").strip()
        limit = int(request.data.get("limit") or 10)
        limit = max(1, min(limit, 50))

        if not query:
            return Response({"error": "query is required."}, status=400)

        query_tokens = set(_tokenize(query))
        if not query_tokens:
            return Response({"error": "query is invalid."}, status=400)

        # Lọc sản phẩm ACTIVE và còn tồn kho
        inventory_map = {inv.variant_id: inv.quantity - inv.reserved_quantity for inv in KBInventory.objects.all()}
        scored = []
        for product in KBProduct.objects.filter(status="ACTIVE"):
            qty = inventory_map.get(product.external_id, 0)
            if qty <= 0:
                continue
            haystack_tokens = set(_tokenize(product.normalized_text))
            overlap = query_tokens.intersection(haystack_tokens)
            if not overlap:
                continue

            score = len(overlap) / max(1, len(query_tokens))
            scored.append(
                {
                    "product_id": product.external_id,
                    "name": product.name,
                    "brand": product.brand,
                    "category": product.category_name,
                    "price": str(product.base_price),
                    "score": round(score, 4),
                    "quantity": qty,
                }
            )

        scored.sort(key=lambda item: item["score"], reverse=True)
        data = scored[:limit]

        return Response(
            {
                "query": query,
                "count": len(data),
                "data": data,
            }
        )


# Endpoint: /api/kb/sync/status/
class KBSyncStatusView(APIView):
    def get(self, request):
        checkpoints = KBSyncCheckpoint.objects.all()
        data = []
        for cp in checkpoints:
            data.append({
                "source_name": cp.source_name,
                "records_synced": cp.records_synced,
                "last_success_at": cp.last_success_at,
                "last_error": cp.last_error,
                "updated_at": cp.updated_at,
            })
        return Response({
            "checkpoints": data,
            "counts": {
                "products": KBProduct.objects.count(),
                "categories": KBCategory.objects.count(),
                "inventories": KBInventory.objects.count(),
            }
        })
