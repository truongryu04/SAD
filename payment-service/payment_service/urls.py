from django.contrib import admin
from django.urls import path

from app.views import (
    PaymentPayView,
    PaymentStatusView,
    PaymentMethodListCreateView,
    PaymentMethodDetailView,
)


urlpatterns = [
    path("admin/", admin.site.urls),
    # Support both with and without trailing slash.
    path("payment/pay", PaymentPayView.as_view(), name="payment-pay"),
    path("payment/pay/", PaymentPayView.as_view(), name="payment-pay-slash"),
    path("payment/status", PaymentStatusView.as_view(), name="payment-status"),
    path("payment/status/", PaymentStatusView.as_view(), name="payment-status-slash"),

    path("payment/methods", PaymentMethodListCreateView.as_view(), name="payment-methods"),
    path("payment/methods/", PaymentMethodListCreateView.as_view(), name="payment-methods-slash"),
    path("payment/methods/<int:pk>", PaymentMethodDetailView.as_view(), name="payment-method-detail"),
    path("payment/methods/<int:pk>/", PaymentMethodDetailView.as_view(), name="payment-method-detail-slash"),
]
