from accounts.models import Cart
from accounts.utils import calculate_cart_total
from products.models import Category


def menu_categories(request):
    categories = Category.objects.all()
    return {'menu_categories': categories}


def cart_context(request):
    """Provide cart data to all templates."""
    default_cart_data = {
        'cart_items': [],
        'subtotal': 0,
        'total': 0,
        'discount': 0,
        'shipping_fee': 0,
        'tax': 0,
    }

    if request.user.is_authenticated:
        cart_obj = Cart.objects.filter(user=request.user, is_paid=False).first()
        if cart_obj:
            return {'cart_data': calculate_cart_total(cart_obj, user=request.user)}

    return {'cart_data': default_cart_data}
