
from django.urls import path 
from accounts.views import add_address,user_orders,order_detail, add_to_cart, address_list, delete_address, edit_address,login_page,register_page,activate_email,cart,apply_coupon,remove_item,remove_coupon, set_default_address,update_cart,logout_view,save_address,user_dashboard



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
    path('save-address/', save_address, name='save_address'),

    path('profile/addresses/', address_list, name='address_list'),
    path('profile/addresses/add/', add_address, name='add_address'),
    path('profile/addresses/edit/<uuid:uid>/', edit_address, name='edit_address'),
    path('profile/addresses/delete/<uuid:uid>/', delete_address, name='delete_address'),
    path('profile/addresses/set-default/<uuid:uid>/', set_default_address, name='set_default_address'),


    path('profile/', user_dashboard, name='user_profile'),
    path('profile/orders/', user_orders, name='user_orders'),
    path('profile/orders/<uuid:order_uid>/', order_detail, name='order_detail'),
    path('profile/addresses/', address_list, name='address_list'),
]