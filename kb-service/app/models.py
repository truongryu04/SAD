from django.db import models


class KBCategory(models.Model):
    external_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    raw_payload = models.JSONField(default=dict)
    synced_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.external_id}:{self.name}"


class KBProduct(models.Model):
    external_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    brand = models.CharField(max_length=120, blank=True)
    category_external_id = models.IntegerField(null=True, blank=True)
    category_name = models.CharField(max_length=200, blank=True)
    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=50, blank=True)
    normalized_text = models.TextField(blank=True)
    raw_payload = models.JSONField(default=dict)
    synced_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.external_id}:{self.name}"


class KBInventory(models.Model):
    external_id = models.IntegerField(unique=True)
    variant_id = models.IntegerField()
    quantity = models.IntegerField(default=0)
    reserved_quantity = models.IntegerField(default=0)
    raw_payload = models.JSONField(default=dict)
    synced_at = models.DateTimeField(auto_now=True)


class KBSyncCheckpoint(models.Model):
    source_name = models.CharField(max_length=50, unique=True)
    records_synced = models.IntegerField(default=0)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
