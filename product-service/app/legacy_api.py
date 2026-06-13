from __future__ import annotations

import uuid

from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .models import Category, Product, Book, Electronics, Fashion


def _safe_int(value, default=None):
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def _safe_float(value, default=None):
	try:
		return float(value)
	except (TypeError, ValueError):
		return default


def _safe_str(value, default=""):
	if value is None:
		return default
	return str(value)


def _derive_status_from_stock(stock: int) -> str:
	return "ACTIVE" if int(stock or 0) > 0 else "INACTIVE"


def _legacy_brand(product: Product) -> str:
	# The legacy UI expects a generic brand field.
	try:
		if product.product_type == Product.PRODUCT_TYPE_ELECTRONICS and getattr(product, "electronics", None):
			return _safe_str(product.electronics.brand, "Unknown")
		if product.product_type == Product.PRODUCT_TYPE_BOOK and getattr(product, "book", None):
			return _safe_str(product.book.author, "Unknown")
		if product.product_type == Product.PRODUCT_TYPE_FASHION and getattr(product, "fashion", None):
			return _safe_str(product.fashion.color, "Unknown")
	except Exception:
		pass
	return "Unknown"


def _serialize_product_legacy(product: Product) -> dict:
	base_price = float(product.price or 0)
	stock = int(product.stock or 0)
	return {
		"id": product.id,
		"name": product.name,
		"image_url": _safe_str(getattr(product, "image_url", "")),
		"category_id": product.category_id,
		"brand": _legacy_brand(product),
		"description": "",
		"base_price": base_price,
		"price": base_price,
		"status": _derive_status_from_stock(stock),
		"stock": stock,
		"attribute_values": [],
		"product_type": product.product_type,
	}


class LegacyCategoryListView(APIView):
	def get(self, request):
		rows = list(Category.objects.all().order_by("id").values("id", "name", "product_type", "parent_id"))
		return Response({"count": len(rows), "data": rows})

	def post(self, request):
		name = _safe_str(request.data.get("name")).strip()
		if not name:
			return Response({"error": "name is required."}, status=status.HTTP_400_BAD_REQUEST)
		product_type = _safe_str(request.data.get("product_type"), Category.PRODUCT_TYPE_ELECTRONICS).strip().upper()
		if product_type not in {
			Category.PRODUCT_TYPE_BOOK,
			Category.PRODUCT_TYPE_ELECTRONICS,
			Category.PRODUCT_TYPE_FASHION,
		}:
			return Response({"error": "Invalid product_type."}, status=status.HTTP_400_BAD_REQUEST)

		parent = None
		parent_id = _safe_int(request.data.get("parent"), None)
		if parent_id is not None:
			parent = Category.objects.filter(id=parent_id).first()
			if parent is None:
				return Response({"error": "parent does not exist."}, status=status.HTTP_400_BAD_REQUEST)
			if parent.product_type != product_type:
				return Response({"error": "Parent category must have the same product_type."}, status=status.HTTP_400_BAD_REQUEST)

		category = Category.objects.create(name=name, product_type=product_type, parent=parent)
		return Response({"id": category.id, "name": category.name}, status=status.HTTP_201_CREATED)


class LegacyCategoryDetailView(APIView):
	def get(self, request, pk: int):
		category = Category.objects.filter(pk=pk).first()
		if category is None:
			return Response({"error": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
		return Response({"id": category.id, "name": category.name})

	def patch(self, request, pk: int):
		category = Category.objects.filter(pk=pk).first()
		if category is None:
			return Response({"error": "Category not found."}, status=status.HTTP_404_NOT_FOUND)

		if "name" in request.data:
			name = _safe_str(request.data.get("name")).strip()
			if not name:
				return Response({"error": "name cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
			category.name = name
			category.save(update_fields=["name"])

		return Response({"id": category.id, "name": category.name})

	def delete(self, request, pk: int):
		category = Category.objects.filter(pk=pk).first()
		if category is None:
			return Response({"error": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
		category.delete()
		return Response({"message": "Category deleted."})


class LegacyProductListView(APIView):
	def get(self, request):
		products = (
			Product.objects.select_related("category", "book", "electronics", "fashion")
			.all()
			.order_by("-id")
		)
		rows = [_serialize_product_legacy(p) for p in products]
		return Response({"count": len(rows), "data": rows})

	def post(self, request):
		name = _safe_str(request.data.get("name")).strip()
		if not name:
			return Response({"error": "name is required."}, status=status.HTTP_400_BAD_REQUEST)

		category_id = _safe_int(request.data.get("category_id"), None)
		if category_id is None:
			return Response({"error": "category_id is required."}, status=status.HTTP_400_BAD_REQUEST)
		category = Category.objects.filter(id=category_id).first()
		if category is None:
			return Response({"error": "category_id does not exist."}, status=status.HTTP_400_BAD_REQUEST)

		base_price = request.data.get("base_price", request.data.get("price"))
		price = _safe_float(base_price, None)
		if price is None or price < 0:
			return Response({"error": "base_price must be a non-negative number."}, status=status.HTTP_400_BAD_REQUEST)

		stock = _safe_int(request.data.get("stock"), None)
		status_value = _safe_str(request.data.get("status")).strip().upper()
		if stock is None:
			# fallback: derive from status if stock omitted
			stock = 1 if status_value == "ACTIVE" else 0
		if stock < 0:
			return Response({"error": "stock must be a non-negative integer."}, status=status.HTTP_400_BAD_REQUEST)

		product_type = _safe_str(request.data.get("product_type")).strip().upper() or Product.PRODUCT_TYPE_ELECTRONICS
		brand = _safe_str(request.data.get("brand")).strip() or "Unknown"
		image_url = _safe_str(request.data.get("image_url") or request.data.get("imageUrl")).strip()

		try:
			if product_type == Product.PRODUCT_TYPE_ELECTRONICS:
				product = Product.create_with_subtype(
					name=name,
					image_url=image_url,
					price=price,
					stock=stock,
					category=category,
					product_type=Product.PRODUCT_TYPE_ELECTRONICS,
					brand=brand,
					warranty=_safe_int(request.data.get("warranty"), 12) or 12,
				)
			elif product_type == Product.PRODUCT_TYPE_BOOK:
				product = Product.create_with_subtype(
					name=name,
					image_url=image_url,
					price=price,
					stock=stock,
					category=category,
					product_type=Product.PRODUCT_TYPE_BOOK,
					author=_safe_str(request.data.get("author"), brand or "Unknown"),
					publisher=_safe_str(request.data.get("publisher"), "Unknown"),
					isbn=_safe_str(request.data.get("isbn"), f"UNKNOWN-{uuid.uuid4().hex[:8]}") ,
				)
			elif product_type == Product.PRODUCT_TYPE_FASHION:
				product = Product.create_with_subtype(
					name=name,
					image_url=image_url,
					price=price,
					stock=stock,
					category=category,
					product_type=Product.PRODUCT_TYPE_FASHION,
					size=_safe_str(request.data.get("size"), "M"),
					color=_safe_str(request.data.get("color"), "Black"),
				)
			else:
				return Response({"error": "Invalid product_type."}, status=status.HTTP_400_BAD_REQUEST)
		except Exception as exc:
			return Response({"error": f"Create product failed: {exc}"}, status=status.HTTP_400_BAD_REQUEST)

		product = Product.objects.select_related("category", "book", "electronics", "fashion").get(pk=product.pk)
		return Response(_serialize_product_legacy(product), status=status.HTTP_201_CREATED)


class LegacyProductDetailView(APIView):
	def get(self, request, pk: int):
		product = Product.objects.select_related("category", "book", "electronics", "fashion").filter(pk=pk).first()
		if product is None:
			return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
		return Response(_serialize_product_legacy(product))

	def patch(self, request, pk: int):
		product = Product.objects.select_related("category", "book", "electronics", "fashion").filter(pk=pk).first()
		if product is None:
			return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

		update_fields = []
		if "name" in request.data:
			product.name = _safe_str(request.data.get("name")).strip()
			update_fields.append("name")

		if "image_url" in request.data or "imageUrl" in request.data:
			product.image_url = _safe_str(request.data.get("image_url") or request.data.get("imageUrl")).strip()
			update_fields.append("image_url")

		if "category_id" in request.data:
			category_id = _safe_int(request.data.get("category_id"), None)
			if category_id is None:
				return Response({"error": "category_id must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
			category = Category.objects.filter(id=category_id).first()
			if category is None:
				return Response({"error": "category_id does not exist."}, status=status.HTTP_400_BAD_REQUEST)
			product.category = category
			update_fields.append("category")

		if "base_price" in request.data or "price" in request.data:
			base_price = request.data.get("base_price", request.data.get("price"))
			price = _safe_float(base_price, None)
			if price is None or price < 0:
				return Response({"error": "base_price must be a non-negative number."}, status=status.HTTP_400_BAD_REQUEST)
			product.price = price
			update_fields.append("price")

		if "stock" in request.data:
			stock = _safe_int(request.data.get("stock"), None)
			if stock is None or stock < 0:
				return Response({"error": "stock must be a non-negative integer."}, status=status.HTTP_400_BAD_REQUEST)
			product.stock = stock
			update_fields.append("stock")

		if "status" in request.data and "stock" not in request.data:
			status_value = _safe_str(request.data.get("status")).strip().upper()
			product.stock = 1 if status_value == "ACTIVE" else 0
			update_fields.append("stock")

		# Best-effort brand update.
		if "brand" in request.data:
			brand = _safe_str(request.data.get("brand")).strip()
			if product.product_type == Product.PRODUCT_TYPE_ELECTRONICS:
				Electronics.objects.update_or_create(
					product=product,
					defaults={
						"brand": brand or "Unknown",
						"warranty": getattr(product.electronics, "warranty", 12) if getattr(product, "electronics", None) else 12,
					},
				)

		if update_fields:
			product.save(update_fields=list(set(update_fields)))

		product = Product.objects.select_related("category", "book", "electronics", "fashion").get(pk=product.pk)
		return Response(_serialize_product_legacy(product))

	def put(self, request, pk: int):
		# Treat PUT as partial update for legacy clients.
		return self.patch(request, pk)

	def delete(self, request, pk: int):
		product = Product.objects.filter(pk=pk).first()
		if product is None:
			return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
		product.delete()
		return Response({"message": "Product deleted."})


class LegacyCategoryAttributesView(APIView):
	def get(self, request, pk: int):
		# Product schema/attribute system was removed from the current product-service schema.
		# Keep a compatible endpoint for the gateway UI.
		return Response({"category_id": int(pk), "attributes": []})


class LegacyAttributeListView(APIView):
	def get(self, request):
		return Response([])


class LegacyCategoryAttributeListView(APIView):
	def get(self, request):
		return Response([])


class LegacyProductAttributeValueListView(APIView):
	def get(self, request):
		return Response([])
