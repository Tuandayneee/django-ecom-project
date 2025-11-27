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
        ('Pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    order_number = models.CharField(max_length=20, unique=True)
    
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    note = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)



    order_total = models.IntegerField(default=0)
    tax = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_ordered = models.BooleanField(default=False)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.user.first_name


class OrderProduct(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    Payment = models.ForeignKey(Payment, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    Variant = models.ForeignKey(Variant, on_delete=models.CASCADE, null=True, blank=True)   
    quantity = models.IntegerField()
    product_price = models.IntegerField() 
    ordered = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product.product_name
