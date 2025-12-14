from django.contrib import admin
from .models import (
    Category, 
    ColorVariant, 
    SizeVariant, 
    Product, 
    Variant,
    ProductImage,
    Coupon,
    Supplier
)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email')
    search_fields = ('name', 'phone')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'slug')
    prepopulated_fields = {'slug': ('category_name',)}

@admin.register(ColorVariant)
class ColorVariantAdmin(admin.ModelAdmin):
    list_display = ('color_name',)

@admin.register(SizeVariant)
class SizeVariantAdmin(admin.ModelAdmin):
    list_display = ('size_name',)



class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1 
    readonly_fields = ('image_preview',) 
    

    def image_preview(self, obj):
        from django.utils.html import mark_safe
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" />')
        return ""

class VariantInline(admin.TabularInline): 
    model = Variant
    extra = 0 
    fields = ('sku', 'color', 'size', 'original_price', 'price', 'stock', 'image') 

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'category', 'price_range', 'updated_at')
    prepopulated_fields = {'slug': ('product_name',)}
    search_fields = ('product_name',)
    list_filter = ('category',)
    
    
    inlines = [ProductImageInline, VariantInline]

    
    def price_range(self, obj):
        items = obj.variants.all() 
        if items.exists():
            min_price = min([item.price for item in items])
            return f"{min_price:,} đ"
        return "Chưa có giá"


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):

    list_display = ('product', 'color', 'size', 'sku', 'price', 'stock', 'updated_at')
    list_filter = ('product', 'color', 'size') 
    search_fields = ('product__product_name', 'sku') 
    list_editable = ('price', 'stock') 

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('coupon_code', 'category', 'discount_price', 'minimum_amount', 'is_active', 'valid_to')
    list_filter = ('is_active', 'valid_to')