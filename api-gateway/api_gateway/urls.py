"""
URL configuration for api_gateway project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from app.views import (
    AIChatProxyView,
    AIRecommendationProxyView,
    AttributeProxyView,
    ApiRoleRegisterView,
    CategoryAttributeProxyView,
    CategoryDetailProxyView,
    CustomerAccountDetailProxyView,
    CustomerAccountProxyView,
    CategoryProxyView,
    KBCollectProxyView,
    KBHealthProxyView,
    KBSemanticSearchProxyView,
    CustomerProductsPageView,
    CustomerProductDetailPageView,
    CustomerActivityProxyView,
    ApiRoleLoginView,
    CustomerCartProxyView,
    CustomerCartItemProxyView,
    CustomerCartItemDetailProxyView,
    CustomerCartPageView,
    CustomerDashboardView,
    CustomerLoginProxyView,
    CustomerRatingProxyView,
    CustomerRegisterProxyView,
    CustomerSearchProxyView,
    LaptopProxyView,
    LoginPageView,
    LogoutView,
    MobileProxyView,
    OrderCheckoutProxyView,
    OrderProxyView,
    ProductProxyView,
    ProductDetailProxyView,
    ProductCategoryAttributesProxyView,
    ProductAttributeValueProxyView,
    RegisterPageView,
    StaffDashboardView,
    StaffCategoryPageView,
    StaffCustomerPageView,
    StaffOrderPageView,
    StaffProductPageView,
    StaffItemDetailProxyView,
    StaffItemProxyView,
    StaffLoginProxyView,
    StaffRegisterProxyView,
    UiLoginView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', LoginPageView.as_view(), name='login-page'),
    path('ui/register/', RegisterPageView.as_view(), name='register-page'),
    path('ui/login/', UiLoginView.as_view(), name='ui-login'),
    path('ui/logout/', LogoutView.as_view(), name='ui-logout'),
    path('ui/customer/', CustomerDashboardView.as_view(), name='customer-dashboard'),
    path('ui/customer/products/', CustomerProductsPageView.as_view(), name='customer-products-page'),
    path('ui/customer/products/<int:product_id>/', CustomerProductDetailPageView.as_view(), name='customer-product-detail-page'),
    path('ui/customer/cart/', CustomerCartPageView.as_view(), name='customer-cart-page'),
    path('ui/staff/', StaffDashboardView.as_view(), name='staff-dashboard'),
    path('ui/staff/products/', StaffProductPageView.as_view(), name='staff-products-page'),
    path('ui/staff/categories/', StaffCategoryPageView.as_view(), name='staff-categories-page'),
    path('ui/staff/orders/', StaffOrderPageView.as_view(), name='staff-orders-page'),
    path('ui/staff/customers/', StaffCustomerPageView.as_view(), name='staff-customers-page'),
    path('api/auth/register/', ApiRoleRegisterView.as_view(), name='api-role-register'),
    path('api/auth/login/', ApiRoleLoginView.as_view(), name='api-role-login'),
    path('api/customer/register/', CustomerRegisterProxyView.as_view(), name='api-customer-register'),
    path('api/customer/login/', CustomerLoginProxyView.as_view(), name='api-customer-login'),
    path('api/customer/accounts/', CustomerAccountProxyView.as_view(), name='api-customer-accounts'),
    path('api/customer/accounts/<int:customer_id>/', CustomerAccountDetailProxyView.as_view(), name='api-customer-account-detail'),
    path('api/customer/carts/', CustomerCartProxyView.as_view(), name='api-customer-carts'),
    path('api/customer/cart-items/', CustomerCartItemProxyView.as_view(), name='api-customer-cart-items'),
    path('api/customer/cart-items/<int:cart_item_id>/', CustomerCartItemDetailProxyView.as_view(), name='api-customer-cart-item-detail'),
    path('api/customer/activities/', CustomerActivityProxyView.as_view(), name='api-customer-activities'),
    path('api/customer/ratings/', CustomerRatingProxyView.as_view(), name='api-customer-ratings'),
    path('api/customer/search/', CustomerSearchProxyView.as_view(), name='api-customer-search'),
    path('api/orders/checkout/', OrderCheckoutProxyView.as_view(), name='api-orders-checkout'),
    path('api/orders/', OrderProxyView.as_view(), name='api-orders'),
    path('api/products/', ProductProxyView.as_view(), name='api-products'),
    path('api/products/<int:product_id>/', ProductDetailProxyView.as_view(), name='api-product-detail'),
    path('api/products/category-schema/<int:category_id>/', ProductCategoryAttributesProxyView.as_view(), name='api-products-category-schema'),
    path('api/kb/health/', KBHealthProxyView.as_view(), name='api-kb-health'),
    path('api/kb/collect/', KBCollectProxyView.as_view(), name='api-kb-collect'),
    path('api/kb/search/semantic/', KBSemanticSearchProxyView.as_view(), name='api-kb-search-semantic'),
    path('api/categories/', CategoryProxyView.as_view(), name='api-categories'),
    path('api/categories/<int:category_id>/', CategoryDetailProxyView.as_view(), name='api-category-detail'),
    path('api/attributes/', AttributeProxyView.as_view(), name='api-attributes'),
    path('api/category-attributes/', CategoryAttributeProxyView.as_view(), name='api-category-attributes'),
    path('api/product-attribute-values/', ProductAttributeValueProxyView.as_view(), name='api-product-attribute-values'),
    path('api/ai/chat/', AIChatProxyView.as_view(), name='api-ai-chat'),
    path('api/ai/recommendations/<int:customer_id>/', AIRecommendationProxyView.as_view(), name='api-ai-recommendations'),
    path('api/staff/register/', StaffRegisterProxyView.as_view(), name='api-staff-register'),
    path('api/staff/login/', StaffLoginProxyView.as_view(), name='api-staff-login'),
    path('api/staff/items/', StaffItemProxyView.as_view(), name='api-staff-items'),
    path('api/staff/items/<int:item_id>/', StaffItemDetailProxyView.as_view(), name='api-staff-item-detail'),
    path('api/laptops/', LaptopProxyView.as_view(), name='api-laptops'),
    path('api/laptops/<int:laptop_id>/', LaptopProxyView.as_view(), name='api-laptop-detail'),
    path('api/mobiles/', MobileProxyView.as_view(), name='api-mobiles'),
    path('api/mobiles/<int:mobile_id>/', MobileProxyView.as_view(), name='api-mobile-detail'),
]
