from django.db import models
from base.models import BaseModel
from django.utils.text import slugify

from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
class Category(BaseModel):
    category_name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    category_image = models.ImageField(upload_to="catgories", null=True, blank=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.category_name)
        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.category_name


class ColorVariant(BaseModel):
    color_name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    price = models.IntegerField(
        
        
        null=True, 
        blank=True, 
        
    )
    def save(self, *args, **kwargs):
        self.slug = slugify(self.color_name)
        super(ColorVariant, self).save(*args, **kwargs)

    def __str__(self):
        return self.color_name



class SizeVariant(BaseModel):
    size_name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    price = models.IntegerField(
        
        
        null=True, 
        blank=True, 
        
    )
    def save(self, *args, **kwargs):
        self.slug = slugify(self.size_name)
        super(SizeVariant, self).save(*args, **kwargs)

    def __str__(self):
        return self.size_name
class Product(BaseModel):
    product_name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="products"
    )
    
   
    price = models.IntegerField(
         
        null=True, 
        blank=True, 
        default=0
    )
    
    
    product_description = models.TextField(null=True, blank=True)

    Color_variant = models.ManyToManyField(
        ColorVariant,blank=True
    )
    size_variant = models.ManyToManyField(
        SizeVariant,blank=True
    )
    def save(self, *args, **kwargs):
        
        if not self.slug: 
            self.slug = slugify(self.product_name)
        
        
        super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return self.product_name
    

    def get_product_price_by_size(self, size):
        
        return SizeVariant.objects.get(size_name = size).price+self.price
    
class ProductImage(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_images")
    image = models.ImageField(upload_to="product")

    def __str__(self):
        return f"Image for {self.product.product_name}"
    

class Coupon(models.Model):
    coupon_code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    
    discount_price = models.IntegerField(
        default=100,  
        help_text="Số tiền giảm giá cố định (ví dụ: 10000 = 10.000đ)"
    )
    
    minimum_amount = models.IntegerField(
        default=500, 
        help_text="Số tiền tối thiểu của đơn hàng (ví dụ: 500000 = 500.000đ)"
    )
    
    is_active = models.BooleanField(default=True, 
                                    help_text="Tắt/mở mã này thủ công")
    
    valid_to = models.DateTimeField(
        null=True, blank=True, 
        help_text="Ngày mã hết hạn (để trống nếu không bao giờ hết hạn)"
    )

    def is_valid(self):
        """Kiểm tra xem mã còn hợp lệ không."""
        if not self.is_active:
            return False
        
        # SỬA LỖI Ở ĐÂY:
        # Dùng 'timezone.now()' thay vì 'datetime.timezone.now()'
        if self.valid_to and timezone.now() > self.valid_to:
            return False
            
        return True 

    def __str__(self):
        return self.coupon_code or "Chưa có mã"

    