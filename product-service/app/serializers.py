from rest_framework import serializers
from .models import Product, ProductVariant

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'product', 'sku', 'price', 'status', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True, source='productvariant_set')
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'category_id', 'brand', 'base_price', 'status', 'created_at', 'updated_at', 'variants']
