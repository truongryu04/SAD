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
	if name == "product":
		return os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8003")
	return None


def _default_category_id_for_type(item_type):
	if item_type == "laptop":
		return 2
	return 1


def _category_to_item_type(category_id):
	# Categories 2/9/10 are laptop families, others are treated as mobile-like for legacy UI.
	if category_id in {2, 9, 10}:
		return "laptop"
	return "mobile"


def _normalize_product_rows(payload):
	if isinstance(payload, list):
		return payload
	if isinstance(payload, dict) and isinstance(payload.get("data"), list):
		return payload.get("data")
	if isinstance(payload, dict) and isinstance(payload.get("results"), list):
		return payload.get("results")
	return []


def _product_to_staff_item(product):
	category_id = int(product.get("category_id") or 1)
	status = str(product.get("status") or "ACTIVE").upper()
	stock = 50 if status == "ACTIVE" else 0
	return {
		"id": product.get("id"),
		"item_type": _category_to_item_type(category_id),
		"name": product.get("name") or "",
		"brand": product.get("brand") or "",
		"description": product.get("description") or "",
		"price": str(product.get("base_price") or "0"),
		"stock": stock,
		"category_id": category_id,
		"status": status,
	}


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
		p_status, p_data = _call_service("GET", _service_url("product"), "/api/products/")
		if p_status == 200:
			rows = _normalize_product_rows(p_data)
			combined = [_product_to_staff_item(row) for row in rows]
			return JsonResponse({"count": len(combined), "data": combined})

		return JsonResponse(p_data if isinstance(p_data, dict) else {"error": "Cannot load items."}, status=p_status)

	def post(self, request):
		body, error = _parse_json_body(request)
		if error:
			return error

		name = (body.get("name") or "").strip()
		item_type = (body.get("item_type") or "").strip().lower()
		price = _validate_price(body.get("price"))
		stock = _validate_quantity(body.get("stock"))
		description = (body.get("description") or "").strip()
		attribute_values = body.get("attribute_values")

		if not name:
			return JsonResponse({"error": "name is required."}, status=400)
		if price is None:
			return JsonResponse({"error": "price must be a non-negative number."}, status=400)
		if stock is None:
			return JsonResponse({"error": "stock must be a non-negative integer."}, status=400)
		if not isinstance(attribute_values, (list, dict)):
			return JsonResponse({"error": "attribute_values is required and must be a list or object map."}, status=400)

		brand = (body.get("brand") or "").strip()
		if not brand:
			return JsonResponse({"error": "brand is required."}, status=400)

		category_id = body.get("category_id")
		try:
			if category_id is not None:
				category_id = int(category_id)
			else:
				if item_type not in {"laptop", "mobile"}:
					return JsonResponse({"error": "category_id is required when item_type is not provided."}, status=400)
				category_id = _default_category_id_for_type(item_type)
		except (TypeError, ValueError):
			return JsonResponse({"error": "category_id must be an integer."}, status=400)

		status_value = "ACTIVE" if stock > 0 else "INACTIVE"
		payload = {
			"name": name,
			"description": description,
			"category_id": category_id,
			"brand": brand,
			"base_price": str(price),
			"status": status_value,
			"attribute_values": attribute_values,
		}

		status, data = _call_service("POST", _service_url("product"), "/api/products/", payload)

		if status in (200, 201) and isinstance(data, dict):
			return JsonResponse(_product_to_staff_item(data), status=201)
		return JsonResponse(data if isinstance(data, dict) else {"error": "Create failed."}, status=status)


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
		p_status, p_data = _call_service("GET", _service_url("product"), f"/api/products/{item_id}/")
		if p_status == 200 and isinstance(p_data, dict):
			return JsonResponse(_product_to_staff_item(p_data), status=200)
		if p_status == 404:
			return JsonResponse({"error": "Item not found."}, status=404)
		return JsonResponse(p_data if isinstance(p_data, dict) else {"error": "Fetch failed."}, status=p_status)

	def put(self, request, item_id):
		return self._update_item(request, item_id)

	def patch(self, request, item_id):
		return self._update_item(request, item_id)

	def delete(self, request, item_id):
		p_status, p_data = _call_service("DELETE", _service_url("product"), f"/api/products/{item_id}/")
		if p_status in (200, 204):
			return JsonResponse({"message": "Item deleted successfully."}, status=200)
		if p_status == 404:
			return JsonResponse({"error": "Item not found."}, status=404)
		return JsonResponse(p_data if isinstance(p_data, dict) else {"error": "Delete failed."}, status=p_status)

	def _update_item(self, request, item_id):
		body, error = _parse_json_body(request)
		if error:
			return error

		# Prefer patching product-service first.
		p_payload = {}
		if "name" in body:
			p_payload["name"] = body.get("name")
		if "description" in body:
			p_payload["description"] = body.get("description")
		if "brand" in body:
			p_payload["brand"] = body.get("brand")
		if "price" in body:
			price = _validate_price(body.get("price"))
			if price is None:
				return JsonResponse({"error": "price must be a non-negative number."}, status=400)
			p_payload["base_price"] = str(price)
		if "category_id" in body:
			try:
				p_payload["category_id"] = int(body.get("category_id"))
			except (TypeError, ValueError):
				return JsonResponse({"error": "category_id must be an integer."}, status=400)
		if "stock" in body:
			try:
				qty = int(body.get("stock"))
				if qty < 0:
					raise ValueError()
				p_payload["status"] = "ACTIVE" if qty > 0 else "INACTIVE"
			except (TypeError, ValueError):
				return JsonResponse({"error": "stock must be a non-negative integer."}, status=400)

		if p_payload:
			p_status, p_data = _call_service("PATCH", _service_url("product"), f"/api/products/{item_id}/", p_payload)
			if p_status == 200 and isinstance(p_data, dict):
				return JsonResponse(_product_to_staff_item(p_data), status=200)
			if p_status == 404:
				return JsonResponse({"error": "Item not found."}, status=404)
			return JsonResponse(p_data if isinstance(p_data, dict) else {"error": "Update failed."}, status=p_status)

		return JsonResponse({"error": "No valid fields to update."}, status=400)
