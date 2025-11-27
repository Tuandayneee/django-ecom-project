from django.urls import path
from . import views, vnpay

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('success/<str:order_uid>/', views.order_success, name='order_success'),

    path('payment/vnpay/', vnpay.vnpay_payment, name='vnpay_payment'),
    path('payment/return/', vnpay.payment_return, name='payment_return'),
]
