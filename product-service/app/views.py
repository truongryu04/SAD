import json
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Product, ProductVariant
from .serializers import ProductSerializer, ProductVariantSerializer


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


def _extract_rows(payload):
	if isinstance(payload, list):
		return payload
	if isinstance(payload, dict) and isinstance(payload.get("data"), list):
		return payload.get("data")
	return []


def _get_category_attributes(category_id):
	status, payload = _attribute_service_request("GET", "/api/category-attributes/", query={"category_id": category_id})
	if status != 200:
		raise ValidationError({"category_id": f"Cannot load category attributes: {payload}"})
	rows = _extract_rows(payload)
	if not rows:
		raise ValidationError({"category_id": "Selected category has no attribute schema."})
	return rows


def _normalize_attribute_values(payload):
	if isinstance(payload, dict):
		normalized = []
		for key, value in payload.items():
			try:
				attribute_id = int(key)
			except (TypeError, ValueError):
				raise ValidationError({"attribute_values": f"Invalid attribute id key: {key}"})
			normalized.append({"attribute_id": attribute_id, "value": value})
		return normalized

	if not isinstance(payload, list):
		raise ValidationError({"attribute_values": "attribute_values must be a list or object map."})

	normalized = []
	for index, item in enumerate(payload):
		if not isinstance(item, dict):
			raise ValidationError({"attribute_values": f"attribute_values[{index}] must be an object."})
		attribute_id = item.get("attribute_id")
		try:
			attribute_id = int(attribute_id)
		except (TypeError, ValueError):
			raise ValidationError({"attribute_values": f"attribute_values[{index}].attribute_id is invalid."})
		normalized.append({"attribute_id": attribute_id, "value": item.get("value")})

	seen = set()
	for item in normalized:
		attribute_id = item["attribute_id"]
		if attribute_id in seen:
			raise ValidationError({"attribute_values": f"Duplicate attribute_id {attribute_id} in attribute_values."})
		seen.add(attribute_id)
	return normalized


def _validate_required_values(category_attributes, attribute_values):
	incoming_map = {}
	for item in attribute_values:
		incoming_map[item["attribute_id"]] = str(item.get("value") or "").strip()

	missing = []
	for category_attribute in category_attributes:
		attribute_id = int(category_attribute.get("attribute_id"))
		attribute_meta = category_attribute.get("attribute") or {}
		attribute_name = attribute_meta.get("name") or f"attribute_id={attribute_id}"
		if incoming_map.get(attribute_id):
			continue
		missing.append(attribute_name)

	if missing:
		raise ValidationError({"attribute_values": f"Missing values for attributes: {', '.join(missing)}"})


def _sync_product_attribute_values(product_id, attribute_values):
	for item in attribute_values:
		lookup_status, lookup_payload = _attribute_service_request(
			"GET",
			"/api/product-attribute-values/",
			query={"product_id": product_id, "attribute_id": item["attribute_id"]},
		)
		if lookup_status != 200:
			raise ValidationError({"attribute_values": f"Cannot query product attribute values: {lookup_payload}"})

		rows = _extract_rows(lookup_payload)
		payload = {
			"product_id": product_id,
			"attribute_id": item["attribute_id"],
			"value": str(item.get("value") or "").strip(),
		}
		if rows:
			row_id = rows[0].get("id")
			status, response_payload = _attribute_service_request("PATCH", f"/api/product-attribute-values/{row_id}/", payload=payload)
		else:
			status, response_payload = _attribute_service_request("POST", "/api/product-attribute-values/", payload=payload)
		if status in (200, 201):
			continue
		raise ValidationError({"attribute_values": f"Cannot save product attribute value: {response_payload}"})

class ProductListCreateView(generics.ListCreateAPIView):
	queryset = Product.objects.all()
	serializer_class = ProductSerializer

	def create(self, request, *args, **kwargs):
		category_id = request.data.get("category_id")
		try:
			category_id = int(category_id)
		except (TypeError, ValueError):
			raise ValidationError({"category_id": "category_id is required and must be an integer."})

		category_attributes = _get_category_attributes(category_id)
		attribute_values = _normalize_attribute_values(request.data.get("attribute_values"))
		_validate_required_values(category_attributes, attribute_values)

		payload = request.data.copy()
		payload.pop("attribute_values", None)
		serializer = self.get_serializer(data=payload)
		serializer.is_valid(raise_exception=True)
		product = serializer.save()

		try:
			_sync_product_attribute_values(product.id, attribute_values)
		except ValidationError:
			product.delete()
			raise

		return Response(serializer.data, status=status.HTTP_201_CREATED)

class ProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
	queryset = Product.objects.all()
	serializer_class = ProductSerializer


class CategoryAttributeSchemaView(APIView):
	def get(self, request, category_id):
		category_attributes = _get_category_attributes(category_id)
		return Response({"category_id": category_id, "attributes": category_attributes})

class ProductVariantListCreateView(APIView):
	def get(self, request, id):
		variants = ProductVariant.objects.filter(product_id=id)
		serializer = ProductVariantSerializer(variants, many=True)
		return Response(serializer.data)

	def post(self, request, id):
		data = request.data.copy()
		data['product'] = id
		serializer = ProductVariantSerializer(data=data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
