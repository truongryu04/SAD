from django.db import models


class ApiRequestLog(models.Model):
	service_name = models.CharField(max_length=50)
	method = models.CharField(max_length=10)
	path = models.CharField(max_length=255)
	status_code = models.IntegerField()
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return f"{self.method} {self.path} -> {self.service_name} ({self.status_code})"
