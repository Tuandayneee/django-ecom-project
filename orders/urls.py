from django.urls import path
from . import views, vnpay
from accounts.utils import calculate_cart_total


app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('success/<str:order_uid>/', views.order_success, name='order_success'),
    path('update-shipping/', views.update_shipping_fee, name='update_shipping_fee'),
    path('payment/vnpay/', vnpay.vnpay_payment, name='vnpay_payment'),
    path('payment/return/', vnpay.payment_return, name='payment_return'),
    path('buy-now/', views.buy_now, name='buy_now'),
    path('remove-order/<str:order_uid>/', views.remove_order, name='remove_order'),
]
