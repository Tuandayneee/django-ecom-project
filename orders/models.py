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
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='payments')
    payment_id = models.CharField(max_length=100, unique=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount_paid = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_id


    



class Order(BaseModel):
    STATUS_CHOICES = [
        ('Pending', 'Chờ xác nhận'),
        ('paid', 'Đã thanh toán'),
        ('shipped', 'Đang giao'),
        ('cancelled', 'Đã hủy'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    order_number = models.CharField(max_length=20, unique=True)
    
    # Thông tin nhận hàng
    full_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)

    # Chi phí đơn hàng
    order_total = models.IntegerField(default=0)  
    shipping_fee = models.IntegerField(default=0) 
    coupon_discount = models.IntegerField(default=0)  
    tax = models.IntegerField(default=0)  # Thuế
    
    # Trạng thái
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    is_ordered = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def grand_total(self):
        """Tính tổng tiền cuối cùng = order_total + shipping + tax - coupon_discount"""
        return self.order_total + self.shipping_fee + self.tax - self.coupon_discount

    def __str__(self):
        return f"Order {self.order_number} - {self.user.first_name if self.user else 'Guest'}"


class OrderProduct(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE,related_name='order_products')
    Payment = models.ForeignKey(Payment, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, null=True, blank=True)   
    quantity = models.IntegerField()
    product_price = models.IntegerField() 
    ordered = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_price(self):
        return self.product_price * self.quantity
    def __str__(self):
        return self.product.product_name
