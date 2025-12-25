from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
import json
from django.db.models import Count
from django.contrib.auth import update_session_auth_hash
# --- IMPORT UTILS (LOGIC TÍNH TOÁN CHUẨN) ---
from .utils import calculate_cart_total 

# Import Models & Forms
from accounts.forms import AddressForm
from orders.models import Order, OrderProduct
from products.models import CouponUsage, Variant, Coupon
from .models import Address, Cart, CartItems, Profile

from django.contrib.auth.forms import PasswordChangeForm


def register_page(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email') 
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        
        if User.objects.filter(username=email).exists():
            messages.error(request, 'Email này đã được sử dụng!')
            return render(request, 'accounts/login_register.html')

        try:
            user_obj = User.objects.create_user(username=email, email=email, first_name=first_name, last_name=last_name)
            user_obj.set_password(password)
            user_obj.save()
            
            # Lưu phone vào Profile
            profile = user_obj.profile
            profile.phone = phone
            profile.save()
            
            messages.success(request, 'Đăng ký thành công! Vui lòng đăng nhập.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Đã xảy ra lỗi: {e}')
            return render(request, 'accounts/login_register.html')

    return render(request, 'accounts/login_register.html')

def activate_email(request, email_token):
    try:
        user_profile = Profile.objects.get(email_token=email_token)
        user_profile.is_email_verified = True
        user_profile.save()
        messages.success(request, 'Tài khoản đã được kích hoạt thành công!')
        return redirect('login')
    except Exception:
        return HttpResponse("Link xác thực không hợp lệ")

def login_page(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        next_url = request.POST.get('next')
        user_obj = authenticate(request, username=email, password=password)
        
        if user_obj is not None:
           
            login(request, user_obj)
            if next_url:
                return redirect(next_url)
            return redirect('home')
        else:
            messages.warning(request, 'Sai tài khoản hoặc mật khẩu!')
    
    return render(request, 'accounts/login_register.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'Bạn đã đăng xuất thành công.')
    return redirect('login')




@login_required(login_url='login')
def cart(request):
    try:
        cart_obj, _ = Cart.objects.get_or_create(user=request.user, is_paid=False)
        
        
        context = calculate_cart_total(cart_obj, user=request.user)
        
        context['cart'] = cart_obj
        context['has_default_address'] = Address.objects.filter(user=request.user, is_default=True).exists()
    except Exception as e:
        print(f"Cart View Error: {e}")
        context = {'cart_items': [], 'subtotal': 0, 'total': 0, 'discount': 0}

    return render(request, 'accounts/cart.html', context)

@login_required(login_url='login')
def add_to_cart(request, uid):
    variant_uid = request.GET.get('variant')
    try:
        quantity = int(request.GET.get('quantity', 1))
    except ValueError:
        quantity = 1

    if not variant_uid:
        messages.warning(request, "Vui lòng chọn màu sắc/kích thước")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    try:
        variant_obj = get_object_or_404(Variant, uid=variant_uid)
        cart_obj, _ = Cart.objects.get_or_create(user=request.user, is_paid=False)
        
        cart_item, created = CartItems.objects.get_or_create(
            cart=cart_obj,
            variant=variant_obj
        )

        if created:
            cart_item.quantity = quantity
        else:
            cart_item.quantity += quantity

        if cart_item.quantity > variant_obj.stock:
            cart_item.quantity = variant_obj.stock
            messages.warning(request, f"Chỉ còn {variant_obj.stock} sản phẩm.")

        cart_item.save()
        messages.success(request, "Đã thêm vào giỏ hàng")
        
    except Exception as e:
        print(e)
        messages.error(request, "Lỗi hệ thống")

    return redirect('cart')

@login_required(login_url='login')
def update_cart(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'Invalid method'}, status=405)

    try:
        data = json.loads(request.body)
        item_uid = data.get('item_uid')
        new_quantity = int(data.get('new_quantity'))

        cart_item = get_object_or_404(CartItems, uid=item_uid, cart__user=request.user)
        item_total_price = 0
        if new_quantity > 0:
            if new_quantity > cart_item.variant.stock:
                return JsonResponse({
                    'status': 'Stock limit', 
                    'message': f'Chỉ còn {cart_item.variant.stock} sản phẩm'
                }, status=400)
            
            cart_item.quantity = new_quantity
            cart_item.save()
            item_total_price = cart_item.get_product_price
        else:
            cart_item.delete()
            item_total_price = 0

        # TÍNH LẠI GIỎ HÀNG BẰNG HÀM CHUẨN
        cart_details = calculate_cart_total(cart_item.cart, user=request.user)

        return JsonResponse({
            'status': 'Success',
            'item_total': item_total_price,
            'subtotal': cart_details['subtotal'],
            'discount': cart_details['discount'],
            'cart_total': cart_details['total'],
            'shipping_fee': cart_details['shipping_fee']
        })

    except Exception as e:
        return JsonResponse({'status': 'Error', 'message': str(e)}, status=400)

@login_required(login_url='login')
def remove_item(request, cart_item_uid):
    try:
        CartItems.objects.filter(uid=cart_item_uid, cart__user=request.user).delete()
        messages.success(request, "Đã xóa sản phẩm")
    except Exception as e:
        print(f"Remove item error: {e}")
        messages.error(request, "Lỗi khi xóa sản phẩm")
    
    return redirect('cart')

@login_required(login_url='login')
def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code')
        
        
        if not request.user.is_authenticated:
            messages.warning(request, 'Vui lòng đăng nhập để sử dụng mã giảm giá.')
            return redirect('login')

        try:
            
            coupon = Coupon.objects.get(coupon_code__iexact=code)
            cart_obj, _ = Cart.objects.get_or_create(user=request.user, is_paid=False)
            
            if not coupon.is_valid():
                messages.error(request, 'Mã giảm giá đã hết hạn hoặc ngưng hoạt động!')
                return redirect('cart')

            
            if coupon in cart_obj.coupons.all():
                messages.warning(request, 'Bạn đang sử dụng mã này rồi!')
                return redirect('cart')

            
            current_total = cart_obj.get_cart_total()
            if current_total < coupon.minimum_amount:
                
                min_str = "{:,.0f}".format(coupon.minimum_amount).replace(",", ".")
                messages.error(request, f'Đơn hàng cần tối thiểu {min_str} đ để dùng mã này!')
                return redirect('cart')

            
            try:
                usage = CouponUsage.objects.get(user=request.user, coupon=coupon)
                if usage.used_count >= coupon.usage_limit_per_user:
                    messages.error(request, 'Bạn đã hết lượt sử dụng mã giảm giá này!')
                    return redirect('cart')
            except CouponUsage.DoesNotExist:
                
                pass

            current_coupons = cart_obj.coupons.all()
            for applied_c in current_coupons:
                if applied_c.coupon_type == coupon.coupon_type:
                    messages.error(request, f'Không thể áp dụng nhiều mã loại "{applied_c.get_coupon_type_display()}" cùng lúc.')
                    return redirect('cart')

           
            cart_obj.coupons.add(coupon)
            messages.success(request, f'Áp dụng mã {coupon.coupon_code} thành công!')

        except Coupon.DoesNotExist:
            messages.error(request, 'Mã giảm giá không tồn tại.')
            
    return redirect('cart')

@login_required(login_url='login')
def remove_coupon(request, coupon_id):
    try:
        cart_obj = Cart.objects.get(user=request.user, is_paid=False)
        coupon = get_object_or_404(Coupon, id=coupon_id)
        cart_obj.coupons.remove(coupon)
        messages.success(request, f'Đã gỡ mã {coupon.coupon_code}.')
    except Exception:
        pass
    return redirect('cart')


# =========================================
# ADDRESS & PROFILE (Địa chỉ & Hồ sơ)
# =========================================

@login_required(login_url='login')
def save_address(request):
    """ Hàm xử lý lưu địa chỉ từ Modal hoặc Form """
    if request.method == 'POST':
        
        full_name = request.POST.get('full_name') 
        phone = request.POST.get('phone')
        city = request.POST.get('city')
        address_line = request.POST.get('address_line')
        
        
        is_default_bool = request.POST.get('is_default') == 'on'
        
        province_id = request.POST.get('province_id')
        district_id = request.POST.get('district_id')
        ward_code = request.POST.get('ward_code')
        
        if is_default_bool:
            Address.objects.filter(user=request.user).update(is_default=False)
            
        Address.objects.create(
            user=request.user,
            full_name=full_name, 
            phone=phone,
            city=city,
            address_line=address_line,
            is_default=is_default_bool,
            province_id=province_id,
            district_id=district_id,
            ward_code=ward_code
        )
        
        messages.success(request, "Đã thêm địa chỉ mới.")
        
        # Redirect thông minh
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
            
    return redirect('address_list')

@login_required(login_url='login')
def address_list(request):
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    return render(request, 'accounts/address_list.html', {'addresses': addresses})

@login_required(login_url='login')
def add_address(request):
    """ View cho trang thêm địa chỉ riêng biệt (nếu không dùng Modal) """
    form = AddressForm()
    
    context = {
        'form': form,
        'title': 'Thêm địa chỉ mới'
    }
    
    return render(request, 'accounts/address_form.html', context)

@login_required(login_url='login')
def edit_address(request, uid):
    address = get_object_or_404(Address, uid=uid, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Cập nhật địa chỉ thành công.")
            return redirect('address_list')
    else:
        form = AddressForm(instance=address)
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Cập nhật địa chỉ'})

@login_required(login_url='login')
def delete_address(request, uid):
    address = get_object_or_404(Address, uid=uid, user=request.user)
    address.delete()
    messages.success(request, "Đã xóa địa chỉ.")
    return redirect('address_list')

@login_required(login_url='login')
def set_default_address(request, uid):
    address = get_object_or_404(Address, uid=uid, user=request.user)
    address.is_default = True
    address.save() 
    return redirect('address_list')

@login_required(login_url='login')
def user_profile(request):
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'accounts/dashboard.html', {'recent_orders': recent_orders})

@login_required(login_url='login')
def user_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'accounts/orders.html', {'orders': orders})

@login_required(login_url='login')
def order_detail(request, order_number):
    try:
        order = Order.objects.get(order_number=order_number, user=request.user)
        order_items = OrderProduct.objects.filter(order=order)

        context = {
            'order': order,
            'order_items': order_items,
        }
        return render(request, 'accounts/order_detail.html', context)
    except Order.DoesNotExist:
        
        return redirect('user_orders')


@login_required(login_url='login')
def user_dashboard(request):
    
    user = request.user
    orders = Order.objects.filter(user=user).order_by('-created_at')
    total_orders = orders.count()
    
   
    pending_count = orders.filter(status='Pending').count()
    
    
    completed_count = orders.filter(status__in=['shipped', 'paid']).count() 
    recent_orders = orders[:5]

    context = { 
        'total_orders': total_orders,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'recent_orders': recent_orders,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required(login_url='login')
def update_avatar(request):
    if request.method == 'POST':
        profile = Profile.objects.get(user=request.user)
        image = request.FILES.get('profile_image')
        if image:
            profile.profile_image = image
            profile.save()
            messages.success(request, "Cập nhật avatar thành cong.")
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

@login_required(login_url='login')
def change_password(request):
    
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        
        if form.is_valid():
            user = form.save()
            
            
            update_session_auth_hash(request, user)  
            
            messages.success(request, 'Mật khẩu của bạn đã được thay đổi thành công!')
            return redirect('user_profile') 
        else:
            
            messages.error(request, 'Vui lòng kiểm tra lại thông tin bên dưới.')
    else:
        
        form = PasswordChangeForm(request.user)
        
    context = {
        'form': form,
        
    }
    return render(request, 'accounts/change_password.html', context)