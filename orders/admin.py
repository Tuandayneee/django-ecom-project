from django.contrib import admin
from .models import Order, OrderItem


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('uid', 'full_name', 'email', 'total', 'status', 'created_at')
    list_filter = ('status',)
    readonly_fields = ('uid', 'created_at')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    readonly_fields = ('uid', 'created_at')
