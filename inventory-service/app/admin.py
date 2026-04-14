from django.contrib import admin
from .models import Inventory, StockTransaction

admin.site.register(Inventory)
admin.site.register(StockTransaction)
