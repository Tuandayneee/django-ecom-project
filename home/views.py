from django.shortcuts import render, redirect
from home.models import Slider
from products.models import Product,Category

from django.db.models import Min




def index(request):
    
    products = Product.objects.all()
    
    categories = Category.objects.all()
    sliders = Slider.objects.all()
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(product_name__icontains=search_query)
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)
    context = {
        'products': products,
        'categories': categories,
        'sliders': sliders, # <--- Truyền biến này sang template
        'search_query': search_query
    }   
    return render(request, 'home/index.html', context) 