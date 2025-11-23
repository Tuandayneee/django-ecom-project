import uuid
from django.db import models
from django.contrib.auth.models import User
from base.models import BaseModel
from django.db.models.signals import post_save
from django.dispatch import receiver
from base.emails import send_account_activation_email
# Import gọn gàng hơn
from products.models import Coupon, Variant 
from django.db.models import Sum


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    is_email_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=100, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile')

    def get_cart_count(self):

        
        item_count = CartItems.objects.filter(
            cart__user=self.user, 
            cart__is_paid=False
        ).aggregate(Sum('quantity'))['quantity__sum']
        return item_count if item_count else 0
    def __str__(self):
        return self.user.username
class Cart(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="carts")
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
        """
        Tính tổng tiền của dòng item này (Giá variant * Số lượng)
        Đã đổi tên thành 'get_product_price' để khớp với views và template
        """
        if self.variant:
            return self.variant.price * self.quantity
        return 0 

    def __str__(self):
        if self.variant:
            return f"{self.variant.product.product_name} ({self.variant.variant_name}) - {self.quantity}"
        return f"Sản phẩm đã xóa - {self.quantity}"

# --- SIGNALS ---
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