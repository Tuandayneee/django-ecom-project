from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.db.models import Prefetch
import json

# Import Models
from accounts.forms import AddressForm
from ecom.settings import DEFAULT_SHIPPING_FEE
from products.models import Product, Variant, Coupon, ProductImage,CouponUsage
from .models import Address, Cart, CartItems, Profile

# --- HELPER FUNCTION: LOGIC TÍNH TOÁN GIỎ HÀNG (DRY) ---
def _get_cart_details(cart_obj):
    cart_items = CartItems.objects.filter(cart=cart_obj).select_related(
        'variant__product', 'variant__size', 'variant__color'
    ).prefetch_related(
        'variant__product__product_images'
    ).order_by('created_at')

    subtotal = cart_obj.get_cart_total()
    
    # 1. Khởi tạo tổng giảm giá bằng 0 (để cộng dồn chuẩn xác)
    total_discount = 0 
    
    valid_coupons = [] 
    applied_coupons = cart_obj.coupons.all()
    
    for coupon in applied_coupons:
        if not coupon.is_valid():
            cart_obj.coupons.remove(coupon)
            continue
        if subtotal < coupon.minimum_amount:
            continue

        discount_amount = 0
        if coupon.coupon_type == 'percent':
            discount_amount = (subtotal * coupon.discount_price) / 100
            
        elif coupon.coupon_type == 'amount':
            discount_amount = coupon.discount_price
            
        elif coupon.coupon_type == 'shipping':
            # Nếu freeship, giảm đúng bằng phí ship mặc định
            discount_amount = settings.DEFAULT_SHIPPING_FEE 

        # 2. CỘNG DỒN (Chỉ dùng +=, không dùng =)
        total_discount += discount_amount
        valid_coupons.append(coupon)

    # 3. Validation cuối cùng: Không cho giảm giá vượt quá (Tiền hàng + Ship)
    shipping_fee = settings.DEFAULT_SHIPPING_FEE
    cart_total_with_ship = subtotal + shipping_fee
    
    if total_discount > cart_total_with_ship:
         total_discount = cart_total_with_ship
         
    # Công thức: Tổng = Tiền hàng + Ship - Tổng giảm giá
    total = cart_total_with_ship - total_discount

    return {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_fee': shipping_fee,
        'discount': int(total_discount),
        'total': int(total),
        'applied_coupons': valid_coupons
    }

def register_page(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email') 
        password = request.POST.get('password')
        
        if User.objects.filter(username=email).exists():
            messages.error(request, 'Email này đã được sử dụng!')
            return render(request, 'accounts/register.html', {'first_name': first_name, 'last_name': last_name, 'email': email})

        try:
            user_obj = User.objects.create_user(username=email, email=email, first_name=first_name, last_name=last_name)
            user_obj.set_password(password)
            user_obj.save()
            messages.success(request, 'Đăng ký thành công! Vui lòng kiểm tra email để xác thực tài khoản.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Đã xảy ra lỗi: {e}')
            return render(request, 'accounts/register.html', {'first_name': first_name, 'last_name': last_name, 'email': email})

    return render(request, 'accounts/register.html')

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
            try:
                if not user_obj.profile.is_email_verified:
                    messages.warning(request, 'Tài khoản của bạn chưa được xác thực email.')
                    return HttpResponseRedirect(request.path_info)
            except Profile.DoesNotExist:
                messages.error(request, 'Tài khoản bị lỗi, không tìm thấy Profile.')
                return HttpResponseRedirect(request.path_info)
            
            login(request, user_obj)
            if next_url:
                return redirect(next_url)
            
            
            return redirect('home')
        else:
            messages.warning(request, 'Sai tài khoản hoặc mật khẩu!')
            return HttpResponseRedirect(request.path_info)
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'Bạn đã đăng xuất thành công.')
    return redirect('login')

# --- CART & ORDER VIEWS ---

@login_required(login_url='login')
def cart(request):
    try:
        cart_obj, _ = Cart.objects.get_or_create(user=request.user, is_paid=False)
        context = _get_cart_details(cart_obj)
        context['cart'] = cart_obj
    except Exception as e:
        print(f"Cart View Error: {e}")
        context = {'cart_items': [], 'subtotal': 0, 'total': 0, 'discount': 0}

    return render(request, 'accounts/cart.html', context)


@login_required(login_url='login') # <--- Mấu chốt là dòng này
def add_to_cart(request, uid):
    variant_uid = request.GET.get('variant')
    
    # Logic lấy số lượng
    try:
        quantity = int(request.GET.get('quantity', 1))
    except ValueError:
        quantity = 1

    if not variant_uid:
        messages.warning(request, "Vui lòng chọn màu sắc/kích thước")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    try:
        variant_obj = get_object_or_404(Variant, uid=variant_uid)
        
        # --- CHỈ CẦN LOGIC NÀY (Vì chắc chắn đã login mới vào được đây) ---
        cart_obj, _ = Cart.objects.get_or_create(user=request.user, is_paid=False)
        
        cart_item, created = CartItems.objects.get_or_create(
            cart=cart_obj,
            variant=variant_obj
        )

        if created:
            cart_item.quantity = quantity
        else:
            cart_item.quantity += quantity

        # Check tồn kho
        if cart_item.quantity > variant_obj.stock:
            cart_item.quantity = variant_obj.stock
            messages.warning(request, f"Chỉ còn {variant_obj.stock} sản phẩm.")

        cart_item.save()
        messages.success(request, "Đã thêm vào giỏ hàng")
        
    except Exception as e:
        print(e)
        messages.error(request, "Lỗi hệ thống")

    # Thêm xong thì quay lại trang trước đó hoặc trang giỏ hàng
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
        
        if new_quantity > 0:
            if new_quantity > cart_item.variant.stock:
                return JsonResponse({
                    'status': 'Stock limit', 
                    'message': f'Chỉ còn {cart_item.variant.stock} sản phẩm'
                }, status=400)
            
            cart_item.quantity = new_quantity
            cart_item.save()
        else:
            cart_item.delete()

        cart_details = _get_cart_details(cart_item.cart)

        return JsonResponse({
            'status': 'Success',
            'item_total': cart_item.get_product_price,
            'subtotal': cart_details['subtotal'],
            'discount': cart_details['discount'],
            'cart_total': cart_details['total']
        })

    except Exception as e:
        return JsonResponse({'status': 'Error', 'message': str(e)}, status=400)

@login_required(login_url='login')
def remove_item(request, cart_item_uid):
    try:
        CartItems.objects.filter(uid=cart_item_uid, cart__user=request.user).delete()
        messages.success(request, "Đã xóa sản phẩm khỏi giỏ hàng")
    except Exception as e:
        print(f"Remove item error: {e}")
        messages.error(request, "Lỗi khi xóa sản phẩm")
    
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', 'cart'))

@login_required(login_url='login')
def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code')
        
        # Yêu cầu login để check usage limit
        if not request.user.is_authenticated:
            messages.error(request, 'Bạn cần đăng nhập để sử dụng mã giảm giá.')
            return redirect('login')

        try:
            coupon = Coupon.objects.get(coupon_code__iexact=code)
            
            # Lấy/Tạo giỏ hàng tạm để tính subtotal
            cart_obj, _ = Cart.objects.get_or_create(user=request.user, is_paid=False)
            subtotal = cart_obj.get_cart_total()
            
            if not coupon.is_valid():
                messages.error(request, 'Mã giảm giá đã hết hạn hoặc không kích hoạt.')
                return redirect('cart')
            
            current_coupons = cart_obj.coupons.all()
            for applied_c in current_coupons:
                if applied_c.coupon_type == coupon.coupon_type:
                    messages.error(request, f'Không thể dùng 2 mã loại {coupon.coupon_type}')
                    return redirect('cart')

            cart_obj.coupons.add(coupon)
            messages.success(request, f'Đã áp dụng mã {coupon.coupon_code}!')
            

        except Coupon.DoesNotExist:
            messages.error(request, 'Mã giảm giá không tồn tại.')
       
            
    return redirect('cart')

def remove_coupon(request, coupon_id):
    
    try:
        cart_obj = Cart.objects.get(user=request.user, is_paid=False)
        coupon = get_object_or_404(Coupon, id=coupon_id)
        cart_obj.coupons.remove(coupon)
        messages.success(request, f'Đã gỡ mã {coupon.coupon_code} khỏi giỏ hàng.')
    except Exception as e:
        print(f"Remove coupon error: {e}")
        pass
    
    
    return redirect('cart')

def save_address(request):
    if request.method == 'POST':
        # Lấy dữ liệu từ form HTML
        recipient_name = request.POST.get('recipient_name')
        phone = request.POST.get('phone')
        city = request.POST.get('city')
        address_line = request.POST.get('address_line')
        is_default = request.POST.get('is_default') == 'on' # Checkbox trả về 'on' nếu được chọn

        # Tạo địa chỉ mới
        Address.objects.create(
            user=request.user,
            recipient_name=recipient_name,
            phone=phone,
            city=city,
            address_line=address_line,
            is_default=is_default
        )
        
        messages.success(request, "Đã thêm địa chỉ mới thành công.")
        
        # Redirect về trang trước đó (thường là checkout)
        return redirect(request.POST.get('next', 'home'))
    
    return redirect('home')


@login_required(login_url='login')
def address_list(request):
    """ Hiển thị danh sách địa chỉ """
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    return render(request, 'accounts/address_list.html', {'addresses': addresses})

@login_required(login_url='login')
def add_address(request):
    """ Thêm địa chỉ mới """
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Thêm địa chỉ mới thành công.")
            
            next_url = request.POST.get('next')
            if next_url == 'checkout':
                return redirect('orders:checkout')

            return redirect('address_list')
    else:
        form = AddressForm()
    
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Thêm địa chỉ mới'})

@login_required(login_url='login')
def edit_address(request, uid):
    """ Sửa địa chỉ """
    # get_object_or_404 kèm user=request.user để đảm bảo không sửa nhầm của người khác
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
    """ Xóa địa chỉ """
    address = get_object_or_404(Address, uid=uid, user=request.user)
    address.delete()
    messages.success(request, "Đã xóa địa chỉ.")
    return redirect('address_list')

@login_required(login_url='login')
def set_default_address(request, uid):
    """ Đặt làm mặc định nhanh """
    address = get_object_or_404(Address, uid=uid, user=request.user)
    address.is_default = True
    address.save() # Logic trong model sẽ tự động bỏ default các cái khác
    return redirect('address_list')