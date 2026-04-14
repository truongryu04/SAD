import json
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from .models import Category
from .serializers import CategorySerializer


def _attribute_service_request(method, path, payload=None, query=None, timeout=20):
	base_url = settings.ATTRIBUTE_SERVICE_URL.rstrip('/')
	url = f"{base_url}{path}"
	if query:
		url = f"{url}?{urllib.parse.urlencode(query)}"

	headers = {"Accept": "application/json"}
	data = None
	if payload is not None:
		headers["Content-Type"] = "application/json"
		data = json.dumps(payload).encode("utf-8")

	request = urllib.request.Request(url=url, method=method, headers=headers, data=data)
	try:
		with urllib.request.urlopen(request, timeout=timeout) as response:
			raw = response.read().decode("utf-8")
			return response.getcode(), json.loads(raw or "{}")
	except urllib.error.HTTPError as exc:
		raw = exc.read().decode("utf-8", errors="ignore")
		try:
			payload = json.loads(raw or "{}")
		except json.JSONDecodeError:
			payload = {"message": raw}
		return exc.code, payload
	except urllib.error.URLError as exc:
		return 502, {"error": "Cannot connect to attribute service.", "details": str(exc)}


def _must_be_positive_int(value, field_name):
	try:
		parsed = int(value)
	except (TypeError, ValueError):
		raise ValidationError({field_name: f"{field_name} must be an integer."})
	if parsed <= 0:
		raise ValidationError({field_name: f"{field_name} must be > 0."})
	return parsed


def _find_attribute_by_name(name):
	status, payload = _attribute_service_request("GET", "/api/attributes/")
	if status != 200:
		return None

	rows = payload if isinstance(payload, list) else payload.get("data", [])
	for row in rows:
		if str(row.get("name") or "").strip().lower() == name.lower():
			return row
	return None


def _normalize_attribute_items(attribute_items):
	if not isinstance(attribute_items, list) or not attribute_items:
		raise ValidationError({"attributes": "attributes is required and must be a non-empty list."})

	normalized = []
	for index, item in enumerate(attribute_items):
		if not isinstance(item, dict):
			raise ValidationError({"attributes": f"attributes[{index}] must be an object."})

		attribute_id = item.get("attribute_id")
		if attribute_id is not None:
			attribute_id = _must_be_positive_int(attribute_id, f"attributes[{index}].attribute_id")
		else:
			name = str(item.get("name") or "").strip()
			data_type = str(item.get("data_type") or "").strip()
			unit = str(item.get("unit") or "").strip()
			if not name or not data_type:
				raise ValidationError({"attributes": f"attributes[{index}] must include attribute_id or (name, data_type)."})

			status, data = _attribute_service_request(
				"POST",
				"/api/attributes/",
				payload={"name": name, "data_type": data_type, "unit": unit},
			)
			if status in (200, 201):
				attribute_id = int(data.get("id"))
			else:
				existing = _find_attribute_by_name(name)
				if existing and existing.get("id") is not None:
					attribute_id = int(existing.get("id"))
				else:
					raise ValidationError({"attributes": f"Cannot create attribute at index {index}: {data}"})

		normalized.append(
			{
				"attribute_id": attribute_id,
				"is_required": bool(item.get("is_required", True)),
				"display_order": int(item.get("display_order", index + 1)),
			}
		)

	seen = set()
	for item in normalized:
		attribute_id = item["attribute_id"]
		if attribute_id in seen:
			raise ValidationError({"attributes": f"Duplicate attribute_id {attribute_id}."})
		seen.add(attribute_id)

	return normalized


def _sync_category_attributes(category_id, normalized_items):
	status, existing_payload = _attribute_service_request("GET", "/api/category-attributes/", query={"category_id": category_id})
	if status != 200:
		raise ValidationError({"attributes": f"Cannot read category attributes: {existing_payload}"})

	existing_rows = existing_payload if isinstance(existing_payload, list) else existing_payload.get("data", [])
	existing_by_attribute = {int(row["attribute_id"]): row for row in existing_rows if row.get("attribute_id") is not None}
	incoming_attribute_ids = {item["attribute_id"] for item in normalized_items}

	for attribute_id, row in existing_by_attribute.items():
		if attribute_id in incoming_attribute_ids:
			continue
		row_id = row.get("id")
		if row_id is None:
			continue
		d_status, d_payload = _attribute_service_request("DELETE", f"/api/category-attributes/{row_id}/")
		if d_status not in (200, 204):
			raise ValidationError({"attributes": f"Cannot delete stale category attribute {row_id}: {d_payload}"})

	for item in normalized_items:
		attribute_id = item["attribute_id"]
		payload = {
			"category_id": category_id,
			"attribute_id": attribute_id,
			"is_required": item["is_required"],
			"display_order": item["display_order"],
		}
		existing_row = existing_by_attribute.get(attribute_id)
		if existing_row:
			row_id = existing_row.get("id")
			u_status, u_payload = _attribute_service_request("PATCH", f"/api/category-attributes/{row_id}/", payload=payload)
			if u_status not in (200, 201):
				raise ValidationError({"attributes": f"Cannot update category attribute {row_id}: {u_payload}"})
			continue

		c_status, c_payload = _attribute_service_request("POST", "/api/category-attributes/", payload=payload)
		if c_status not in (200, 201):
			raise ValidationError({"attributes": f"Cannot create category attribute: {c_payload}"})


def _get_category_attributes(category_id):
	status, payload = _attribute_service_request("GET", "/api/category-attributes/", query={"category_id": category_id})
	if status != 200:
		return []
	return payload if isinstance(payload, list) else payload.get("data", [])

class CategoryListCreateView(generics.ListCreateAPIView):
	queryset = Category.objects.all()
	serializer_class = CategorySerializer

	def create(self, request, *args, **kwargs):
		attributes = request.data.get("attributes")
		normalized_items = _normalize_attribute_items(attributes)
		payload = request.data.copy()
		payload.pop("attributes", None)

		serializer = self.get_serializer(data=payload)
		serializer.is_valid(raise_exception=True)
		category = serializer.save()
		_sync_category_attributes(category.id, normalized_items)

		data = serializer.data
		data["attributes"] = _get_category_attributes(category.id)
		return Response(data, status=201)

	def list(self, request, *args, **kwargs):
		response = super().list(request, *args, **kwargs)
		if not isinstance(response.data, list):
			return response
		for row in response.data:
			category_id = row.get("id")
			row["attributes"] = _get_category_attributes(category_id)
		return response

class CategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
	queryset = Category.objects.all()
	serializer_class = CategorySerializer

	def retrieve(self, request, *args, **kwargs):
		response = super().retrieve(request, *args, **kwargs)
		category_id = response.data.get("id")
		response.data["attributes"] = _get_category_attributes(category_id)
		return response

	def update(self, request, *args, **kwargs):
		partial = kwargs.pop("partial", False)
		instance = self.get_object()
		attributes = request.data.get("attributes")
		normalized_items = _normalize_attribute_items(attributes) if attributes is not None else None
		payload = request.data.copy()
		payload.pop("attributes", None)

		serializer = self.get_serializer(instance, data=payload, partial=partial)
		serializer.is_valid(raise_exception=True)
		category = serializer.save()

		if normalized_items is not None:
			_sync_category_attributes(category.id, normalized_items)

		data = serializer.data
		data["attributes"] = _get_category_attributes(category.id)
		return Response(data)
