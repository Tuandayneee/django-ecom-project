import uuid
from django.db import models
from django.contrib.auth.models import User
from base.models import BaseModel
from django.db.models.signals import post_save
from django.dispatch import receiver
from base.emails import send_account_activation_email
# Import gọn gàng hơn
from products.models import Coupon, Product, Variant 
from django.db.models import Sum


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    is_email_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=100, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile')
    phone = models.CharField(max_length=20, null=True, blank=True)

    def get_cart_count(self):

        
        item_count = CartItems.objects.filter(
            cart__user=self.user, 
            cart__is_paid=False
        ).aggregate(Sum('quantity'))['quantity__sum']
        return item_count if item_count else 0
    def __str__(self):
        return self.user.username
class Cart(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="carts", null=True, blank=True)
    coupons = models.ManyToManyField(Coupon, blank=True, related_name='carts')
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def get_cart_total(self):
        cart_items = self.cart_items.all()
        price = []
        for cart_item in cart_items:
            price.append(cart_item.get_product_price)
        return sum(price)

class CartItems(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(default=1)

    @property
    def get_product_price(self):
        if self.variant:
            return self.variant.price * self.quantity
        return 0 

    def __str__(self):
        
        if self.variant:
            return f"{self.variant.product.product_name} ({self.variant.variant_name}) - {self.quantity}"
        return f"Sản phẩm đã xóa - {self.quantity}"

class Address(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address_line = models.TextField() 
    city = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False) 
    province_id = models.IntegerField(null=True, blank=True)
    district_id = models.IntegerField(null=True, blank=True)
    ward_code = models.CharField(max_length=50, null=True, blank=True)
    def save(self, *args, **kwargs):
        # Logic: Nếu địa chỉ này là mặc định, các địa chỉ khác của user phải bỏ mặc định đi
        if self.is_default:
            Address.objects.filter(user=self.user).update(is_default=False)
        super(Address, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.address_line}"



@receiver(post_save, sender=User)
def send_email_token(sender, instance, created, **kwargs):
    try:
        if created:
            email_token = str(uuid.uuid4())
            Profile.objects.create(user=instance, email_token=email_token)
            email = instance.email
            send_account_activation_email(email, email_token)
    except Exception as e:
        print(e)



    

def get_user_avatar(self):
    try:
        if self.profile.profile_image:
            return self.profile.profile_image.url
    except:
        pass
    return None

User.add_to_class('avatar', property(get_user_avatar))