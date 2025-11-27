from django.contrib import admin
from .models import Order, OrderProduct


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    readonly_fields = ['quantity', 'product_price', 'ordered']
    extra = 0



@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'order_total', 'status', 'is_ordered', 'created_at']
    list_filter = ['status', 'is_ordered']
    search_fields = ['order_number', 'first_name', 'last_name', 'email']
    list_per_page = 20
    inlines = [OrderProductInline]



