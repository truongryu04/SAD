from django.contrib import admin

from .models import KBCategory, KBInventory, KBProduct, KBSyncCheckpoint

admin.site.register(KBProduct)
admin.site.register(KBCategory)
admin.site.register(KBInventory)
admin.site.register(KBSyncCheckpoint)
