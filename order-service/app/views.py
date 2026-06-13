import json
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import Order, OrderItem


def _parse_json_body(request):
    try:
        return json.loads(request.body or '{}'), None
    except json.JSONDecodeError:
        return None, JsonResponse({'error': 'Invalid JSON body.'}, status=400)


def _to_decimal(value):
    try:
        return Decimal(str(value or 0))
    except Exception:
        return Decimal('0')


def _call_customer_service(method, path, query=None, payload=None, timeout=20):
    base = settings.CUSTOMER_SERVICE_URL.rstrip('/')
    url = f"{base}{path}"
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"

    headers = {'Accept': 'application/json'}
    data = None
    if payload is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(payload).encode('utf-8')

    req = urllib.request.Request(url=url, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            try:
                return resp.getcode(), json.loads(raw.decode('utf-8') or '{}')
            except json.JSONDecodeError:
                return resp.getcode(), {'message': raw.decode('utf-8', errors='ignore')}
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            return exc.code, json.loads(raw.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return exc.code, {'message': raw.decode('utf-8', errors='ignore')}
    except urllib.error.URLError as exc:
        return 502, {'error': 'Cannot connect to customer service', 'details': str(exc)}


def _call_payment_service(method, path, query=None, payload=None, timeout=20):
    base = settings.PAYMENT_SERVICE_URL.rstrip('/')
    url = f"{base}{path}"
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"

    headers = {'Accept': 'application/json'}
    data = None
    if payload is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(payload).encode('utf-8')

    req = urllib.request.Request(url=url, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            try:
                return resp.getcode(), json.loads(raw.decode('utf-8') or '{}')
            except json.JSONDecodeError:
                return resp.getcode(), {'message': raw.decode('utf-8', errors='ignore')}
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            return exc.code, json.loads(raw.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return exc.code, {'message': raw.decode('utf-8', errors='ignore')}
    except urllib.error.URLError as exc:
        return 502, {'error': 'Cannot connect to payment service', 'details': str(exc)}


def _call_shipping_service(method, path, query=None, payload=None, timeout=20):
    base = settings.SHIPPING_SERVICE_URL.rstrip('/')
    url = f"{base}{path}"
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"

    headers = {'Accept': 'application/json'}
    data = None
    if payload is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(payload).encode('utf-8')

    req = urllib.request.Request(url=url, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            try:
                return resp.getcode(), json.loads(raw.decode('utf-8') or '{}')
            except json.JSONDecodeError:
                return resp.getcode(), {'message': raw.decode('utf-8', errors='ignore')}
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            return exc.code, json.loads(raw.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return exc.code, {'message': raw.decode('utf-8', errors='ignore')}
    except urllib.error.URLError as exc:
        return 502, {'error': 'Cannot connect to shipping service', 'details': str(exc)}


@method_decorator(csrf_exempt, name='dispatch')
class CheckoutView(View):
    def post(self, request):
        body, error = _parse_json_body(request)
        if error:
            return error

        payment_method = (body.get('payment_method') or Order.PAYMENT_METHOD_COD).strip().upper()

        supported_payment_methods = {
            Order.PAYMENT_METHOD_COD,
            Order.PAYMENT_METHOD_CARD,
            Order.PAYMENT_METHOD_VNPAY,
            Order.PAYMENT_METHOD_MOMO,
        }

        # If payment service defines methods, validate against active methods there.
        pay_methods_status, pay_methods_payload = _call_payment_service('GET', '/payment/methods/', timeout=10)
        if pay_methods_status is not None and pay_methods_status < 400:
            rows = pay_methods_payload.get('data') if isinstance(pay_methods_payload, dict) else None
            if rows is None and isinstance(pay_methods_payload, list):
                rows = pay_methods_payload
            if isinstance(rows, list) and rows:
                active_codes = {
                    str(m.get('code') or '').strip().upper()
                    for m in rows
                    if bool(m.get('is_active'))
                }
                if payment_method not in active_codes:
                    return JsonResponse({'error': 'Unsupported or inactive payment_method.'}, status=400)
        else:
            if payment_method not in supported_payment_methods:
                return JsonResponse({'error': 'Unsupported payment_method.'}, status=400)

        shipping_method_code = (body.get('shipping_method_code') or body.get('shipping_method') or '').strip().upper()
        shipping_fee = Decimal('0')
        if shipping_method_code:
            ship_methods_status, ship_methods_payload = _call_shipping_service('GET', '/shipping/methods/', timeout=10)
            if ship_methods_status is None or ship_methods_status >= 400:
                return JsonResponse({'error': 'Cannot load shipping methods.'}, status=502)

            rows = ship_methods_payload.get('data') if isinstance(ship_methods_payload, dict) else None
            if rows is None and isinstance(ship_methods_payload, list):
                rows = ship_methods_payload

            # If shipping service has no configured methods yet, allow checkout to proceed
            # with fee=0 (the UI may send a fallback code like STANDARD).
            if isinstance(rows, list) and len(rows) == 0:
                shipping_fee = Decimal('0')
            else:
                matched = None
                if isinstance(rows, list):
                    for m in rows:
                        code = str(m.get('code') or '').strip().upper()
                        if code == shipping_method_code:
                            matched = m
                            break

                if not matched or not bool(matched.get('is_active')):
                    return JsonResponse({'error': 'Unsupported or inactive shipping_method_code.'}, status=400)

                shipping_fee = _to_decimal(matched.get('fee'))

        customer_id = body.get('customer_id')
        cart_id = body.get('cart_id')
        if customer_id is None and cart_id is None:
            return JsonResponse({'error': 'customer_id or cart_id is required.'}, status=400)

        if cart_id is not None:
            status, cart_payload = _call_customer_service('GET', '/customer/carts/', query={'cart_id': cart_id})
        else:
            status, cart_payload = _call_customer_service('GET', '/customer/carts/', query={'customer_id': customer_id})

        if status >= 400:
            return JsonResponse(cart_payload, status=status)

        items = cart_payload.get('items') or []
        if not items:
            return JsonResponse({'error': 'Cart is empty.'}, status=400)

        phone = (body.get('phone') or '').strip()
        address = (body.get('address') or body.get('shipping_address') or '').strip()

        with transaction.atomic():
            order = Order.objects.create(
                customer_id=int(cart_payload.get('customer_id') or customer_id),
                cart_id=int(cart_payload.get('id') or cart_id or 0),
                phone=phone,
                shipping_address=address,
                shipping_method_code=shipping_method_code,
                shipping_fee=shipping_fee,
                payment_method=payment_method,
                payment_status=Order.PAYMENT_STATUS_PENDING,
                order_status=Order.ORDER_STATUS_CREATED,
                total_amount=_to_decimal(cart_payload.get('total')) + shipping_fee,
            )

            for item in items:
                OrderItem.objects.create(
                    order=order,
                    item_type=item.get('item_type') or '',
                    item_id=int(item.get('item_id') or 0),
                    item_name=item.get('name') or '',
                    quantity=int(item.get('quantity') or 0),
                    unit_price=_to_decimal(item.get('price')),
                    line_total=_to_decimal(item.get('line_total')),
                )

        payment_call_status, payment_payload = _call_payment_service(
            'POST',
            '/payment/pay',
            payload={'order_id': order.id, 'amount': float(order.total_amount)},
        )

        payment_state = (payment_payload.get('status') or '').strip()
        if payment_call_status < 400 and payment_state == 'Success':
            order.payment_status = Order.PAYMENT_STATUS_PAID
            order.order_status = Order.ORDER_STATUS_CONFIRMED
            order.save(update_fields=['payment_status', 'order_status'])
        elif payment_call_status < 400 and payment_state == 'Failed':
            order.payment_status = Order.PAYMENT_STATUS_FAILED
            order.order_status = Order.ORDER_STATUS_CANCELLED
            order.save(update_fields=['payment_status', 'order_status'])

        shipping_call_status = None
        shipping_payload = None
        if payment_call_status < 400 and payment_state == 'Success' and order.shipping_address:
            shipping_call_status, shipping_payload = _call_shipping_service(
                'POST',
                '/shipping/create',
                payload={'order_id': order.id, 'address': order.shipping_address},
            )

        clear_status = None
        clear_payload = None
        if payment_call_status < 400 and payment_state == 'Success':
            clear_status, clear_payload = _call_customer_service(
                'POST',
                '/customer/carts/clear/',
                payload={'cart_id': order.cart_id},
            )

        return JsonResponse(
            {
                'message': 'Checkout successful.' if (clear_status is not None and clear_status < 400) else 'Checkout created. Payment/shipping may still be processing.',
                'order': {
                    'id': order.id,
                    'customer_id': order.customer_id,
                    'cart_id': order.cart_id,
                    'phone': order.phone,
                    'shipping_address': order.shipping_address,
                    'shipping_method_code': order.shipping_method_code,
                    'shipping_fee': float(order.shipping_fee),
                    'payment_method': order.payment_method,
                    'payment_status': order.payment_status,
                    'order_status': order.order_status,
                    'total_amount': float(order.total_amount),
                    'items_count': len(items),
                },
                'payment': {
                    'http_status': payment_call_status,
                    'response': payment_payload,
                },
                'shipping': {
                    'http_status': shipping_call_status,
                    'response': shipping_payload,
                },
                'cart_cleared': (clear_status is not None and clear_status < 400),
                'cart_clear_response': clear_payload,
            },
            status=201,
        )


@method_decorator(csrf_exempt, name='dispatch')
class OrderView(View):
    def get(self, request):
        customer_id = request.GET.get('customer_id')
        order_id = request.GET.get('order_id')

        qs = Order.objects.all().order_by('-id')

        if order_id is not None:
            try:
                oid = int(order_id)
            except (TypeError, ValueError):
                return JsonResponse({'error': 'order_id must be an integer.'}, status=400)
            qs = qs.filter(id=oid)

        if customer_id is not None:
            try:
                cid = int(customer_id)
            except (TypeError, ValueError):
                return JsonResponse({'error': 'customer_id must be an integer.'}, status=400)
            qs = qs.filter(customer_id=cid)

        data = []
        for order in qs[:500]:
            items = list(
                order.items.values(
                    'id',
                    'item_type',
                    'item_id',
                    'item_name',
                    'quantity',
                    'unit_price',
                    'line_total',
                )
            )
            for item in items:
                item['unit_price'] = float(item['unit_price'])
                item['line_total'] = float(item['line_total'])

            data.append(
                {
                    'id': order.id,
                    'customer_id': order.customer_id,
                    'cart_id': order.cart_id,
                    'phone': order.phone,
                    'shipping_address': order.shipping_address,
                    'shipping_method_code': order.shipping_method_code,
                    'shipping_fee': float(order.shipping_fee),
                    'payment_method': order.payment_method,
                    'payment_status': order.payment_status,
                    'order_status': order.order_status,
                    'total_amount': float(order.total_amount),
                    'created_at': order.created_at,
                    'items': items,
                }
            )

        return JsonResponse({'count': len(data), 'data': data})
