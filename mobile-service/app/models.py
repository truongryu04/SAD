from django.db import models


class Mobile(models.Model):
	name = models.CharField(max_length=200)
	brand = models.CharField(max_length=100)
	screen_size = models.CharField(max_length=50)
	battery_mah = models.PositiveIntegerField()
	camera_specs = models.CharField(max_length=200)
	price = models.DecimalField(max_digits=12, decimal_places=2)
	stock = models.PositiveIntegerField(default=0)
	description = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self) -> str:
		return f"{self.brand} {self.name}"
