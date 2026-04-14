
from rest_framework import generics
from .models import Attribute, CategoryAttribute, ProductAttributeValue
from .serializers import AttributeSerializer, CategoryAttributeSerializer, ProductAttributeValueSerializer

# Attribute APIs
class AttributeListCreateView(generics.ListCreateAPIView):
	queryset = Attribute.objects.all()
	serializer_class = AttributeSerializer

class AttributeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
	queryset = Attribute.objects.all()
	serializer_class = AttributeSerializer

# CategoryAttribute APIs
class CategoryAttributeListCreateView(generics.ListCreateAPIView):
	serializer_class = CategoryAttributeSerializer

	def get_queryset(self):
		queryset = CategoryAttribute.objects.all()
		category_id = self.request.GET.get('category_id')
		attribute_id = self.request.GET.get('attribute_id')
		if category_id is not None:
			queryset = queryset.filter(category_id=category_id)
		if attribute_id is not None:
			queryset = queryset.filter(attribute_id=attribute_id)
		return queryset


class CategoryAttributeDetailView(generics.RetrieveUpdateDestroyAPIView):
	queryset = CategoryAttribute.objects.all()
	serializer_class = CategoryAttributeSerializer

# ProductAttributeValue APIs
class ProductAttributeValueListCreateView(generics.ListCreateAPIView):
	serializer_class = ProductAttributeValueSerializer

	def get_queryset(self):
		queryset = ProductAttributeValue.objects.all()
		product_id = self.request.GET.get('product_id')
		attribute_id = self.request.GET.get('attribute_id')
		if product_id is not None:
			queryset = queryset.filter(product_id=product_id)
		if attribute_id is not None:
			queryset = queryset.filter(attribute_id=attribute_id)
		return queryset


class ProductAttributeValueDetailView(generics.RetrieveUpdateDestroyAPIView):
	queryset = ProductAttributeValue.objects.all()
	serializer_class = ProductAttributeValueSerializer
