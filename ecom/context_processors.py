from products.models import Category
from accounts.models import Cart
from accounts.utils import calculate_cart_total

def menu_categories(request):
    categories = Category.objects.all()
    return {'menu_categories': categories}

def cart_context(request):
    """Provide cart data to all templates"""
    cart_data = {}
    
    if request.user.is_authenticated:
        try:
            cart_obj = Cart.objects.get(user=request.user, is_paid=False)
            cart_data = calculate_cart_total(cart_obj, user=request.user)
        except Cart.DoesNotExist:
            
            cart_data = {
                'cart_items': [],
                'subtotal': 0,
                'total': 0,
                'discount': 0,
                'shipping_fee': 0,
                'tax': 0
            }
    else:
        
        cart_data = {
            'cart_items': [],
            'subtotal': 0,
            'total': 0,
            'discount': 0,
            'shipping_fee': 0,
            'tax': 0
        }
    
    return {'cart_data': cart_data}