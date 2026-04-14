from django.db import models

class Inventory(models.Model):
    variant_id = models.IntegerField()
    quantity = models.PositiveIntegerField(default=0)
    reserved_quantity = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

class StockTransaction(models.Model):
    variant_id = models.IntegerField()
    change_quantity = models.IntegerField()
    type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
