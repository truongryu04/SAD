from rest_framework import serializers
from .models import Attribute, CategoryAttribute, ProductAttributeValue

class AttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = ['id', 'name', 'data_type', 'unit', 'created_at']

class CategoryAttributeSerializer(serializers.ModelSerializer):
    attribute = serializers.SerializerMethodField(read_only=True)

    def get_attribute(self, obj):
        attr = Attribute.objects.filter(id=obj.attribute_id).first()
        if attr is None:
            return None
        return AttributeSerializer(attr).data

    def validate_attribute_id(self, value):
        if not Attribute.objects.filter(id=value).exists():
            raise serializers.ValidationError('attribute_id does not exist.')
        return value

    class Meta:
        model = CategoryAttribute
        fields = ['id', 'category_id', 'attribute_id', 'is_required', 'display_order', 'attribute']

class ProductAttributeValueSerializer(serializers.ModelSerializer):
    attribute = serializers.SerializerMethodField(read_only=True)

    def get_attribute(self, obj):
        attr = Attribute.objects.filter(id=obj.attribute_id).first()
        if attr is None:
            return None
        return AttributeSerializer(attr).data

    def validate_attribute_id(self, value):
        if not Attribute.objects.filter(id=value).exists():
            raise serializers.ValidationError('attribute_id does not exist.')
        return value

    class Meta:
        model = ProductAttributeValue
        fields = ['id', 'product_id', 'attribute_id', 'value', 'attribute']
