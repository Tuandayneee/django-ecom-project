from django.conf import settings
from accounts.models import Address

DEFAULT_SHIPPING_FEE = getattr(settings, 'DEFAULT_SHIPPING_FEE', 30000)


def get_user_shipping_fee(user, subtotal, address=None):
    """Compute shipping fee based on order subtotal and destination city."""
    if subtotal > 3000000:
        return 0

    if not user or not user.is_authenticated:
        return DEFAULT_SHIPPING_FEE

    if not address:
        address = (
            Address.objects.filter(user=user, is_default=True).first()
            or Address.objects.filter(user=user).first()
        )

    if address:
        city_lower = (address.city or '').lower()
        if 'côn đảo' in city_lower or 'phú quốc' in city_lower:
            return 70000
        if (
            'hà nội' in city_lower
            or 'ha noi' in city_lower
            or 'hồ chí minh' in city_lower
            or 'hcm' in city_lower
        ):
            return 25000
        return 35000

    return DEFAULT_SHIPPING_FEE
