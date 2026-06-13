from django.db import models


class Shipment(models.Model):
    STATUS_PROCESSING = "Processing"
    STATUS_SHIPPING = "Shipping"
    STATUS_DELIVERED = "Delivered"

    SHIPPING_STATUS = [
        (STATUS_PROCESSING, STATUS_PROCESSING),
        (STATUS_SHIPPING, STATUS_SHIPPING),
        (STATUS_DELIVERED, STATUS_DELIVERED),
    ]

    order_id = models.IntegerField(db_index=True)
    address = models.TextField()
    status = models.CharField(max_length=50, choices=SHIPPING_STATUS, default=STATUS_PROCESSING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Shipment(order_id={self.order_id}, status={self.status})"


class ShippingMethod(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    fee = models.FloatField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"ShippingMethod(code={self.code}, active={self.is_active})"
