from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import Cart, CartItems
from .models import Order, OrderItem


@login_required(login_url='login')
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user, is_paid=False)
    except Cart.DoesNotExist:
        messages.error(request, 'Bạn không có giỏ hàng để thanh toán.')
        return redirect('cart')

    if request.method == 'POST':
        full_name = request.POST.get('full_name') or request.user.get_full_name() or request.user.username
        email = request.POST.get('email') or request.user.email
        phone = request.POST.get('phone', '')
        address = request.POST.get('address', '')
        city = request.POST.get('city', '')
        postal_code = request.POST.get('postal_code', '')

        # create order
        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            postal_code=postal_code,
            total=0,
        )

        total = 0
        for item in cart.cart_items.all():
            price_per_item = item.product.price
            if item.color_variant and getattr(item.color_variant, 'price', None):
                price_per_item += item.color_variant.price
            if item.size_variant and getattr(item.size_variant, 'price', None):
                price_per_item += item.size_variant.price

            oi = OrderItem.objects.create(
                order=order,
                product=item.product,
                size_variant=item.size_variant,
                color_variant=item.color_variant,
                quantity=item.quantity,
                price=price_per_item,
            )
            total += oi.get_total()

        order.total = total
        order.status = 'pending'
        order.save()

        # mark cart as paid (offline) and clear session
        cart.is_paid = True
        cart.save()
        request.session.pop('cart_id', None)
        request.session.pop('coupon_ids', None)

        messages.success(request, 'Đơn hàng của bạn đã được tạo.')
        return redirect('orders:success', order_uid=order.uid)

    # GET: render checkout form
    initial = {
        'full_name': request.user.get_full_name(),
        'email': request.user.email,
    }
    context = {'cart': cart, 'initial': initial}
    return render(request, 'orders/checkout.html', context)


def success(request, order_uid):
    order = get_object_or_404(Order, uid=order_uid)
    return render(request, 'orders/success.html', {'order': order})
