import hashlib
import hmac
import urllib.parse
from datetime import datetime
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.db import transaction

# Import Models & Utils
from accounts.models import Cart, Address
from accounts.utils import calculate_cart_total # <--- DÙNG HÀM NÀY
from .models import Order, OrderProduct, Payment

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# --- 1. GỬI YÊU CẦU SANG VNPAY ---
def vnpay_payment(request):
    # Lấy địa chỉ từ Session (đã lưu ở bước Checkout)
    address_uid = request.session.get('shipping_address_uid')
    if not address_uid:
        messages.warning(request, "Vui lòng chọn địa chỉ giao hàng trước.")
        return redirect('orders:checkout')

    try:
        # Lấy giỏ hàng và tính tiền
        cart_obj = Cart.objects.get(user=request.user, is_paid=False)
        cart_data = calculate_cart_total(cart_obj, user=request.user) # <--- SỬA LỖI TẠI ĐÂY
        total_amount = int(cart_data['total']) # VNPay yêu cầu số nguyên

        # Tạo mã đơn hàng tạm (Ref)
        order_id = f"ORD-{request.user.id}-{datetime.now().strftime('%H%M%S')}"
        
        # Lưu Order ID tạm vào session để check lại khi return
        request.session['order_ref'] = order_id

        # Cấu hình tham số VNPay
        ipaddr = get_client_ip(request)
        
        inputData = {
            "vnp_Version": "2.1.0",
            "vnp_Command": "pay",
            "vnp_TmnCode": settings.VNPAY_TMN_CODE,
            "vnp_Amount": str(total_amount * 100), # Bắt buộc nhân 100
            "vnp_CreateDate": datetime.now().strftime('%Y%m%d%H%M%S'),
            "vnp_CurrCode": "VND",
            "vnp_IpAddr": ipaddr,
            "vnp_Locale": "vn",
            "vnp_OrderInfo": f"Thanh toan don hang {order_id}",
            "vnp_OrderType": "billpayment",
            "vnp_ReturnUrl": settings.VNPAY_RETURN_URL,
            "vnp_TxnRef": order_id, 
        }

        # Sắp xếp dữ liệu (Yêu cầu bắt buộc của VNPay)
        inputData = sorted(inputData.items())
        queryData = urllib.parse.urlencode(inputData)
        
        # Tạo chữ ký bảo mật (Secure Hash)
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
                # Bắt đầu Transaction để tạo đơn hàng
                with transaction.atomic():
                    # 1. Lấy lại thông tin từ Session/DB
                    address_uid = request.session.get('shipping_address_uid')
                    address = Address.objects.get(uid=address_uid)
                    
                    cart_obj = Cart.objects.get(user=request.user, is_paid=False)
                    cart_data = calculate_cart_total(cart_obj, user=request.user)
                    
                    # 2. Tạo Payment (Đã thanh toán)
                    payment = Payment.objects.create(
                        user=request.user,
                        payment_id=vnp_TxnRef, # Lưu mã đơn của VNPay
                        payment_method='VNPay',
                        amount_paid=str(cart_data['total']),
                        status='Completed' # <--- QUAN TRỌNG: Đã trả tiền
                    )

                    # 3. Tạo Order
                    order = Order.objects.create(
                        user=request.user,
                        payment=payment,
                        order_number=vnp_TxnRef, # Dùng luôn mã Ref làm mã đơn
                        full_name=address.full_name,
                        phone=address.phone,
                        address=address.address_line,
                        city=address.city,
                        order_total=cart_data['subtotal'],
                        shipping_fee=cart_data['shipping_fee'],
                        coupon_discount=cart_data['discount'],
                        tax=cart_data['tax'],
                        status='Accepted', # Đã xác nhận vì đã trả tiền
                        is_ordered=True
                    )

                    # 4. Chuyển sản phẩm & Trừ kho
                    for item in cart_data['cart_items']:
                        variant = item.variant
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

                    # 5. Xóa giỏ hàng
                    cart_obj.cart_items.all().delete()
                    cart_obj.coupons.clear()
                    cart_obj.save()

                    # Xóa session
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