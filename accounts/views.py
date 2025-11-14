from .models import Cart, Profile
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect,HttpResponse
from django.contrib.auth import authenticate, login, logout
from products.models import *
from accounts.models import Cart,CartItems
from django.http import HttpResponseRedirect
from django.http import JsonResponse
import json 
def login_page(request):

    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_obj = authenticate(request, username=email, password=password)
        
        if user_obj is not None:
            try:
                if not user_obj.profile.is_email_verified:
                    messages.warning(request, 'Tài khoản của bạn chưa được xác thực email.')
                    return HttpResponseRedirect(request.path_info)
            # Chú ý: Bắt ngoại lệ đúng
            except Profile.DoesNotExist: 
                messages.error(request, 'Tài khoản bị lỗi, không tìm thấy Profile.')
                return HttpResponseRedirect(request.path_info)
            
            # Đăng nhập
            login(request, user_obj)
            
            user_cart, created = Cart.objects.get_or_create(user=request.user, is_paid=False)
            try:
               
               # --- Merge session coupons into user cart (if any) ---
                session_coupon_ids = request.session.get('coupon_ids', [])
                if session_coupon_ids and user_cart:
                    try:
                        coupons_to_add = Coupon.objects.filter(id__in=session_coupon_ids)
                        for c in coupons_to_add:
                            user_cart.coupons.add(c)
                        # persist and clear session coupons
                        user_cart.save()
                        try:
                            del request.session['coupon_ids']
                        except KeyError:
                            pass
                    except Exception as e:
                        print(f"Lỗi khi merge coupon vào user cart: {e}")

                # --- Merge session coupons into user cart (if any) ---
                session_coupon_ids = request.session.get('coupon_ids', [])
                if session_coupon_ids and user_cart:
                    try:
                        coupons_to_add = Coupon.objects.filter(id__in=session_coupon_ids)
                        for c in coupons_to_add:
                            user_cart.coupons.add(c)
                        # persist and clear session coupons
                        user_cart.save()
                        try:
                            del request.session['coupon_ids']
                        except KeyError:
                            pass
                    except Exception as e:
                        print(f"Lỗi khi merge coupon vào user cart: {e}")

            except Cart.DoesNotExist:
                # Bỏ qua nếu không tìm thấy giỏ hàng trong session
                if 'cart_id' in request.session:
                    del request.session['cart_id']
            except Exception as e:
                print(f"Lỗi khi gộp giỏ hàng: {e}")
                pass
            # --- KẾT THÚC LOGIC GỘP GIỎ HÀNG ---

            return redirect('/')
        
        else:
            messages.warning(request, 'Sai tài khoản hoặc mật khẩu!')
            return HttpResponseRedirect(request.path_info)

    
    return render(request, 'accounts/login.html')


def logout_view(request):
    print("LOGOUT: before auth?", request.user.is_authenticated, "session_key:", request.session.session_key)
    print("SESSION BEFORE:", dict(request.session.items()))
    logout(request)
    print("AFTER logout; session_key:", request.session.session_key, "session items:", dict(request.session.items()))
    messages.info(request, 'Bạn đã đăng xuất thành công.')
    return redirect('home')

def register_page(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email') 
        password = request.POST.get('password')
        
        # Kiểm tra username (email) tồn tại
        if User.objects.filter(username=email).exists(): # [cite: 110]
            messages.error(request, 'Email này đã được sử dụng!')
            # Giữ lại giá trị form cũ để người dùng không phải nhập lại
            context = {'first_name': first_name, 'last_name': last_name, 'email': email}
            return render(request, 'accounts/register.html', context) 

        # Tạo User (Signal sẽ tự động kích hoạt để tạo Profile và gửi mail)
        try:
            user_obj = User.objects.create_user(
                username=email, 
                email=email,
                first_name=first_name,
                last_name=last_name
            ) 
            user_obj.set_password(password) # [cite: 110]
            user_obj.save() 
            
            # Thông báo thành công và chuyển hướng đến trang đăng nhập
            messages.success(request, 'Đăng ký thành công! Vui lòng kiểm tra email để xác thực tài khoản.')
            return redirect('login') # Thay 'login' bằng name URL đăng nhập của bạn
            
        except Exception as e:
            messages.error(request, f'Đã xảy ra lỗi trong quá trình đăng ký: {e}')
            context = {'first_name': first_name, 'last_name': last_name, 'email': email}
            return render(request, 'accounts/register.html', context) 

    return render(request, 'accounts/register.html')
    


def activate_email(request, email_token):
    try:
        user = Profile.objects.get(email_token=email_token)
        user.is_email_verified = True
        user.save()
        return redirect('/')
    except Exception as e:
       
        return HttpResponse("Link xac thuc khong hop le")

@login_required(login_url='login')
def add_to_cart(request, uid):
    try:
        product = Product.objects.get(uid=uid)
        user = request.user 
        cart, _ = Cart.objects.get_or_create(user=user, is_paid=False)
        
        size = None
        variant = request.GET.get('variant')
        if variant:
            size = SizeVariant.objects.get(size_name=variant)

       
        cart_item, created = CartItems.objects.get_or_create(
            cart=cart,
            product=product,
            size_variant=size
        )
        
        if created:
            cart_item.quantity = 1
        else:
            
            cart_item.quantity += 1
            
        cart_item.save()
        

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    except Exception as e:
        print(e)
        
        return redirect('/')





# accounts/views.py

@login_required(login_url='login')
def cart(request):
    cart_items = None
    cart_obj = None
    subtotal = 0
    total_discount = 0
    total = 0
    applied_coupons = []

    try:
        # nếu user authenticated thì lấy cart của họ, còn không thì bỏ qua (hoặc fallback session cart)
        if request.user.is_authenticated:
            cart_obj = Cart.objects.get(user=request.user, is_paid=False)
        else:
            session_cart_id = request.session.get('cart_id')
            if session_cart_id:
                cart_obj = Cart.objects.get(id=session_cart_id, is_paid=False)

        if cart_obj:
            cart_items = cart_obj.cart_items.all()
            subtotal = cart_obj.get_cart_total()

            # 1) Lấy coupon từ DB (Cart.coupons) - source of truth
            persisted_coupons = list(cart_obj.coupons.all())

            # 2) Fallback / augmentation: nếu session vẫn có coupon ids (chưa được persist), thêm chúng
            session_ids = request.session.get('coupon_ids', [])
            if session_ids:
                session_coupons = Coupon.objects.filter(id__in=session_ids)
            else:
                session_coupons = []

            # Combine - keep unique ids (DB + session)
            seen = set()
            all_coupons = []
            for c in persisted_coupons + list(session_coupons):
                if c.id not in seen:
                    seen.add(c.id)
                    all_coupons.append(c)

            # Validate each coupon and build applied list + discount
            valid_ids_to_keep = []
            for coupon in all_coupons:
                if coupon.is_valid() and subtotal >= coupon.minimum_amount:
                    total_discount += coupon.discount_price
                    applied_coupons.append(coupon)
                    valid_ids_to_keep.append(coupon.id)

            # Update session so invalid/expired are removed
            request.session['coupon_ids'] = valid_ids_to_keep

            total = subtotal - total_discount
            if total < 0:
                total = 0

    except Cart.DoesNotExist:
        # no cart - keep zeros
        pass
    except Exception as e:
        print(f"Error loading cart: {e}")

    context = {
        'cart': cart_obj,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'discount': total_discount,
        'total': total,
        'applied_coupons': applied_coupons,
    }
    return render(request, 'accounts/cart.html', context)

def update_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_uid = data.get('item_uid')
            new_quantity = int(data.get('new_quantity'))

            cart_item = CartItems.objects.get(uid=item_uid, cart__user=request.user)
            
            if new_quantity > 0:
                cart_item.quantity = new_quantity
                cart_item.save()
            else:
                cart_item.delete()

            cart = cart_item.cart
            subtotal = cart.get_cart_total() # Lấy tổng tiền mới
            
            # --- CẬP NHẬT LOGIC TÍNH TOÁN (Giống hệt hàm cart) ---
            coupon_ids = request.session.get('coupon_ids', [])
            total_discount = 0
            valid_coupons_ids_to_keep = []

            if coupon_ids:
                valid_coupons = Coupon.objects.filter(id__in=coupon_ids)
                for coupon in valid_coupons:
                    if coupon.is_valid() and subtotal >= coupon.minimum_amount:
                        total_discount += coupon.discount_price
                        valid_coupons_ids_to_keep.append(coupon.id)
            
            request.session['coupon_ids'] = valid_coupons_ids_to_keep
            total = subtotal - total_discount
            if total < 0:
                total = 0
            # --- KẾT THÚC CẬP NHẬT ---
            
            if new_quantity <= 0:
                   return JsonResponse({ 
                       'status': 'Item removed', 
                       'subtotal': subtotal, 
                       'discount': total_discount, # Gửi TỔNG
                       'cart_total': total 
                   })

            return JsonResponse({ 
                'status': 'Success', 
                'item_subtotal': cart_item.get_total(), 
                'subtotal': subtotal, 
                'discount': total_discount, # Gửi TỔNG
                'cart_total': total 
            })
            
        except Exception as e:
            return JsonResponse({'status': 'Error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'Invalid request'}, status=400)
def remove_item(request, cart_item_uid):
    try:
        cart_item = CartItems.objects.get(uid=cart_item_uid, cart__user=request.user)
        cart_item.delete()
       
    except Exception as e:
        print(e)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code')
        
        try:
            # Try to find a Cart for the authenticated user first
            cart_obj = None
            if request.user.is_authenticated:
                try:
                    cart_obj = Cart.objects.get(user=request.user, is_paid=False)
                except Cart.DoesNotExist:
                    cart_obj = None

            # Fallback: try session cart (anonymous flow)
            if cart_obj is None:
                session_cart_id = request.session.get('cart_id')
                if session_cart_id:
                    try:
                        cart_obj = Cart.objects.get(id=session_cart_id, is_paid=False)
                    except Cart.DoesNotExist:
                        cart_obj = None

            if cart_obj is None:
                messages.error(request, 'Bạn không có giỏ hàng để áp dụng mã.')
                return redirect('cart')

            subtotal = cart_obj.get_cart_total()
            coupon = Coupon.objects.get(coupon_code__iexact=code)
            
            # --- ĐÂY LÀ PHẦN SỬA LỖI ---
            
            # 1. LẤY DANH SÁCH ID HIỆN CÓ (hoặc tạo list rỗng)
            #    Đây là bước quan trọng nhất mà code cũ của bạn đã thiếu.
            current_coupon_ids = request.session.get('coupon_ids', [])
            
            # 2. Kiểm tra điều kiện
            if not coupon.is_valid():
                messages.error(request, 'Mã giảm giá đã hết hạn hoặc bị vô hiệu hóa.')
            elif subtotal < coupon.minimum_amount:
                messages.error(request, f'Đơn hàng phải đạt tối thiểu {coupon.minimum_amount}đ để áp dụng mã này.')
            
            # 3. Kiểm tra xem mã ĐÃ CÓ trong danh sách chưa
            elif coupon.id in current_coupon_ids:
                messages.warning(request, 'Bạn đã áp dụng mã này rồi.')
            
            else:
                # 4. THÊM mã mới vào danh sách (append)
                current_coupon_ids.append(coupon.id)
                
                # 5. LƯU LẠI danh sách ĐÃ CẬP NHẬT vào session
                request.session['coupon_ids'] = current_coupon_ids
                # Also persist coupon into the Cart object's M2M for durability
                try:
                    
                    if not cart_obj.coupons.filter(id=coupon.id).exists():
                        cart_obj.coupons.add(coupon)
                        cart_obj.save()
                except Exception as e:
                    print(f"Không thể lưu coupon vào Cart.coupons: {e}")

                messages.success(request, f'Đã áp dụng mã {coupon.coupon_code}!')
            # --- KẾT THÚC SỬA LỖI ---

        except Coupon.DoesNotExist:
            messages.error(request, 'Mã giảm giá không tồn tại.')
        except Cart.DoesNotExist:
            messages.error(request, 'Bạn không có giỏ hàng để áp dụng mã.')
        except Exception as e:
            messages.error(request, f'Đã xảy ra lỗi: {e}')
            
    return redirect('cart')



def remove_coupon(request, coupon_id):
    current_coupon_ids = request.session.get('coupon_ids', [])
    try:
        current_coupon_ids.remove(int(coupon_id))
    except ValueError:
        pass
    request.session['coupon_ids'] = current_coupon_ids

    
    try:
        if request.user.is_authenticated:
            cart_obj = Cart.objects.get(user=request.user, is_paid=False)
        else:
            session_cart_id = request.session.get('cart_id')
            cart_obj = Cart.objects.get(id=session_cart_id, is_paid=False) if session_cart_id else None

        if cart_obj:
            cart_obj.coupons.remove(coupon_id)
            cart_obj.save()
    except Exception:
        # ignore missing cart / coupon
        pass

    return redirect('cart')