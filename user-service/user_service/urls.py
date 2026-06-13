"""
URL configuration for user_service project.

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
    AddCartItemView,
    ClearCartView,
    CreateCartView,
    CreateItemView,
    CustomerAccountDetailView,
    CustomerAccountView,
    LoginView,
    ManageCartItemView,
    ProductRatingView,
    RegisterCustomerView,
    RegisterStaffView,
    SearchItemView,
    StaffAccountDetailView,
    StaffAccountView,
    StaffLoginView,
    StaffPermissionView,
    UpdateItemView,
    UserActivityView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('customer/register/', RegisterCustomerView.as_view(), name='customer-register'),
    path('customer/login/', LoginView.as_view(), name='customer-login'),
    path('customer/accounts/', CustomerAccountView.as_view(), name='customer-accounts'),
    path('customer/accounts/<int:customer_id>/', CustomerAccountDetailView.as_view(), name='customer-account-detail'),
    path('customer/carts/', CreateCartView.as_view(), name='create-cart'),
    path('customer/carts/items/', AddCartItemView.as_view(), name='add-cart-item'),
    path('customer/carts/items/<int:cart_item_id>/', ManageCartItemView.as_view(), name='manage-cart-item'),
    path('customer/carts/clear/', ClearCartView.as_view(), name='clear-cart'),
    path('customer/search/', SearchItemView.as_view(), name='search-item'),
    path('customer/ratings/', ProductRatingView.as_view(), name='product-rating'),
    path('customer/activities/', UserActivityView.as_view(), name='user-activity'),
    path('staff/register/', RegisterStaffView.as_view(), name='staff-register'),
    path('staff/login/', StaffLoginView.as_view(), name='staff-login'),
    path('staff/permissions/', StaffPermissionView.as_view(), name='staff-permissions'),
    path('staff/accounts/', StaffAccountView.as_view(), name='staff-accounts'),
    path('staff/accounts/<int:staff_id>/', StaffAccountDetailView.as_view(), name='staff-account-detail'),
    path('staff/items/', CreateItemView.as_view(), name='create-item'),
    path('staff/items/<int:item_id>/', UpdateItemView.as_view(), name='update-item'),
]
