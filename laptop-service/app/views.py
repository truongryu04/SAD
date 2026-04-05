from django.db.models import Q
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal, InvalidOperation

from .models import Laptop


@method_decorator(csrf_exempt, name="dispatch")
class LaptopInfoView(View):
	def get(self, request, laptop_id=None):
		if laptop_id is None:
			query = (request.GET.get("q") or "").strip()
			laptop_queryset = Laptop.objects.all()
			if query:
				laptop_queryset = laptop_queryset.filter(
					Q(name__icontains=query)
					| Q(brand__icontains=query)
					| Q(cpu__icontains=query)
				)

			laptops = list(
				laptop_queryset.values(
					"id",
					"name",
					"brand",
					"cpu",
					"ram_gb",
					"storage_gb",
					"price",
					"stock",
				)
			)
			return JsonResponse({"count": len(laptops), "data": laptops})

		laptop = Laptop.objects.filter(id=laptop_id).values(
			"id",
			"name",
			"brand",
			"cpu",
			"ram_gb",
			"storage_gb",
			"price",
			"stock",
			"description",
		).first()
		if laptop is None:
			return JsonResponse({"error": "Laptop not found."}, status=404)

		return JsonResponse(laptop)

	def post(self, request, laptop_id=None):
		# create new laptop when no id provided
		if laptop_id is not None:
			return JsonResponse({"error": "Method not allowed."}, status=405)

		try:
			body = json.loads(request.body or "{}")
		except json.JSONDecodeError:
			return JsonResponse({"error": "Invalid JSON body."}, status=400)

		name = (body.get("name") or "").strip()
		brand = (body.get("brand") or "").strip()
		cpu = (body.get("cpu") or "").strip()
		ram_gb = body.get("ram_gb")
		storage_gb = body.get("storage_gb")
		price = body.get("price")
		stock = body.get("stock")
		description = (body.get("description") or "").strip()

		if not name or not brand:
			return JsonResponse({"error": "name and brand are required."}, status=400)

		try:
			price_val = Decimal(str(price))
			if price_val < 0:
				raise InvalidOperation()
		except (InvalidOperation, TypeError):
			return JsonResponse({"error": "price must be a non-negative number."}, status=400)

		try:
			stock_val = int(stock or 0)
			if stock_val < 0:
				raise ValueError()
		except (TypeError, ValueError):
			return JsonResponse({"error": "stock must be a non-negative integer."}, status=400)

		try:
			ram_val = int(ram_gb) if ram_gb is not None else 8
		except (TypeError, ValueError):
			ram_val = 8
		try:
			storage_val = int(storage_gb) if storage_gb is not None else 256
		except (TypeError, ValueError):
			storage_val = 256

		l = Laptop.objects.create(
			name=name,
			brand=brand,
			cpu=cpu,
			ram_gb=ram_val,
			storage_gb=storage_val,
			price=price_val,
			stock=stock_val,
			description=description,
		)
		return JsonResponse({"message": "Laptop created.", "id": l.id}, status=201)

	def patch(self, request, laptop_id):
		return self._update(request, laptop_id)

	def put(self, request, laptop_id):
		return self._update(request, laptop_id)

	def _update(self, request, laptop_id):
		try:
			body = json.loads(request.body or "{}")
		except json.JSONDecodeError:
			return JsonResponse({"error": "Invalid JSON body."}, status=400)

		l = Laptop.objects.filter(id=laptop_id).first()
		if l is None:
			return JsonResponse({"error": "Laptop not found."}, status=404)

		if "name" in body:
			l.name = (body.get("name") or "").strip()
		if "brand" in body:
			l.brand = (body.get("brand") or "").strip()
		if "cpu" in body:
			l.cpu = (body.get("cpu") or "").strip()
		if "ram_gb" in body:
			try:
				l.ram_gb = int(body.get("ram_gb"))
			except (TypeError, ValueError):
				pass
		if "storage_gb" in body:
			try:
				l.storage_gb = int(body.get("storage_gb"))
			except (TypeError, ValueError):
				pass
		if "price" in body:
			try:
				p = Decimal(str(body.get("price")))
				if p >= 0:
					l.price = p
			except (InvalidOperation, TypeError):
				pass
		if "stock" in body:
			try:
				l.stock = int(body.get("stock"))
			except (TypeError, ValueError):
				pass
		if "description" in body:
			l.description = (body.get("description") or "").strip()

		l.save()
		return JsonResponse({"message": "Laptop updated.", "id": l.id})


class HealthView(View):
	def get(self, request):
		# Simple health check for liveness/readiness
		return JsonResponse({"status": "ok"})
