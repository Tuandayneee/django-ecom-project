from django.conf import settings
from django.core.mail import send_mail




def send_account_activation_email(email, email_token):
    subject = 'Tài khoản của bạn chưa được xác thực. Vui lọc xác thức tài khoản.'
    email_from = settings.EMAIL_HOST_USER
    message = f'Chương trình xác thức tài khoản. Vui lọc xác thức tài khoản. Link xác thức tài khoản: http://127.0.0.1:8000/accounts/activate/{email_token}'
    send_mail(subject, message, email_from, [email])