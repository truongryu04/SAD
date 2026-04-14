import json
import time
import urllib.error
import urllib.request

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import ApiRequestLog


def _parse_json_body(request):
	try:
		return json.loads(request.body or "{}"), None
	except json.JSONDecodeError:
		return None, JsonResponse({"error": "Invalid JSON body."}, status=400)


def _build_target_url(base_url, path, query_string=""):
	target = f"{base_url.rstrip('/')}{path}"
	if query_string:
		target = f"{target}?{query_string}"
	return target


def _json_response_from_raw(raw_body, status_code):
	text = raw_body.decode("utf-8", errors="ignore")
	try:
		payload = json.loads(text) if text else {}
	except json.JSONDecodeError:
		payload = {"message": text}
	return JsonResponse(payload, status=status_code)


def _log_proxy_call(service_name, request, status_code):
	try:
		ApiRequestLog.objects.create(
			service_name=service_name,
			method=request.method,
			path=request.path,
			status_code=status_code,
		)
	except Exception:
		pass


def _proxy_request(request, service_name, service_base_url, service_path, timeout=20):
	target_url = _build_target_url(
		service_base_url,
		service_path,
		request.META.get("QUERY_STRING", ""),
	)

	headers = {"Accept": "application/json"}
	if request.content_type:
		headers["Content-Type"] = request.content_type

	data = request.body if request.method in {"POST", "PUT", "PATCH"} else None
	outbound = urllib.request.Request(
		url=target_url,
		data=data if data else None,
		method=request.method,
		headers=headers,
	)

	try:
		with urllib.request.urlopen(outbound, timeout=timeout) as response:
			raw_body = response.read()
			status_code = response.getcode()
			content_type = response.headers.get("Content-Type", "application/json")
	except urllib.error.HTTPError as exc:
		raw_body = exc.read()
		status_code = exc.code
		content_type = exc.headers.get("Content-Type", "application/json")
	except urllib.error.URLError as exc:
		status_code = 502
		# include exception details to aid debugging (connection refused, name resolution, timeout...)
		raw_body = json.dumps(
			{
				"error": f"Cannot connect to {service_name} service.",
				"details": str(exc),
			}
		).encode("utf-8")
		content_type = "application/json"

	_log_proxy_call(service_name, request, status_code)
	return HttpResponse(raw_body, status=status_code, content_type=content_type)


def _call_login_service(role, username, password):
	normalized_role = (role or "").strip().upper()
	if normalized_role == "CUSTOMER":
		service_name = "customer"
		base_url = settings.CUSTOMER_SERVICE_URL
		path = "/customer/login/"
		id_key = "customer_id"
		dashboard_url = "/ui/customer/"
	elif normalized_role == "STAFF":
		service_name = "staff"
		base_url = settings.STAFF_SERVICE_URL
		path = "/staff/login/"
		id_key = "staff_id"
		dashboard_url = "/ui/staff/"
	else:
		return {
			"ok": False,
			"status": 400,
			"data": {"error": "role must be CUSTOMER or STAFF."},
			"id_key": None,
			"dashboard_url": "/",
		}

	payload = json.dumps({"username": username, "password": password}).encode("utf-8")
	outbound = urllib.request.Request(
		url=_build_target_url(base_url, path),
		data=payload,
		method="POST",
		headers={"Content-Type": "application/json", "Accept": "application/json"},
	)

	try:
		with urllib.request.urlopen(outbound, timeout=20) as response:
			raw_body = response.read()
			status_code = response.getcode()
	except urllib.error.HTTPError as exc:
		raw_body = exc.read()
		status_code = exc.code
	except urllib.error.URLError:
		return {
			"ok": False,
			"status": 502,
			"data": {"error": f"Cannot connect to {service_name} service."},
			"id_key": id_key,
			"dashboard_url": dashboard_url,
		}

	try:
		data = json.loads(raw_body.decode("utf-8") or "{}")
	except json.JSONDecodeError:
		data = {"message": raw_body.decode("utf-8", errors="ignore")}

	if not isinstance(data, dict):
		data = {"message": str(data)}

	return {
		"ok": status_code < 400,
		"status": status_code,
		"data": data,
		"id_key": id_key,
		"dashboard_url": dashboard_url,
	}


def _call_register_service(role, username, password, full_name):
	normalized_role = (role or "").strip().upper()
	if normalized_role == "CUSTOMER":
		service_name = "customer"
		base_url = settings.CUSTOMER_SERVICE_URL
		path = "/customer/register/"
	elif normalized_role == "STAFF":
		service_name = "staff"
		base_url = settings.STAFF_SERVICE_URL
		path = "/staff/register/"
	else:
		return {
			"ok": False,
			"status": 400,
			"data": {"error": "role must be CUSTOMER or STAFF."},
		}

	payload = json.dumps(
		{
			"username": username,
			"password": password,
			"full_name": full_name,
		}
	).encode("utf-8")
	outbound = urllib.request.Request(
		url=_build_target_url(base_url, path),
		data=payload,
		method="POST",
		headers={"Content-Type": "application/json", "Accept": "application/json"},
	)

	try:
		with urllib.request.urlopen(outbound, timeout=20) as response:
			raw_body = response.read()
			status_code = response.getcode()
	except urllib.error.HTTPError as exc:
		raw_body = exc.read()
		status_code = exc.code
	except urllib.error.URLError:
		return {
			"ok": False,
			"status": 502,
			"data": {"error": f"Cannot connect to {service_name} service."},
		}

	try:
		data = json.loads(raw_body.decode("utf-8") or "{}")
	except json.JSONDecodeError:
		data = {"message": raw_body.decode("utf-8", errors="ignore")}

	if not isinstance(data, dict):
		data = {"message": str(data)}

	return {
		"ok": status_code < 400,
		"status": status_code,
		"data": data,
	}


def _save_login_session(request, login_payload, id_key, fallback_role):
	request.session["is_authenticated"] = True
	request.session["role"] = (login_payload.get("role") or fallback_role).upper()
	request.session["username"] = login_payload.get("username", "")
	request.session["full_name"] = login_payload.get("full_name", "")
	request.session["user_id"] = login_payload.get(id_key)


def _has_role(request, role):
	return request.session.get("is_authenticated") and request.session.get("role") == role


def _emit_view_activity(customer_service_url, customer_id, product_id):
	if not customer_service_url:
		return
	payload = {
		"customer_id": int(customer_id),
		"action": "VIEW_PRODUCT",
		"item_type": "product",
		"item_id": int(product_id),
		"quantity": 1,
	}
	request = urllib.request.Request(
		url=f"{customer_service_url.rstrip('/')}/customer/activities/",
		method="POST",
		headers={"Content-Type": "application/json", "Accept": "application/json"},
		data=json.dumps(payload).encode("utf-8"),
	)
	try:
		with urllib.request.urlopen(request, timeout=3):
			return
	except (urllib.error.HTTPError, urllib.error.URLError, ValueError, TypeError):
		# Tracking must never block page rendering.
		return


def _should_emit_view_event(request, customer_id, product_id):
	window_seconds = max(1, int(getattr(settings, "VIEWED_EVENT_WINDOW_SECONDS", 300)))
	now = int(time.time())
	dedupe_key = f"{int(customer_id)}:{int(product_id)}"

	guard = request.session.get("viewed_event_guard", {})
	if not isinstance(guard, dict):
		guard = {}

	last_seen = guard.get(dedupe_key)
	try:
		last_seen = int(last_seen)
	except (TypeError, ValueError):
		last_seen = 0

	if last_seen and (now - last_seen) < window_seconds:
		return False

	# Keep only recent keys to prevent session payload growth.
	min_keep = now - (window_seconds * 2)
	pruned_guard = {}
	for key, ts in guard.items():
		try:
			parsed = int(ts)
		except (TypeError, ValueError):
			continue
		if parsed >= min_keep:
			pruned_guard[key] = parsed

	pruned_guard[dedupe_key] = now
	request.session["viewed_event_guard"] = pruned_guard
	request.session.modified = True
	return True


class LoginPageView(View):
	def get(self, request):
		if _has_role(request, "CUSTOMER"):
			return redirect("/ui/customer/")
		if _has_role(request, "STAFF"):
			return redirect("/ui/staff/")
		info = ""
		if request.GET.get("info") == "registered":
			info = "Register successful. Please login."
		return render(
			request,
			"app/login.html",
			{"error": "", "info": info, "role": "CUSTOMER"},
		)


class RegisterPageView(View):
	def get(self, request):
		if _has_role(request, "CUSTOMER"):
			return redirect("/ui/customer/")
		if _has_role(request, "STAFF"):
			return redirect("/ui/staff/")
		return render(
			request,
			"app/register.html",
			{"error": "", "role": "CUSTOMER", "username": "", "full_name": ""},
		)

	def post(self, request):
		username = (request.POST.get("username") or "").strip()
		password = request.POST.get("password") or ""
		full_name = (request.POST.get("full_name") or "").strip()
		role = (request.POST.get("role") or "").strip().upper()

		if not username or not password or not full_name:
			return render(
				request,
				"app/register.html",
				{
					"error": "username, password and full_name are required.",
					"role": role or "CUSTOMER",
					"username": username,
					"full_name": full_name,
				},
			)

		register_result = _call_register_service(role, username, password, full_name)
		if not register_result["ok"]:
			error_message = register_result["data"].get("error", "Register failed.")
			return render(
				request,
				"app/register.html",
				{
					"error": error_message,
					"role": role or "CUSTOMER",
					"username": username,
					"full_name": full_name,
				},
			)

		return redirect("/?info=registered")


class UiLoginView(View):
	def post(self, request):
		username = (request.POST.get("username") or "").strip()
		password = request.POST.get("password") or ""
		role = (request.POST.get("role") or "").strip().upper()

		if not username or not password:
			return render(
				request,
				"app/login.html",
				{
					"error": "username and password are required.",
					"info": "",
					"role": role or "CUSTOMER",
				},
			)

		login_result = _call_login_service(role, username, password)
		if not login_result["ok"]:
			error_message = login_result["data"].get("error", "Login failed.")
			return render(
				request,
				"app/login.html",
				{"error": error_message, "info": "", "role": role or "CUSTOMER"},
			)

		_save_login_session(
			request,
			login_result["data"],
			login_result["id_key"],
			role,
		)
		return redirect(login_result["dashboard_url"])


class LogoutView(View):
	def get(self, request):
		request.session.flush()
		return redirect("/")


class CustomerDashboardView(View):
	def get(self, request):
		if not _has_role(request, "CUSTOMER"):
			return redirect("/")
		return render(
			request,
			"app/customer_dashboard.html",
			{
				"username": request.session.get("username"),
				"full_name": request.session.get("full_name"),
				"user_id": request.session.get("user_id"),
			},
		)


class CustomerCartPageView(View):
	def get(self, request):
		if not _has_role(request, "CUSTOMER"):
			return redirect("/")
		return render(
			request,
			"app/customer_cart.html",
			{
				"username": request.session.get("username"),
				"full_name": request.session.get("full_name"),
				"user_id": request.session.get("user_id"),
			},
		)


class CustomerProductsPageView(View):
	def get(self, request):
		if not _has_role(request, "CUSTOMER"):
			return redirect("/")
		return render(
			request,
			"app/customer_products.html",
			{
				"username": request.session.get("username"),
				"full_name": request.session.get("full_name"),
				"user_id": request.session.get("user_id"),
			},
		)


class CustomerProductDetailPageView(View):
	def get(self, request, product_id):
		if not _has_role(request, "CUSTOMER"):
			return redirect("/")
		customer_id = request.session.get("user_id")
		if customer_id and _should_emit_view_event(request, customer_id, product_id):
			_emit_view_activity(
				customer_service_url=settings.CUSTOMER_SERVICE_URL,
				customer_id=customer_id,
				product_id=product_id,
			)
		return render(
			request,
			"app/customer_product_detail.html",
			{
				"username": request.session.get("username"),
				"full_name": request.session.get("full_name"),
				"user_id": request.session.get("user_id"),
				"product_id": product_id,
			},
		)


class StaffDashboardView(View):
	def get(self, request):
		if not _has_role(request, "STAFF"):
			return redirect("/")
		return render(
			request,
			"app/staff_dashboard.html",
			{
				"username": request.session.get("username"),
				"full_name": request.session.get("full_name"),
				"user_id": request.session.get("user_id"),
			},
		)


class StaffProductPageView(View):
	def get(self, request):
		if not _has_role(request, "STAFF"):
			return redirect("/")
		return render(
			request,
			"app/staff_products.html",
			{
				"username": request.session.get("username"),
				"full_name": request.session.get("full_name"),
				"user_id": request.session.get("user_id"),
			},
		)


class StaffOrderPageView(View):
	def get(self, request):
		if not _has_role(request, "STAFF"):
			return redirect("/")
		return render(
			request,
			"app/staff_orders.html",
			{
				"username": request.session.get("username"),
				"full_name": request.session.get("full_name"),
				"user_id": request.session.get("user_id"),
			},
		)


class StaffCategoryPageView(View):
	def get(self, request):
		if not _has_role(request, "STAFF"):
			return redirect("/")
		return render(
			request,
			"app/staff_categories.html",
			{
				"username": request.session.get("username"),
				"full_name": request.session.get("full_name"),
				"user_id": request.session.get("user_id"),
			},
		)


class StaffCustomerPageView(View):
	def get(self, request):
		if not _has_role(request, "STAFF"):
			return redirect("/")
		return render(
			request,
			"app/staff_customers.html",
			{
				"username": request.session.get("username"),
				"full_name": request.session.get("full_name"),
				"user_id": request.session.get("user_id"),
			},
		)


@method_decorator(csrf_exempt, name="dispatch")
class ApiRoleRegisterView(View):
	def post(self, request):
		body, error = _parse_json_body(request)
		if error:
			return error

		username = (body.get("username") or "").strip()
		password = body.get("password") or ""
		full_name = (body.get("full_name") or "").strip()
		role = (body.get("role") or "").strip().upper()

		if not username or not password or not full_name:
			return JsonResponse(
				{"error": "username, password and full_name are required."},
				status=400,
			)

		register_result = _call_register_service(role, username, password, full_name)
		return JsonResponse(register_result["data"], status=register_result["status"])


@method_decorator(csrf_exempt, name="dispatch")
class ApiRoleLoginView(View):
	def post(self, request):
		body, error = _parse_json_body(request)
		if error:
			return error

		username = (body.get("username") or "").strip()
		password = body.get("password") or ""
		role = (body.get("role") or "").strip().upper()

		if not username or not password:
			return JsonResponse({"error": "username and password are required."}, status=400)

		login_result = _call_login_service(role, username, password)
		if not login_result["ok"]:
			return JsonResponse(login_result["data"], status=login_result["status"])

		_save_login_session(
			request,
			login_result["data"],
			login_result["id_key"],
			role,
		)

		response_payload = dict(login_result["data"])
		response_payload["dashboard_url"] = login_result["dashboard_url"]
		return JsonResponse(response_payload)


@method_decorator(csrf_exempt, name="dispatch")
class CustomerRegisterProxyView(View):
	def post(self, request):
		return _proxy_request(request, "customer", settings.CUSTOMER_SERVICE_URL, "/customer/register/")


@method_decorator(csrf_exempt, name="dispatch")
class CustomerLoginProxyView(View):
	def post(self, request):
		return _proxy_request(request, "customer", settings.CUSTOMER_SERVICE_URL, "/customer/login/")


@method_decorator(csrf_exempt, name="dispatch")
class CustomerAccountProxyView(View):
	def get(self, request):
		return _proxy_request(request, "customer", settings.CUSTOMER_SERVICE_URL, "/customer/accounts/")


@method_decorator(csrf_exempt, name="dispatch")
class CustomerAccountDetailProxyView(View):
	def patch(self, request, customer_id):
		return _proxy_request(request, "customer", settings.CUSTOMER_SERVICE_URL, f"/customer/accounts/{customer_id}/")


@method_decorator(csrf_exempt, name="dispatch")
class CustomerCartProxyView(View):
	def post(self, request):
		return _proxy_request(request, "customer", settings.CUSTOMER_SERVICE_URL, "/customer/carts/")

	def get(self, request):
		# Proxy GET to allow fetching cart by customer_id or cart_id
		return _proxy_request(request, "customer", settings.CUSTOMER_SERVICE_URL, "/customer/carts/")


@method_decorator(csrf_exempt, name="dispatch")
class CustomerCartItemProxyView(View):
	def post(self, request):
		# Proxy add-item-to-cart requests to customer service.
		# The customer service is expected to expose an endpoint that accepts
		# POST to /customer/carts/items/ (or similar). We forward the request body
		# as-is so the customer service can interpret product_id, quantity, etc.
		return _proxy_request(request, "customer", settings.CUSTOMER_SERVICE_URL, "/customer/carts/items/")


@method_decorator(csrf_exempt, name="dispatch")
class CustomerCartItemDetailProxyView(View):
	def patch(self, request, cart_item_id):
		return _proxy_request(request, "customer", settings.CUSTOMER_SERVICE_URL, f"/customer/carts/items/{cart_item_id}/")

	def delete(self, request, cart_item_id):
		return _proxy_request(request, "customer", settings.CUSTOMER_SERVICE_URL, f"/customer/carts/items/{cart_item_id}/")


@method_decorator(csrf_exempt, name="dispatch")
class OrderCheckoutProxyView(View):
	def post(self, request):
		return _proxy_request(request, "order", settings.ORDER_SERVICE_URL, "/orders/checkout/")


@method_decorator(csrf_exempt, name="dispatch")
class OrderProxyView(View):
	def get(self, request):
		return _proxy_request(request, "order", settings.ORDER_SERVICE_URL, "/orders/")


@method_decorator(csrf_exempt, name="dispatch")
class CategoryProxyView(View):
	def get(self, request):
		return _proxy_request(request, "category", settings.CATEGORY_SERVICE_URL, "/api/categories/")

	def post(self, request):
		return _proxy_request(request, "category", settings.CATEGORY_SERVICE_URL, "/api/categories/")


@method_decorator(csrf_exempt, name="dispatch")
class CategoryDetailProxyView(View):
	def get(self, request, category_id):
		return _proxy_request(request, "category", settings.CATEGORY_SERVICE_URL, f"/api/categories/{category_id}/")

	def put(self, request, category_id):
		return _proxy_request(request, "category", settings.CATEGORY_SERVICE_URL, f"/api/categories/{category_id}/")

	def patch(self, request, category_id):
		return _proxy_request(request, "category", settings.CATEGORY_SERVICE_URL, f"/api/categories/{category_id}/")

	def delete(self, request, category_id):
		return _proxy_request(request, "category", settings.CATEGORY_SERVICE_URL, f"/api/categories/{category_id}/")


@method_decorator(csrf_exempt, name="dispatch")
class ProductProxyView(View):
	def get(self, request):
		return _proxy_request(request, "product", settings.PRODUCT_SERVICE_URL, "/api/products/")

	def post(self, request):
		return _proxy_request(request, "product", settings.PRODUCT_SERVICE_URL, "/api/products/")


@method_decorator(csrf_exempt, name="dispatch")
class ProductDetailProxyView(View):
	def get(self, request, product_id):
		return _proxy_request(request, "product", settings.PRODUCT_SERVICE_URL, f"/api/products/{product_id}/")

	def put(self, request, product_id):
		return _proxy_request(request, "product", settings.PRODUCT_SERVICE_URL, f"/api/products/{product_id}/")

	def patch(self, request, product_id):
		return _proxy_request(request, "product", settings.PRODUCT_SERVICE_URL, f"/api/products/{product_id}/")

	def delete(self, request, product_id):
		return _proxy_request(request, "product", settings.PRODUCT_SERVICE_URL, f"/api/products/{product_id}/")


@method_decorator(csrf_exempt, name="dispatch")
class ProductCategoryAttributesProxyView(View):
	def get(self, request, category_id):
		return _proxy_request(request, "product", settings.PRODUCT_SERVICE_URL, f"/api/categories/{category_id}/attributes/")


@method_decorator(csrf_exempt, name="dispatch")
class AttributeProxyView(View):
	def get(self, request):
		return _proxy_request(request, "attribute", settings.ATTRIBUTE_SERVICE_URL, "/api/attributes/")

	def post(self, request):
		return _proxy_request(request, "attribute", settings.ATTRIBUTE_SERVICE_URL, "/api/attributes/")


@method_decorator(csrf_exempt, name="dispatch")
class CategoryAttributeProxyView(View):
	def get(self, request):
		return _proxy_request(request, "attribute", settings.ATTRIBUTE_SERVICE_URL, "/api/category-attributes/")

	def post(self, request):
		return _proxy_request(request, "attribute", settings.ATTRIBUTE_SERVICE_URL, "/api/category-attributes/")


@method_decorator(csrf_exempt, name="dispatch")
class ProductAttributeValueProxyView(View):
	def get(self, request):
		return _proxy_request(request, "attribute", settings.ATTRIBUTE_SERVICE_URL, "/api/product-attribute-values/")

	def post(self, request):
		return _proxy_request(request, "attribute", settings.ATTRIBUTE_SERVICE_URL, "/api/product-attribute-values/")


@method_decorator(csrf_exempt, name="dispatch")
class KBHealthProxyView(View):
	def get(self, request):
		return _proxy_request(request, "kb", settings.KB_SERVICE_URL, "/api/kb/health/")


@method_decorator(csrf_exempt, name="dispatch")
class KBCollectProxyView(View):
	def post(self, request):
		return _proxy_request(request, "kb", settings.KB_SERVICE_URL, "/api/kb/collect/", timeout=60)


@method_decorator(csrf_exempt, name="dispatch")
class KBSemanticSearchProxyView(View):
	def post(self, request):
		return _proxy_request(request, "kb", settings.KB_SERVICE_URL, "/api/kb/search/semantic/")


@method_decorator(csrf_exempt, name="dispatch")
class CustomerSearchProxyView(View):
	def get(self, request):
		return _proxy_request(request, "customer", settings.CUSTOMER_SERVICE_URL, "/customer/search/")


@method_decorator(csrf_exempt, name="dispatch")
class CustomerRatingProxyView(View):
	def get(self, request):
		return _proxy_request(request, "customer", settings.CUSTOMER_SERVICE_URL, "/customer/ratings/")

	def post(self, request):
		return _proxy_request(request, "customer", settings.CUSTOMER_SERVICE_URL, "/customer/ratings/")


@method_decorator(csrf_exempt, name="dispatch")
class CustomerActivityProxyView(View):
	def post(self, request):
		return _proxy_request(request, "customer", settings.CUSTOMER_SERVICE_URL, "/customer/activities/")


@method_decorator(csrf_exempt, name="dispatch")
class AIRecommendationProxyView(View):
	def get(self, request, customer_id):
		return _proxy_request(
			request,
			"ai",
			settings.AI_SERVICE_URL,
			f"/ai/recommendations/{customer_id}/",
		)


@method_decorator(csrf_exempt, name="dispatch")
class AIChatProxyView(View):
	def post(self, request):
		# Chat can take longer due to retrieval + LLM generation.
		return _proxy_request(request, "ai", settings.AI_SERVICE_URL, "/ai/chat/", timeout=90)


@method_decorator(csrf_exempt, name="dispatch")
class StaffRegisterProxyView(View):
	def post(self, request):
		return _proxy_request(request, "staff", settings.STAFF_SERVICE_URL, "/staff/register/")


@method_decorator(csrf_exempt, name="dispatch")
class StaffLoginProxyView(View):
	def post(self, request):
		return _proxy_request(request, "staff", settings.STAFF_SERVICE_URL, "/staff/login/")


@method_decorator(csrf_exempt, name="dispatch")
class StaffItemProxyView(View):
	def get(self, request):
		return _proxy_request(request, "staff", settings.STAFF_SERVICE_URL, "/staff/items/")

	def post(self, request):
		return _proxy_request(request, "staff", settings.STAFF_SERVICE_URL, "/staff/items/")


@method_decorator(csrf_exempt, name="dispatch")
class StaffItemDetailProxyView(View):
	def get(self, request, item_id):
		return _proxy_request(
			request,
			"staff",
			settings.STAFF_SERVICE_URL,
			f"/staff/items/{item_id}/",
		)

	def put(self, request, item_id):
		return _proxy_request(
			request,
			"staff",
			settings.STAFF_SERVICE_URL,
			f"/staff/items/{item_id}/",
		)

	def patch(self, request, item_id):
		return _proxy_request(
			request,
			"staff",
			settings.STAFF_SERVICE_URL,
			f"/staff/items/{item_id}/",
		)

	def delete(self, request, item_id):
		return _proxy_request(
			request,
			"staff",
			settings.STAFF_SERVICE_URL,
			f"/staff/items/{item_id}/",
		)


@method_decorator(csrf_exempt, name="dispatch")
class LaptopProxyView(View):
	def get(self, request, laptop_id=None):
		if laptop_id is None:
			path = "/laptops/"
		else:
			path = f"/laptops/{laptop_id}/"
		return _proxy_request(request, "laptop", settings.LAPTOP_SERVICE_URL, path)


@method_decorator(csrf_exempt, name="dispatch")
class MobileProxyView(View):
	def get(self, request, mobile_id=None):
		if mobile_id is None:
			path = "/mobiles/"
		else:
			path = f"/mobiles/{mobile_id}/"
		return _proxy_request(request, "mobile", settings.MOBILE_SERVICE_URL, path)
