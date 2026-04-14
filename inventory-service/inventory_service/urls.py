from django.contrib import admin
from django.urls import path
from app.views import (
    InventoryListCreateView,
    InventoryRetrieveUpdateView,
    StockTransactionListView,
    StockTransactionCreateView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/inventories/', InventoryListCreateView.as_view(), name='inventory-list-create'),
    path('api/inventories/<int:pk>/', InventoryRetrieveUpdateView.as_view(), name='inventory-detail-update'),
    path('api/stock-transactions/', StockTransactionListView.as_view(), name='stock-transaction-list'),
    path('api/stock-transactions/', StockTransactionCreateView.as_view(), name='stock-transaction-create'),
]
