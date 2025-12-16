from django.db import models
from django.contrib.auth.models import User
from base.models import BaseModel
from products.models import Product, SizeVariant, ColorVariant
from products.models import Product, Variant


class Payment(BaseModel):
    PAYMENT_METHODS = [
        ('VNPay', 'VNPay'),
        ('cod', 'Cash on Delivery'),
    ]
    class PaymentStatus(models.TextChoices):
        PENDING = 'Pending', 'Chờ xử lý'
        COMPLETED = 'Completed', 'Thành công'
        FAILED = 'Failed', 'Thất bại'
        REFUNDED = 'Refunded', 'Đã hoàn tiền'
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='payments')
    payment_id = models.CharField(max_length=100, unique=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount_paid = models.CharField(max_length=100)
    

    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        
        return self.payment_id


    



class Order(BaseModel):
    STATUS_CHOICES = [
        ('Pending', 'Chờ xác nhận'),
        ('Confirmed','Đã xác nhận'),
        ('shipped', 'Đang giao'),
        ('paid', 'Đã thanh toán'),
        ('cancelled', 'Đã hủy'),
        
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    order_number = models.CharField(max_length=20, unique=True)
    
    
    full_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=50, blank=True)
    address_line = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)

    
    order_total = models.FloatField(default=0)  
    shipping_fee = models.FloatField(default=0) 
    coupon_discount = models.FloatField(default=0)  
    tax = models.IntegerField(default=0)  
    
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    is_ordered = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def grand_total(self):
        return self.order_total + self.shipping_fee + self.tax - self.coupon_discount

    def __str__(self):
        return f"Order {self.order_number} - {self.user.first_name if self.user else 'Guest'}"


class OrderProduct(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE,related_name='order_products')

    product = models.ForeignKey(Product, on_delete=models.SET_NULL,null=True)
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True, blank=True)   
    product_name = models.CharField(max_length=100)
    quantity = models.IntegerField()
    product_price = models.IntegerField() 
    

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_price(self):
        return self.product_price * self.quantity
    def __str__(self):
        product_name = self.product.product_name if self.product else "Sản phẩm đã xóa"
        variant_info = str(self.variant) if self.variant else ""
        return f"{product_name} {variant_info}"
    def save(self, *args, **kwargs):
        if not self.product_name and self.product:
            self.product_name = self.product.product_name
        if not self.product_price and self.variant:
            self.product_price = self.variant.price
        super().save(*args, **kwargs)