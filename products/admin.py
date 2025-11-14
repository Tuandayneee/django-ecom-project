from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Category)
admin.site.register(Coupon)
class productImageAdmin(admin.StackedInline):
    model = ProductImage

class ProductAdmin(admin.ModelAdmin):
    inlines = [productImageAdmin]
    list_display = ('product_name', 'price')
admin.site.register(Product,ProductAdmin)


admin.register(ColorVariant)
class ColorVariantAdmin(admin.ModelAdmin):
    list_display = ('color_name', 'price')
    model = ColorVariant


admin.register(SizeVariant)
class SizeVariantAdmin(admin.ModelAdmin):
    list_display = ('size_name', 'price')
    model = SizeVariant

admin.site.register(ColorVariant,ColorVariantAdmin)
admin.site.register(SizeVariant,SizeVariantAdmin)
admin.site.register(ProductImage)