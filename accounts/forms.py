from django import forms
from .models import Address
class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['recipient_name', 'phone', 'address_line', 'city', 'is_default']
        widgets = {
            'recipient_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên người nhận'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Số điện thoại'}),
            'address_line': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Địa chỉ cụ thể'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tỉnh/Thành phố'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }