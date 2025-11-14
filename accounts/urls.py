
from django.urls import path 
from accounts.views import add_to_cart,login_page,register_page,activate_email,cart,apply_coupon,remove_item,remove_coupon,update_cart,logout_view
from . import views  


urlpatterns = [
    path('login/', login_page, name='login'),
    path('register/', register_page, name='register'),
    path('activate/<email_token>/', activate_email, name='activate_email'),
    path('cart/', cart,name='cart'),
    path('add-to-cart/<uid>/', add_to_cart, name='add_to_cart'),
    path('update-cart/', update_cart, name='update_cart'),
    path('cart/apply-coupon/', apply_coupon, name='apply_coupon'),
    path('remove-item/<cart_item_uid>/', remove_item, name='remove_item'),
   path('remove-coupon/<int:coupon_id>/', remove_coupon, name='remove_coupon'),
    path('logout/', logout_view, name='logout'),
]