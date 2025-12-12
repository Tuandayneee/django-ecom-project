from django.conf import settings
from .models import Address
from geopy.geocoders import Nominatim
from geopy.distance import geodesic 

# --- CẤU HÌNH ---
# Tọa độ kho (Ví dụ: Hà Nội)
STORE_COORDS = (21.028511, 105.854444) 
STORE_CITY = "Hà Nội" # Tên tỉnh/thành phố đặt kho

def get_shipping_fee_by_location(address_obj):
    
    customer_city = address_obj.city.lower()
    
   
    if "côn đảo" in customer_city or "phú quốc" in customer_city:
        return 70000 
    
    
    if "hà nội" in customer_city or "ha noi" in customer_city:
        return 25000 
    return 35000 

# --- HÀM MAIN ---
# --- HÀM MAIN (Trong utils.py) ---
# Thêm tham số selected_address=None
def calculate_cart_total(cart_obj, user=None, selected_address=None):
    cart_items = cart_obj.cart_items.all()
    subtotal = sum(item.get_product_price for item in cart_items)
    
    
    shipping_fee = 30000 
    
    address_to_use = None
    if selected_address:
        address_to_use = selected_address 
    else:
       
        current_user = user if user else cart_obj.user
        if current_user and current_user.is_authenticated:
            address_to_use = Address.objects.filter(user=current_user, is_default=True).first()
            if not address_to_use:
                address_to_use = Address.objects.filter(user=current_user).first()
    
    
    if subtotal > 1000000:
        shipping_fee = 0 
    elif address_to_use:
        shipping_fee = get_shipping_fee_by_location(address_to_use)

    
    total_discount = 0 
    if cart_obj.coupons.exists():
        for coupon in cart_obj.coupons.all():
            if subtotal < coupon.minimum_amount: continue
            eligible_amount = 0
            if coupon.category:
                for item in cart_items:
                    if item.variant.product.category == coupon.category:
                        eligible_amount += item.get_product_price
            else:
                eligible_amount = subtotal
            
            if eligible_amount == 0 : continue

            if coupon.coupon_type == 'percent':
                discount_val = (eligible_amount*coupon.discount_price)/100
                total_discount += discount_val
            elif coupon.coupon_type == 'amount':
                 total_discount += coupon.discount_price
            elif coupon.coupon_type == 'shipping':
                 total_discount += shipping_fee 

    grand_total_temp = subtotal + shipping_fee
    if total_discount > grand_total_temp: total_discount = grand_total_temp
    
    tax = 0
    grand_total = int(subtotal + shipping_fee + tax - total_discount)

    
    return {
        'cart_items': cart_items,
        'subtotal': int(subtotal),
        'shipping_fee': int(shipping_fee),
        'tax': int(tax),
        'discount': int(total_discount),
        'total': int(grand_total)
    }