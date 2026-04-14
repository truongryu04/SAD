import json

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import AIRequest
from .chatbot import EcomRAGChatbot
from .recommender import ProductRecommenderService


def _parse_json_body(request):
    raw_body = request.body or b"{}"
    if isinstance(raw_body, str):
        raw_text = raw_body
    else:
        raw_text = raw_body.decode("utf-8", errors="replace")

    try:
        return json.loads(raw_text or "{}"), None
    except json.JSONDecodeError:
        return None, JsonResponse({"error": "Invalid JSON body."}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class AIRequestView(View):
    def get(self, request, request_id=None):
        if request_id is None:
            query = (request.GET.get("q") or "").strip()
            queryset = AIRequest.objects.all().order_by("-id")
            if query:
                queryset = queryset.filter(prompt__icontains=query)

            data = list(
                queryset.values(
                    "id",
                    "prompt",
                    "response",
                    "model_name",
                    "status",
                    "created_at",
                )
            )
            return JsonResponse({"count": len(data), "data": data})

        item = AIRequest.objects.filter(id=request_id).values(
            "id",
            "prompt",
            "response",
            "model_name",
            "status",
            "created_at",
        ).first()
        if item is None:
            return JsonResponse({"error": "AI request not found."}, status=404)
        return JsonResponse(item)

    def post(self, request, request_id=None):
        if request_id is not None:
            return JsonResponse({"error": "Method not allowed."}, status=405)

        body, error = _parse_json_body(request)
        if error:
            return error

        prompt = (body.get("prompt") or "").strip()
        model_name = (body.get("model_name") or "demo-model").strip()

        if not prompt:
            return JsonResponse({"error": "prompt is required."}, status=400)

        # Placeholder response so the service works as a standalone scaffold.
        response_text = f"Echo: {prompt}"

        obj = AIRequest.objects.create(
            prompt=prompt,
            response=response_text,
            model_name=model_name,
            status="completed",
        )
        return JsonResponse({"message": "AI request created.", "id": obj.id}, status=201)


class HealthView(View):
    def get(self, request):
        return JsonResponse({"status": "ok"})


class AIChatUiView(View):
    def get(self, request):
        customer_id_raw = request.GET.get("customer_id", "0")
        try:
            customer_id = max(0, int(customer_id_raw))
        except (TypeError, ValueError):
            customer_id = 0

        return render(
            request,
            "app/chat_ui.html",
            {
                "customer_id": customer_id,
            },
        )


class ProductRecommendationView(View):
    def get(self, request, customer_id):
        limit_raw = request.GET.get("limit", "20")
        mode = (request.GET.get("mode") or "hybrid").strip().lower()
        try:
            limit = int(limit_raw)
        except (TypeError, ValueError):
            return JsonResponse({"error": "limit must be an integer."}, status=400)

        if limit <= 0:
            return JsonResponse({"error": "limit must be > 0."}, status=400)
        limit = min(limit, 100)

        recommender = ProductRecommenderService(
            customer_service_url=settings.CUSTOMER_SERVICE_URL,
            product_service_url=settings.PRODUCT_SERVICE_URL,
            laptop_service_url=settings.LAPTOP_SERVICE_URL,
            mobile_service_url=settings.MOBILE_SERVICE_URL,
        )

        try:
            if mode == "activity":
                recommendations = recommender.recommend(customer_id=customer_id, limit=limit)
            elif mode == "graph":
                recommendations = recommender.recommend_graph(customer_id=customer_id, limit=limit)
            elif mode == "hybrid":
                recommendations = recommender.recommend_hybrid(customer_id=customer_id, limit=limit)
            else:
                return JsonResponse({"error": "mode must be one of: hybrid, activity, graph."}, status=400)
        except Exception as ex:
            return JsonResponse({"error": f"Failed to generate recommendations: {ex}"}, status=502)

        return JsonResponse(
            {
                "customer_id": customer_id,
                "mode": mode,
                "count": len(recommendations),
                "data": recommendations,
            }
        )


# Recommendation từ graph (ví dụ demo)
@method_decorator(csrf_exempt, name="dispatch")
class RecommendationFromGraphView(View):
    def get(self, request):
        product_id = int(request.GET.get("product_id", 0))
        mode = request.GET.get("mode", "same_category")
        limit = int(request.GET.get("limit", 10))
        recommender = ProductRecommenderService(
            customer_service_url=settings.CUSTOMER_SERVICE_URL,
            product_service_url=settings.PRODUCT_SERVICE_URL,
            laptop_service_url=settings.LAPTOP_SERVICE_URL,
            mobile_service_url=settings.MOBILE_SERVICE_URL,
        )
        data = recommender.recommend_from_graph(product_id, mode, limit)
        return JsonResponse({"recommendations": data})


@method_decorator(csrf_exempt, name="dispatch")
class NovaChatbotView(View):
    def post(self, request):
        body, error = _parse_json_body(request)
        if error:
            return error

        question = (body.get("question") or "").strip()
        if not question:
            return JsonResponse({"error": "question is required."}, status=400)

        top_k_raw = body.get("top_k", 8)
        try:
            top_k = int(top_k_raw)
        except (TypeError, ValueError):
            return JsonResponse({"error": "top_k must be an integer."}, status=400)

        if top_k <= 0:
            return JsonResponse({"error": "top_k must be > 0."}, status=400)
        top_k = min(top_k, 15)

        bot = EcomRAGChatbot(
            product_service_url=settings.PRODUCT_SERVICE_URL,
            ollama_base_url=settings.OLLAMA_BASE_URL,
            ollama_model=settings.OLLAMA_MODEL,
        )

        try:
            result = bot.chat(question, top_k=top_k)
        except Exception as ex:
            return JsonResponse({"error": f"Chatbot failed: {ex}"}, status=502)

        obj = AIRequest.objects.create(
            prompt=question,
            response=result.get("answer", ""),
            model_name=settings.OLLAMA_MODEL,
            status="completed",
        )

        return JsonResponse(
            {
                "message": "Chat response generated.",
                "request_id": obj.id,
                "model": settings.OLLAMA_MODEL,
                "answer": result.get("answer", ""),
                "sources": result.get("sources", []),
                "context_count": result.get("context_count", 0),
            }
        )
