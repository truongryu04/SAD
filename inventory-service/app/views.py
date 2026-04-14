
from rest_framework import generics
from .models import Inventory, StockTransaction
from .serializers import InventorySerializer, StockTransactionSerializer

# Inventory APIs
class InventoryListCreateView(generics.ListCreateAPIView):
	queryset = Inventory.objects.all()
	serializer_class = InventorySerializer

class InventoryRetrieveUpdateView(generics.RetrieveUpdateAPIView):
	queryset = Inventory.objects.all()
	serializer_class = InventorySerializer

# StockTransaction APIs
class StockTransactionListView(generics.ListAPIView):
	queryset = StockTransaction.objects.all()
	serializer_class = StockTransactionSerializer

class StockTransactionCreateView(generics.CreateAPIView):
	queryset = StockTransaction.objects.all()
	serializer_class = StockTransactionSerializer
