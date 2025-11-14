from django.contrib import admin
from .models import (
    Category, 
    ColorVariant, 
    SizeVariant, 
    Product, 
    Variant, 
    ProductImage,
    Coupon
)

# Đăng ký Category
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'slug')
    prepopulated_fields = {'slug': ('category_name',)}

# Đăng ký ColorVariant (Đã xóa 'price' khỏi list_display)
@admin.register(ColorVariant)
class ColorVariantAdmin(admin.ModelAdmin):
    list_display = ('color_name',)

# Đăng ký SizeVariant (Đã xóa 'price' khỏi list_display)
@admin.register(SizeVariant)
class SizeVariantAdmin(admin.ModelAdmin):
    list_display = ('size_name',)

# --- Cấu hình trang Product Admin (QUAN TRỌNG) ---

# Hiển thị các ảnh con bên trong trang Product
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1 # Cho phép thêm 1 ảnh mới mỗi lần

# Hiển thị các biến thể con bên trong trang Product
class VariantInline(admin.TabularInline):
    model = Variant
    extra = 1 # Cho phép thêm 1 biến thể mới
    # Hiển thị các trường quan trọng
    fields = ('color', 'size', 'price', 'stock', 'variant_name') 

# Đăng ký Product (Đã xóa 'price' khỏi list_display)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'category', 'slug')
    prepopulated_fields = {'slug': ('product_name',)}
    # Thêm 2 dòng này để bạn có thể quản lý Ảnh và Biến thể
    # ngay bên trong trang chi tiết Product. Đây là cách làm chuyên nghiệp.
    inlines = [ProductImageInline, VariantInline]

# Đăng ký Variant (Model MỚI)
@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    # Hiển thị các trường quan trọng khi liệt kê tất cả Variant
    list_display = ('__str__', 'product', 'color', 'size', 'price', 'stock')
    list_filter = ('product', 'color', 'size') # Thêm bộ lọc
    search_fields = ('product__product_name', 'variant_name') # Thêm thanh tìm kiếm

# Đăng ký Coupon (Giữ nguyên)
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('coupon_code', 'discount_price', 'minimum_amount', 'is_active', 'valid_to')