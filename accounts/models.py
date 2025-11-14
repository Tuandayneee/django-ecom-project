import uuid
from django.db import models
from django.contrib.auth.models import User
from base.models import BaseModel
from django.db.models.signals import post_save
from django.dispatch import receiver
from base.emails import send_account_activation_email
from products.models import Coupon
from products.models import Coupon, Variant
class Profile(BaseModel):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name="profile")
    is_email_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=100,null=True,blank=True)
    profile_image = models.ImageField(upload_to='profile')
    def get_cart_count(self):
        return CartItems.objects.filter(cart__is_paid=False,cart__user=self.user).count()

class Cart(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="carts")
    coupons = models.ManyToManyField(Coupon, blank=True)
    is_paid = models.BooleanField(default=False)
    
    def get_cart_total(self):
        total = 0
        cart_items = self.cart_items.all()
        for item in cart_items:
            # Logic tính tổng mới (đơn giản hơn)
            total += item.get_item_total() 
        return total

class CartItems(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    
    # SỬA LỖI KIẾN TRÚC Ở ĐÂY:
    # Chỉ liên kết đến 'Variant', vì nó đã chứa tất cả thông tin
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Thêm trường 'quantity' (bạn đã có, rất tốt)
    quantity = models.IntegerField(default=1)

    # Đổi tên hàm
    def get_item_total(self):
        # Logic tính tổng mới (dựa trên Variant)
        if self.variant:
            return self.variant.price * self.quantity
        return 0 # Trả về 0 nếu variant bị xóa

    def __str__(self):
        if self.variant:
            return f"{self.variant.product.product_name} ({self.variant.variant_name}) - {self.quantity}"
        return f"Sản phẩm đã xóa - {self.quantity}"
        

@receiver(post_save,sender=User)
def send_email_token(sender,instance,created,**kwargs):
    try:
        if created:
            
            email_token = str(uuid.uuid4())
            Profile.objects.create(user=instance,email_token=email_token)
            email = instance.email
            send_account_activation_email(email,email_token)
    except Exception as e:
        print(e)

            