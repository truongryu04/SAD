from django.contrib import admin
from .models import Attribute, CategoryAttribute, ProductAttributeValue

admin.site.register(Attribute)
admin.site.register(CategoryAttribute)
admin.site.register(ProductAttributeValue)
