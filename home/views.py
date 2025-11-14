from django.shortcuts import render, redirect
from products.models import Product

from django.db.models import Min




def index(request):
    
    products_list = Product.objects.annotate(
        min_price=Min('variants__price')
    ).all()
    
    context = {
        'products': products_list
    }
    return render(request, 'home/index.html', context)