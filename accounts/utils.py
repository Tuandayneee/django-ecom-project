from accounts.models import Address
from orders.utils import get_user_shipping_fee
from products.models import CouponUsage


def get_shipping_fee_by_location(address_obj):
    customer_city = (address_obj.city or '').lower()
    if 'côn đảo' in customer_city or 'phú quốc' in customer_city:
        return 70000
    if (
        'hà nội' in customer_city
        or 'ha noi' in customer_city
        or 'hồ chí minh' in customer_city
        or 'hcm' in customer_city
    ):
        return 25000
    return 35000


def calculate_cart_total(cart_obj, user=None, selected_address=None):
    """Canonical cart pricing calculator with shipping, category coupons, validity, and usage limits."""
    cart_items = cart_obj.cart_items.select_related('variant__product__category').all()
    subtotal = sum(item.get_product_price for item in cart_items)

    current_user = user if user else cart_obj.user
    address_to_use = selected_address
    if not address_to_use and current_user and current_user.is_authenticated:
        address_to_use = (
            Address.objects.filter(user=current_user, is_default=True).first()
            or Address.objects.filter(user=current_user).first()
        )

    shipping_fee = get_user_shipping_fee(current_user, subtotal, address=address_to_use)

    total_discount = 0
    if cart_obj.coupons.exists():
        usage_map = {}
        if current_user and current_user.is_authenticated:
            usage_map = dict(
                CouponUsage.objects.filter(
                    user=current_user,
                    coupon__in=cart_obj.coupons.all(),
                ).values_list('coupon_id', 'used_count')
            )

        for coupon in cart_obj.coupons.all():
            if not coupon.is_valid():
                continue
            if subtotal < coupon.minimum_amount:
                continue
            if current_user and current_user.is_authenticated:
                if usage_map.get(coupon.id, 0) >= coupon.usage_limit_per_user:
                    continue

            if coupon.category:
                eligible_amount = sum(
                    item.get_product_price
                    for item in cart_items
                    if item.variant and item.variant.product.category == coupon.category
                )
            else:
                eligible_amount = subtotal

            if eligible_amount <= 0:
                continue

            if coupon.coupon_type == 'percent':
                total_discount += (eligible_amount * coupon.discount_price) / 100
            elif coupon.coupon_type == 'amount':
                total_discount += coupon.discount_price
            elif coupon.coupon_type == 'shipping':
                total_discount += shipping_fee

    grand_total_temp = subtotal + shipping_fee
    if total_discount > grand_total_temp:
        total_discount = grand_total_temp

    tax = 0
    grand_total = int(subtotal + shipping_fee + tax - total_discount)

    return {
        'cart_items': cart_items,
        'subtotal': int(subtotal),
        'shipping_fee': int(shipping_fee),
        'tax': int(tax),
        'discount': int(total_discount),
        'total': int(grand_total),
    }
