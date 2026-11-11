from collections.abc import Mapping
from datetime import datetime
import hashlib
import hmac
import urllib.parse
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect

from accounts.models import Address, Cart
from accounts.utils import calculate_cart_total
from orders.utils import get_user_shipping_fee
from products.models import CouponUsage, Variant
from .models import Order, OrderProduct, Payment


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR') or '127.0.0.1'


def _clean_vnpay_params(params: Mapping[str, object]) -> list[tuple[str, str]]:
    """Filter and sort VNPay parameters prior to HMAC-SHA512 signing."""
    filtered = {
        str(key): str(value)
        for key, value in params.items()
        if key not in ('vnp_SecureHash', 'vnp_SecureHashType') and value not in (None, '')
    }
    return sorted(filtered.items())


def build_vnpay_query_and_hash(params: Mapping[str, object], secret_key: str) -> tuple[str, str]:
    """Build URL-encoded VNPay query string and its HMAC-SHA512 hex digest."""
    sorted_items = _clean_vnpay_params(params)
    query_data = urllib.parse.urlencode(sorted_items)
    secure_hash = hmac.new(
        secret_key.encode('utf-8'),
        query_data.encode('utf-8'),
        hashlib.sha512,
    ).hexdigest()
    return query_data, secure_hash


def validate_vnpay_checksum(query_params: Mapping[str, object], secret_key: str) -> bool:
    """Verify VNPay return/IPN checksum using constant-time HMAC-SHA512 comparison."""
    if not secret_key or not query_params:
        return False

    received_hash = query_params.get('vnp_SecureHash')
    if not received_hash:
        return False

    params_dict = query_params.dict() if hasattr(query_params, 'dict') else dict(query_params)
    _, expected_hash = build_vnpay_query_and_hash(params_dict, secret_key)
    return hmac.compare_digest(expected_hash.lower(), str(received_hash).strip().lower())


def _build_order_payload(request, address):
    """Compute totals and lock-validate line items from buy-now session or active cart."""
    is_buy_now = request.session.get('is_buy_now', False)
    order_items_payload = []

    if is_buy_now:
        item_data = request.session.get('direct_buy_item')
        if not item_data:
            raise ValueError("Không tìm thấy thông tin sản phẩm mua ngay.")

        variant = Variant.objects.select_for_update().get(uid=item_data['variant_uid'])
        qty = int(item_data['quantity'])
        if qty < 1 or variant.stock < qty:
            raise ValueError(f"Sản phẩm {variant.product.product_name} không đủ tồn kho.")

        final_subtotal = variant.price * qty
        final_shipping = get_user_shipping_fee(request.user, final_subtotal, address)
        final_total = final_subtotal + final_shipping
        order_items_payload.append({
            'variant': variant,
            'quantity': qty,
            'price': variant.price,
        })
        return {
            'is_buy_now': True,
            'cart_obj': None,
            'subtotal': final_subtotal,
            'shipping_fee': final_shipping,
            'tax': 0,
            'discount': 0,
            'total': final_total,
            'items': order_items_payload,
            'order_info': f"Thanh toan mua ngay: {variant.product.product_name}",
        }

    cart_obj = Cart.objects.filter(user=request.user, is_paid=False).order_by('-created_at').first()
    if not cart_obj or not cart_obj.cart_items.exists():
        raise ValueError("Giỏ hàng của bạn trống.")

    cart_data = calculate_cart_total(cart_obj, user=request.user, selected_address=address)
    for item in cart_data['cart_items']:
        if not item.variant or item.quantity < 1:
            raise ValueError("Sản phẩm trong giỏ hàng không hợp lệ.")
        locked_variant = Variant.objects.select_for_update().get(uid=item.variant.uid)
        if locked_variant.stock < item.quantity:
            raise ValueError(f"{locked_variant.product.product_name} không đủ tồn kho.")
        order_items_payload.append({
            'variant': locked_variant,
            'quantity': item.quantity,
            'price': locked_variant.price,
        })

    return {
        'is_buy_now': False,
        'cart_obj': cart_obj,
        'subtotal': cart_data['subtotal'],
        'shipping_fee': cart_data['shipping_fee'],
        'tax': cart_data['tax'],
        'discount': cart_data['discount'],
        'total': cart_data['total'],
        'items': order_items_payload,
        'order_info': f"Thanh toan gio hang User {request.user.id}",
    }


@login_required(login_url='login')
def vnpay_payment(request):
    address_uid = request.session.get('shipping_address_uid')
    if not address_uid:
        messages.warning(request, "Vui lòng chọn địa chỉ giao hàng trước.")
        return redirect('orders:checkout')

    if not settings.VNPAY_TMN_CODE or not settings.VNPAY_HASH_SECRET_KEY:
        messages.error(request, "Cổng thanh toán VNPay chưa được cấu hình.")
        return redirect('orders:checkout')

    address = get_object_or_404(Address, uid=address_uid, user=request.user)

    try:
        with transaction.atomic():
            payload = _build_order_payload(request, address)
            txn_ref = f"ORD-{uuid.uuid4().hex[:12].upper()}"

            payment = Payment.objects.create(
                user=request.user,
                payment_id=txn_ref,
                payment_method='VNPay',
                amount_paid=str(payload['total']),
                status=Payment.PaymentStatus.PENDING,
            )

            order = Order.objects.create(
                user=request.user,
                payment=payment,
                order_number=txn_ref,
                full_name=address.full_name,
                phone=address.phone,
                address_line=address.address_line,
                city=address.city,
                order_total=payload['subtotal'],
                shipping_fee=payload['shipping_fee'],
                coupon_discount=payload['discount'],
                tax=payload['tax'],
                status='Pending',
                is_ordered=False,
            )

            for item in payload['items']:
                var = item['variant']
                OrderProduct.objects.create(
                    order=order,
                    product=var.product,
                    variant=var,
                    product_name=var.product.product_name,
                    quantity=item['quantity'],
                    product_price=item['price'],
                )

            request.session['order_ref'] = txn_ref
            request.session.modified = True

    except (Cart.DoesNotExist, Variant.DoesNotExist, ValueError) as exc:
        messages.warning(request, str(exc) or "Không thể khởi tạo thanh toán VNPay.")
        return redirect('orders:checkout')

    input_data = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": settings.VNPAY_TMN_CODE,
        "vnp_Amount": str(int(payload['total']) * 100),
        "vnp_CreateDate": datetime.now().strftime('%Y%m%d%H%M%S'),
        "vnp_CurrCode": "VND",
        "vnp_IpAddr": get_client_ip(request),
        "vnp_Locale": "vn",
        "vnp_OrderInfo": payload['order_info'],
        "vnp_OrderType": "billpayment",
        "vnp_ReturnUrl": settings.VNPAY_RETURN_URL,
        "vnp_TxnRef": txn_ref,
    }

    query_data, secure_hash = build_vnpay_query_and_hash(
        input_data,
        settings.VNPAY_HASH_SECRET_KEY,
    )
    payment_url = f"{settings.VNPAY_PAYMENT_URL}?{query_data}&vnp_SecureHash={secure_hash}"
    return redirect(payment_url)


def payment_return(request):
    """Handle VNPay browser return and IPN webhook using HMAC-SHA512 verification and DB order lookup."""
    input_data = request.GET
    if not input_data:
        return redirect('home')

    is_authenticated = request.user.is_authenticated

    if not validate_vnpay_checksum(input_data, settings.VNPAY_HASH_SECRET_KEY):
        if not is_authenticated:
            return JsonResponse({'RspCode': '97', 'Message': 'Invalid Checksum'}, status=400)
        messages.error(request, "Chữ ký xác thực VNPay không hợp lệ.")
        return redirect('orders:checkout')

    vnp_txn_ref = input_data.get('vnp_TxnRef')
    vnp_response_code = input_data.get('vnp_ResponseCode')
    vnp_transaction_status = input_data.get('vnp_TransactionStatus')
    vnp_amount = input_data.get('vnp_Amount')

    if not vnp_txn_ref:
        if not is_authenticated:
            return JsonResponse({'RspCode': '01', 'Message': 'Order not found'}, status=400)
        messages.error(request, "Thiếu mã giao dịch VNPay.")
        return redirect('orders:checkout')

    try:
        with transaction.atomic():
            order = (
                Order.objects.select_for_update()
                .select_related('payment', 'user')
                .filter(order_number=vnp_txn_ref)
                .first()
            )
            if not order:
                if not is_authenticated:
                    return JsonResponse({'RspCode': '01', 'Message': 'Order not found'}, status=404)
                messages.error(request, "Không tìm thấy đơn hàng tương ứng.")
                return redirect('orders:checkout')

            if is_authenticated and order.user_id != request.user.id:
                messages.error(request, "Bạn không có quyền truy cập giao dịch này.")
                return redirect('orders:checkout')

            if order.is_ordered and order.status == 'paid':
                if not is_authenticated:
                    return JsonResponse({'RspCode': '02', 'Message': 'Order already confirmed'})
                return redirect('orders:order_success', order_uid=order.uid)

            if order.status != 'Pending':
                if not is_authenticated:
                    return JsonResponse({'RspCode': '02', 'Message': 'Order already processed'}, status=400)
                messages.warning(request, "Đơn hàng đã được xử lý hoặc đã hủy trước đó.")
                return redirect('orders:checkout')

            try:
                paid_amount = int(vnp_amount)
            except (TypeError, ValueError):
                if not is_authenticated:
                    return JsonResponse({'RspCode': '04', 'Message': 'Invalid amount'}, status=400)
                messages.error(request, "Số tiền thanh toán VNPay không hợp lệ.")
                return redirect('orders:checkout')

            if paid_amount != int(order.grand_total) * 100:
                if not is_authenticated:
                    return JsonResponse({'RspCode': '04', 'Message': 'Invalid amount'}, status=400)
                messages.error(request, "Số tiền thanh toán không khớp với đơn hàng.")
                return redirect('orders:checkout')

            if vnp_response_code != '00' or (vnp_transaction_status and vnp_transaction_status != '00'):
                order.status = 'cancelled'
                order.save(update_fields=['status', 'updated_at'])
                if order.payment:
                    order.payment.status = Payment.PaymentStatus.FAILED
                    order.payment.save(update_fields=['status'])

                request.session.pop('order_ref', None)
                if not is_authenticated:
                    return JsonResponse({'RspCode': '00', 'Message': 'Confirm Failed Transaction'})
                messages.error(request, "Giao dịch thất bại hoặc bị hủy.")
                return redirect('orders:checkout')

            order_items = list(order.order_products.select_related('variant__product').all())
            if not order_items:
                raise ValueError("Đơn hàng không có sản phẩm.")

            for item in order_items:
                if not item.variant:
                    raise ValueError("Biến thể sản phẩm không tồn tại.")
                locked_variant = Variant.objects.select_for_update().get(uid=item.variant.uid)
                if locked_variant.stock < item.quantity:
                    raise ValueError(f"Sản phẩm {locked_variant.product.product_name} không đủ số lượng.")
                Variant.objects.filter(uid=locked_variant.uid, stock__gte=item.quantity).update(
                    stock=F('stock') - item.quantity
                )

            if order.payment:
                order.payment.status = Payment.PaymentStatus.COMPLETED
                order.payment.save(update_fields=['status'])

            order.status = 'paid'
            order.is_ordered = True
            order.save(update_fields=['status', 'is_ordered', 'updated_at'])

            is_buy_now = bool(request.session.get('is_buy_now', False))
            if is_buy_now:
                request.session.pop('direct_buy_item', None)
                request.session.pop('is_buy_now', None)
            elif order.user:
                cart_obj = Cart.objects.filter(user=order.user, is_paid=False).order_by('-created_at').first()
                if cart_obj:
                    for coupon in cart_obj.coupons.all():
                        usage, _ = CouponUsage.objects.get_or_create(
                            user=order.user,
                            coupon=coupon,
                        )
                        usage.used_count += 1
                        usage.save()
                    cart_obj.cart_items.all().delete()
                    cart_obj.coupons.clear()
                    cart_obj.save()

            request.session.pop('shipping_address_uid', None)
            request.session.pop('order_ref', None)

            if not is_authenticated:
                return JsonResponse({'RspCode': '00', 'Message': 'Confirm Success'})

            messages.success(request, "Thanh toán thành công!")
            return redirect('orders:order_success', order_uid=order.uid)

    except Exception as exc:
        print(f"Lỗi xử lý VNPay Return: {exc}")
        if not is_authenticated:
            return JsonResponse({'RspCode': '99', 'Message': 'Unknown error'}, status=500)
        messages.error(request, "Thanh toán thành công nhưng lỗi cập nhật đơn hàng. Liên hệ Admin.")
        return redirect('orders:checkout')
