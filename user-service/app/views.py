import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import Cart, CartItem, Rating, SearchHistory, UserAccount, UserActivity


def _utc_now_iso():
	return datetime.now(timezone.utc).isoformat()


def _actor_role(request):
	return (request.headers.get("X-Actor-Role") or "").strip().upper()


def _actor_id(request):
	value = request.headers.get("X-Actor-Id")
	try:
		return int(value)
	except (TypeError, ValueError):
		return None


def _is_admin_request(request):
	return _actor_role(request) == UserAccount.ROLE_ADMIN


def _require_admin(request):
	if _is_admin_request(request):
		return None
	return JsonResponse({"error": "Admin role is required."}, status=403)


def _permissions_for_role(role):
	normalized = (role or "").strip().upper()
	if normalized == UserAccount.ROLE_ADMIN:
		return [
			"users:manage",
			"users:assign-role",
			"products:create",
			"products:update",
			"products:delete",
			"categories:manage",
			"inventory:manage",
			"orders:view-all",
			"orders:update-status",
			"payments:view",
			"payments:refund",
			"system:settings",
			"system:api-security-logs",
			"reports:revenue",
			"reports:best-sellers",
			"reports:user-behavior",
		]
	if normalized == UserAccount.ROLE_STAFF:
		return [
			"products:create",
			"products:update",
			"inventory:update",
			"orders:view",
			"orders:confirm",
			"orders:update-shipping",
			"support:chat-ticket",
			"support:complaints",
			"shipping:track",
			"shipping:link-provider",
			"reports:basic-revenue",
			"reports:order-count",
		]
	return []


def _emit_kb_behavior_event(customer_id, event_type, product_id=None, query=None, rating=None, timestamp=None):
	kb_base_url = getattr(settings, "KB_SERVICE_URL", "").strip()
	if not kb_base_url:
		return

	payload = {
		"customer_id": int(customer_id),
		"event_type": str(event_type or "").upper(),
		"timestamp": timestamp or _utc_now_iso(),
	}
	if product_id is not None:
		payload["product_id"] = int(product_id)
	if query:
		payload["query"] = str(query)
	if rating is not None:
		payload["rating"] = float(rating)

	request = urllib.request.Request(
		url=f"{kb_base_url.rstrip('/')}/api/kb/behavior/",
		method="POST",
		headers={"Content-Type": "application/json", "Accept": "application/json"},
		data=json.dumps(payload).encode("utf-8"),
	)
	try:
		with urllib.request.urlopen(request, timeout=5):
			return
	except (urllib.error.HTTPError, urllib.error.URLError, ValueError, TypeError):
		return


def _parse_json_body(request):
	try:
		return json.loads(request.body or "{}"), None
	except json.JSONDecodeError:
		return None, JsonResponse({"error": "Invalid JSON body."}, status=400)


def _service_url(name):
	if name == "product":
		return os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8003")
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
		return 502, {"error": "Cannot connect to service", "details": str(exc)}


def _fetch_all_product_rows():
	base_url = _service_url("product")
	path = "/products/?limit=100"
	rows = []
	seen_urls = set()

	while path:
		status, payload = _call_service("GET", base_url, path)
		if status != 200:
			return status, payload

		page_rows = _normalize_product_rows(payload)
		rows.extend(page_rows)

		next_url = payload.get("next") if isinstance(payload, dict) else None
		if not next_url:
			break

		if next_url in seen_urls:
			break
		seen_urls.add(next_url)

		parsed = urllib.parse.urlsplit(next_url)
		path = parsed.path
		if parsed.query:
			path = f"{path}?{parsed.query}"

	return 200, {"count": len(rows), "data": rows}


def _build_cart_response(cart):
	items = []
	total = 0
	for it in cart.items.all():
		status, data = _call_service("GET", _service_url("product"), f"/products/{it.item_id}/")
		name = data.get("name") if isinstance(data, dict) else None
		price = data.get("price") if isinstance(data, dict) else None

		try:
			price_num = float(price) if price is not None else 0
		except Exception:
			price_num = 0

		line_total = price_num * it.quantity
		total += line_total
		items.append(
			{
				"id": it.id,
				"item_type": it.item_type,
				"item_id": it.item_id,
				"name": name or "Khong co ten",
				"quantity": it.quantity,
				"price": price_num,
				"line_total": line_total,
			}
		)

	return {
		"id": cart.id,
		"customer_id": cart.user.id,
		"items_count": cart.items.count(),
		"total": total,
		"items": items,
	}


def _log_activity(user, action, item_type="", item_id=None, quantity=0, rating_score=None, metadata=None):
	try:
		UserActivity.objects.create(
			user=user,
			action=action,
			item_type=item_type or "",
			item_id=item_id,
			quantity=quantity if quantity and quantity > 0 else 0,
			rating_score=rating_score,
			metadata=metadata or {},
		)
	except Exception:
		pass


def _default_category_id_for_type(item_type):
	if item_type == "laptop":
		return 2
	return 1


def _category_to_item_type(category_id):
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
	category_id = int(product.get("category_id") or (product.get("category", {}).get("id") if isinstance(product.get("category"), dict) else 1))
	# status may be provided by legacy API, new API exposes stock and price
	stock_val = None
	try:
		stock_val = int(product.get("stock")) if product.get("stock") is not None else None
	except Exception:
		stock_val = None
	if stock_val is None:
		status = str(product.get("status") or "ACTIVE").upper()
		stock = 50 if status == "ACTIVE" else 0
	else:
		stock = stock_val
		status = "ACTIVE" if stock > 0 else "INACTIVE"

	# price may be under 'price' (new) or 'base_price' (legacy)
	price_val = product.get("price") if product.get("price") is not None else product.get("base_price")
	# brand may be nested under electronics in new API
	brand = ""
	if isinstance(product, dict):
		if isinstance(product.get("electronics"), dict):
			brand = product.get("electronics").get("brand") or ""
		brand = brand or (product.get("brand") or "")

	return {
		"id": product.get("id"),
		"item_type": _category_to_item_type(category_id),
		"name": product.get("name") or "",
		"brand": brand,
		"description": product.get("description") or "",
		"image_url": product.get("image_url") or product.get("imageUrl") or "",
		"price": str(price_val or "0"),
		"stock": stock,
		"category_id": category_id,
		"product_type": str(product.get("product_type") or "ELECTRONICS").upper(),
		"status": status,
	}


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


@method_decorator(csrf_exempt, name="dispatch")
class RegisterCustomerView(View):
	def post(self, request):
		body, error = _parse_json_body(request)
		if error:
			return error

		username = (body.get("username") or "").strip()
		password = body.get("password") or ""
		full_name = (body.get("full_name") or "").strip()

		if not username or not password:
			return JsonResponse({"error": "username and password are required."}, status=400)
		if UserAccount.objects.filter(username=username).exists():
			return JsonResponse({"error": "Username already exists."}, status=409)

		user = UserAccount(username=username, full_name=full_name, role=UserAccount.ROLE_CUSTOMER)
		user.set_password(password)
		user.save()

		return JsonResponse(
			{
				"message": "Customer registered successfully.",
				"customer_id": user.id,
				"username": user.username,
				"role": user.role,
			},
			status=201,
		)


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(View):
	def post(self, request):
		body, error = _parse_json_body(request)
		if error:
			return error

		username = (body.get("username") or "").strip()
		password = body.get("password") or ""

		if not username or not password:
			return JsonResponse({"error": "username and password are required."}, status=400)

		user = UserAccount.objects.filter(username=username).first()
		if user is None or not user.verify_password(password):
			return JsonResponse({"error": "Invalid credentials."}, status=401)
		if user.role != UserAccount.ROLE_CUSTOMER:
			return JsonResponse({"error": "This account is not a customer account."}, status=403)
		if not user.is_active:
			return JsonResponse({"error": "Customer is inactive."}, status=403)

		return JsonResponse(
			{
				"message": "Login successful.",
				"customer_id": user.id,
				"username": user.username,
				"full_name": user.full_name,
				"role": user.role,
			}
		)


@method_decorator(csrf_exempt, name="dispatch")
class CustomerAccountView(View):
	def get(self, request):
		query = (request.GET.get("q") or "").strip().lower()
		active_text = (request.GET.get("is_active") or "").strip().lower()

		accounts = UserAccount.objects.filter(role=UserAccount.ROLE_CUSTOMER).order_by("-id")
		if query:
			accounts = accounts.filter(username__icontains=query)
		if active_text in {"true", "false"}:
			accounts = accounts.filter(is_active=(active_text == "true"))

		rows = [
			{
				"id": item.id,
				"username": item.username,
				"full_name": item.full_name,
				"role": item.role,
				"is_active": item.is_active,
				"created_at": item.created_at.isoformat() if item.created_at else None,
			}
			for item in accounts
		]
		return JsonResponse({"count": len(rows), "data": rows})


@method_decorator(csrf_exempt, name="dispatch")
class CustomerAccountDetailView(View):
	def patch(self, request, customer_id):
		body, error = _parse_json_body(request)
		if error:
			return error

		user = UserAccount.objects.filter(id=customer_id, role=UserAccount.ROLE_CUSTOMER).first()
		if user is None:
			return JsonResponse({"error": "Customer not found."}, status=404)

		actor_role = _actor_role(request)
		actor_id = _actor_id(request)
		is_owner = actor_role == UserAccount.ROLE_CUSTOMER and actor_id == user.id
		is_admin = actor_role == UserAccount.ROLE_ADMIN

		if "is_active" in body and not is_admin:
			return JsonResponse({"error": "Only admin can update is_active."}, status=403)

		if "full_name" in body:
			user.full_name = (body.get("full_name") or "").strip()
		if "password" in body:
			new_password = body.get("password") or ""
			if not new_password:
				return JsonResponse({"error": "password cannot be empty."}, status=400)
			if not (is_owner or is_admin):
				return JsonResponse({"error": "Permission denied."}, status=403)
			user.set_password(new_password)
		if "is_active" in body:
			user.is_active = bool(body.get("is_active"))

		user.save()
		return JsonResponse(
			{
				"id": user.id,
				"username": user.username,
				"full_name": user.full_name,
				"role": user.role,
				"is_active": user.is_active,
				"created_at": user.created_at.isoformat() if user.created_at else None,
			}
		)

	def delete(self, request, customer_id):
		actor_role = _actor_role(request)
		is_admin = actor_role == UserAccount.ROLE_ADMIN

		if not is_admin:
			return JsonResponse({"error": "Only admin can delete accounts."}, status=403)

		user = UserAccount.objects.filter(id=customer_id, role=UserAccount.ROLE_CUSTOMER).first()
		if user is None:
			return JsonResponse({"error": "Customer not found."}, status=404)

		user.delete()
		return JsonResponse({"message": "Customer deleted successfully."})


@method_decorator(csrf_exempt, name="dispatch")
class CreateCartView(View):
	def post(self, request):
		body, error = _parse_json_body(request)
		if error:
			return error

		customer_id = body.get("customer_id")
		if customer_id is None:
			return JsonResponse({"error": "customer_id is required."}, status=400)

		customer = UserAccount.objects.filter(
			id=customer_id,
			role=UserAccount.ROLE_CUSTOMER,
		).first()
		if customer is None:
			return JsonResponse({"error": "Customer not found."}, status=404)
		if not customer.is_active:
			return JsonResponse({"error": "Customer is inactive."}, status=403)

		cart = Cart.objects.filter(user=customer).order_by("-id").first()
		if cart is None:
			cart = Cart.objects.create(user=customer)
			status_code = 201
		else:
			status_code = 200

		return JsonResponse(_build_cart_response(cart), status=status_code)

	def get(self, request):
		customer_id = request.GET.get("customer_id")
		cart_id = request.GET.get("cart_id")
		if not customer_id and not cart_id:
			return JsonResponse({"error": "customer_id or cart_id is required."}, status=400)

		if cart_id:
			cart = Cart.objects.filter(id=cart_id).first()
		else:
			customer = UserAccount.objects.filter(
				id=customer_id,
				role=UserAccount.ROLE_CUSTOMER,
			).first()
			if customer is None:
				return JsonResponse({"error": "Customer not found."}, status=404)
			cart = Cart.objects.filter(user=customer).order_by("-id").first()

		if cart is None:
			return JsonResponse({"error": "Cart not found."}, status=404)
		return JsonResponse(_build_cart_response(cart))


@method_decorator(csrf_exempt, name="dispatch")
class AddCartItemView(View):
	def post(self, request):
		body, error = _parse_json_body(request)
		if error:
			return error

		cart_id = body.get("cart_id")
		item_id = body.get("item_id") or body.get("product_id") or body.get("productId")
		item_type = (body.get("item_type") or "product").strip().lower()
		quantity = body.get("quantity") or 1

		if cart_id is None:
			customer_id = body.get("customer_id")
			if customer_id is None:
				return JsonResponse({"error": "cart_id or customer_id is required."}, status=400)
			customer = UserAccount.objects.filter(
				id=customer_id,
				role=UserAccount.ROLE_CUSTOMER,
			).first()
			if customer is None:
				return JsonResponse({"error": "Customer not found."}, status=404)
			if not customer.is_active:
				return JsonResponse({"error": "Customer is inactive."}, status=403)
			cart = Cart.objects.filter(user=customer).order_by("-id").first()
			if cart is None:
				cart = Cart.objects.create(user=customer)
		else:
			cart = Cart.objects.filter(id=cart_id).first()
			if cart is None:
				return JsonResponse({"error": "Cart not found."}, status=404)

		if item_id is None:
			return JsonResponse({"error": "item_id is required."}, status=400)

		try:
			qty = int(quantity)
			if qty <= 0:
				raise ValueError()
		except (TypeError, ValueError):
			return JsonResponse({"error": "quantity must be a positive integer."}, status=400)

		product_status, product_data = _call_service("GET", _service_url("product"), f"/products/{int(item_id)}/")
		if product_status >= 400:
			return JsonResponse(
				product_data if isinstance(product_data, dict) else {"error": "Product not found."},
				status=product_status,
			)

		ci = CartItem.objects.create(cart=cart, item_type=item_type or "product", item_id=int(item_id), quantity=qty)
		_log_activity(
			user=cart.user,
			action=UserActivity.ACTION_ADD_TO_CART,
			item_type=item_type,
			item_id=int(item_id),
			quantity=qty,
			metadata={"cart_id": cart.id, "cart_item_id": ci.id},
		)
		_emit_kb_behavior_event(
			customer_id=cart.user_id,
			event_type="ADDED_TO_CART",
			product_id=int(item_id),
		)

		return JsonResponse(_build_cart_response(cart))


@method_decorator(csrf_exempt, name="dispatch")
class ManageCartItemView(View):
	def patch(self, request, cart_item_id):
		body, error = _parse_json_body(request)
		if error:
			return error

		quantity = body.get("quantity")
		try:
			qty = int(quantity)
			if qty <= 0:
				raise ValueError()
		except (TypeError, ValueError):
			return JsonResponse({"error": "quantity must be a positive integer."}, status=400)

		cart_item = CartItem.objects.select_related("cart").filter(id=cart_item_id).first()
		if cart_item is None:
			return JsonResponse({"error": "Cart item not found."}, status=404)

		cart_item.quantity = qty
		cart_item.save(update_fields=["quantity"])
		return JsonResponse(_build_cart_response(cart_item.cart), status=200)

	def delete(self, request, cart_item_id):
		cart_item = CartItem.objects.select_related("cart").filter(id=cart_item_id).first()
		if cart_item is None:
			return JsonResponse({"error": "Cart item not found."}, status=404)

		cart = cart_item.cart
		cart_item.delete()
		return JsonResponse(_build_cart_response(cart), status=200)


@method_decorator(csrf_exempt, name="dispatch")
class ClearCartView(View):
	def post(self, request):
		body, error = _parse_json_body(request)
		if error:
			return error

		cart = None
		cart_id = body.get("cart_id")
		customer_id = body.get("customer_id")

		if cart_id is not None:
			cart = Cart.objects.filter(id=cart_id).first()
		elif customer_id is not None:
			customer = UserAccount.objects.filter(
				id=customer_id,
				role=UserAccount.ROLE_CUSTOMER,
				is_active=True,
			).first()
			if customer is None:
				return JsonResponse({"error": "Customer not found or inactive."}, status=404)
			cart = Cart.objects.filter(user=customer).order_by("-id").first()

		if cart is None:
			return JsonResponse({"error": "Cart not found."}, status=404)

		deleted_items = cart.items.count()
		cart.items.all().delete()
		return JsonResponse(
			{
				"message": "Cart cleared.",
				"cart_id": cart.id,
				"customer_id": cart.user_id,
				"deleted_items": deleted_items,
			},
			status=200,
		)


@method_decorator(csrf_exempt, name="dispatch")
class SearchItemView(View):
	def get(self, request):
		keyword = (request.GET.get("q") or "").strip()
		if not keyword:
			return JsonResponse({"error": "q is required."}, status=400)

		customer = None
		customer_id = request.GET.get("customer_id")
		if customer_id:
			customer = UserAccount.objects.filter(id=customer_id, role=UserAccount.ROLE_CUSTOMER).first()

		SearchHistory.objects.create(user=customer, keyword=keyword)
		if customer is not None:
			_emit_kb_behavior_event(customer_id=customer.id, event_type="SEARCHED", query=keyword)

		return JsonResponse(
			{
				"message": "Search keyword recorded successfully.",
				"keyword": keyword,
				"customer_id": customer.id if customer else None,
				"next": "Use api-gateway to query product-service by keyword.",
			}
		)


@method_decorator(csrf_exempt, name="dispatch")
class ProductRatingView(View):
	def get(self, request):
		item_type = (request.GET.get("item_type") or "product").strip().lower()
		item_id = request.GET.get("item_id")
		customer_id = request.GET.get("customer_id")

		if not item_type:
			return JsonResponse({"error": "item_type is required."}, status=400)
		if item_id is None:
			return JsonResponse({"error": "item_id is required."}, status=400)

		try:
			product_id = int(item_id)
		except (TypeError, ValueError):
			return JsonResponse({"error": "item_id must be an integer."}, status=400)

		ratings = Rating.objects.filter(item_type=item_type, item_id=product_id)
		votes = ratings.count()
		total_score = sum(r.score for r in ratings)
		average_score = (total_score / votes) if votes > 0 else 0

		my_score = None
		my_review = ""
		if customer_id is not None:
			try:
				cid = int(customer_id)
			except (TypeError, ValueError):
				return JsonResponse({"error": "customer_id must be an integer."}, status=400)
			my_rating = ratings.filter(user_id=cid).first()
			if my_rating:
				my_score = my_rating.score
				my_review = my_rating.review

		return JsonResponse(
			{
				"item_type": item_type,
				"item_id": product_id,
				"average_score": round(average_score, 2),
				"votes": votes,
				"my_score": my_score,
				"my_review": my_review,
			}
		)

	def post(self, request):
		body, error = _parse_json_body(request)
		if error:
			return error

		customer_id = body.get("customer_id")
		item_type = (body.get("item_type") or "product").strip().lower()
		item_id = body.get("item_id")
		score = body.get("score")
		review = (body.get("review") or "").strip()

		if customer_id is None or item_id is None or score is None:
			return JsonResponse({"error": "customer_id, item_id and score are required."}, status=400)
		if not item_type:
			return JsonResponse({"error": "item_type is required."}, status=400)

		try:
			cid = int(customer_id)
			pid = int(item_id)
			score_value = int(score)
		except (TypeError, ValueError):
			return JsonResponse({"error": "customer_id, item_id and score must be integers."}, status=400)

		if score_value < 1 or score_value > 5:
			return JsonResponse({"error": "score must be between 1 and 5."}, status=400)

		user = UserAccount.objects.filter(
			id=cid,
			role=UserAccount.ROLE_CUSTOMER,
			is_active=True,
		).first()
		if user is None:
			return JsonResponse({"error": "Customer not found or inactive."}, status=404)

		rating, created = Rating.objects.update_or_create(
			user=user,
			item_type=item_type,
			item_id=pid,
			defaults={"score": score_value, "review": review},
		)
		_log_activity(
			user=user,
			action=UserActivity.ACTION_RATE_PRODUCT,
			item_type=item_type,
			item_id=pid,
			rating_score=score_value,
			metadata={"rating_id": rating.id, "created": created},
		)

		ratings = Rating.objects.filter(item_type=item_type, item_id=pid)
		votes = ratings.count()
		total_score = sum(r.score for r in ratings)
		average_score = (total_score / votes) if votes > 0 else 0

		return JsonResponse(
			{
				"message": "Rating created." if created else "Rating updated.",
				"rating_id": rating.id,
				"item_type": item_type,
				"item_id": pid,
				"my_score": rating.score,
				"my_review": rating.review,
				"average_score": round(average_score, 2),
				"votes": votes,
			},
			status=201 if created else 200,
		)


@method_decorator(csrf_exempt, name="dispatch")
class UserActivityView(View):
	def get(self, request):
		customer_id = request.GET.get("customer_id")
		action = (request.GET.get("action") or "").strip().upper()
		limit_raw = request.GET.get("limit")

		activities = UserActivity.objects.all().order_by("-created_at")

		if customer_id is not None:
			try:
				cid = int(customer_id)
			except (TypeError, ValueError):
				return JsonResponse({"error": "customer_id must be an integer."}, status=400)
			activities = activities.filter(user_id=cid)

		if action:
			activities = activities.filter(action=action)

		limit = 200
		if limit_raw is not None:
			try:
				limit = int(limit_raw)
			except (TypeError, ValueError):
				return JsonResponse({"error": "limit must be an integer."}, status=400)
			if limit <= 0:
				return JsonResponse({"error": "limit must be > 0."}, status=400)
			limit = min(limit, 5000)

		data = list(
			activities.values(
				"id",
				"user_id",
				"action",
				"item_type",
				"item_id",
				"quantity",
				"rating_score",
				"metadata",
				"created_at",
			)[:limit]
		)

		for row in data:
			row["customer_id"] = row.pop("user_id")
		return JsonResponse({"count": len(data), "data": data})

	def post(self, request):
		body, error = _parse_json_body(request)
		if error:
			return error

		customer_id = body.get("customer_id")
		action = (body.get("action") or "").strip().upper()
		item_type = (body.get("item_type") or "").strip().lower()
		item_id = body.get("item_id")
		quantity = body.get("quantity") or 0
		rating_score = body.get("rating_score")
		metadata = body.get("metadata")

		if customer_id is None or not action:
			return JsonResponse({"error": "customer_id and action are required."}, status=400)
		if action not in {
			UserActivity.ACTION_VIEW_PRODUCT,
			UserActivity.ACTION_ADD_TO_CART,
			UserActivity.ACTION_RATE_PRODUCT,
		}:
			return JsonResponse({"error": "Unsupported action."}, status=400)

		try:
			cid = int(customer_id)
		except (TypeError, ValueError):
			return JsonResponse({"error": "customer_id must be an integer."}, status=400)

		user = UserAccount.objects.filter(
			id=cid,
			role=UserAccount.ROLE_CUSTOMER,
			is_active=True,
		).first()
		if user is None:
			return JsonResponse({"error": "Customer not found or inactive."}, status=404)

		parsed_item_id = None
		if item_id is not None:
			try:
				parsed_item_id = int(item_id)
			except (TypeError, ValueError):
				return JsonResponse({"error": "item_id must be an integer."}, status=400)

		parsed_quantity = 0
		if quantity not in (None, ""):
			try:
				parsed_quantity = int(quantity)
			except (TypeError, ValueError):
				return JsonResponse({"error": "quantity must be an integer."}, status=400)
			if parsed_quantity < 0:
				return JsonResponse({"error": "quantity must be >= 0."}, status=400)

		parsed_rating = None
		if rating_score not in (None, ""):
			try:
				parsed_rating = int(rating_score)
			except (TypeError, ValueError):
				return JsonResponse({"error": "rating_score must be an integer."}, status=400)
			if parsed_rating < 1 or parsed_rating > 5:
				return JsonResponse({"error": "rating_score must be between 1 and 5."}, status=400)

		activity = UserActivity.objects.create(
			user=user,
			action=action,
			item_type=item_type,
			item_id=parsed_item_id,
			quantity=parsed_quantity,
			rating_score=parsed_rating,
			metadata=metadata if isinstance(metadata, dict) else {},
		)

		if parsed_item_id is not None:
			if action == UserActivity.ACTION_VIEW_PRODUCT:
				_emit_kb_behavior_event(customer_id=user.id, event_type="VIEWED", product_id=parsed_item_id)
			elif action == UserActivity.ACTION_ADD_TO_CART:
				_emit_kb_behavior_event(customer_id=user.id, event_type="ADDED_TO_CART", product_id=parsed_item_id)

		return JsonResponse({"message": "Activity logged.", "activity_id": activity.id}, status=201)


@method_decorator(csrf_exempt, name="dispatch")
class RegisterStaffView(View):
	def post(self, request):
		body, error = _parse_json_body(request)
		if error:
			return error

		username = (body.get("username") or "").strip()
		password = body.get("password") or ""
		full_name = (body.get("full_name") or "").strip()
		role = (body.get("role") or UserAccount.ROLE_STAFF).strip().upper()

		if not username or not password or not full_name:
			return JsonResponse({"error": "username, password and full_name are required."}, status=400)
		if role not in {UserAccount.ROLE_ADMIN, UserAccount.ROLE_STAFF}:
			return JsonResponse({"error": "role must be ADMIN or STAFF."}, status=400)

		has_admin = UserAccount.objects.filter(role=UserAccount.ROLE_ADMIN).exists()
		if has_admin and not _is_admin_request(request):
			return JsonResponse({"error": "Only admin can create staff/admin accounts."}, status=403)
		if UserAccount.objects.filter(username=username).exists():
			return JsonResponse({"error": "Username already exists."}, status=409)

		user = UserAccount(username=username, full_name=full_name, role=role)
		user.set_password(password)
		user.save()

		return JsonResponse(
			{
				"message": "Account registered successfully.",
				"staff_id": user.id,
				"username": user.username,
				"role": user.role,
				"permissions": _permissions_for_role(user.role),
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
		role = (body.get("role") or "").strip().upper()

		if not username or not password:
			return JsonResponse({"error": "username and password are required."}, status=400)

		user = UserAccount.objects.filter(username=username).first()
		if user is None or not user.verify_password(password):
			return JsonResponse({"error": "Invalid credentials."}, status=401)
		if user.role not in {UserAccount.ROLE_STAFF, UserAccount.ROLE_ADMIN}:
			return JsonResponse({"error": "This account is not a staff/admin account."}, status=403)
		if role and role != user.role:
			return JsonResponse({"error": "Role does not match this account."}, status=403)
		if not user.is_active:
			return JsonResponse({"error": "Staff account is inactive."}, status=403)

		return JsonResponse(
			{
				"message": "Login successful.",
				"staff_id": user.id,
				"username": user.username,
				"full_name": user.full_name,
				"role": user.role,
				"permissions": _permissions_for_role(user.role),
			}
		)


@method_decorator(csrf_exempt, name="dispatch")
class StaffPermissionView(View):
	def get(self, request):
		role = _actor_role(request)
		if role not in {UserAccount.ROLE_ADMIN, UserAccount.ROLE_STAFF}:
			return JsonResponse({"error": "Authentication is required."}, status=401)
		return JsonResponse({"role": role, "permissions": _permissions_for_role(role)})


@method_decorator(csrf_exempt, name="dispatch")
class StaffAccountView(View):
	def get(self, request):
		forbidden = _require_admin(request)
		if forbidden:
			return forbidden

		query = (request.GET.get("q") or "").strip().lower()
		role = (request.GET.get("role") or "").strip().upper()
		active_text = (request.GET.get("is_active") or "").strip().lower()

		accounts = UserAccount.objects.exclude(role=UserAccount.ROLE_CUSTOMER).order_by("-id")
		if query:
			accounts = accounts.filter(username__icontains=query)
		if role in {UserAccount.ROLE_ADMIN, UserAccount.ROLE_STAFF}:
			accounts = accounts.filter(role=role)
		if active_text in {"true", "false"}:
			accounts = accounts.filter(is_active=(active_text == "true"))

		rows = [
			{
				"id": item.id,
				"username": item.username,
				"full_name": item.full_name,
				"role": item.role,
				"is_active": item.is_active,
				"created_at": item.created_at.isoformat() if item.created_at else None,
			}
			for item in accounts
		]
		return JsonResponse({"count": len(rows), "data": rows})

	def post(self, request):
		forbidden = _require_admin(request)
		if forbidden:
			return forbidden

		body, error = _parse_json_body(request)
		if error:
			return error

		username = (body.get("username") or "").strip()
		password = body.get("password") or ""
		full_name = (body.get("full_name") or "").strip()
		role = (body.get("role") or UserAccount.ROLE_STAFF).strip().upper()
		is_active = bool(body.get("is_active", True))

		if not username or not password or not full_name:
			return JsonResponse({"error": "username, password and full_name are required."}, status=400)
		if role not in {UserAccount.ROLE_ADMIN, UserAccount.ROLE_STAFF}:
			return JsonResponse({"error": "role must be ADMIN or STAFF."}, status=400)
		if UserAccount.objects.filter(username=username).exists():
			return JsonResponse({"error": "Username already exists."}, status=409)

		user = UserAccount(username=username, full_name=full_name, role=role, is_active=is_active)
		user.set_password(password)
		user.save()

		return JsonResponse(
			{
				"message": "Account created successfully.",
				"id": user.id,
				"username": user.username,
				"full_name": user.full_name,
				"role": user.role,
				"is_active": user.is_active,
				"permissions": _permissions_for_role(user.role),
			},
			status=201,
		)


@method_decorator(csrf_exempt, name="dispatch")
class StaffAccountDetailView(View):
	def patch(self, request, staff_id):
		forbidden = _require_admin(request)
		if forbidden:
			return forbidden

		body, error = _parse_json_body(request)
		if error:
			return error

		user = UserAccount.objects.filter(id=staff_id).exclude(role=UserAccount.ROLE_CUSTOMER).first()
		if user is None:
			return JsonResponse({"error": "Account not found."}, status=404)

		update_fields = []
		if "full_name" in body:
			user.full_name = (body.get("full_name") or "").strip()
			update_fields.append("full_name")
		if "is_active" in body:
			user.is_active = bool(body.get("is_active"))
			update_fields.append("is_active")
		if "role" in body:
			new_role = (body.get("role") or "").strip().upper()
			if new_role not in {UserAccount.ROLE_ADMIN, UserAccount.ROLE_STAFF}:
				return JsonResponse({"error": "role must be ADMIN or STAFF."}, status=400)
			if (
				user.role == UserAccount.ROLE_ADMIN
				and new_role != UserAccount.ROLE_ADMIN
				and UserAccount.objects.filter(role=UserAccount.ROLE_ADMIN, is_active=True).count() <= 1
			):
				return JsonResponse({"error": "Cannot demote the last active admin."}, status=400)
			user.role = new_role
			update_fields.append("role")
		if "password" in body:
			new_password = body.get("password") or ""
			if not new_password:
				return JsonResponse({"error": "password cannot be empty."}, status=400)
			user.set_password(new_password)
			update_fields.append("password")

		if not update_fields:
			return JsonResponse({"error": "No valid fields to update."}, status=400)

		user.save(update_fields=update_fields)
		return JsonResponse(
			{
				"id": user.id,
				"username": user.username,
				"full_name": user.full_name,
				"role": user.role,
				"is_active": user.is_active,
				"created_at": user.created_at.isoformat() if user.created_at else None,
				"permissions": _permissions_for_role(user.role),
			}
		)

	def delete(self, request, staff_id):
		forbidden = _require_admin(request)
		if forbidden:
			return forbidden

		user = UserAccount.objects.filter(id=staff_id).exclude(role=UserAccount.ROLE_CUSTOMER).first()
		if user is None:
			return JsonResponse({"error": "Account not found."}, status=404)
		if _actor_id(request) == user.id:
			return JsonResponse({"error": "You cannot delete your own account."}, status=400)
		if (
			user.role == UserAccount.ROLE_ADMIN
			and UserAccount.objects.filter(role=UserAccount.ROLE_ADMIN, is_active=True).count() <= 1
		):
			return JsonResponse({"error": "Cannot delete the last active admin."}, status=400)

		user.delete()
		return JsonResponse({"message": "Account deleted successfully."})


@method_decorator(csrf_exempt, name="dispatch")
class CreateItemView(View):
	def get(self, request):
		actor_role = _actor_role(request)
		if actor_role not in {UserAccount.ROLE_STAFF, UserAccount.ROLE_ADMIN}:
			return JsonResponse({"error": "STAFF or ADMIN role is required."}, status=403)

		p_status, p_data = _fetch_all_product_rows()
		if p_status == 200:
			rows = _normalize_product_rows(p_data)
			combined = [_product_to_staff_item(row) for row in rows]
			return JsonResponse({"count": len(combined), "data": combined})
		return JsonResponse(p_data if isinstance(p_data, dict) else {"error": "Cannot load items."}, status=p_status)

	def post(self, request):
		actor_role = _actor_role(request)
		if actor_role not in {UserAccount.ROLE_STAFF, UserAccount.ROLE_ADMIN}:
			return JsonResponse({"error": "STAFF or ADMIN role is required."}, status=403)

		body, error = _parse_json_body(request)
		if error:
			return error

		name = (body.get("name") or "").strip()
		item_type = (body.get("item_type") or "").strip().lower()
		price = _validate_price(body.get("price") or body.get("base_price"))
		stock = _validate_quantity(body.get("stock") or body.get("quantity") or body.get("stock"))
		description = (body.get("description") or "").strip()
		image_url = (body.get("image_url") or body.get("imageUrl") or "").strip()
		product_type = (body.get("product_type") or "").strip().upper()
		if not product_type:
			if item_type in {"mobile", "laptop"}:
				product_type = "ELECTRONICS"
			elif item_type == "book":
				product_type = "BOOK"
			elif item_type == "fashion":
				product_type = "FASHION"


		if not name:
			return JsonResponse({"error": "name is required."}, status=400)
		if price is None:
			return JsonResponse({"error": "price must be a non-negative number."}, status=400)
		# default stock to 1 when not provided
		if stock is None:
			stock = 1
		if product_type not in {"BOOK", "ELECTRONICS", "FASHION"}:
			return JsonResponse({"error": "product_type is required and must be BOOK, ELECTRONICS, or FASHION."}, status=400)

		category_id = body.get("category_id")
		try:
			if category_id is not None:
				category_id = int(category_id)
			else:
				category_id = _default_category_id_for_type(item_type or product_type.lower())
		except (TypeError, ValueError):
			return JsonResponse({"error": "category_id must be an integer."}, status=400)

		status_value = "ACTIVE" if stock > 0 else "INACTIVE"
		payload = {
			"name": name,
			"price": float(price),
			"stock": int(stock),
			"category_id": category_id,
			"product_type": product_type,
			"image_url": image_url,
		}

		if product_type == "BOOK":
			payload["author"] = (body.get("author") or body.get("brand") or "").strip()
			payload["publisher"] = (body.get("publisher") or "").strip()
			payload["isbn"] = (body.get("isbn") or "").strip()
		elif product_type == "FASHION":
			payload["size"] = (body.get("size") or "").strip()
			payload["color"] = (body.get("color") or "").strip()
		else:
			brand = (body.get("brand") or "").strip()
			if not brand:
				return JsonResponse({"error": "brand is required for ELECTRONICS products."}, status=400)
			payload["brand"] = brand
			payload["warranty"] = int(body.get("warranty") or 12)

		status, data = _call_service("POST", _service_url("product"), "/products/", payload)
		if status in (200, 201) and isinstance(data, dict):
			return JsonResponse(_product_to_staff_item(data), status=201)
		return JsonResponse(data if isinstance(data, dict) else {"error": "Create failed."}, status=status)


@method_decorator(csrf_exempt, name="dispatch")
class UpdateItemView(View):
	def get(self, request, item_id):
		actor_role = _actor_role(request)
		if actor_role not in {UserAccount.ROLE_STAFF, UserAccount.ROLE_ADMIN}:
			return JsonResponse({"error": "STAFF or ADMIN role is required."}, status=403)

		p_status, p_data = _call_service("GET", _service_url("product"), f"/products/{item_id}/")
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
		if _actor_role(request) != UserAccount.ROLE_ADMIN:
			return JsonResponse({"error": "ADMIN role is required to delete products."}, status=403)

		p_status, p_data = _call_service("DELETE", _service_url("product"), f"/products/{item_id}/")
		if p_status in (200, 204):
			return JsonResponse({"message": "Item deleted successfully."}, status=200)
		if p_status == 404:
			return JsonResponse({"error": "Item not found."}, status=404)
		return JsonResponse(p_data if isinstance(p_data, dict) else {"error": "Delete failed."}, status=p_status)

	def _update_item(self, request, item_id):
		actor_role = _actor_role(request)
		if actor_role not in {UserAccount.ROLE_STAFF, UserAccount.ROLE_ADMIN}:
			return JsonResponse({"error": "STAFF or ADMIN role is required."}, status=403)

		body, error = _parse_json_body(request)
		if error:
			return error

		p_payload = {}
		if "name" in body:
			p_payload["name"] = body.get("name")
		if "description" in body:
			p_payload["description"] = body.get("description")
		if "image_url" in body or "imageUrl" in body:
			p_payload["image_url"] = body.get("image_url") or body.get("imageUrl")
		if "brand" in body:
			p_payload["brand"] = body.get("brand")
		if "price" in body:
			price = _validate_price(body.get("price"))
			if price is None:
				return JsonResponse({"error": "price must be a non-negative number."}, status=400)
			p_payload["price"] = float(price)
		if "category_id" in body:
			try:
				p_payload["category_id"] = int(body.get("category_id"))
			except (TypeError, ValueError):
				return JsonResponse({"error": "category_id must be an integer."}, status=400)
		if "product_type" in body:
			product_type = (body.get("product_type") or "").strip().upper()
			if product_type not in {"BOOK", "ELECTRONICS", "FASHION"}:
				return JsonResponse({"error": "product_type must be BOOK, ELECTRONICS, or FASHION."}, status=400)
			p_payload["product_type"] = product_type
		if "stock" in body:
			try:
				qty = int(body.get("stock"))
				if qty < 0:
					raise ValueError()
				p_payload["stock"] = qty
			except (TypeError, ValueError):
				return JsonResponse({"error": "stock must be a non-negative integer."}, status=400)

		if not p_payload:
			return JsonResponse({"error": "No valid fields to update."}, status=400)

		p_status, p_data = _call_service("PATCH", _service_url("product"), f"/products/{item_id}/", p_payload)
		if p_status == 200 and isinstance(p_data, dict):
			return JsonResponse(_product_to_staff_item(p_data), status=200)
		if p_status == 404:
			return JsonResponse({"error": "Item not found."}, status=404)
		return JsonResponse(p_data if isinstance(p_data, dict) else {"error": "Update failed."}, status=p_status)
