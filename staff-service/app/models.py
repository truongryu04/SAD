from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class StaffAccount(models.Model):
	ROLE_STAFF = "STAFF"
	ROLE_CHOICES = ((ROLE_STAFF, "Staff"),)

	username = models.CharField(max_length=100, unique=True)
	full_name = models.CharField(max_length=150)
	password = models.CharField(max_length=255)
	role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STAFF)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def set_password(self, raw_password: str) -> None:
		self.password = make_password(raw_password)

	def verify_password(self, raw_password: str) -> bool:
		return check_password(raw_password, self.password)

	def __str__(self) -> str:
		return self.username

# InventoryItem removed: staff-service now proxies create/update to laptop/mobile services.
