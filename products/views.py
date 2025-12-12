from django.shortcuts import render
from .models import Product,  Variant
from django.http import Http404 
import json
from django.db.models import Min  # <-- QUAN TRỌNG: Import Min
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
def get_product(request, slug):
    try:
        product = Product.objects.get(slug=slug)
        variants = product.variants.all() 
        available_colors = set()
        available_sizes = set()
        variants_map = {}

        for variant in variants:
            if variant.color:
                available_colors.add(variant.color)
            if variant.size:
                available_sizes.add(variant.size)
            
            color_uid = variant.color.uid if variant.color else 'None'
            size_uid = variant.size.uid if variant.size else 'None'
            key = f"{color_uid}-{size_uid}"
            
            variants_map[key] = {
                'price': variant.price,
                'stock': variant.stock,
                'variant_uid': str(variant.uid) 
            }

       
        default_price = 0
        if variants.exists():
            min_price_data = variants.aggregate(min_price=Min('price'))
            default_price = min_price_data['min_price']
        

        context = {
            'product': product,
            'default_price': default_price, 
            'available_colors': list(available_colors),
            'available_sizes': list(available_sizes),
            'variants_map_json': json.dumps(variants_map)
        }
        
        return render(request, 'product/product.html', context=context)

    except Product.DoesNotExist:
        raise Http404("Sản phẩm không tồn tại")
    except Exception as e:
        print(f"LỖI TRONG get_product (console): {e}") 
        raise Http404("Đã xảy ra lỗi khi xử lý biến thể. Kiểm tra console.")


def get_variant_price(request):
    product_uid = request.GET.get('product_uid')
    color_uid = request.GET.get('color_uid')
    size_uid = request.GET.get('size_uid')
    quantity_str = request.GET.get('quantity','1')
    try:
        quantity = int(quantity_str)
        if(quantity < 1): quantity = 1
    except ValueError:
        quantity = 1
    

    response_data = {
        'success':False,
        'message':'Vui lòng chọn đủ màu sắc kích thược',
        'price': '',
        'stock': '',
        'stock_class' :'text-danger',
        'can_add_to_cart': False,
        'variant_uid':None
    }
    
    if not color_uid or not size_uid or color_uid=="None" or size_uid=="None":
        return JsonResponse(response_data)
    
    try:
       item = Variant.objects.get(product__uid=product_uid, color__uid=color_uid, size__uid=size_uid).first()
       if item:
           unit_price = item.price if item.price>0 else item.product.price
           total_price = unit_price * quantity
           response_data['price'] = f"{total_price:,} VND".replace(',', '.')
           response_data['variant_uid']= item.uid
           if(item>0):
               response_data['stock'] = f"Còn {item.stock} sản phẩm"
               response_data['stock_class'] = 'text-success'

               if quantity > item.stock:
                    response_data['can_add_to_cart'] = False
                    response_data['message'] = f"Kho chỉ còn {item.stock} sản phẩm"
                    response_data['stock_class'] = "text-danger"
               else:
                   response_data['can_add_to_cart'] = True
                   response_data['message'] = "Có sẵn hàng"
                   response_data['stock_class'] = "text-success"
           else:
               response_data['stock'] = "Hết hàng"
               response_data['can_add_to_cart'] = False
               response_data['message'] = "Sản phẩm tạm hết hàng"
       else:  
           response_data['message'] = "Sản phẩm này không tồn tại"
    except Exception as e:
        print(e) 
        response_data['message'] = "Lỗi hệ thống khi lấy giá"
    
    return JsonResponse(response_data)

            

