"""
URL configuration for ai_service project.
"""

from django.contrib import admin
from django.urls import path

from app.views import AIRequestView, HealthView, NovaChatbotView, ProductRecommendationView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ai/requests/', AIRequestView.as_view(), name='ai-request-list-create'),
    path('ai/requests/<int:request_id>/', AIRequestView.as_view(), name='ai-request-detail'),
    path('ai/recommendations/<int:customer_id>/', ProductRecommendationView.as_view(), name='product-recommendations'),
    path('ai/chat/', NovaChatbotView.as_view(), name='nova-chatbot'),
    path('health/', HealthView.as_view(), name='health'),
]
