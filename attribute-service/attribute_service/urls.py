from django.contrib import admin
from django.urls import path
from app.views import (
    AttributeListCreateView,
    AttributeRetrieveUpdateDestroyView,
    CategoryAttributeListCreateView,
    CategoryAttributeDetailView,
    ProductAttributeValueListCreateView,
    ProductAttributeValueDetailView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/attributes/', AttributeListCreateView.as_view(), name='attribute-list-create'),
    path('api/attributes/<int:pk>/', AttributeRetrieveUpdateDestroyView.as_view(), name='attribute-detail'),
    path('api/category-attributes/', CategoryAttributeListCreateView.as_view(), name='category-attribute-list-create'),
    path('api/category-attributes/<int:pk>/', CategoryAttributeDetailView.as_view(), name='category-attribute-detail'),
    path('api/product-attribute-values/', ProductAttributeValueListCreateView.as_view(), name='product-attribute-value-list-create'),
    path('api/product-attribute-values/<int:pk>/', ProductAttributeValueDetailView.as_view(), name='product-attribute-value-detail'),
]
