# 💻 CODE REFERENCE & IMPLEMENTATION CHECKLIST

## 🎯 DANH SÁCH KIỂM TRA TRIỂN KHAI

### 3.3.1 - Quản Lý Sản Phẩm & Danh Mục

#### ✅ Slug Auto
- [x] `slugify()` từ `django.utils.text`
- [x] Override `save()` trong Model
- [x] `unique=True` trên SlugField
- [x] URL pattern: `<slug:slug>/`

**File cần kiểm tra:** `products/models.py` (Lines: 10-20, 45-75)

---

#### ✅ Image Management
- [x] Model `ProductImage` với FK tới Variant
- [x] Model `Variant` có ImageField
- [x] Upload path: `products/variants`
- [x] Field `is_thumbnail` để chỉ định ảnh đại diện

**File cần kiểm tra:** `products/models.py` (Lines: 150-156)

**Tính năng Pillow (Optional):**
```python
# Để tối ưu hóa ảnh, thêm vào settings.py:
from PIL import Image
import os

def optimize_image(image_path, max_width=1200, max_height=1200):
    img = Image.open(image_path)
    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    img.save(image_path, quality=85, optimize=True)
```

---

### 3.3.2 - Giỏ Hàng & Thanh Toán

#### ✅ Database Cart
- [x] Model `Cart` (user, coupons, is_paid)
- [x] Model `CartItems` (cart, variant, quantity)
- [x] Method `get_cart_total()`
- [x] Property `get_product_price`

**File cần kiểm tra:** `accounts/models.py` (Lines: 31-46)

---

#### ✅ Cart Views
- [x] `cart()` - hiển thị giỏ hàng
- [x] `add_to_cart()` - thêm sản phẩm
- [x] `update_cart()` - cập nhật số lượng (AJAX)
- [x] `remove_item()` - xóa sản phẩm
- [x] `apply_coupon()` - áp dụng coupon

**File cần kiểm tra:** `accounts/views.py` (Lines: 80-250)

---

#### ✅ VNPay Integration
- [x] Bước 1: Tạo request data + mã hóa HMAC-SHA512
- [x] Bước 2: Redirect sang VNPay payment page
- [x] ⚠️ Bước 3: **CẦN THÊM** checksum validation trên return

**File cần kiểm tra:** `orders/vnpay.py`

**Cần thêm vào payment_return():**
```python
def validate_vnpay_checksum(data):
    """Xác thực checksum từ VNPay response"""
    vnp_SecureHash = data.get('vnp_SecureHash')
    inputData = dict(data)
    inputData.pop('vnp_SecureHash', None)
    
    inputData = sorted(inputData.items())
    queryData = urllib.parse.urlencode(inputData)
    
    computed_hash = hmac.new(
        bytes(settings.VNPAY_HASH_SECRET_KEY, 'utf-8'),
        bytes(queryData, 'utf-8'),
        hashlib.sha512
    ).hexdigest()
    
    return computed_hash == vnp_SecureHash
```

---

### 3.3.3 - Xác Thực & Bảo Mật

#### ✅ Password Hashing
- [x] Django mặc định dùng PBKDF2-SHA256
- [x] `user.set_password()` tự động mã hóa
- [x] 100,000 iterations
- [x] Salt độc lập cho mỗi password

**File cần kiểm tra:** `accounts/views.py` (Lines: 18-45)

---

#### ✅ Email Verification
- [x] Signal `send_email_token()` kích hoạt khi User tạo
- [x] Tạo UUID token
- [x] Gửi email với link xác thực
- [x] View `activate_email()` xác thực email

**File cần kiểm tra:**
- `accounts/models.py` (Lines: 88-103) - Signal
- `base/emails.py` - Email function
- `accounts/views.py` (Lines: 55-65) - Activate view

---

#### ✅ OAuth (Django Allauth)
- [x] Installed apps: allauth + providers
- [x] SITE_ID = 1
- [x] Login/logout redirect URLs
- [x] Provider cấu hình (Google, FB, GitHub)

**File cần kiểm tra:** `ecom/settings.py` (Lines: 35-50, 280-320)

---

## 📝 QUICK REFERENCE - Các Lệnh Hữu Ích

### Database & Migrations
```bash
# Tạo migration
python manage.py makemigrations

# Áp dụng migration
python manage.py migrate

# Kiểm tra SQL của migration
python manage.py sqlmigrate products 0001

# Reset database (DEV ONLY)
python manage.py flush
```

### Testing
```bash
# Chạy test cho app
python manage.py test products

# Test với verbose
python manage.py test products -v 2

# Test 1 test case
python manage.py test products.tests.ProductTestCase.test_slug_creation
```

### Admin
```bash
# Tạo superuser
python manage.py createsuperuser

# Shell Django (test logic)
python manage.py shell
```

### Running
```bash
# Dev server
python manage.py runserver

# Chỉ định port
python manage.py runserver 8080

# Bind IP khác
python manage.py runserver 0.0.0.0:8000
```

---

## 🔍 TROUBLESHOOTING

### ❌ Email không gửi
**Kiểm tra:**
- Cấu hình SMTP trong `settings.py`
- Gmail: Dùng App Password (không password account)
- Port 587 vs 465
- EMAIL_USE_TLS = True

```python
# Kiểm tra bằng shell
from django.core.mail import send_mail
send_mail(
    'Test',
    'Test message',
    'your-email@gmail.com',
    ['recipient@gmail.com']
)
```

---

### ❌ VNPay checksum lỗi
**Kiểm tra:**
1. Secret key đúng: `B159DXK3140FGOFHWGYJ29B8J77IVVOZ`
2. Sắp xếp tham số A-Z ✓
3. HMAC-SHA512 (không SHA1) ✓
4. Amount nhân 100 ✓

---

### ❌ Variant SKU trùng lặp
**Kiểm tra:**
- Variant `save()` có tạo SKU? ✓
- Slug color/size đúng không? ✓
- Unique constraint có được apply? ✓

---

## 📊 Database Schema

### Cart Tables
```
┌─────────────────────────────────────┐
│         Cart (accounts_cart)         │
├──────────────┬──────────────────────┤
│ id (PK)      │ integer              │
│ uid          │ UUID (unique)        │
│ user_id (FK) │ auth_user.id         │
│ is_paid      │ boolean              │
│ created_at   │ datetime             │
└─────────────────────────────────────┘
           ↓ (1:N)
┌─────────────────────────────────────┐
│    CartItems (accounts_cartitems)    │
├──────────────┬──────────────────────┤
│ id (PK)      │ integer              │
│ uid          │ UUID (unique)        │
│ cart_id (FK) │ accounts_cart.id     │
│ variant_id   │ products_variant.id  │
│ quantity     │ integer              │
└─────────────────────────────────────┘
```

### Product Tables
```
┌─────────────────────────────────────┐
│      Product (products_product)      │
├──────────────┬──────────────────────┤
│ id (PK)      │ integer              │
│ uid          │ UUID (unique)        │
│ product_name │ varchar(100)         │
│ slug         │ SlugField (unique)   │
│ price        │ integer              │
│ created_at   │ datetime             │
└─────────────────────────────────────┘
           ↓ (1:N)
┌─────────────────────────────────────┐
│       Variant (products_variant)     │
├──────────────┬──────────────────────┤
│ id (PK)      │ integer              │
│ uid          │ UUID (unique)        │
│ product_id   │ products_product.id  │
│ color_id     │ products_color...id  │
│ size_id      │ products_size...id   │
│ sku          │ varchar(100)(unique) │
│ price        │ integer              │
│ stock        │ integer              │
│ image        │ ImageField           │
└─────────────────────────────────────┘
           ↓ (1:N)
┌─────────────────────────────────────┐
│   ProductImage (products_image)      │
├──────────────┬──────────────────────┤
│ id (PK)      │ integer              │
│ product_id   │ products_product.id  │
│ variant_id   │ products_variant.id  │
│ image        │ ImageField           │
│ is_thumbnail │ boolean              │
└─────────────────────────────────────┘
```

---

## 🔐 Bảo Mật Checklist

- [x] Password hashing PBKDF2-SHA256
- [x] CSRF protection (Django default)
- [x] SQL injection protection (ORM)
- [x] XSS protection (template escaping)
- [x] Email verification token
- [x] VNPay checksum validation (CẦN THÊM)
- [x] Session security (secure cookies)
- [ ] Rate limiting (TODO)
- [ ] Two-factor authentication (TODO)
- [ ] API key management (TODO)

---

## 📈 Performance Tips

### Optimize Queries
```python
# ❌ N+1 Query Problem
for cart_item in cart_items:
    print(cart_item.variant.product.product_name)  # Query per item!

# ✅ Select Related
cart_items = CartItems.objects.select_related('variant__product').all()
for cart_item in cart_items:
    print(cart_item.variant.product.product_name)  # 1 query!
```

### Cache frequently accessed data
```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # Cache 5 minutes
def product_detail(request, slug):
    ...
```

### Image optimization
```python
# Compress on upload
from PIL import Image
from io import BytesIO

def compress_image(image_file, quality=85):
    img = Image.open(image_file)
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=quality, optimize=True)
    return buffer
```

---

## 🧪 Test Examples

### Test Slug Creation
```python
# products/tests.py
from django.test import TestCase
from products.models import Product

class ProductTestCase(TestCase):
    def test_slug_auto_creation(self):
        product = Product.objects.create(
            product_name="Áo Thun Mùa Hè"
        )
        self.assertEqual(product.slug, "ao-thun-mua-he")
    
    def test_slug_uniqueness(self):
        Product.objects.create(product_name="Test Product")
        with self.assertRaises(Exception):
            Product.objects.create(product_name="Test Product")
```

### Test Cart Addition
```python
# accounts/tests.py
from django.test import TestCase, Client
from django.contrib.auth.models import User
from products.models import Product, Variant
from accounts.models import Cart, CartItems

class CartTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='test@test.com',
            password='test123'
        )
        self.product = Product.objects.create(
            product_name="Test Product"
        )
        self.variant = Variant.objects.create(
            product=self.product,
            price=100000,
            stock=10
        )
    
    def test_add_to_cart(self):
        self.client.login(username='test@test.com', password='test123')
        response = self.client.post(
            f'/cart/add/{self.product.uid}/',
            {'variant': self.variant.uid, 'quantity': 2}
        )
        
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.cart_items.count(), 1)
        self.assertEqual(cart.cart_items.first().quantity, 2)
```

---

## 📚 Resources & Documentation

- Django Docs: https://docs.djangoproject.com/en/5.2/
- VNPay Integration: https://sandbox.vnpayment.vn/
- Allauth Docs: https://django-allauth.readthedocs.io/
- Pillow (Image): https://pillow.readthedocs.io/
- Django Security: https://docs.djangoproject.com/en/5.2/topics/security/

---

## 🚀 Deployment Checklist

Trước khi deploy lên production:

- [ ] `DEBUG = False` trong settings
- [ ] Thay `SECRET_KEY` bằng env variable
- [ ] Cấu hình `ALLOWED_HOSTS` chính xác
- [ ] Dùng HTTPS (SSL certificate)
- [ ] Cấu hình Email production
- [ ] VNPay dùng production URL (không sandbox)
- [ ] Database backup plan
- [ ] Media files storage (S3, Cloudinary)
- [ ] Static files serve (nginx, whitenoise)
- [ ] Logging & monitoring setup
- [ ] Error tracking (Sentry)

---

**File này cần cập nhật thường xuyên khi thêm tính năng mới**

Last updated: 5/1/2026
