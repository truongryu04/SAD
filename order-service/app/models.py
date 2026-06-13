from django.db import models


class Order(models.Model):
    PAYMENT_METHOD_COD = 'COD'
    PAYMENT_METHOD_CARD = 'CARD'
    PAYMENT_METHOD_VNPAY = 'VNPAY'
    PAYMENT_METHOD_MOMO = 'MOMO'
    PAYMENT_METHOD_CHOICES = (
        (PAYMENT_METHOD_COD, 'Cash On Delivery'),
        (PAYMENT_METHOD_CARD, 'Card'),
        (PAYMENT_METHOD_VNPAY, 'VNPay'),
        (PAYMENT_METHOD_MOMO, 'MoMo'),
    )

    PAYMENT_STATUS_PENDING = 'PENDING'
    PAYMENT_STATUS_PAID = 'PAID'
    PAYMENT_STATUS_FAILED = 'FAILED'
    PAYMENT_STATUS_CHOICES = (
        (PAYMENT_STATUS_PENDING, 'Pending'),
        (PAYMENT_STATUS_PAID, 'Paid'),
        (PAYMENT_STATUS_FAILED, 'Failed'),
    )

    ORDER_STATUS_CREATED = 'CREATED'
    ORDER_STATUS_CONFIRMED = 'CONFIRMED'
    ORDER_STATUS_CANCELLED = 'CANCELLED'
    ORDER_STATUS_CHOICES = (
        (ORDER_STATUS_CREATED, 'Created'),
        (ORDER_STATUS_CONFIRMED, 'Confirmed'),
        (ORDER_STATUS_CANCELLED, 'Cancelled'),
    )

    customer_id = models.IntegerField(db_index=True)
    cart_id = models.IntegerField(null=True, blank=True)
    phone = models.CharField(max_length=32, blank=True, default="")
    shipping_address = models.TextField(blank=True, default="")
    shipping_method_code = models.CharField(max_length=50, blank=True, default="")
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default=PAYMENT_METHOD_COD)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_PENDING)
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default=ORDER_STATUS_CREATED)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'Order #{self.id} - customer {self.customer_id}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=20)
    item_id = models.IntegerField()
    item_name = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self) -> str:
        return f'OrderItem #{self.id} - order {self.order_id}'
