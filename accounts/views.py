import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.forms import AddressForm
from orders.models import Order, OrderProduct
from products.models import Coupon, CouponUsage, Review, Variant
from .models import Address, Cart, CartItems, Profile
from .utils import calculate_cart_total


def _parse_optional_int(value):
    if value is None:
        return None
    val_str = str(value).strip()
    return int(val_str) if val_str.isdigit() else None


def register_page(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if confirm_password is not None and password != confirm_password:
            messages.error(request, 'Mật khẩu xác nhận không khớp!')
            return render(request, 'accounts/login_register.html')

        if User.objects.filter(username=email).exists():
            messages.error(request, 'Email này đã được sử dụng!')
            return render(request, 'accounts/login_register.html')

        try:
            user_obj = User.objects.create_user(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            user_obj.set_password(password)
            user_obj.save()

            profile, _ = Profile.objects.get_or_create(user=user_obj)
            profile.phone = phone
            profile.save()

            messages.success(request, 'Đăng ký thành công! Vui lòng đăng nhập.')
            return redirect('login')
        except Exception as exc:
            messages.error(request, f'Đã xảy ra lỗi: {exc}')
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
        messages.warning(request, 'Sai tài khoản hoặc mật khẩu!')

    return render(request, 'accounts/login_register.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'Bạn đã đăng xuất thành công.')
    return redirect('login')


@login_required(login_url='login')
def cart(request):
    # Khi người dùng chủ động vào xem giỏ hàng, xóa phiên mua ngay (nếu có)
    if 'direct_buy_item' in request.session or 'is_buy_now' in request.session:
        request.session.pop('direct_buy_item', None)
        request.session.pop('is_buy_now', None)
        request.session.modified = True

    try:
        cart_obj = Cart.get_or_create_active(request.user)
        context = calculate_cart_total(cart_obj, user=request.user)
        context['cart'] = cart_obj
        context['has_default_address'] = Address.objects.filter(
            user=request.user,
            is_default=True,
        ).exists()
    except Exception as exc:
        print(f"Cart View Error: {exc}")
        context = {'cart_items': [], 'subtotal': 0, 'total': 0, 'discount': 0}

    return render(request, 'accounts/cart.html', context)


@login_required(login_url='login')
@require_POST
def add_to_cart(request, uid):
    variant_uid = request.POST.get('variant') or request.GET.get('variant')
    raw_qty = request.POST.get('quantity') or request.GET.get('quantity', '1')
    try:
        quantity = int(raw_qty)
    except (TypeError, ValueError):
        messages.warning(request, "Số lượng không hợp lệ.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    if quantity < 1:
        messages.warning(request, "Số lượng phải lớn hơn hoặc bằng 1.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    if not variant_uid:
        messages.warning(request, "Vui lòng chọn màu sắc/kích thước")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    variant_obj = get_object_or_404(Variant, uid=variant_uid)
    if variant_obj.stock < 1 or quantity > variant_obj.stock:
        messages.warning(request, f"Chỉ còn {variant_obj.stock} sản phẩm trong kho.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    cart_obj = Cart.get_or_create_active(request.user)
    cart_item, created = CartItems.objects.get_or_create(
        cart=cart_obj,
        variant=variant_obj,
    )

    new_quantity = quantity if created else cart_item.quantity + quantity
    if new_quantity > variant_obj.stock:
        if created:
            cart_item.delete()
        messages.warning(request, f"Chỉ còn {variant_obj.stock} sản phẩm.")
        return redirect('cart')

    cart_item.quantity = new_quantity
    cart_item.save()
    messages.success(request, "Đã thêm vào giỏ hàng")
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
                    'message': f'Chỉ còn {cart_item.variant.stock} sản phẩm',
                }, status=400)

            cart_item.quantity = new_quantity
            cart_item.save()
            item_total_price = cart_item.get_product_price
        else:
            cart_item.delete()

        cart_details = calculate_cart_total(cart_item.cart, user=request.user)
        return JsonResponse({
            'status': 'Success',
            'item_total': item_total_price,
            'subtotal': cart_details['subtotal'],
            'discount': cart_details['discount'],
            'cart_total': cart_details['total'],
            'shipping_fee': cart_details['shipping_fee'],
        })
    except Exception as exc:
        return JsonResponse({'status': 'Error', 'message': str(exc)}, status=400)


@login_required(login_url='login')
def remove_item(request, cart_item_uid):
    try:
        CartItems.objects.filter(uid=cart_item_uid, cart__user=request.user).delete()
        messages.success(request, "Đã xóa sản phẩm")
    except Exception as exc:
        print(f"Remove item error: {exc}")
        messages.error(request, "Lỗi khi xóa sản phẩm")

    return redirect('cart')


@login_required(login_url='login')
def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code')
        try:
            coupon = Coupon.objects.get(coupon_code__iexact=code)
            cart_obj = Cart.get_or_create_active(request.user)

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

            for applied_c in cart_obj.coupons.all():
                if applied_c.coupon_type == coupon.coupon_type:
                    messages.error(
                        request,
                        f'Không thể áp dụng nhiều mã loại "{applied_c.get_coupon_type_display()}" cùng lúc.',
                    )
                    return redirect('cart')

            cart_obj.coupons.add(coupon)
            messages.success(request, f'Áp dụng mã {coupon.coupon_code} thành công!')
        except Coupon.DoesNotExist:
            messages.error(request, 'Mã giảm giá không tồn tại.')

    return redirect('cart')


@login_required(login_url='login')
def remove_coupon(request, coupon_id):
    try:
        cart_obj = Cart.objects.filter(user=request.user, is_paid=False).order_by('-created_at').first()
        if cart_obj:
            coupon = get_object_or_404(Coupon, id=coupon_id)
            cart_obj.coupons.remove(coupon)
            messages.success(request, f'Đã gỡ mã {coupon.coupon_code}.')
    except Exception:
        pass
    return redirect('cart')


@login_required(login_url='login')
def save_address(request):
    """Lưu địa chỉ giao hàng mới từ modal hoặc form."""
    if request.method == 'POST':
        full_name = (request.POST.get('full_name') or '').strip()
        phone = (request.POST.get('phone') or '').strip()
        city = (request.POST.get('city') or '').strip()
        district = (request.POST.get('district') or '').strip()
        ward = (request.POST.get('ward') or '').strip()
        address_line = (request.POST.get('address_line') or '').strip()
        parts = [part for part in (address_line, ward, district, city) if part]
        full_address_display = ", ".join(parts)

        is_default_bool = request.POST.get('is_default') == 'on'
        province_id = _parse_optional_int(request.POST.get('province_id'))
        district_id = _parse_optional_int(request.POST.get('district_id'))
        ward_code = (request.POST.get('ward_code') or '').strip() or None

        if is_default_bool:
            Address.objects.filter(user=request.user).update(is_default=False)

        Address.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            city=city,
            address_line=full_address_display,
            is_default=is_default_bool,
            province_id=province_id,
            district_id=district_id,
            ward_code=ward_code,
        )

        messages.success(request, "Đã thêm địa chỉ mới.")
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
    """Trang thêm địa chỉ riêng biệt."""
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Đã thêm địa chỉ mới.")
            return redirect('address_list')
    else:
        form = AddressForm()
    return render(request, 'accounts/address_edit.html', {'form': form, 'title': 'Thêm địa chỉ mới'})


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
    return render(request, 'accounts/address_edit.html', {'form': form, 'title': 'Cập nhật địa chỉ'})


@login_required(login_url='login')
@require_POST
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
def user_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'accounts/orders.html', {'orders': orders})


@login_required(login_url='login')
def order_detail(request, order_number):
    try:
        order = Order.objects.get(order_number=order_number, user=request.user)
        order_items = OrderProduct.objects.filter(order=order)
        reviewed_products = set(
            Review.objects.filter(
                user=request.user,
                order=order,
            ).values_list('product__uid', flat=True)
        )
        for item in order_items:
            item.has_reviewed = bool(item.product and item.product.uid in reviewed_products)
        return render(
            request,
            'accounts/order_detail.html',
            {'order': order, 'order_items': order_items},
        )
    except Order.DoesNotExist:
        return redirect('user_orders')


@login_required(login_url='login')
def user_dashboard(request):
    user = request.user
    orders = Order.objects.filter(user=user).order_by('-created_at')
    total_orders = orders.count()
    pending_count = orders.filter(status='Pending').count()
    completed_count = orders.filter(status__in=['shipped', 'paid', 'completed']).count()
    recent_orders = orders[:5]
    default_address = Address.objects.filter(user=user, is_default=True).first()

    context = {
        'total_orders': total_orders,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'recent_orders': recent_orders,
        'default_address': default_address,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required(login_url='login')
def update_avatar(request):
    if request.method == 'POST':
        profile, _ = Profile.objects.get_or_create(user=request.user)
        image = request.FILES.get('profile_image')
        if image:
            profile.profile_image = image
            profile.save()
            messages.success(request, "Cập nhật avatar thành công.")
    return redirect(request.META.get('HTTP_REFERER') or 'user_profile')


@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Mật khẩu của bạn đã được thay đổi thành công!')
            return redirect('user_profile')
        messages.error(request, 'Vui lòng kiểm tra lại thông tin bên dưới.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})
