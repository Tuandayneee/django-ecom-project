import hashlib
import hmac
import urllib.parse
from datetime import datetime
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.db import transaction
from products.models import Variant
# Import Models & Utils
from accounts.models import Cart, Address
from accounts.utils import calculate_cart_total
from orders.utils import get_user_shipping_fee # <--- DÙNG HÀM NÀY
from .models import Order, OrderProduct, Payment

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def vnpay_payment(request):
    address_uid = request.session.get('shipping_address_uid')
    if not address_uid:
        messages.warning(request, "Vui lòng chọn địa chỉ giao hàng trước.")
        return redirect('orders:checkout')

    try:
        # Kiểm tra cờ xem đang là Mua ngay hay Giỏ hàng
        is_buy_now = request.session.get('is_buy_now', False)
        
        total_amount = 0
        order_info_str = ""

        if is_buy_now:
            # === TRƯỜNG HỢP 1: MUA NGAY ===
            item_data = request.session.get('direct_buy_item')
            if not item_data:
                return redirect('product') # Hoặc trang lỗi
            
            # Lấy sản phẩm từ DB
            variant = Variant.objects.get(uid=item_data['variant_uid'])
            quantity = int(item_data['quantity'])
            
            # Tính tiền (Giá * Số lượng + Ship)
            # Lưu ý: Bạn cần đảm bảo logic tính ship ở đây khớp với lúc hiển thị checkout
            subtotal = variant.price * quantity
            shipping_fee = 35000 # Ví dụ cố định, hoặc gọi hàm get_shipping_fee(subtotal)
            
            total_amount = subtotal + shipping_fee
            order_info_str = f"Thanh toan mua ngay: {variant.product.product_name}"
            
        else:
            # === TRƯỜNG HỢP 2: GIỎ HÀNG ===
            # Tìm giỏ hàng có sản phẩm
            carts = Cart.objects.filter(user=request.user, is_paid=False)
            cart_obj = None
            for cart in carts:
                if cart.cart_items.exists():
                    cart_obj = cart
                    break
            
            if not cart_obj:
                return redirect('store')

            cart_data = calculate_cart_total(cart_obj, user=request.user)
            total_amount = int(cart_data['total'])
            order_info_str = f"Thanh toan gio hang User {request.user.id}"

        # --- PHẦN TẠO URL VNPAY ---
        order_id = f"ORD-{request.user.id}-{datetime.now().strftime('%H%M%S')}"
        request.session['order_ref'] = order_id # Lưu lại để check
        
        ipaddr = get_client_ip(request)
        
        inputData = {
            "vnp_Version": "2.1.0",
            "vnp_Command": "pay",
            "vnp_TmnCode": settings.VNPAY_TMN_CODE,
            "vnp_Amount": str(int(total_amount) * 100), # Bắt buộc nhân 100
            "vnp_CreateDate": datetime.now().strftime('%Y%m%d%H%M%S'),
            "vnp_CurrCode": "VND",
            "vnp_IpAddr": ipaddr,
            "vnp_Locale": "vn",
            "vnp_OrderInfo": order_info_str,
            "vnp_OrderType": "billpayment",
            "vnp_ReturnUrl": settings.VNPAY_RETURN_URL,
            "vnp_TxnRef": order_id, 
        }

        inputData = sorted(inputData.items())
        queryData = urllib.parse.urlencode(inputData)
        
        if settings.VNPAY_HASH_SECRET_KEY:
            vnp_SecureHash = hmac.new(
                bytes(settings.VNPAY_HASH_SECRET_KEY, 'utf-8'),
                bytes(queryData, 'utf-8'),
                hashlib.sha512
            ).hexdigest()
            queryData += "&vnp_SecureHash=" + vnp_SecureHash

        payment_url = settings.VNPAY_PAYMENT_URL + "?" + queryData
        return redirect(payment_url)

    except Exception as e:
        print(f"Lỗi tạo URL VNPay: {e}")
        return redirect('orders:checkout')

# --- 2. XỬ LÝ KẾT QUẢ TRẢ VỀ (QUAN TRỌNG NHẤT) ---
def payment_return(request):
    inputData = request.GET
    if inputData:
        vnp_ResponseCode = inputData.get('vnp_ResponseCode')
        vnp_TxnRef = inputData.get('vnp_TxnRef')
        
        # Kiểm tra thành công (Mã 00 là thành công)
        if vnp_ResponseCode == '00':
            try:
                with transaction.atomic():
                    # 1. Lấy thông tin địa chỉ
                    address_uid = request.session.get('shipping_address_uid')
                    address = Address.objects.get(uid=address_uid)
                    
                    # --- XÁC ĐỊNH NGUỒN DỮ LIỆU (MUA NGAY hay GIỎ HÀNG) ---
                    is_buy_now = request.session.get('is_buy_now', False)
                    
                    # Khai báo biến chung để hứng dữ liệu
                    final_subtotal = 0
                    final_shipping = 35000 # Logic tính ship phải khớp với lúc gọi pay
                    final_total = 0
                    final_tax = 0
                    final_discount = 0
                    order_items_payload = [] # List chứa các món hàng cần tạo

                    if is_buy_now:
                        # == XỬ LÝ MUA NGAY ==
                        item_data = request.session.get('direct_buy_item')
                        variant = Variant.objects.get(uid=item_data['variant_uid'])
                        qty = int(item_data['quantity'])
                        
                        final_subtotal = variant.price * qty
                        # final_shipping = get_shipping_fee(...) # Nếu có hàm tính ship riêng
                        final_total = final_subtotal + final_shipping
                        
                        # Thêm vào list để lát nữa loop tạo OrderProduct
                        order_items_payload.append({
                            'variant': variant,
                            'quantity': qty,
                            'price': variant.price
                        })
                        
                    else:
                        # == XỬ LÝ GIỎ HÀNG ==
                        carts = Cart.objects.filter(user=request.user, is_paid=False)
                        cart_obj = None
                        for cart in carts:
                            if cart.cart_items.exists():
                                cart_obj = cart
                                break
                        
                        cart_data = calculate_cart_total(cart_obj, user=request.user)
                        
                        final_subtotal = cart_data['subtotal']
                        final_shipping = cart_data['shipping_fee']
                        final_tax = cart_data['tax']
                        final_discount = cart_data['discount'] # Nếu có
                        final_total = cart_data['total']
                        
                        # Chuyển đổi item trong giỏ thành list chuẩn
                        for item in cart_data['cart_items']:
                            order_items_payload.append({
                                'variant': item.variant,
                                'quantity': item.quantity,
                                'price': item.variant.price
                            })

                    # -----------------------------------------------------

                    # 2. Tạo Payment
                    payment = Payment.objects.create(
                        user=request.user,
                        payment_id=vnp_TxnRef, 
                        payment_method='VNPay',
                        amount_paid=str(final_total),
                        status='Completed' 
                    )

                    # 3. Tạo Order
                    order = Order.objects.create(
                        user=request.user,
                        payment=payment,
                        order_number=vnp_TxnRef, 
                        full_name=address.full_name,
                        phone=address.phone,
                        address=address.address_line,
                        city=address.city,
                        order_total=final_subtotal,
                        shipping_fee=final_shipping,
                        coupon_discount=final_discount,
                        tax=final_tax,
                        status='Accepted', 
                        is_ordered=True
                    )

                    # 4. Tạo OrderProduct & Trừ kho (Dùng chung cho cả 2 trường hợp)
                    for item in order_items_payload:
                        var = item['variant']
                        qty = item['quantity']
                        price = item['price']

                        # Trừ kho
                        var.stock -= qty
                        var.save()

                        OrderProduct.objects.create(
                            order=order,
                            user=request.user,
                            payment=payment,
                            product=var.product,
                            variant=var,
                            quantity=qty,
                            product_price=price,
                            ordered=True
                        )

                    # 5. Dọn dẹp dữ liệu (Cleanup)
                    if is_buy_now:
                        # Xóa session mua ngay
                        if 'direct_buy_item' in request.session:
                            del request.session['direct_buy_item']
                        if 'is_buy_now' in request.session:
                            del request.session['is_buy_now']
                    else:
                        # Xóa giỏ hàng
                        if cart_obj:
                            cart_obj.cart_items.all().delete()
                            cart_obj.coupons.clear()
                            cart_obj.save()

                    # Xóa session địa chỉ chung
                    if 'shipping_address_uid' in request.session:
                        del request.session['shipping_address_uid']
                    
                    messages.success(request, "Thanh toán thành công!")
                    return redirect('orders:order_success', order_uid=order.uid)

            except Exception as e:
                print(f"Lỗi xử lý VNPay Return: {e}")
                messages.error(request, "Thanh toán thành công nhưng lỗi tạo đơn. Liên hệ Admin.")
                return redirect('orders:checkout')
        
        else:
            # Thanh toán thất bại / Hủy bỏ
            messages.error(request, "Giao dịch thất bại hoặc bị hủy.")
            return redirect('orders:checkout')

    return redirect('home')