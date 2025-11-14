from django.shortcuts import redirect, render
from products.models import Product
def home_view(request):
    all_products = Product.objects.all()
    context = {
        'products': all_products
    }
    return render(request, 'home/index.html',context)