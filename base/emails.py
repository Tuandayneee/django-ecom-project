from django.conf import settings
from django.core.mail import send_mail


def send_account_activation_email(email, email_token):
    if not email:
        return
    subject = 'Tài khoản của bạn chưa được xác thực. Vui lòng xác thực tài khoản.'
    email_from = settings.EMAIL_HOST_USER or settings.DEFAULT_FROM_EMAIL
    base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000').rstrip('/')
    message = (
        'Vui lòng xác thực tài khoản của bạn bằng liên kết sau: '
        f'{base_url}/accounts/activate/{email_token}/'
    )
    send_mail(subject, message, email_from, [email])
