import json
import urllib.error
import urllib.request
import os
from datetime import datetime, timezone

from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import Cart, CartItem, CustomerAccount, Rating, SearchHistory, UserActivity


def _utc_now_iso():
	return datetime.now(timezone.utc).isoformat()


def _emit_kb_behavior_event(customer_id, event_type, product_id=None, query=None, rating=None, timestamp=None):
	# Fire-and-forget sync so business APIs stay responsive even when KB is unavailable.
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
		# Never break user flow because of telemetry sync failures.
		return


def _build_cart_response(cart):
	# Build cart response with item details fetched from services
	items = []
	total = 0
	for it in cart.items.all():
		status, data = _call_service("GET", _service_url("product"), f"/api/products/{it.item_id}/")
		name = data.get("name") if isinstance(data, dict) else None
		price = data.get("base_price") if isinstance(data, dict) else None

		try:
			price_num = float(price) if price is not None else 0
		except Exception:
			price_num = 0

		line_total = price_num * it.quantity
		total += line_total

		items.append({
			"id": it.id,
			"item_type": it.item_type,
			"item_id": it.item_id,
			"name": name or "Không có tên",
			"quantity": it.quantity,
			"price": price_num,
			"line_total": line_total,
		})

	response = {
		"id": cart.id,
		"customer_id": cart.customer.id,
		"items_count": cart.items.count(),
		"total": total,
		"items": items,
	}
	return response


def _parse_json_body(request):
	try:
		return json.loads(request.body or "{}"), None
	except json.JSONDecodeError:
		return None, JsonResponse({"error": "Invalid JSON body."}, status=400)


def _log_activity(
	customer,
	action,
	item_type="",
	item_id=None,
	quantity=0,
	rating_score=None,
	metadata=None,
):
	try:
		UserActivity.objects.create(
			customer=customer,
			action=action,
			item_type=item_type or "",
			item_id=item_id,
			quantity=quantity if quantity and quantity > 0 else 0,
			rating_score=rating_score,
			metadata=metadata or {},
		)
	except Exception:
		# Logging activity should never break main business flow.
		pass


@method_decorator(csrf_exempt, name="dispatch")
class CreateCartView(View):
	def post(self, request):
		body, error = _parse_json_body(request)
		if error:
			return error

		customer_id = body.get("customer_id")
		if customer_id is None:
			return JsonResponse({"error": "customer_id is required."}, status=400)

		customer = CustomerAccount.objects.filter(id=customer_id).first()
		if customer is None:
			return JsonResponse({"error": "Customer not found."}, status=404)
		if not customer.is_active:
			return JsonResponse({"error": "Customer is inactive."}, status=403)

		# Return existing cart if one exists for this customer (single active cart behavior)
		cart = Cart.objects.filter(customer=customer).order_by("-id").first()
		if cart is None:
			cart = Cart.objects.create(customer=customer)
			status_code = 201
		else:
			status_code = 200

		response = _build_cart_response(cart)
		return JsonResponse(response, status=status_code)

	def get(self, request):
		# Allow fetching cart by customer_id (query param) or cart_id
		customer_id = request.GET.get("customer_id")
		cart_id = request.GET.get("cart_id")
		if not customer_id and not cart_id:
			return JsonResponse({"error": "customer_id or cart_id is required."}, status=400)

		if cart_id:
			cart = Cart.objects.filter(id=cart_id).first()
		else:
			customer = CustomerAccount.objects.filter(id=customer_id).first()
			if customer is None:
				return JsonResponse({"error": "Customer not found."}, status=404)
			cart = Cart.objects.filter(customer=customer).order_by("-id").first()

		if cart is None:
			return JsonResponse({"error": "Cart not found."}, status=404)

		response = _build_cart_response(cart)
		return JsonResponse(response)


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
		if CustomerAccount.objects.filter(username=username).exists():
			return JsonResponse({"error": "Username already exists."}, status=409)

		customer = CustomerAccount(
			username=username,
			full_name=full_name,
			role=CustomerAccount.ROLE_CUSTOMER,
		)
		customer.set_password(password)
		customer.save()

		return JsonResponse(
			{
				"message": "Customer registered successfully.",
				"customer_id": customer.id,
				"username": customer.username,
				"role": customer.role,
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
			return JsonResponse(
				{"error": "username and password are required."},
				status=400,
			)

		customer = CustomerAccount.objects.filter(username=username).first()
		if customer is None or not customer.verify_password(password):
			return JsonResponse({"error": "Invalid credentials."}, status=401)
		if not customer.is_active:
			return JsonResponse({"error": "Customer is inactive."}, status=403)

		return JsonResponse(
			{
				"message": "Login successful.",
				"customer_id": customer.id,
				"username": customer.username,
				"full_name": customer.full_name,
				"role": customer.role,
			}
		)


@method_decorator(csrf_exempt, name="dispatch")
class CustomerAccountView(View):
	def get(self, request):
		query = (request.GET.get("q") or "").strip().lower()
		active_text = (request.GET.get("is_active") or "").strip().lower()

		accounts = CustomerAccount.objects.all().order_by("-id")
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

		customer = CustomerAccount.objects.filter(id=customer_id).first()
		if customer is None:
			return JsonResponse({"error": "Customer not found."}, status=404)

		if "full_name" in body:
			customer.full_name = (body.get("full_name") or "").strip()

		if "is_active" in body:
			customer.is_active = bool(body.get("is_active"))

		customer.save(update_fields=["full_name", "is_active"])

		return JsonResponse(
			{
				"id": customer.id,
				"username": customer.username,
				"full_name": customer.full_name,
				"role": customer.role,
				"is_active": customer.is_active,
				"created_at": customer.created_at.isoformat() if customer.created_at else None,
			}
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
			customer = CustomerAccount.objects.filter(id=customer_id).first()

		SearchHistory.objects.create(customer=customer, keyword=keyword)
		if customer is not None:
			_emit_kb_behavior_event(
				customer_id=customer.id,
				event_type="SEARCHED",
				query=keyword,
			)

		return JsonResponse(
			{
				"message": "Search keyword recorded successfully.",
				"keyword": keyword,
				"customer_id": customer.id if customer else None,
				"next": "Use api-gateway to query product-service by keyword.",
			}
		)


def _service_url(name):
	if name == "product":
		return os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8003")
	return None


def _call_service(method, base_url, path, timeout=10):
	url = f"{base_url.rstrip('/')}{path}"
	req = urllib.request.Request(url=url, method=method, headers={"Accept": "application/json"})
	try:
		with urllib.request.urlopen(req, timeout=timeout) as resp:
			raw = resp.read()
			try:
				return resp.getcode(), json.loads(raw.decode("utf-8") or "{}")
			except json.JSONDecodeError:
				return resp.getcode(), {"message": raw.decode("utf-8", errors="ignore")}
	except urllib.error.HTTPError as exc:
		raw = exc.read()
		try:
			return exc.code, json.loads(raw.decode("utf-8") or "{}")
		except json.JSONDecodeError:
			return exc.code, {"message": raw.decode("utf-8", errors="ignore")}
	except urllib.error.URLError as exc:
		return 502, {"error": "Cannot connect to service", "details": str(exc)}


@method_decorator(csrf_exempt, name="dispatch")
class AddCartItemView(View):
	def post(self, request):
		body, error = _parse_json_body(request)
		if error:
			return error

		cart_id = body.get("cart_id")
		# support product_id (frontend) as alias for item_id
		item_id = body.get("item_id") or body.get("product_id") or body.get("productId")
		item_type = (body.get("item_type") or "product").strip().lower()
		quantity = body.get("quantity") or 1

		# If cart_id not provided, allow creating/finding cart by customer_id
		if cart_id is None:
			customer_id = body.get("customer_id")
			if customer_id is None:
				return JsonResponse({"error": "cart_id or customer_id is required."}, status=400)
			customer = CustomerAccount.objects.filter(id=customer_id).first()
			if customer is None:
				return JsonResponse({"error": "Customer not found."}, status=404)
			if not customer.is_active:
				return JsonResponse({"error": "Customer is inactive."}, status=403)

			# find latest cart or create one
			cart = Cart.objects.filter(customer=customer).order_by("-id").first()
			if cart is None:
				cart = Cart.objects.create(customer=customer)
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

		product_status, product_data = _call_service("GET", _service_url("product"), f"/api/products/{int(item_id)}/")
		if product_status >= 400:
			return JsonResponse(
				product_data if isinstance(product_data, dict) else {"error": "Product not found."},
				status=product_status,
			)

		ci = CartItem.objects.create(cart=cart, item_type=item_type or "product", item_id=int(item_id), quantity=qty)
		_log_activity(
			customer=cart.customer,
			action=UserActivity.ACTION_ADD_TO_CART,
			item_type=item_type,
			item_id=int(item_id),
			quantity=qty,
			metadata={"cart_id": cart.id, "cart_item_id": ci.id},
		)
		_emit_kb_behavior_event(
			customer_id=cart.customer_id,
			event_type="ADDED_TO_CART",
			product_id=int(item_id),
		)

		response = _build_cart_response(cart)
		return JsonResponse(response)


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

		cart_item = CartItem.objects.select_related("cart", "cart__customer").filter(id=cart_item_id).first()
		if cart_item is None:
			return JsonResponse({"error": "Cart item not found."}, status=404)

		cart_item.quantity = qty
		cart_item.save(update_fields=["quantity"])

		response = _build_cart_response(cart_item.cart)
		return JsonResponse(response, status=200)

	def delete(self, request, cart_item_id):
		cart_item = CartItem.objects.select_related("cart", "cart__customer").filter(id=cart_item_id).first()
		if cart_item is None:
			return JsonResponse({"error": "Cart item not found."}, status=404)

		cart = cart_item.cart
		cart_item.delete()

		response = _build_cart_response(cart)
		return JsonResponse(response, status=200)


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
			customer = CustomerAccount.objects.filter(id=customer_id, is_active=True).first()
			if customer is None:
				return JsonResponse({"error": "Customer not found or inactive."}, status=404)
			cart = Cart.objects.filter(customer=customer).order_by("-id").first()

		if cart is None:
			return JsonResponse({"error": "Cart not found."}, status=404)

		deleted_items = cart.items.count()
		cart.items.all().delete()

		return JsonResponse(
			{
				"message": "Cart cleared.",
				"cart_id": cart.id,
				"customer_id": cart.customer_id,
				"deleted_items": deleted_items,
			},
			status=200,
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
			my_rating = ratings.filter(customer_id=cid).first()
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
			return JsonResponse(
				{"error": "customer_id, item_id and score are required."},
				status=400,
			)
		if not item_type:
			return JsonResponse({"error": "item_type is required."}, status=400)

		try:
			cid = int(customer_id)
			pid = int(item_id)
			score_value = int(score)
		except (TypeError, ValueError):
			return JsonResponse(
				{"error": "customer_id, item_id and score must be integers."},
				status=400,
			)

		if score_value < 1 or score_value > 5:
			return JsonResponse({"error": "score must be between 1 and 5."}, status=400)

		customer = CustomerAccount.objects.filter(id=cid, is_active=True).first()
		if customer is None:
			return JsonResponse({"error": "Customer not found or inactive."}, status=404)

		rating, created = Rating.objects.update_or_create(
			customer=customer,
			item_type=item_type,
			item_id=pid,
			defaults={"score": score_value, "review": review},
		)
		_log_activity(
			customer=customer,
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
			activities = activities.filter(customer_id=cid)

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
				"customer_id",
				"action",
				"item_type",
				"item_id",
				"quantity",
				"rating_score",
				"metadata",
				"created_at",
			)[:limit]
		)

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

		customer = CustomerAccount.objects.filter(id=cid, is_active=True).first()
		if customer is None:
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
			customer=customer,
			action=action,
			item_type=item_type,
			item_id=parsed_item_id,
			quantity=parsed_quantity,
			rating_score=parsed_rating,
			metadata=metadata if isinstance(metadata, dict) else {},
		)

		if parsed_item_id is not None:
			if action == UserActivity.ACTION_VIEW_PRODUCT:
				_emit_kb_behavior_event(
					customer_id=customer.id,
					event_type="VIEWED",
					product_id=parsed_item_id,
				)
			elif action == UserActivity.ACTION_ADD_TO_CART:
				_emit_kb_behavior_event(
					customer_id=customer.id,
					event_type="ADDED_TO_CART",
					product_id=parsed_item_id,
				)

		return JsonResponse(
			{
				"message": "Activity logged.",
				"activity_id": activity.id,
			},
			status=201,
		)
