from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import json
from datetime import datetime

# Import Models
from accounts.models import Cart, Address
from .models import Order, OrderProduct, Payment
from products.models import Variant
# Import hàm tính tiền chung
from accounts.utils import calculate_cart_total

# --- 1. VIEW THANH TOÁN (CHECKOUT) ---
@login_required(login_url='login')
def checkout(request):
    try:
        # Lấy giỏ hàng
        cart_obj = Cart.objects.get(user=request.user, is_paid=False)
        # Tính toán chi phí
        cart_data = calculate_cart_total(cart_obj, user=request.user)
    except Cart.DoesNotExist:
        return redirect('home')

    addresses = Address.objects.filter(user=request.user).order_by('-is_default')

    if request.method == 'POST':
        selected_address_uid = request.POST.get('selected_address')
        payment_method = request.POST.get('payment_method')

        if not selected_address_uid:
            messages.warning(request, "Vui lòng chọn địa chỉ giao hàng.")
            return redirect('orders:checkout')

        # Xử lý thanh toán
        if payment_method == 'vnpay':
            return redirect('orders:vnpay_payment') 
        elif payment_method == 'cod':
            # Gọi hàm xử lý COD
            return handle_cod_payment(request, cart_obj, selected_address_uid)

    context = {
        'cart_data': cart_data,
        'addresses': addresses,
    }
    return render(request, 'orders/checkout.html', context)


# --- 2. XỬ LÝ THANH TOÁN COD ---
def handle_cod_payment(request, cart_obj, address_uid):
    print(f"--- BẮT ĐẦU XỬ LÝ COD ---")
    
    if not address_uid:
        messages.error(request, "Lỗi: Không tìm thấy địa chỉ giao hàng.")
        return redirect('orders:checkout')

    try:
        address = Address.objects.get(uid=address_uid)
        
        # QUAN TRỌNG: Tính toán lại cart_data dựa trên địa chỉ đã chọn
        # Để đảm bảo số tiền lưu vào DB là chính xác nhất tại thời điểm đặt
        cart_data = calculate_cart_total(cart_obj, user=request.user, selected_address=address)
        
        timestamp = datetime.now().strftime('%H%M%S')
        
        # 1. Tạo Payment
        payment = Payment.objects.create(
            user=request.user,
            payment_id=f"COD-{timestamp}",
            payment_method='COD',
            amount_paid=str(cart_data['total']),
            status='Pending'
        )

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

        # 3. Chuyển sản phẩm & Trừ kho
        for item in cart_data['cart_items']:
            variant = item.variant
            
            # Check tồn kho
            if variant.stock < item.quantity:
                messages.error(request, f"Sản phẩm {variant.product.product_name} không đủ số lượng.")
                order.delete()
                payment.delete()
                return redirect('cart')

            variant.stock -= item.quantity
            variant.save()

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
        
        # 4. Xóa giỏ hàng
        cart_obj.cart_items.all().delete() 
        cart_obj.coupons.clear() 
        cart_obj.save()
        
        messages.success(request, "Đặt hàng thành công!")
        return redirect('orders:order_success', order_uid=order.uid)

    except Exception as e:
        print(f"--- LỖI COD: {e} ---")
        messages.error(request, "Có lỗi xảy ra khi xử lý đơn hàng.")
        return redirect('orders:checkout')

# --- 3. TRANG THÀNH CÔNG ---
@login_required
def order_success(request, order_uid):
    order = get_object_or_404(Order, uid=order_uid)
    # Lấy danh sách sản phẩm (Dùng related_name hoặc _set)
    order_items = order.order_products.all()
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'orders/success.html', context)

# --- 4. API CẬP NHẬT PHÍ SHIP (AJAX) ---
def update_shipping_fee(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            address_uid = data.get('address_uid')
            
            address = Address.objects.get(uid=address_uid)
            cart_obj = Cart.objects.get(user=request.user, is_paid=False)

            # Tính lại với địa chỉ mới chọn
            cart_data = calculate_cart_total(cart_obj, user=request.user, selected_address=address)
            
            return JsonResponse({
                'status': 'success',
                'shipping_fee': cart_data['shipping_fee'],
                'total': cart_data['total'],
                'subtotal': cart_data['subtotal'],
                'discount': cart_data['discount'],
            })
        except Address.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Địa chỉ không tồn tại.'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error'}, status=400)