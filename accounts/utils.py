from django.conf import settings
from .models import Address

# Lấy giá trị mặc định từ settings hoặc set cứng
DEFAULT_SHIPPING_FEE = getattr(settings, 'DEFAULT_SHIPPING_FEE', 30000)

def get_user_shipping_fee(user, subtotal):
    """
    Hàm tính phí vận chuyển dựa trên:
    1. Tổng giá trị đơn hàng (Freeship nếu > 1 triệu)
    2. Địa chỉ mặc định của người dùng (Logic Vùng miền)
    """
    # 1. Logic Freeship đơn hàng lớn
    if subtotal > 1000000:
        return 0
    
    # Nếu chưa đăng nhập hoặc không có user -> Phí mặc định
    if not user or not user.is_authenticated:
        return DEFAULT_SHIPPING_FEE

    try:
        # 2. Tìm địa chỉ để tính phí
        # Ưu tiên địa chỉ mặc định, nếu không có thì lấy địa chỉ đầu tiên
        address = Address.objects.filter(user=user, is_default=True).first()
        if not address:
            address = Address.objects.filter(user=user).first()

        if address:
            # 3. Logic tính phí theo khu vực (Giả lập)
            # Bạn có thể tích hợp API Giao Hàng Nhanh hoặc Geopy tại đây
            city_lower = address.city.lower()
            
            # Ví dụ: Nội thành (Hà Nội, HCM) rẻ hơn
            if "hà nội" in city_lower or "ha noi" in city_lower or "hồ chí minh" in city_lower or "hcm" in city_lower:
                return 20000
            else:
                return 35000 # Ngoại thành/Tỉnh khác
    except Exception as e:
        print(f"Lỗi tính phí ship: {e}")
        
    return DEFAULT_SHIPPING_FEE

def calculate_cart_total(cart_obj, user=None):
    """
    Hàm trung tâm tính toán toàn bộ chi phí giỏ hàng/đơn hàng.
    Trả về: Subtotal, Ship, Tax, Discount, Total.
    """
    cart_items = cart_obj.cart_items.all()
    
    # 1. Tính tổng tiền hàng (Subtotal)
    subtotal = sum(item.get_product_price for item in cart_items)
    
    # 2. Tính phí Ship
    # Ưu tiên user được truyền vào (ví dụ user đang login), nếu không thì lấy user của giỏ hàng
    current_user = user if user else cart_obj.user
    shipping_fee = get_user_shipping_fee(current_user, subtotal)
    
    # 3. Tính giảm giá (Coupon)
    total_discount = 0
    
    # Kiểm tra ManyToMany field coupons
    if cart_obj.coupons.exists():
        for coupon in cart_obj.coupons.all():
            # Kiểm tra điều kiện tối thiểu của coupon
            if subtotal < coupon.minimum_amount:
                continue

            discount_amount = 0
            
            if coupon.coupon_type == 'percent':
                # Giảm theo %: (Tổng tiền * số %) / 100
                discount_amount = (subtotal * coupon.discount_price) / 100
                
            elif coupon.coupon_type == 'amount':
                # Giảm số tiền cố định
                discount_amount = coupon.discount_price
                
            elif coupon.coupon_type == 'shipping':
                # Giảm phí ship (Freeship)
                discount_amount = shipping_fee

            total_discount += discount_amount

    # 4. Validation: Giảm giá không được vượt quá (Tổng tiền + Ship)
    # (Để tránh trường hợp tổng thanh toán bị âm)
    grand_total_temp = subtotal + shipping_fee
    if total_discount > grand_total_temp:
        total_discount = grand_total_temp

    # 5. Tính Thuế (Nếu có, ví dụ 0% hoặc 8%)
    tax = 0 
    
    # 6. Tính Tổng cuối cùng (Grand Total)
    grand_total = int(subtotal + shipping_fee + tax - total_discount)

    return {
        'cart_items': cart_items,
        'subtotal': int(subtotal),
        'shipping_fee': int(shipping_fee),
        'tax': int(tax),
        'discount': int(total_discount),
        'total': int(grand_total)
    }