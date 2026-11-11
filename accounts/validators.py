from django.core.exceptions import ValidationError
import re

class ComplexPassWordValidator:
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError("Password phải có ít nhất 8 kí tự.")

        if not re.search(r'[A-Z]', password):
            raise ValidationError("Mật khẩu phải chứa ít nhất một chữ cái VIẾT HOA.",
                code='password_no_upper',)

        if not re.search(r'[a-z]', password):
            raise ValidationError("Mật khẩu phải chứa ít nhất một chữ cái thường.",
                code='password_no_lower',)

        if not re.search(r'[0-9]', password):
            raise ValidationError(
                "Mật khẩu phải chứa ít nhất một chữ số.",
                code='password_no_number',
            )
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
             raise ValidationError(
                "Mật khẩu phải chứa ít nhất một ký tự đặc biệt (!@#$%...).",
                code='password_no_symbol',
            )

    def get_help_text(self):
        return "Mật khẩu phải có chữ hoa, chữ thường, số và ký tự đặc biệt."