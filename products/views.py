from django.shortcuts import redirect, render
from .models import Product,SizeVariant
from django.http import Http404 
from accounts.models import Cart,CartItems
from django.http import HttpResponseRedirect
def get_product(request, slug):

    try:

        product = Product.objects.get(slug=slug)
        context = {
            'product': product,

        }
        if request.GET.get('size'):
            size = request.GET.get('size')
            price = product.get_product_price_by_size(size)
            context['selected_size'] = size
            context['updated_price'] = price
            print(price)

        return render(request, 'product/product.html', context=context)

    except Exception as e:
        print(e)
            
        raise Http404("Sản phẩm không tồn tại")

