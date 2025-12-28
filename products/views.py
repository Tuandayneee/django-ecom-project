from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404

from orders.models import Order
from products.forms import ReviewForm
from .models import Product, Review, Variant
from django.http import Http404, JsonResponse
from django.db.models import Min, Avg
import json

def get_product(request, slug):
    try:
        product = get_object_or_404(Product, slug=slug)
        variants = product.variants.all()
        
        
        default_image_url = ""
        if product.product_images.first():
            default_image_url = product.product_images.first().image.url
            
        variants_map = {}
        
       
        available_colors = set()
        available_sizes = set()

        for variant in variants:
            if variant.color: available_colors.add(variant.color)
            if variant.size: available_sizes.add(variant.size)
            
            color_uid = variant.color.uid if variant.color else 'None'
            size_uid = variant.size.uid if variant.size else 'None'
            key = f"{color_uid}-{size_uid}"
            
           
            image_url = default_image_url
            if variant.image:
                image_url = variant.image.url
                
            variants_map[key] = {
                'price': float(variant.price) if variant.price else product.original_price,
                'original_price': float(variant.original_price) if variant.original_price > 0 else float(variant.price or 0),
                'stock': variant.stock,
                'variant_uid': str(variant.uid),
                'image_url': image_url  
            }

        
        default_price = 0
        if variants.exists():
            min_price_data = variants.aggregate(min_price=Min('price'))
            default_price = min_price_data['min_price']

        
        count = product.reviews.count()
        avg_data = product.reviews.aggregate(avg_rating=Avg('rating'))
        average = avg_data['avg_rating'] or 0
        sold_count = product.sold_count
        reviews = product.reviews.all().order_by('-created_at')

        context = {
            'product': product,
            'reviews': reviews,
            'default_price': default_price,
            'available_colors': list(available_colors),
            'available_sizes': list(available_sizes),
            'variants_map_json': json.dumps(variants_map), 
            'original_price': product.original_price,
            'review_count': count,
            'average': average,
            'sold_count': sold_count,
        }
        
        return render(request, 'product/product.html', context=context)

    except Product.DoesNotExist:
        raise Http404("Sản phẩm không tồn tại")
    except Exception as e:
        print(f"LỖI: {e}")
        raise Http404("Lỗi hệ thống")


def get_variant_price(request):
    product_uid = request.GET.get('product_uid')
    color_uid = request.GET.get('color_uid')
    size_uid = request.GET.get('size_uid')
    quantity_str = request.GET.get('quantity', '1')
    
    try:
        quantity = int(quantity_str)
        if quantity < 1: quantity = 1
    except ValueError:
        quantity = 1
    
    response_data = {
        'success': False,
        'message': 'Vui lòng chọn đủ màu sắc kích thước',
    }

    if not color_uid or not size_uid or color_uid == "None" or size_uid == "None":
        return JsonResponse(response_data)

    try:
        
        item = Variant.objects.filter(
            product__uid=product_uid, 
            color__uid=color_uid, 
            size__uid=size_uid
        ).first()

        if item:
            unit_price = item.price if item.price > 0 else item.product.price
            total_price = unit_price * quantity
            
            response_data['price'] = f"{total_price:,.0f} VND".replace(',', '.')
            response_data['variant_uid'] = str(item.uid)
            
            
            if item.stock > 0:
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
                response_data['stock_class'] = "text-danger"
                
            # Thêm image url trả về cho API (nếu cần dùng AJAX sau này)
            response_data['image_url'] = item.image.url if item.image else ""
            response_data['success'] = True
            
        else:
            response_data['message'] = "Biến thể không tồn tại"
            
    except Exception as e:
        print(f"Error AJAX: {e}")
        response_data['message'] = "Lỗi hệ thống"

    return JsonResponse(response_data)


def submit_review(request, order_id, product_id):
    url = request.META.get('HTTP_REFERER')
    if not request.user.is_authenticated:
        return redirect('login')
    product = get_object_or_404(Product, uid=product_id)
    order = get_object_or_404(Order, order_number=order_id, user=request.user)
    try:
        existing_review = Review.objects.get(
            user__id=request.user.id,
            product=product,
            order=order 
        )
        if existing_review:
            form = None 
            messages.warning(request, 'Bạn đã đánh giá sản phẩm này trong đơn hàng này rồi!')
            return redirect(url) 

    except Review.DoesNotExist:
        form = ReviewForm(request.POST or None)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            data = Review()
            data.subject = form.cleaned_data['subject']
            data.rating = form.cleaned_data['rating']
            data.review = form.cleaned_data['review']
            data.ip = request.META.get('REMOTE_ADDR')
            
            data.product = product
            data.user_id = request.user.id
            data.order = order 
            
            data.save()
            messages.success(request, 'Cảm ơn bạn đã đánh giá!')
            return redirect('user_orders') 

    
    context = {
        'product': product,
        'order': order
    }
    return render(request, 'accounts/add_review.html', context)