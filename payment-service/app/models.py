from django.db import models


class Payment(models.Model):
    STATUS_PENDING = "Pending"
    STATUS_SUCCESS = "Success"
    STATUS_FAILED = "Failed"

    PAYMENT_STATUS = [
        (STATUS_PENDING, STATUS_PENDING),
        (STATUS_SUCCESS, STATUS_SUCCESS),
        (STATUS_FAILED, STATUS_FAILED),
    ]

    order_id = models.IntegerField(db_index=True)
    amount = models.FloatField()
    status = models.CharField(max_length=50, choices=PAYMENT_STATUS, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Payment(order_id={self.order_id}, status={self.status})"


class PaymentMethod(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"PaymentMethod(code={self.code}, active={self.is_active})"
