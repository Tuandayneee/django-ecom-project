from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import json
from datetime import datetime

# Import Models
from accounts.models import Cart, Address
from orders.utils import get_user_shipping_fee
from .models import Order, OrderProduct, Payment
from products.models import Variant
# Import hàm tính tiền chung
from accounts.utils import calculate_cart_total

# --- 1. VIEW THANH TOÁN (CHECKOUT) ---
@login_required(login_url='login')
def checkout(request):
    # 1. Khởi tạo biến để tránh lỗi UnboundLocalError
    cart_obj = None  
    cart_data = {}
    
    # 2. Kiểm tra xem có phải luồng Mua Ngay (Direct Buy) không
    direct_buy_data = request.session.get('direct_buy_item')

    if direct_buy_data:
        # --- LOGIC MUA NGAY ---
        try:
            variant = Variant.objects.get(uid=direct_buy_data['variant_uid'])
            qty = direct_buy_data['quantity']
            total_price = variant.price * qty
            
            # Tạo lớp giả lập để template hiển thị được giống như CartItem
            class MockCartItem:
                def __init__(self, variant, qty):
                    self.variant = variant
                    self.quantity = qty
                    self.get_product_price = variant.price * qty

            cart_data = {
                'cart_items': [MockCartItem(variant, qty)],
                'subtotal': total_price,
                'shipping_fee': 0, # Mặc định 0, AJAX sẽ cập nhật sau
                'discount': 0,
                'tax': 0,
                'total': total_price
            }
        except Variant.DoesNotExist:
            del request.session['direct_buy_item']
            return redirect('cart')
    else:
        # --- LOGIC GIỎ HÀNG THƯỜNG ---
        try:
            cart_obj = Cart.objects.get(user=request.user, is_paid=False)
            cart_data = calculate_cart_total(cart_obj, user=request.user)
            
            # Kiểm tra giỏ hàng trống
            if not cart_data['cart_items']:
                messages.warning(request, "Giỏ hàng của bạn đang trống.")
                return redirect('home')
                
        except Cart.DoesNotExist:
            return redirect('home')

    # 3. Lấy danh sách địa chỉ
    addresses = Address.objects.filter(user=request.user).order_by('-is_default')

    # 4. XỬ LÝ KHI BẤM NÚT ĐẶT HÀNG (POST)
    if request.method == 'POST':
        selected_address_uid = request.POST.get('selected_address')
        payment_method = request.POST.get('payment_method')

        if not selected_address_uid:
            messages.warning(request, "Vui lòng chọn địa chỉ giao hàng.")
            return redirect('orders:checkout')

        # --- Xử lý VNPay ---
        if payment_method == 'vnpay':
            request.session['shipping_address_uid'] = selected_address_uid
            # VNPay sẽ tự đọc session 'direct_buy_item' ở view vnpay_payment để biết thanh toán bao nhiêu
            return redirect('orders:vnpay_payment') 

        # --- Xử lý COD (Thanh toán khi nhận hàng) ---
        elif payment_method == 'cod':
            # QUAN TRỌNG: Bạn cần truyền thêm direct_buy_data vào hàm này
            # để hàm biết nên tạo đơn từ Session hay từ Database Cart
            return handle_cod_payment(request, cart_obj, selected_address_uid, direct_buy_data)

    context = {
        'cart_data': cart_data,
        'addresses': addresses,
    }
    return render(request, 'orders/checkout.html', context)


def handle_cod_payment(request, cart_obj, address_uid, direct_buy_data=None):
    
    if not address_uid:
        messages.error(request, "Lỗi: Không tìm thấy địa chỉ giao hàng.")
        return redirect('orders:checkout')

    try:
        address = Address.objects.get(uid=address_uid)
        
        # Initialize variables
        subtotal = 0
        shipping_fee = 0
        discount = 0
        tax = 0
        final_total = 0
        order_items_list = []
        
        if direct_buy_data:
            variant = Variant.objects.get(uid=direct_buy_data['variant_uid'])
            qty = direct_buy_data['quantity']
            price = variant.price
            
            # Tính toán
            subtotal = price * qty
            shipping_fee = get_user_shipping_fee(request.user, subtotal, address)
            discount = 0
            tax = 0
            
            final_total = subtotal + shipping_fee - discount + tax
            
            # Chuẩn bị item để tạo
            order_items_list.append({
                'variant': variant,
                'quantity': qty,
                'price': price
            })
        elif cart_obj:
            cart_data = calculate_cart_total(cart_obj, user=request.user, selected_address=address)
            subtotal = cart_data['subtotal']
            final_total = cart_data['total']
            shipping_fee = cart_data['shipping_fee']
            discount = cart_data['discount']
            tax = cart_data['tax']

            for item in cart_data['cart_items']:
                order_items_list.append({
                    'variant': item.variant,
                    'quantity': item.quantity,
                    'price': item.variant.price
                })
        else:
            return redirect('home')
            
        timestamp = datetime.now().strftime('%H%M%S')
        
        # 1. Tạo Payment
        payment = Payment.objects.create(
            user=request.user,
            payment_id=f"COD-{timestamp}",
            payment_method='COD',
            amount_paid=str(final_total),
            status='Pending'
        )

        # 2. Tạo Order
        order = Order.objects.create(
            user=request.user,
            payment=payment,
            order_number=f"ORD-{request.user.id}-{timestamp}",
            full_name=address.full_name, 
            phone=address.phone,
            address_line=address.address_line,
            city=address.city,
            order_total=subtotal,
            shipping_fee=shipping_fee,
            coupon_discount=discount,
            tax=tax,
            status='Pending',
            is_ordered=True,
            created_at=timestamp
        )

        # 3. Chuyển sản phẩm & Trừ kho
        for item_data in order_items_list:
            variant = item_data['variant']
            
            # Check tồn kho
            if variant.stock < item_data['quantity']:
                messages.error(request, f"Sản phẩm {variant.product.product_name} không đủ số lượng.")
                order.delete()
                payment.delete()
                return redirect('cart')

            variant.stock -= item_data['quantity']
            variant.save()

            OrderProduct.objects.create(
                order=order,
                product=variant.product,
                variant=variant,
                product_name=variant.product.product_name,
                quantity=item_data['quantity'],
                product_price=variant.price
            )
        
        if direct_buy_data:
            if 'direct_buy_item' in request.session:
                del request.session['direct_buy_item']
        else:
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
# orders/views.py

def update_shipping_fee(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            address_uid = data.get('address_uid')
            
            # Lấy địa chỉ từ UID gửi lên
            address = Address.objects.get(uid=address_uid)
            
            # --- 1. ƯU TIÊN KIỂM TRA MUA NGAY (SESSION) ---
            direct_buy_data = request.session.get('direct_buy_item')
            
            if direct_buy_data:
                # Lấy thông tin sản phẩm từ session
                try:
                    variant = Variant.objects.get(uid=direct_buy_data['variant_uid'])
                    qty = direct_buy_data['quantity']
                    
                    # Tính toán lại Subtotal
                    subtotal = variant.price * qty
                    
                    # Gọi hàm tính ship từ utils.py (QUAN TRỌNG: Truyền address vừa chọn)
                    shipping_fee = get_user_shipping_fee(request.user, subtotal, address)
                    
                    # Mua ngay tạm thời chưa có mã giảm giá -> discount = 0
                    discount = 0
                    tax = 0
                    
                    # Tính tổng cuối
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

            # --- 2. NẾU KHÔNG CÓ SESSION -> TÍNH THEO GIỎ HÀNG (CART) ---
            else:
                cart_obj = Cart.objects.get(user=request.user, is_paid=False)
                
                # Hàm này trong utils.py đã có logic tính ship, CHỈ CẦN TRUYỀN ADRESS VÀO
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
        except Cart.DoesNotExist:
            return JsonResponse({
                'status': 'success', 
                'shipping_fee': 0, 
                'total': 0, 
                'subtotal': 0
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error'}, status=400)


def buy_now(request):
    if request.method=='POST':
        try:
            data = json.loads(request.body)
            variant_uid = data.get('variant_uid')
            quantity = int(data.get('quantity', 1))


            request.session['direct_buy_item'] = {
                'variant_uid': variant_uid,
                'quantity': quantity
            }

            request.session.modified = True

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error','message': 'Invalid request'}, )