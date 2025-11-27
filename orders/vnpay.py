# orders/vnpay_views.py
import hashlib
import hmac
import urllib.parse
from datetime import datetime
from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponse
from accounts.models import Cart

def vnpay_payment(request):
    # Lấy địa chỉ user vừa chọn ở Checkout (quan trọng)
    address_uid = request.session.get('shipping_address_uid')
    if not address_uid:
        return redirect('checkout')

    if request.method == 'GET' or request.method == 'POST': # Chấp nhận cả GET từ redirect checkout
        try:
            cart_obj = Cart.objects.get(user=request.user, is_paid=False)
        except Cart.DoesNotExist:
            return HttpResponse("Giỏ hàng trống.")
        
        # Gọi helper tính tiền (Import từ accounts.views hoặc utils nếu đã tách)
        from accounts.views import _get_cart_details 
        cart_data = _get_cart_details(cart_obj)
        total_amount = cart_data['total']
        
        if total_amount <= 0:
            return HttpResponse("Số tiền không hợp lệ")

        # --- CẤU HÌNH VNPAY ---
        order_type = 'billpayment'
        # Tạo Order ID có chứa User ID để dễ tra cứu sau này
        order_id = f"ORD-{request.user.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Lưu order_id tạm vào session để dùng ở bước Return
        request.session['vnp_order_id'] = order_id
        
        ipaddr = get_client_ip(request)

        inputData = {
            "vnp_Version": "2.1.0",
            "vnp_Command": "pay",
            "vnp_TmnCode": settings.VNPAY_TMN_CODE,
            "vnp_Amount": str(int(total_amount * 100)), # Nhân 100
            "vnp_CreateDate": datetime.now().strftime('%Y%m%d%H%M%S'),
            "vnp_CurrCode": "VND",
            "vnp_IpAddr": ipaddr,
            "vnp_Locale": "vn",
            "vnp_OrderInfo": f"Thanh toan don hang {order_id}",
            "vnp_OrderType": order_type,
            "vnp_ReturnUrl": settings.VNPAY_RETURN_URL,
            "vnp_TxnRef": order_id,
        }

        # Sắp xếp và Hash (Logic bắt buộc của VNPay)
        inputData = sorted(inputData.items())
        queryData = urllib.parse.urlencode(inputData)

        vnp_SecureHash = hmac.new(
            bytes(settings.VNPAY_HASH_SECRET_KEY, 'utf-8'),
            bytes(queryData, 'utf-8'),
            hashlib.sha512
        ).hexdigest()

        payment_url = settings.VNPAY_PAYMENT_URL + "?" + queryData + "&vnp_SecureHash=" + vnp_SecureHash
        
        return redirect(payment_url)

    return redirect('checkout')

# Hàm xử lý khi VNPay trả kết quả về
def payment_return(request):
    # Logic xử lý kết quả (Update DB, tạo Order...) sẽ viết ở đây
    # ...
    return HttpResponse("Đang xử lý kết quả thanh toán...")

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip