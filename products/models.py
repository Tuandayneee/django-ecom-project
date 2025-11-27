from django.conf import settings
from django.db import models
from base.models import BaseModel
from django.utils.text import slugify
from django.utils import timezone
from django.db.models import Min
# --- CÁC MODEL BIẾN THỂ (TEMPLATE) ---
# Đây là các model "mẫu" để bạn chọn trong Admin

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
    # Không cần slug hay price ở đây

    def __str__(self):
        return self.color_name

class SizeVariant(BaseModel):
    size_name = models.CharField(max_length=100)
    # Không cần slug hay price ở đây

    def __str__(self):
        return self.size_name

# --- CÁC MODEL SẢN PHẨM (ĐÃ SỬA KIẾN TRÚC) ---

class Product(BaseModel):
    """
    Model "vỏ bọc" cho sản phẩm.
    Chỉ chứa thông tin chung (tên, mô tả, category).
    """
    product_name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="products"
    )
    product_description = models.TextField(null=True, blank=True)
    
    @property
    def min_price(self):
        """
        Hàm này tự động tìm giá rẻ nhất trong các biến thể (Variant)
        Ví dụ: Áo có size S (100k), size L (120k) -> Hàm trả về 100k
        """
        # self.variants là do related_name="variants" ở model Variant
        result = self.variants.aggregate(Min('price'))
        return result['price__min'] if result['price__min'] is not None else 0

    def save(self, *args, **kwargs):
        if not self.slug: 
            self.slug = slugify(self.product_name)
        super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return self.product_name

class Variant(BaseModel):
    
    variant_name = models.CharField(max_length=255, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    color = models.ForeignKey(ColorVariant, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(SizeVariant, on_delete=models.SET_NULL, null=True, blank=True)
    
    price = models.IntegerField(default=0)
    stock = models.PositiveIntegerField(default=0, help_text="Số lượng tồn kho")

    def __str__(self):
        parts = [self.product.product_name]
        if self.color:
            parts.append(self.color.color_name)
        if self.size:
            parts.append(self.size.size_name)
        return " - ".join(parts)

    def save(self, *args, **kwargs):
        # Tự động tạo tên (nếu cần)
        if not self.variant_name and self.color and self.size:
            self.variant_name = f"{self.color.color_name} - {self.size.size_name}"
        super(Variant, self).save(*args, **kwargs)


class ProductImage(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_images")
    image = models.ImageField(upload_to="product")

    def __str__(self):
        return f"Image for {self.product.product_name}"

# --- Model COUPON (Không thay đổi) ---
class Coupon(models.Model):
    TYPE_CHOICES = (
        ('shipping', 'Free Shipping'),
        ('amount', 'Giảm tiền trực tiếp'),
        ('percent', 'Giảm phần trăm'),
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