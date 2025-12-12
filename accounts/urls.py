
from django.urls import path 
from accounts.views import add_address,user_orders,update_avatar,order_detail, add_to_cart, address_list, delete_address, edit_address,login_page,register_page,activate_email,cart,apply_coupon,remove_item,remove_coupon, set_default_address,update_cart,logout_view,save_address,user_dashboard
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('login/', login_page, name='login'),
    path('register/', register_page, name='register'),
    path('activate/<email_token>/', activate_email, name='activate_email'),
    path('reset_password/',auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'),name='reset_password'),
    path('reset_password_sent/',auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_sent.html'),name='password_reset_done'),
    path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_form.html'),name='password_reset_confirm'),
    path('reset_password_complete/',auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_done.html'),name='password_reset_complete'),
    path('change_password/',auth_views.PasswordChangeView.as_view(template_name='accounts/change_password.html'),name='change_password'),
    path('change_password_done/',auth_views.PasswordChangeDoneView.as_view(template_name='accounts/change_password_done.html'),name='change_password_done'),
    path('update-avatar/', update_avatar, name='update_avatar'),
    
    
    path('cart/', cart,name='cart'),
    path('add-to-cart/<uid>/', add_to_cart, name='add_to_cart'),
    path('update-cart/', update_cart, name='update_cart'),
    path('cart/apply-coupon/', apply_coupon, name='apply_coupon'),
    path('remove-item/<cart_item_uid>/', remove_item, name='remove_item'),
    path('remove-coupon/<int:coupon_id>/', remove_coupon, name='remove_coupon'),
    path('logout/', logout_view, name='logout'),
    path('save-address/', save_address, name='save_address'),

    path('profile/addresses/', address_list, name='address_list'),
    
    path('profile/addresses/edit/<uuid:uid>/', edit_address, name='edit_address'),
    path('profile/addresses/delete/<uuid:uid>/', delete_address, name='delete_address'),
    path('profile/addresses/set-default/<uuid:uid>/', set_default_address, name='set_default_address'),


    path('profile/', user_dashboard, name='user_profile'),
    path('profile/orders/', user_orders, name='user_orders'),
    path('profile/orders/<uuid:order_uid>/', order_detail, name='order_detail'),
    path('profile/addresses/', address_list, name='address_list'),
]