from django.db import models
from pgvector.django import VectorField


class AIRequest(models.Model):
    prompt = models.TextField()
    response = models.TextField(blank=True)
    model_name = models.CharField(max_length=100, default="demo-model")
    status = models.CharField(max_length=30, default="completed")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"AIRequest #{self.id}"


class ProductVectorIndex(models.Model):
    item_type = models.CharField(max_length=20)
    item_id = models.PositiveIntegerField()
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=255, blank=True)
    price = models.CharField(max_length=80, blank=True)
    stock = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    content_text = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    embedding = VectorField(dimensions=256)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["item_type", "item_id"], name="uniq_product_vector_item"),
        ]
        indexes = [
            models.Index(fields=["item_type", "item_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.item_type}:{self.item_id}"
