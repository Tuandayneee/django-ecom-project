from django.shortcuts import render, redirect
from products.models import Product
from django.contrib.auth import logout





def index(request):
    # Do not auto-logout users on visiting the index.
    # Keep original behavior: render homepage for both anonymous and authenticated users.
    context = {
        'products': Product.objects.all()
    }
    return render(request, 'home/index.html', context)
