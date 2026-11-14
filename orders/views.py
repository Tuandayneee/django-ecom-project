import json
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import Address, Cart
from accounts.utils import calculate_cart_total
from orders.models import Order, OrderProduct, Payment
from orders.utils import get_user_shipping_fee
from products.models import CouponUsage, Variant


def _generate_ref(prefix: str) -> str:
    """Generate a unique order/payment reference fitting Order.order_number (max 20 chars)."""
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


def thong_bao_don_hang(request, order_number, email):
    if not email:
        return
    email_from = settings.EMAIL_HOST_USER or settings.DEFAULT_FROM_EMAIL
    send_mail(
        f'Xác nhận đơn hàng {order_number}',
        'Cảm ơn bạn đã mua hàng. Đơn hàng đang được chuẩn bị.',
        email_from,
        [email],
        fail_silently=False,
    )


@login_required(login_url='login')
def checkout(request):
    cart_obj = None
    cart_data = {}

    direct_buy_data = request.session.get('direct_buy_item')

    if direct_buy_data:
        try:
            variant = Variant.objects.get(uid=direct_buy_data['variant_uid'])
            qty = int(direct_buy_data['quantity'])
            total_price = variant.price * qty

            class MockCartItem:
                def __init__(self, variant_obj, quantity):
                    self.variant = variant_obj
                    self.quantity = quantity
                    self.get_product_price = variant_obj.price * quantity

            shipping_fee = get_user_shipping_fee(request.user, total_price)

            cart_data = {
                'cart_items': [MockCartItem(variant, qty)],
                'subtotal': total_price,
                'shipping_fee': shipping_fee,
                'discount': 0,
                'tax': 0,
                'total': total_price + shipping_fee,
            }
        except Variant.DoesNotExist:
            request.session.pop('direct_buy_item', None)
            return redirect('cart')
    else:
        cart_obj = Cart.objects.filter(user=request.user, is_paid=False).order_by('-created_at').first()
        if not cart_obj:
            messages.warning(request, "Không có giỏ hàng hoặc giỏ hàng đang trống.")
            return redirect('home')

        cart_data = calculate_cart_total(cart_obj, user=request.user)
        if not cart_data['cart_items']:
            messages.warning(request, "Giỏ hàng của bạn đang trống.")
            return redirect('home')

    addresses = Address.objects.filter(user=request.user).order_by('-is_default')

    if request.method == 'POST':
        selected_address_uid = request.POST.get('selected_address')
        payment_method = request.POST.get('payment_method')

        if not selected_address_uid:
            messages.warning(request, "Vui lòng chọn địa chỉ giao hàng.")
            return redirect('orders:checkout')

        if payment_method == 'vnpay':
            request.session['shipping_address_uid'] = selected_address_uid
            request.session['is_buy_now'] = bool(direct_buy_data)
            request.session.modified = True
            return redirect('orders:vnpay_payment')

        if payment_method == 'cod':
            return handle_cod_payment(request, cart_obj, selected_address_uid, direct_buy_data)

    context = {
        'cart_data': cart_data,
        'addresses': addresses,
        'free_shipping_threshold': 1000000,
        'remaining_for_free_shipping': max(0, 1000000 - cart_data['subtotal']),
        'is_buy_now': bool(direct_buy_data),
    }
    return render(request, 'orders/checkout.html', context)


@login_required(login_url='login')
def handle_cod_payment(request, cart_obj, address_uid, direct_buy_data=None):
    if not address_uid:
        messages.error(request, "Lỗi: Không tìm thấy địa chỉ giao hàng.")
        return redirect('orders:checkout')

    address = get_object_or_404(Address, uid=address_uid, user=request.user)

    try:
        subtotal = 0
        shipping_fee = 0
        discount = 0
        tax = 0
        final_total = 0
        order_items_list = []

        if direct_buy_data:
            variant = Variant.objects.get(uid=direct_buy_data['variant_uid'])
            qty = int(direct_buy_data['quantity'])
            if qty < 1:
                raise ValueError("Số lượng đặt hàng không hợp lệ.")
            price = variant.price

            subtotal = price * qty
            shipping_fee = get_user_shipping_fee(request.user, subtotal, address)
            final_total = subtotal + shipping_fee - discount + tax

            order_items_list.append({
                'variant': variant,
                'quantity': qty,
                'price': price,
            })
        elif cart_obj:
            cart_data = calculate_cart_total(cart_obj, user=request.user, selected_address=address)
            subtotal = cart_data['subtotal']
            final_total = cart_data['total']
            shipping_fee = cart_data['shipping_fee']
            discount = cart_data['discount']
            tax = cart_data['tax']

            for item in cart_data['cart_items']:
                if not item.variant or item.quantity < 1:
                    raise ValueError("Sản phẩm trong giỏ hàng không hợp lệ.")
                order_items_list.append({
                    'variant': item.variant,
                    'quantity': item.quantity,
                    'price': item.variant.price,
                })
        else:
            return redirect('home')

        with transaction.atomic():
            payment = Payment.objects.create(
                user=request.user,
                payment_id=_generate_ref("COD"),
                payment_method='cod',
                amount_paid=str(final_total),
                status=Payment.PaymentStatus.PENDING,
            )

            order = Order.objects.create(
                user=request.user,
                payment=payment,
                order_number=_generate_ref("ORD"),
                full_name=address.full_name,
                phone=address.phone,
                address_line=address.address_line,
                city=address.city,
                order_total=subtotal,
                shipping_fee=shipping_fee,
                coupon_discount=discount,
                tax=tax,
                status='Pending',
                is_ordered=False,
            )

            for item_data in order_items_list:
                qty = item_data['quantity']
                locked_variant = Variant.objects.select_for_update().get(uid=item_data['variant'].uid)
                if locked_variant.stock < qty:
                    raise ValueError(f"Sản phẩm {locked_variant.product.product_name} không đủ số lượng.")

                Variant.objects.filter(uid=locked_variant.uid, stock__gte=qty).update(
                    stock=F('stock') - qty
                )

                OrderProduct.objects.create(
                    order=order,
                    product=locked_variant.product,
                    variant=locked_variant,
                    product_name=locked_variant.product.product_name,
                    quantity=qty,
                    product_price=locked_variant.price,
                )

            if not direct_buy_data and cart_obj and cart_obj.coupons.exists():
                for coupon in cart_obj.coupons.all():
                    usage, _ = CouponUsage.objects.get_or_create(
                        user=request.user,
                        coupon=coupon,
                    )
                    usage.used_count += 1
                    usage.save()

            if direct_buy_data:
                request.session.pop('direct_buy_item', None)
            else:
                cart_obj.cart_items.all().delete()
                cart_obj.coupons.clear()
                cart_obj.save()

        thong_bao_don_hang(request, order.order_number, request.user.email)
        messages.success(request, "Đặt hàng thành công!")
        return redirect('orders:order_success', order_uid=order.uid)

    except Exception as exc:
        print(f"--- LỖI COD: {exc} ---")
        messages.error(request, "Có lỗi xảy ra khi xử lý đơn hàng.")
        return redirect('orders:checkout')


@login_required(login_url='login')
def order_success(request, order_uid):
    order = get_object_or_404(Order, uid=order_uid, user=request.user)
    order_items = order.order_products.all()
    return render(
        request,
        'orders/success.html',
        {'order': order, 'order_items': order_items},
    )


@login_required(login_url='login')
@require_POST
def update_shipping_fee(request):
    try:
        data = json.loads(request.body)
        address_uid = data.get('address_uid')
        address = get_object_or_404(Address, uid=address_uid, user=request.user)

        direct_buy_data = request.session.get('direct_buy_item')
        if direct_buy_data:
            try:
                variant = Variant.objects.get(uid=direct_buy_data['variant_uid'])
                qty = int(direct_buy_data['quantity'])
                subtotal = variant.price * qty
                shipping_fee = get_user_shipping_fee(request.user, subtotal, address)
                discount = 0
                tax = 0
                total = subtotal + shipping_fee - discount + tax

                return JsonResponse({
                    'status': 'success',
                    'shipping_fee': shipping_fee,
                    'total': total,
                    'subtotal': subtotal,
                    'discount': discount,
                })
            except Variant.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Sản phẩm lỗi'}, status=400)

        cart_obj = Cart.objects.filter(user=request.user, is_paid=False).order_by('-created_at').first()
        if not cart_obj:
            return JsonResponse({
                'status': 'success',
                'shipping_fee': 0,
                'total': 0,
                'subtotal': 0,
            })

        cart_data = calculate_cart_total(cart_obj, user=request.user, selected_address=address)
        return JsonResponse({
            'status': 'success',
            'shipping_fee': cart_data['shipping_fee'],
            'total': cart_data['total'],
            'subtotal': cart_data['subtotal'],
            'discount': cart_data['discount'],
        })
    except Exception as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@login_required(login_url='login')
@require_POST
def buy_now(request):
    try:
        data = json.loads(request.body)
        variant_uid = data.get('variant_uid')
        try:
            quantity = int(data.get('quantity', 1))
        except (TypeError, ValueError):
            return JsonResponse({'status': 'error', 'message': 'Số lượng không hợp lệ'}, status=400)

        if quantity < 1:
            return JsonResponse({'status': 'error', 'message': 'Số lượng phải >= 1'}, status=400)

        variant = get_object_or_404(Variant, uid=variant_uid)
        if quantity > variant.stock:
            return JsonResponse(
                {'status': 'error', 'message': f'Chỉ còn {variant.stock} sản phẩm trong kho'},
                status=400,
            )

        request.session['direct_buy_item'] = {
            'variant_uid': str(variant.uid),
            'quantity': quantity,
        }
        request.session['is_buy_now'] = True
        request.session.modified = True

        return JsonResponse({'status': 'success'})
    except Exception as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@login_required(login_url='login')
@require_POST
def remove_order(request, order_uid):
    with transaction.atomic():
        order = get_object_or_404(
            Order.objects.select_for_update().select_related('payment'),
            uid=order_uid,
            user=request.user,
        )
        if order.status == 'Pending':
            stock_already_deducted = bool(
                order.is_ordered or (order.payment and order.payment.payment_method.lower() == 'cod')
            )
            if stock_already_deducted:
                for item in order.order_products.select_related('variant').all():
                    if item.variant_id:
                        Variant.objects.filter(uid=item.variant_id).update(
                            stock=F('stock') + item.quantity
                        )

            order.status = 'cancelled'
            order.save(update_fields=['status', 'updated_at'])
            messages.success(request, "Đơn hàng đã được hủy thành công.")
        else:
            messages.error(request, "Đơn hàng không thể hủy ở trạng thái hiện tại.")
    return redirect('user_orders')


@login_required(login_url='login')
def cancel_buy_now(request):
    request.session.pop('direct_buy_item', None)
    request.session.pop('is_buy_now', None)
    request.session.modified = True
    messages.info(request, "Đã hủy phiên Mua ngay. Đang hiển thị giỏ hàng của bạn.")
    return redirect('cart')

