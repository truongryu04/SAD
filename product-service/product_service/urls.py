from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from app.views import (
    CategoryProductsView,
    CategoryListCreateView,
    CategoryRetrieveUpdateDestroyView,
    ProductListCreateView,
    ProductRetrieveUpdateDestroyView,
)

from app.legacy_api import (
    LegacyAttributeListView,
    LegacyCategoryAttributeListView,
    LegacyCategoryAttributesView,
    LegacyCategoryDetailView,
    LegacyCategoryListView,
    LegacyProductAttributeValueListView,
    LegacyProductDetailView,
    LegacyProductListView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # Legacy compatibility APIs used by gateway/staff/ai/kb services.
    path('api/products/', LegacyProductListView.as_view(), name='legacy-api-products'),
    path('api/products/<int:pk>/', LegacyProductDetailView.as_view(), name='legacy-api-product-detail'),
    path('api/categories/', LegacyCategoryListView.as_view(), name='legacy-api-categories'),
    path('api/categories/<int:pk>/', LegacyCategoryDetailView.as_view(), name='legacy-api-category-detail'),
    path('api/categories/<int:pk>/attributes/', LegacyCategoryAttributesView.as_view(), name='legacy-api-category-attributes'),
    path('api/attributes/', LegacyAttributeListView.as_view(), name='legacy-api-attributes'),
    path('api/category-attributes/', LegacyCategoryAttributeListView.as_view(), name='legacy-api-category-attributes-list'),
    path('api/product-attribute-values/', LegacyProductAttributeValueListView.as_view(), name='legacy-api-product-attribute-values'),

    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductRetrieveUpdateDestroyView.as_view(), name='product-detail'),
    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', CategoryRetrieveUpdateDestroyView.as_view(), name='category-detail'),
    path('categories/<int:pk>/products/', CategoryProductsView.as_view(), name='category-products'),
    path('ui/products/new/', TemplateView.as_view(template_name='product_form.html'), name='product-form'),
]
