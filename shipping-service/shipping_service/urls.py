from django.contrib import admin
from django.urls import path

from app.views import (
    ShippingCreateView,
    ShippingStatusView,
    ShippingMethodListCreateView,
    ShippingMethodDetailView,
)


urlpatterns = [
    path("admin/", admin.site.urls),
    # Support both with and without trailing slash.
    path("shipping/create", ShippingCreateView.as_view(), name="shipping-create"),
    path("shipping/create/", ShippingCreateView.as_view(), name="shipping-create-slash"),
    path("shipping/status", ShippingStatusView.as_view(), name="shipping-status"),
    path("shipping/status/", ShippingStatusView.as_view(), name="shipping-status-slash"),

    path("shipping/methods", ShippingMethodListCreateView.as_view(), name="shipping-methods"),
    path("shipping/methods/", ShippingMethodListCreateView.as_view(), name="shipping-methods-slash"),
    path("shipping/methods/<int:pk>", ShippingMethodDetailView.as_view(), name="shipping-method-detail"),
    path("shipping/methods/<int:pk>/", ShippingMethodDetailView.as_view(), name="shipping-method-detail-slash"),
]
