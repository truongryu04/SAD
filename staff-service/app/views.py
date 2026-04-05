import json
import os
import urllib.error
import urllib.request
from decimal import Decimal, InvalidOperation

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import StaffAccount


def _parse_json_body(request):
	try:
		return json.loads(request.body or "{}"), None
	except json.JSONDecodeError:
		return None, JsonResponse({"error": "Invalid JSON body."}, status=400)


def _validate_price(price_value):
	try:
		price = Decimal(str(price_value))
	except (InvalidOperation, TypeError):
		return None

	if price < 0:
		return None
	return price


def _validate_quantity(quantity_value):
	try:
		quantity = int(quantity_value)
	except (TypeError, ValueError):
		return None

	if quantity < 0:
		return None
	return quantity


def _service_url(name):
	# resolve service base URLs from environment or defaults used in docker-compose
	if name == "laptop":
		return os.getenv("LAPTOP_SERVICE_URL", "http://laptop-service:8003")
	if name == "mobile":
		return os.getenv("MOBILE_SERVICE_URL", "http://mobile-service:8004")
	return None


def _call_service(method, base_url, path, payload=None, timeout=15):
	url = f"{base_url.rstrip('/')}{path}"
	data = None
	headers = {"Accept": "application/json"}
	if payload is not None:
		data = json.dumps(payload).encode("utf-8")
		headers["Content-Type"] = "application/json"

	req = urllib.request.Request(url=url, data=data, method=method, headers=headers)
	try:
		with urllib.request.urlopen(req, timeout=timeout) as resp:
			raw = resp.read()
			status = resp.getcode()
			try:
				return status, json.loads(raw.decode("utf-8") or "{}")
			except json.JSONDecodeError:
				return status, {"message": raw.decode("utf-8", errors="ignore")}
	except urllib.error.HTTPError as exc:
		raw = exc.read()
		status = exc.code
		try:
			return status, json.loads(raw.decode("utf-8") or "{}")
		except json.JSONDecodeError:
			return status, {"message": raw.decode("utf-8", errors="ignore")}
	except urllib.error.URLError as exc:
		return 502, {"error": f"Cannot connect to service", "details": str(exc)}


@method_decorator(csrf_exempt, name="dispatch")
class CreateItemView(View):

	def get(self, request):
		# Aggregate items from laptop and mobile services
		l_status, l_data = _call_service("GET", _service_url("laptop"), "/laptops/")
		m_status, m_data = _call_service("GET", _service_url("mobile"), "/mobiles/")

		combined = []
		if l_status == 200:
			combined = combined + (l_data.get("data") if isinstance(l_data, dict) and isinstance(l_data.get("data"), list) else (l_data if isinstance(l_data, list) else []))
		if m_status == 200:
			combined = combined + (m_data.get("data") if isinstance(m_data, dict) and isinstance(m_data.get("data"), list) else (m_data if isinstance(m_data, list) else []))

		return JsonResponse({"count": len(combined), "data": combined})

	def post(self, request):
		body, error = _parse_json_body(request)
		if error:
			return error

		name = (body.get("name") or "").strip()
		item_type = (body.get("item_type") or "").strip().lower()
		price = _validate_price(body.get("price"))
		stock = _validate_quantity(body.get("stock"))
		description = (body.get("description") or "").strip()

		if not name:
			return JsonResponse({"error": "name is required."}, status=400)
		if item_type not in {"laptop", "mobile"}:
			return JsonResponse({"error": "item_type must be laptop or mobile."}, status=400)
		if price is None:
			return JsonResponse({"error": "price must be a non-negative number."}, status=400)
		if stock is None:
			return JsonResponse({"error": "stock must be a non-negative integer."}, status=400)

		# map fields for target service
		# Build payload strictly following the target model fields
		if item_type == "laptop":
			brand = (body.get("brand") or "").strip()
			cpu = (body.get("cpu") or "").strip()
			ram_gb = body.get("ram_gb")
			storage_gb = body.get("storage_gb")

			if not brand:
				return JsonResponse({"error": "brand is required for laptop."}, status=400)

			try:
				ram_val = int(ram_gb) if ram_gb is not None else 8
			except (TypeError, ValueError):
				ram_val = 8
			try:
				storage_val = int(storage_gb) if storage_gb is not None else 256
			except (TypeError, ValueError):
				storage_val = 256

			payload = {
				"name": name,
				"brand": brand,
				"cpu": cpu,
				"ram_gb": ram_val,
				"storage_gb": storage_val,
				"price": str(price),
				"stock": stock,
				"description": description,
			}
			status, data = _call_service("POST", _service_url("laptop"), "/laptops/", payload)
		else:
			# mobile
			brand = (body.get("brand") or "").strip()
			screen_size = (body.get("screen_size") or "").strip()
			battery_mah = body.get("battery_mah")
			camera_specs = (body.get("camera_specs") or "").strip()

			if not brand:
				return JsonResponse({"error": "brand is required for mobile."}, status=400)

			try:
				battery_val = int(battery_mah) if battery_mah is not None else 0
			except (TypeError, ValueError):
				battery_val = 0

			payload = {
				"name": name,
				"brand": brand,
				"screen_size": screen_size,
				"battery_mah": battery_val,
				"camera_specs": camera_specs,
				"price": str(price),
				"stock": stock,
				"description": description,
			}
			status, data = _call_service("POST", _service_url("mobile"), "/mobiles/", payload)

		# If creation was successful and downstream returned an id, fetch full item
		if status in (200, 201) and isinstance(data, dict) and data.get("id"):
			created_id = data.get("id")
			# attempt to fetch the created resource for full fields (brand, stock, ...)
			get_status, get_data = _call_service("GET", _service_url(item_type), f"/{'laptops' if item_type=='laptop' else 'mobiles'}/{created_id}/")
			if get_status == 200 and isinstance(get_data, dict):
				return JsonResponse(get_data, status=201)
			# fallback to original response if fetch failed
		return JsonResponse(data, status=status)


@method_decorator(csrf_exempt, name="dispatch")
class RegisterStaffView(View):
	def post(self, request):
		body, error = _parse_json_body(request)
		if error:
			return error

		username = (body.get("username") or "").strip()
		password = body.get("password") or ""
		full_name = (body.get("full_name") or "").strip()

		if not username or not password or not full_name:
			return JsonResponse(
				{"error": "username, password and full_name are required."},
				status=400,
			)
		if StaffAccount.objects.filter(username=username).exists():
			return JsonResponse({"error": "Username already exists."}, status=409)

		staff = StaffAccount(
			username=username,
			full_name=full_name,
			role=StaffAccount.ROLE_STAFF,
		)
		staff.set_password(password)
		staff.save()

		return JsonResponse(
			{
				"message": "Staff account registered successfully.",
				"staff_id": staff.id,
				"username": staff.username,
				"role": staff.role,
			},
			status=201,
		)


@method_decorator(csrf_exempt, name="dispatch")
class StaffLoginView(View):
	def post(self, request):
		body, error = _parse_json_body(request)
		if error:
			return error

		username = (body.get("username") or "").strip()
		password = body.get("password") or ""

		if not username or not password:
			return JsonResponse({"error": "username and password are required."}, status=400)

		staff = StaffAccount.objects.filter(username=username).first()
		if staff is None or not staff.verify_password(password):
			return JsonResponse({"error": "Invalid credentials."}, status=401)
		if not staff.is_active:
			return JsonResponse({"error": "Staff account is inactive."}, status=403)

		return JsonResponse(
			{
				"message": "Login successful.",
				"staff_id": staff.id,
				"username": staff.username,
				"full_name": staff.full_name,
				"role": staff.role,
			}
		)


@method_decorator(csrf_exempt, name="dispatch")
class UpdateItemView(View):

	def get(self, request, item_id):
		# Try fetching from laptop service, then mobile service
		l_status, l_data = _call_service("GET", _service_url("laptop"), f"/laptops/{item_id}/")
		if l_status == 200:
			return JsonResponse(l_data)
		m_status, m_data = _call_service("GET", _service_url("mobile"), f"/mobiles/{item_id}/")
		if m_status == 200:
			return JsonResponse(m_data)
		# not found or error
		if l_status >= 400 and m_status >= 400:
			return JsonResponse({"error": "Item not found."}, status=404)
		# If one of services returned an error (like 502), propagate it
		return JsonResponse(l_data if l_status != 200 else m_data, status=(l_status if l_status != 200 else m_status))

	def put(self, request, item_id):
		return self._update_item(request, item_id)

	def patch(self, request, item_id):
		return self._update_item(request, item_id)

	def _update_item(self, request, item_id):
		body, error = _parse_json_body(request)
		if error:
			return error

		# Try update on laptop service
		# Map incoming fields to laptop/mobile payloads where appropriate
		# First attempt laptop
		l_payload = {}
		m_payload = {}

		if "name" in body:
			l_payload["name"] = body.get("name")
			m_payload["name"] = body.get("name")
		if "price" in body:
			price = _validate_price(body.get("price"))
			if price is None:
				return JsonResponse({"error": "price must be a non-negative number."}, status=400)
			l_payload["price"] = str(price)
			m_payload["price"] = str(price)
		if "stock" in body:
			try:
				quantity = int(body.get("stock"))
				if quantity < 0:
					raise ValueError()
			except (TypeError, ValueError):
				return JsonResponse({"error": "stock must be a non-negative integer."}, status=400)
			l_payload["stock"] = quantity
			m_payload["stock"] = quantity
		if "description" in body:
			l_payload["description"] = body.get("description")
			m_payload["description"] = body.get("description")
		# fields specific to laptop/mobile
		if "brand" in body:
			l_payload["brand"] = body.get("brand")
			m_payload["brand"] = body.get("brand")
		if "cpu" in body:
			l_payload["cpu"] = body.get("cpu")
		if "ram_gb" in body:
			try:
				l_payload["ram_gb"] = int(body.get("ram_gb"))
			except (TypeError, ValueError):
				return JsonResponse({"error": "ram_gb must be an integer."}, status=400)
		if "storage_gb" in body:
			try:
				l_payload["storage_gb"] = int(body.get("storage_gb"))
			except (TypeError, ValueError):
				return JsonResponse({"error": "storage_gb must be an integer."}, status=400)
		if "screen_size" in body:
			m_payload["screen_size"] = body.get("screen_size")
		if "battery_mah" in body:
			try:
				m_payload["battery_mah"] = int(body.get("battery_mah"))
			except (TypeError, ValueError):
				return JsonResponse({"error": "battery_mah must be an integer."}, status=400)
		if "camera_specs" in body:
			m_payload["camera_specs"] = body.get("camera_specs")

		# Try laptop update
		l_status, l_data = (0, {})
		if l_payload:
			l_status, l_data = _call_service("PATCH", _service_url("laptop"), f"/laptops/{item_id}/", l_payload)
		else:
			# attempt patch with empty payload to check existence
			l_status, l_data = _call_service("GET", _service_url("laptop"), f"/laptops/{item_id}/")

		if l_status == 200 and l_payload:
			return JsonResponse(l_data, status=200)

		# Try mobile update
		m_status, m_data = (0, {})
		if m_payload:
			m_status, m_data = _call_service("PATCH", _service_url("mobile"), f"/mobiles/{item_id}/", m_payload)
		else:
			m_status, m_data = _call_service("GET", _service_url("mobile"), f"/mobiles/{item_id}/")

		if m_status == 200 and m_payload:
			return JsonResponse(m_data, status=200)

		# If neither updated, return appropriate error
		if l_status >= 400 and m_status >= 400:
			# prefer returning service error details if available
			return JsonResponse(l_data if l_status >= m_status else m_data, status=(l_status if l_status >= m_status else m_status))
		# else return whatever found
		return JsonResponse(l_data if l_status == 200 else m_data, status=200)
