from rest_framework import serializers
from .models import Inventory, StockTransaction

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['id', 'variant_id', 'quantity', 'reserved_quantity', 'updated_at']

class StockTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockTransaction
        fields = ['id', 'variant_id', 'change_quantity', 'type', 'created_at']
