from django.contrib import admin
from django.urls import path

from app.views import CheckoutView, OrderView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('orders/', OrderView.as_view(), name='orders'),
    path('orders/checkout/', CheckoutView.as_view(), name='orders-checkout'),
]
