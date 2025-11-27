from .models import *
from django.contrib import admin




admin.site.register(Profile)
admin.site.register(Cart)
admin.site.register(CartItems)
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['recipient_name', 'user', 'city', 'phone', 'is_default']
    list_filter = ['is_default', 'city']
    search_fields = ['recipient_name', 'phone', 'address_line']