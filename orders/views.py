from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime

# Import Models
from accounts.models import Cart, Address
from .models import Order, OrderProduct, Payment
from products.models import Variant
from accounts.utils import calculate_cart_total

# --- 1. HÀM HELPER TÍNH TOÁN TIỀN (Dùng chung) ---
# orders/views.py



@login_required(login_url='login')
def checkout(request):
    try:
        # Lấy giỏ hàng chưa thanh toán
        cart_obj = Cart.objects.get(user=request.user, is_paid=False)
        
        # Gọi hàm tính tiền ở trên
        cart_data = calculate_cart_total(cart_obj, user=request.user)
        
    except Cart.DoesNotExist:
        return redirect('home')

    # Lấy danh sách địa chỉ để hiển thị
    addresses = Address.objects.filter(user=request.user).order_by('-is_default')

    # Xử lý khi bấm nút "Đặt hàng"
    if request.method == 'POST':
        selected_address_uid = request.POST.get('selected_address')
        payment_method = request.POST.get('payment_method')

        if not selected_address_uid:
            messages.warning(request, "Vui lòng chọn địa chỉ giao hàng.")
            return redirect('orders:checkout')

        # Lưu thông tin vào session để dùng cho bước sau
        request.session['shipping_address_uid'] = selected_address_uid
        request.session['order_total_data'] = {
            'grand_total': cart_data['total'],
            'shipping_fee': cart_data['shipping_fee']
        }

        # --- ĐIỀU HƯỚNG THANH TOÁN ---
        if payment_method == 'vnpay':
            return redirect('orders:vnpay_payment') 
        
        elif payment_method == 'cod':
            return handle_cod_payment(request, cart_obj, cart_data, selected_address_uid)

    context = {
        'cart_data': cart_data, # Truyền cục dữ liệu đã tính xuống HTML
        'addresses': addresses,
    }
    return render(request, 'orders/checkout.html', context)


# --- 3. XỬ LÝ THANH TOÁN COD ---
def handle_cod_payment(request, cart_obj, cart_data, address_uid):
    print(f"--- BẮT ĐẦU XỬ LÝ COD ---")
    print(f"Address UID: {address_uid}")
    
    if not address_uid:
        messages.error(request, "Lỗi: Không tìm thấy địa chỉ giao hàng.")
        return redirect('orders:checkout')

    try:
        # Lấy địa chỉ
        address = Address.objects.get(uid=address_uid)
        timestamp = datetime.now().strftime('%H%M%S')
        
        # 1. Tạo Payment
        payment = Payment.objects.create(
            user=request.user,
            payment_id=f"COD-{timestamp}",
            payment_method='COD',
            amount_paid=str(cart_data['total']),
            status='Pending'
        )
        print("-> Đã tạo Payment")

        # 2. Tạo Order
        order = Order.objects.create(
            user=request.user,
            payment=payment,
            order_number=f"ORD-{request.user.id}-{timestamp}",
            full_name=address.full_name, 
            phone=address.phone,
            address=address.address_line,
            city=address.city,
            order_total=cart_data['subtotal'],
            shipping_fee=cart_data['shipping_fee'],
            coupon_discount=cart_data['discount'],
            tax=cart_data['tax'],
            status='Pending',
            is_ordered=True
        )
        print(f"-> Đã tạo Order: {order.order_number}")

        # 3. Chuyển sản phẩm
        for item in cart_data['cart_items']:
            variant = item.variant
            
            # Kiểm tra tồn kho
            if variant.stock < item.quantity:
                print(f"-> LỖI TỒN KHO: {variant.product.product_name}")
                messages.error(request, f"Sản phẩm {variant.product.product_name} không đủ số lượng.")
                # Xóa Order và Payment vừa tạo để tránh rác
                order.delete()
                payment.delete()
                return redirect('cart')

            # Trừ kho
            variant.stock -= item.quantity
            variant.save()

            # Tạo OrderProduct
            OrderProduct.objects.create(
                order=order,
                user=request.user,
                Payment=payment,
                product=variant.product,
                variant=variant,
                quantity=item.quantity,
                product_price=variant.price,
                ordered=True
            )
        
        print("-> Đã tạo xong OrderProduct")

        # 4. Xóa giỏ hàng (QUAN TRỌNG)
        
        cart_obj.cart_items.all().delete() 
        cart_obj.coupons.clear() 
        cart_obj.save()
        
        print("-> Đã clear giỏ hàng thành công")

        messages.success(request, "Đặt hàng thành công!")
        return redirect('orders:order_success', order_uid=order.uid)

    except Exception as e:
        print(f"--- LỖI CRITICAL COD: {e} ---")
        messages.error(request, f"Lỗi hệ thống: {e}")
        return redirect('orders:checkout')
@login_required
def order_success(request, order_uid):
    order = get_object_or_404(Order, uid=order_uid)
    return render(request, 'orders/success.html', {'order': order})