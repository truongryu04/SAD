"""
URL configuration for customer_service project.

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

from app.views import AddCartItemView, CreateCartView, LoginView, ProductRatingView, RegisterCustomerView, SearchItemView, UserActivityView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('customer/register/', RegisterCustomerView.as_view(), name='customer-register'),
    path('customer/login/', LoginView.as_view(), name='customer-login'),
    path('customer/carts/', CreateCartView.as_view(), name='create-cart'),
    path('customer/carts/items/', AddCartItemView.as_view(), name='add-cart-item'),
    path('customer/search/', SearchItemView.as_view(), name='search-item'),
    path('customer/ratings/', ProductRatingView.as_view(), name='product-rating'),
    path('customer/activities/', UserActivityView.as_view(), name='user-activity'),
]
