from django.conf import settings
from django.db import models
from base.models import BaseModel
from django.utils.text import slugify
from django.utils import timezone
from django.db.models import Min


class Category(BaseModel):
    category_name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    category_image = models.ImageField(upload_to="categories", null=True, blank=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.category_name)
        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.category_name

class ColorVariant(BaseModel):
    color_name = models.CharField(max_length=100)
    color_code = models.CharField(max_length=7, default='#000000', help_text='Hex color code (e.g., #FF5733)')
    

    def __str__(self):
        return self.color_name

class SizeVariant(BaseModel):
    size_name = models.CharField(max_length=100)
    def __str__(self):
        return self.size_name


class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    address = models.TextField(null=True, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    def __str__(self):
        return self.supplier_name
class Product(BaseModel):
    
    product_name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="products"
    )
    product_description = models.TextField(null=True, blank=True)
    original_price = models.IntegerField(default=0)
    price = models.IntegerField(default=0)
    sold_count = models.IntegerField(default=0)
    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="products"
    )
    updated_at = models.DateTimeField(auto_now=True)
    @property
    def min_price(self):
        result = self.variants.aggregate(Min('price'))
        return result['price__min'] if result['price__min'] is not None else 0

    def save(self, *args, **kwargs):
        if not self.slug: 
            self.slug = slugify(self.product_name)
        super(Product, self).save(*args, **kwargs)


    def get_percentage_off(self):
        if self.original_price > 0 and self.price < self.original_price:
            discount = (self.original_price - self.price) / self.original_price * 100
            return int(discount)
    def __str__(self):
        return self.product_name

class Variant(BaseModel):
    
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    color = models.ForeignKey(ColorVariant, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(SizeVariant, on_delete=models.SET_NULL, null=True, blank=True)
    stock = models.IntegerField(default=0)
    
    sku = models.CharField(max_length=100, unique=True,blank=True)
    original_price = models.IntegerField(default=0)
    price = models.IntegerField(default=0)
    image = models.ImageField(upload_to="products/variants", null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    @property
    def get_price(self):
        if self.price>0:
            return self.price
        return self.product.min_price

    @property
    def variant_name(self):
        
        return f"{self.product.product_name} - {self.color.color_name if self.color else ''} - {self.size.size_name if self.size else ''}"
    def __str__(self):
        parts = [self.product.product_name]
        if self.color:
            parts.append(self.color.color_name)
        if self.size:
            parts.append(self.size.size_name)
        return " - ".join(parts)

    def save(self, *args, **kwargs):
        if not self.sku:
            
            slug_product = slugify(self.product.product_name)
            slug_color = slugify(self.color.color_name)
            slug_size = slugify(self.size.size_name)
            
            
            self.sku = f"{slug_product}-{slug_color}-{slug_size}".upper()
            
        super().save(*args, **kwargs)


class ProductImage(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_images")
    image = models.ImageField(upload_to="product")
    is_thumbnail = models.BooleanField(default=False)
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return self.product.product_name
class Coupon(models.Model):
    TYPE_CHOICES = (
        ('shipping', 'Free Shipping'),
        ('amount', 'Giảm tiền trực tiếp'),
        ('percent', 'Giảm phần trăm'),
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
    )
    coupon_code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    discount_price = models.IntegerField(default=100)
    minimum_amount = models.IntegerField(default=500)
    is_active = models.BooleanField(default=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    usage_limit_per_user = models.PositiveIntegerField(default=1)
    coupon_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='amount')
    def is_valid(self):
        if not self.is_active:
            return False
        if self.valid_to and timezone.now() > self.valid_to:
            return False
        return True 

    def __str__(self):
        return self.coupon_code or "Chưa có mã"
    
class CouponUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    used_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'coupon')



    

