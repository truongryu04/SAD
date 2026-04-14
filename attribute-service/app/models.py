from django.db import models

class Attribute(models.Model):
    name = models.CharField(max_length=200)
    data_type = models.CharField(max_length=50)
    unit = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name"], name="uniq_attribute_name"),
        ]

    def __str__(self):
        return self.name

class CategoryAttribute(models.Model):
    category_id = models.IntegerField()
    attribute_id = models.IntegerField()
    is_required = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["category_id", "attribute_id"], name="uniq_category_attribute"),
        ]
        ordering = ["display_order", "id"]

    def __str__(self):
        return f"category={self.category_id}, attribute={self.attribute_id}"

class ProductAttributeValue(models.Model):
    product_id = models.IntegerField()
    attribute_id = models.IntegerField()
    value = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product_id", "attribute_id"], name="uniq_product_attribute_value"),
        ]

    def __str__(self):
        return f"product={self.product_id}, attribute={self.attribute_id}"
