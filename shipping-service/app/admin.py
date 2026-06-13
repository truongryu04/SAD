from django.contrib import admin

from .models import Shipment, ShippingMethod


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("id", "order_id", "status", "created_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("order_id",)


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "fee", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
