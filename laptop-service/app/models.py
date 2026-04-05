from django.db import models


class Laptop(models.Model):
	name = models.CharField(max_length=200)
	brand = models.CharField(max_length=100)
	cpu = models.CharField(max_length=100)
	ram_gb = models.PositiveIntegerField()
	storage_gb = models.PositiveIntegerField()
	price = models.DecimalField(max_digits=12, decimal_places=2)
	stock = models.PositiveIntegerField(default=0)
	description = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self) -> str:
		return f"{self.brand} {self.name}"
