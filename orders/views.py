# orders/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse

# Import Models
from accounts.models import Cart, Address
from .models import Order, OrderProduct, Payment
from products.models import Variant

# Import Helper để tính tiền chuẩn xác
from accounts.views import _get_cart_details

@login_required(login_url='login')
def checkout(request):
    try:
        cart_obj = Cart.objects.get(user=request.user, is_paid=False)
        cart_data = _get_cart_details(cart_obj)
    except Cart.DoesNotExist:
        return redirect('home')

    # Lấy danh sách địa chỉ của user
    addresses = Address.objects.filter(user=request.user).order_by('-is_default')

    if request.method == 'POST':
        selected_address_uid = request.POST.get('selected_address')
        payment_method = request.POST.get('payment_method')

        if not selected_address_uid:
            messages.warning(request, "Vui lòng chọn địa chỉ giao hàng.")
            return redirect('checkout')

        # Lưu địa chỉ vào Session
        request.session['shipping_address_uid'] = selected_address_uid

        # --- TRƯỜNG HỢP 1: VNPay ---
        if payment_method == 'vnpay':
            # Redirect này tìm URL có name='vnpay_payment' trong urls.py
            # Nên không cần import view function vào đây.
            return redirect('vnpay_payment') 
        
        # --- TRƯỜNG HỢP 2: COD ---
        elif payment_method == 'cod':
            return handle_cod_payment(request, cart_obj, cart_data, selected_address_uid)

    context = {
        'cart_data': cart_data,
        'addresses': addresses,
    }
    return render(request, 'orders/checkout.html', context)


def handle_cod_payment(request, cart_obj, cart_data, address_uid):
    try:
        address = Address.objects.get(uid=address_uid)

        # Tạo Payment record cho COD (Để quản lý thống nhất)
        payment = Payment.objects.create(
            user=request.user,
            payment_id=f"COD-{cart_obj.uid[:8]}",
            payment_method='COD',
            amount_paid=str(cart_data['total']), # Lưu dạng string
            status='Pending' # COD chưa nhận tiền ngay
        )

        order = Order.objects.create(
            user=request.user,
            payment=payment, # Gắn payment vào order
            order_number=f"ORD-{request.user.id}-{cart_obj.uid[:6]}",
            first_name=address.recipient_name, # Tạm gán full name vào first_name
            last_name="", # Có thể tách tên nếu cần
            phone=address.phone,
            address_line_1=address.address_line,
            city=address.city,
            order_total=cart_data['total'],
            tax=0,
            status='New',
            is_ordered=True
        )

        for item in cart_data['cart_items']:
            variant = item.variant
            if variant.stock >= item.quantity:
                variant.stock -= item.quantity
                variant.save()
            else:
                 messages.error(request, f"Sản phẩm {variant.product.product_name} hết hàng.")
                 return redirect('cart')

            OrderProduct.objects.create(
                order=order,
                user=request.user,
                payment=payment, # Gắn payment vào sản phẩm lun nếu cần
                product=variant.product,
                variant=variant,
                quantity=item.quantity,
                product_price=variant.price,
                ordered=True
            )

        # Clear giỏ hàng
        cart_obj.is_paid = True
        cart_obj.save()
        
        messages.success(request, "Đặt hàng thành công!")
        return redirect('order_success', order_uid=order.uid)

    except Exception as e:
        print(f"COD Error: {e}")
        messages.error(request, "Có lỗi xảy ra khi xử lý đơn hàng.")
        return redirect('checkout')

def order_success(request, order_uid):
    order = get_object_or_404(Order, uid=order_uid)
    return render(request, 'orders/success.html', {'order': order})