from django.contrib import admin
from django.urls import path
from app.views import (
    CategoryAttributeSchemaView,
    ProductListCreateView,
    ProductRetrieveUpdateDestroyView,
    ProductVariantListCreateView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('api/products/<int:pk>/', ProductRetrieveUpdateDestroyView.as_view(), name='product-detail'),
    path('api/categories/<int:category_id>/attributes/', CategoryAttributeSchemaView.as_view(), name='category-attribute-schema'),
    path('api/products/<int:id>/variants/', ProductVariantListCreateView.as_view(), name='product-variant-list-create'),
]
