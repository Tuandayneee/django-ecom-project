from django.shortcuts import render
from .models import Product, Variant
from django.http import Http404 
import json
from django.db.models import Min  # <-- QUAN TRỌNG: Import Min

def get_product(request, slug):
    try:
        product = Product.objects.get(slug=slug)
        # Lấy queryset của các biến thể
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
            # Dùng .aggregate() để tìm giá trị nhỏ nhất (Min)
            # trong tất cả các biến thể của sản phẩm này.
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

