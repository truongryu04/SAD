from django.db.models import Q
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal, InvalidOperation

from .models import Mobile


@method_decorator(csrf_exempt, name="dispatch")
class MobileInfoView(View):
	def get(self, request, mobile_id=None):
		if mobile_id is None:
			query = (request.GET.get("q") or "").strip()
			mobile_queryset = Mobile.objects.all()
			if query:
				mobile_queryset = mobile_queryset.filter(
					Q(name__icontains=query)
					| Q(brand__icontains=query)
					| Q(camera_specs__icontains=query)
				)

			mobiles = list(
				mobile_queryset.values(
					"id",
					"name",
					"brand",
					"screen_size",
					"battery_mah",
					"camera_specs",
					"price",
					"stock",
				)
			)
			return JsonResponse({"count": len(mobiles), "data": mobiles})

		mobile = Mobile.objects.filter(id=mobile_id).values(
			"id",
			"name",
			"brand",
			"screen_size",
			"battery_mah",
			"camera_specs",
			"price",
			"stock",
			"description",
		).first()
		if mobile is None:
			return JsonResponse({"error": "Mobile not found."}, status=404)

		return JsonResponse(mobile)

	def post(self, request, mobile_id=None):
		if mobile_id is not None:
			return JsonResponse({"error": "Method not allowed."}, status=405)

		try:
			body = json.loads(request.body or "{}")
		except json.JSONDecodeError:
			return JsonResponse({"error": "Invalid JSON body."}, status=400)

		name = (body.get("name") or "").strip()
		brand = (body.get("brand") or "").strip()
		screen_size = (body.get("screen_size") or "").strip()
		battery_mah = body.get("battery_mah")
		camera_specs = (body.get("camera_specs") or "").strip()
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
			battery_val = int(battery_mah) if battery_mah is not None else 0
		except (TypeError, ValueError):
			battery_val = 0

		m = Mobile.objects.create(
			name=name,
			brand=brand,
			screen_size=screen_size,
			battery_mah=battery_val,
			camera_specs=camera_specs,
			price=price_val,
			stock=stock_val,
			description=description,
		)
		return JsonResponse({"message": "Mobile created.", "id": m.id}, status=201)

	def patch(self, request, mobile_id):
		return self._update(request, mobile_id)

	def put(self, request, mobile_id):
		return self._update(request, mobile_id)

	def _update(self, request, mobile_id):
		try:
			body = json.loads(request.body or "{}")
		except json.JSONDecodeError:
			return JsonResponse({"error": "Invalid JSON body."}, status=400)

		m = Mobile.objects.filter(id=mobile_id).first()
		if m is None:
			return JsonResponse({"error": "Mobile not found."}, status=404)

		if "name" in body:
			m.name = (body.get("name") or "").strip()
		if "brand" in body:
			m.brand = (body.get("brand") or "").strip()
		if "screen_size" in body:
			m.screen_size = (body.get("screen_size") or "").strip()
		if "battery_mah" in body:
			try:
				m.battery_mah = int(body.get("battery_mah"))
			except (TypeError, ValueError):
				pass
		if "camera_specs" in body:
			m.camera_specs = (body.get("camera_specs") or "").strip()
		if "price" in body:
			try:
				p = Decimal(str(body.get("price")))
				if p >= 0:
					m.price = p
			except (InvalidOperation, TypeError):
				pass
		if "stock" in body:
			try:
				m.stock = int(body.get("stock"))
			except (TypeError, ValueError):
				pass
		if "description" in body:
			m.description = (body.get("description") or "").strip()

		m.save()
		return JsonResponse({"message": "Mobile updated.", "id": m.id})
