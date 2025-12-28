from django.conf import settings
from accounts.models import Address

# Lấy giá trị mặc định từ settings hoặc set cứng
DEFAULT_SHIPPING_FEE = getattr(settings, 'DEFAULT_SHIPPING_FEE', 30000)

def get_user_shipping_fee(user, subtotal, address=None):
    
    # 1. Logic Freeship đơn hàng lớn
    if subtotal > 3000000:
        return 0
    
    # Nếu chưa đăng nhập hoặc không có user -> Phí mặc định
    if not user or not user.is_authenticated:
        return DEFAULT_SHIPPING_FEE

    try:
        # 2. Xác định địa chỉ để tính phí
        # Nếu KHÔNG có address truyền vào, mới đi tìm trong DB
        if not address:
            address = Address.objects.filter(user=user, is_default=True).first()
            if not address:
                address = Address.objects.filter(user=user).first()

        # 3. Logic tính phí theo khu vực
        if address:
            city_lower = address.city.lower() if address.city else ""
            
            # Ví dụ: Nội thành (Hà Nội, HCM) rẻ hơn
            if "hà nội" in city_lower or "ha noi" in city_lower or "hồ chí minh" in city_lower or "hcm" in city_lower:
                return 25000
            else:
                return 35000 
                
    except Exception as e:
        print(f"Lỗi tính phí ship: {e}")
        
    return DEFAULT_SHIPPING_FEE

def calculate_cart_total(cart_obj, user=None, selected_address=None):
    
    cart_items = cart_obj.cart_items.all()
    
    # 1. Tính tổng tiền hàng (Subtotal)
    subtotal = sum(item.get_product_price for item in cart_items)
    
    # 2. Tính phí Ship
    current_user = user if user else cart_obj.user
    
    # QUAN TRỌNG: Truyền selected_address xuống hàm tính ship
    shipping_fee = get_user_shipping_fee(current_user, subtotal, address=selected_address)
    
    # 3. Tính giảm giá (Coupon)
    total_discount = 0
    
    if cart_obj.coupons.exists():
        for coupon in cart_obj.coupons.all():
            if subtotal < coupon.minimum_amount:
                continue

            discount_amount = 0
            
            if coupon.coupon_type == 'percent':
                discount_amount = (subtotal * coupon.discount_price) / 100
                
            elif coupon.coupon_type == 'amount':
                discount_amount = coupon.discount_price
                
            elif coupon.coupon_type == 'shipping':
                discount_amount = shipping_fee

            total_discount += discount_amount

    # 4. Validation
    grand_total_temp = subtotal + shipping_fee
    if total_discount > grand_total_temp:
        total_discount = grand_total_temp

    # 5. Tính Thuế
    tax = 0 
    
    # 6. Tính Tổng cuối cùng
    grand_total = int(subtotal + shipping_fee + tax - total_discount)

    return {
        'cart_items': cart_items,
        'subtotal': int(subtotal),
        'shipping_fee': int(shipping_fee),
        'tax': int(tax),
        'discount': int(total_discount),
        'total': int(grand_total)
    }