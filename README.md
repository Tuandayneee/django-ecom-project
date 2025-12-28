# E-Commerce Django

Một nền tảng thương mại điện tử hiện đại được xây dựng bằng **Django 5.x** với các tính năng quản lý sản phẩm, giỏ hàng, thanh toán VNPay, quản lý đơn hàng, và hệ thống tài khoản người dùng đầy đủ.

---

## 📋 Mục Lục

- [Tổng Quan](#tổng-quan)
- [Các Tính Năng Chính](#các-tính-năng-chính)
- [Yêu Cầu Hệ Thống](#yêu-cầu-hệ-thống)
- [Cài Đặt & Thiết Lập](#cài-đặt--thiết-lập)
- [Cấu Trúc Dự Án](#cấu-trúc-dự-án)
- [Hướng Dẫn Sử Dụng](#hướng-dẫn-sử-dụng)
- [Quản Lý Cơ Sở Dữ Liệu](#quản-lý-cơ-sở-dữ-liệu)
- [Cấu Hình Thanh Toán VNPay](#cấu-hình-thanh-toán-vnpay)
- [API & Serializers](#api--serializers)
- [Những Điều Cần Lưu Ý](#những-điều-cần-lưu-ý)
- [Khắc Phục Sự Cố](#khắc-phục-sự-cố)

---

## Tổng Quan

Dự án này là một ứng dụng web thương mại điện tử hoàn chỉnh cho phép:

- **Người dùng**: Duyệt sản phẩm, thêm vào giỏ hàng, thanh toán qua VNPay, theo dõi đơn hàng
- **Quản trị viên**: Quản lý sản phẩm, biến thể, khách hàng, đơn hàng và thanh toán
- **Hệ thống**: Xử lý giỏ hàng tự động, áp dụng mã giảm giá, xác thực email, tính phí vận chuyển

---

## Các Tính Năng Chính

### 1. **Quản Lý Sản Phẩm**

- Quản lý danh mục sản phẩm với slug tự động
- Hỗ trợ biến thể sản phẩm (kích cỡ, màu sắc)
- Quản lý hình ảnh sản phẩm cho từng biến thể
- Định giá linh hoạt: giá gốc + phụ phí biến thể
- Theo dõi số lượng bán hàng và tồn kho

### 2. **Quản Lý Người Dùng & Tài Khoản**

- Đăng ký / Đăng nhập với xác thực email
- Quản lý hồ sơ người dùng (ảnh, số điện thoại)
- Quản lý địa chỉ giao hàng (thêm, sửa, xóa)
- Đặt lại mật khẩu qua email
- Đăng nhập xã hội (OAuth)

### 3. **Giỏ Hàng & Thanh Toán**

- Giỏ hàng duy trì theo phiên / người dùng
- Thêm/xóa sản phẩm từ giỏ hàng
- Hợp nhất giỏ hàng tự động khi đăng nhập
- Áp dụng mã giảm giá (coupon)
- Tính toán tổng tiền + phí vận chuyển + thuế

### 4. **Thanh Toán VNPay**

- Tích hợp cổng thanh toán VNPay
- Xử lý hai trường hợp: Mua ngay + Giỏ hàng
- Xác minh chữ ký bảo mật (HMAC-SHA512)
- Truy vết thanh toán với order_id và status
- Tự động cập nhật trạng thái đơn hàng

### 5. **Quản Lý Đơn Hàng**

- Tạo đơn hàng từ giỏ hàng hoặc mua ngay
- Theo dõi trạng thái đơn hàng (Pending → Accepted → Shipped → Delivered)
- Trữ chi tiết sản phẩm, giá, phí vận chuyển
- Xem lịch sử đơn hàng cá nhân

### 6. **Tài khoản quản trị viên**

- Giao diện admin nâng cao (Jazzmin)
- Quản lý toàn bộ dữ liệu (sản phẩm, người dùng, đơn hàng)
- Lọc, tìm kiếm nâng cao
- Xuất dữ liệu (CSV)

### 7. **Đánh Giá & Nhận Xét**

- Người dùng có thể viết đánh giá sản phẩm
- Xem tổng sao đánh giá sản phẩm
- Liên kết với đơn hàng để xác thực mua hàng

### 8. **Email & Thông Báo**

- Gửi email kích hoạt tài khoản
- Email xác nhận đơn hàng
- Email đặt lại mật khẩu

---

## 💻 Yêu Cầu Hệ Thống

- **Python**: 3.9+
- **Django**: 5.2.7
- **Cơ sở dữ liệu**: MySQL 5.7+ (hoặc MariaDB)
- **Trình quản lý gói**: pip hoặc conda
- **Tài khoản VNPay**: Để tích hợp thanh toán
- **SMTP Server**: Để gửi email (Gmail, Mailgun, v.v.)
- **MySQL Client Driver**: `mysqlclient` hoặc `PyMySQL`

---

## 🚀 Cài Đặt & Thiết Lập

### 1. Clone Repository

```bash
cd d:\tu hoc\python\ecom
```

### 2. Tạo Virtual Environment (Nếu chưa có)

```bash
# Tạo venv
python -m venv venv

# Kích hoạt (Windows)
venv\Scripts\activate

# Kích hoạt (macOS/Linux)
source venv/bin/activate
```

### 3. Cài Đặt Dependencies

```bash
pip install -r requirements.txt
```

Nếu chưa có `requirements.txt`, cài các package chính:

```bash
pip install django==5.2.7
pip install mysqlclient
pip install pillow
pip install django-jazzmin
pip install django-allauth
pip install django-image-uploader-widget
pip install djangorestframework
pip install djangorestframework-simplejwt
```

> **Lưu ý**: Nếu gặp lỗi cài `mysqlclient`, bạn có thể dùng `PyMySQL` thay thế:
>
> ```bash
> pip install PyMySQL
> # Thêm vào manage.py: import pymysql; pymysql.install_as_MySQLdb()
> ```

### 4. Cấu Hình MySQL

Sửa file [ecom/settings.py](ecom/settings.py) - phần DATABASE:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'urbanvibe_db',      # Tên database
        'USER': 'root',               # User MySQL
        'PASSWORD': '123456',         # Mật khẩu MySQL
        'HOST': '127.0.0.1',          # Địa chỉ MySQL server
        'PORT': '3306',               # Port MySQL
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}
```

> **Tạo Database MySQL**:
>
> ```sql
> CREATE DATABASE urbanvibe_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
> ```

### 5. Cấu Hình Email & VNPay

Tiếp tục sửa [ecom/settings.py](ecom/settings.py):

```python
# Email SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'letuan16112004@gmail.com'  # Email của bạn
EMAIL_HOST_PASSWORD = 'app-password'  # App password (không phải mật khẩu Gmail)

# VNPay Configuration
VNPAY_TMN_CODE = 'SIXDZGUD'  # TMN Code của bạn
VNPAY_HASH_SECRET_KEY = 'B159DXK3140FGOFHWGYJ29B8J77IVVOZ'  # Secret Key
VNPAY_PAYMENT_URL = 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'  # Sandbox
VNPAY_RETURN_URL = 'http://127.0.0.1:8000/payment_return/'
```

### 6. Chạy Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Tạo Tài Khoản Admin

```bash
python manage.py createsuperuser
```

Nhập thông tin:

- Username: admin
- Email: admin@example.com
- Password: (nhập mật khẩu)

### 8. Khởi Động Server

```bash
python manage.py runserver
```

Truy cập:

- **Trang chủ**: http://localhost:8000
- **Admin**: http://localhost:8000/admin

---

## 📁 Cấu Trúc Dự Án

```
ecom/
├── manage.py                    # Lệnh Django
├── requirements.txt             # Dependencies
├── database.mdj                 # Diagram cơ sở dữ liệu
│
├── ecom/                        # Cấu hình chính
│   ├── settings.py             # Cài đặt Django
│   ├── urls.py                 # URL gốc
│   ├── wsgi.py                 # WSGI (Sản xuất)
│   ├── asgi.py                 # ASGI (Async)
│   └── context_processors.py   # Xử lý ngữ cảnh template
│
├── base/                        # Ứng dụng cơ sở
│   ├── models.py               # BaseModel (UUID, created_at)
│   └── emails.py               # Hàm gửi email
│
├── products/                    # Ứng dụng sản phẩm
│   ├── models.py               # Product, Variant, Category, Coupon, Review
│   ├── views.py                # Xem sản phẩm, danh sách, chi tiết
│   ├── urls.py                 # URL sản phẩm
│   ├── forms.py                # Form tạo/sửa sản phẩm
│   ├── admin.py                # Admin panel
│   ├── serializers.py          # API serializers
│   └── migrations/             # Cơ sở dữ liệu migrations
│
├── accounts/                    # Ứng dụng tài khoản
│   ├── models.py               # User, Profile, Cart, CartItems, Address
│   ├── views.py                # Đăng nhập, đăng ký, giỏ hàng
│   ├── urls.py                 # URL tài khoản
│   ├── forms.py                # Form đăng nhập, đăng ký
│   ├── middleware.py           # Xóa coupon khi rời khỏi cart
│   ├── admin.py                # Admin panel
│   ├── utils.py                # Hàm tiện ích
│   ├── validators.py           # Xác thực dữ liệu
│   └── migrations/             # Cơ sở dữ liệu migrations
│
├── orders/                      # Ứng dụng đơn hàng
│   ├── models.py               # Order, OrderProduct, Payment
│   ├── views.py                # Xem đơn hàng
│   ├── urls.py                 # URL đơn hàng
│   ├── vnpay.py                # Xử lý VNPay
│   ├── utils.py                # Hàm tiện ích
│   ├── admin.py                # Admin panel
│   └── migrations/             # Cơ sở dữ liệu migrations
│
├── home/                        # Ứng dụng trang chủ
│   ├── models.py               # Banner, Slider
│   ├── views.py                # Trang chủ
│   ├── urls.py                 # URL trang chủ
│   └── migrations/             # Cơ sở dữ liệu migrations
│
├── templates/                   # Template HTML
│   ├── base/
│   │   ├── base.html           # Template cơ sở
│   │   └── alert.html          # Thông báo
│   ├── product/
│   │   ├── product.html        # Chi tiết sản phẩm
│   │   ├── products.html       # Danh sách sản phẩm
│   │   └── ...
│   ├── accounts/
│   │   ├── login_register.html # Đăng nhập/đăng ký
│   │   ├── cart.html           # Giỏ hàng
│   │   ├── dashboard.html      # Bảng điều khiển người dùng
│   │   ├── address_list.html   # Địa chỉ giao hàng
│   │   ├── orders.html         # Lịch sử đơn hàng
│   │   └── ...
│   ├── orders/
│   │   ├── checkout.html       # Thanh toán
│   │   ├── order_success.html  # Thành công
│   │   └── ...
│   ├── home/
│   │   ├── index.html          # Trang chủ
│   │   └── ...
│   └── includes/
│       ├── user_sidebar.html   # Sidebar người dùng
│       └── ...
│
├── public/                      # File tĩnh
│   └── static/
│       ├── css/                # CSS
│       ├── js/                 # JavaScript
│       ├── images/             # Hình ảnh
│       └── ...
│
└── media/                       # File upload
    ├── products/               # Hình ảnh sản phẩm
    ├── profile/                # Ảnh hồ sơ
    └── ...
```

---

## 🔧 Hướng Dẫn Sử Dụng

### Cho Khách Hàng

#### 1. Đăng Ký Tài Khoản

```
1. Truy cập: http://localhost:8000/accounts/login/
2. Nhấp "Đăng ký"
3. Nhập email, username, mật khẩu
4. Kiểm tra email để xác thực
5. Đăng nhập
```

#### 2. Duyệt Sản Phẩm

```
1. Trang chủ: http://localhost:8000/
2. Chọn danh mục hoặc dùng tìm kiếm
3. Nhấp sản phẩm để xem chi tiết
4. Chọn kích cỡ, màu sắc, số lượng
```

#### 3. Thêm Vào Giỏ Hàng

```
- Từ trang chi tiết sản phẩm: Nhấp "Thêm vào giỏ"
- Hoặc: Từ danh sách, nhấp icon giỏ hàng
- Số lượng sản phẩm hiển thị trên icon giỏ
```

#### 4. Thanh Toán

**Từ Giỏ Hàng:**

```
1. Nhấp icon giỏ hàng
2. Kiểm tra sản phẩm, chọn áp dụng coupon (tùy chọn)
3. Nhấp "Thanh toán"
4. Chọn/tạo địa chỉ giao hàng
5. Chọn "Thanh toán VNPay"
6. Hoàn thành thanh toán trên VNPay
7. Xác nhận thành công
```

**Mua Ngay:**

```
1. Từ trang chi tiết sản phẩm
2. Chọn biến thể + số lượng
3. Nhấp "Mua Ngay"
4. Chọn địa chỉ, thanh toán
```

#### 5. Theo Dõi Đơn Hàng

```
1. Vào dashboard: http://localhost:8000/accounts/dashboard/
2. Nhấp "Lịch sử đơn hàng"
3. Xem chi tiết từng đơn hàng
```

### Cho Quản Trị Viên

#### 1. Truy Cập Admin Panel

```
http://localhost:8000/admin/
Username: admin
Password: (mật khẩu admin)
```

#### 2. Quản Lý Sản Phẩm

**Tạo Danh Mục:**

```
Admin > Products > Categories > Add
- Category Name: "Áo phông"
- Slug: (tự động) → "ao-phong"
- Category Image: (tùy chọn)
```

**Tạo Sản Phẩm:**

```
Admin > Products > Products > Add
- Product Name: "Áo phông trắng tay ngắn"
- Category: "Áo phông"
- Original Price: 150000 (VND)
- Price: 120000 (VND)
- Description: (chi tiết sản phẩm)
```

**Thêm Biến Thể:**

```
Từ trang sửa sản phẩm:
- Chọn Color: "Xanh" / "Đỏ"
- Chọn Size: "S" / "M" / "L"
- Price Offset: +10000 (nếu cỡ L đắt hơn 10k)
- Stock: 50
- SKU: AO-T-TRANG-S-1
```

**Thêm Hình Ảnh:**

```
Admin > Products > ProductImages > Add
- Product: "Áo phông trắng tay ngắn"
- Variant: (tùy chọn - để trống = tất cả)
- Image: (chọn file)
```

#### 3. Quản Lý Mã Giảm Giá

```
Admin > Products > Coupons > Add
- Code: "SUMMER50"
- Discount Percent: 50
- Discount Amount: 0 (hoặc nhập số tiền cố định)
- Valid From: 01/01/2025
- Valid To: 31/12/2025
- Usage Limit: 100
- Is Active: ✓
```

#### 4. Quản Lý Đơn Hàng

```
Admin > Orders > Orders
- Xem danh sách đơn hàng
- Nhấp để xem chi tiết
- Cập nhật Status: Pending → Accepted → Shipped → Delivered
- Xem thông tin thanh toán
```

#### 5. Quản Lý Người Dùng

```
Admin > Auth > Users
- Xem danh sách người dùng
- Kích hoạt/vô hiệu hóa tài khoản
- Đặt lại mật khẩu

Admin > Accounts > Profiles
- Xem hồ sơ chi tiết
- Xác minh email
```

---

## Quản Lý Cơ Sở Dữ liệu

### Các Model Chính

#### **Product Model** (Sản Phẩm)

```python
- uid (UUID Primary Key)
- product_name (str)
- slug (SlugField - tự động từ product_name)
- category (ForeignKey → Category)
- product_description (TextField)
- original_price (int)
- price (int)
- sold_count (int)
- created_at (DateTime)
```

#### **Variant Model** (Biến Thể)

```python
- uid (UUID Primary Key)
- product (ForeignKey → Product)
- color (ForeignKey → ColorVariant, nullable)
- size (ForeignKey → SizeVariant, nullable)
- price (int) - Phụ phí so với sản phẩm
- stock (int)
- sku (str - Unique)
- original_price (int)
```

#### **Cart Model** (Giỏ Hàng)

```python
- uid (UUID Primary Key)
- user (ForeignKey → User, nullable)
- coupons (M2M → Coupon)
- is_paid (bool)
```

#### **CartItems Model** (Mục Giỏ Hàng)

```python
- uid (UUID Primary Key)
- cart (ForeignKey → Cart)
- variant (ForeignKey → Variant)
- quantity (int)
```

#### **Order Model** (Đơn Hàng)

```python
- uid (UUID Primary Key)
- user (ForeignKey → User)
- payment (ForeignKey → Payment)
- order_number (str)
- full_name (str)
- phone (str)
- address (TextField)
- city (str)
- order_total (int)
- shipping_fee (int)
- coupon_discount (int)
- tax (int)
- status (Choices: Pending/Accepted/Shipped/Delivered)
- is_ordered (bool)
```

#### **Coupon Model** (Mã Giảm Giá)

```python
- uid (UUID Primary Key)
- code (str - Unique)
- discount_percent (int)
- discount_amount (int)
- valid_from (DateTime)
- valid_to (DateTime)
- is_active (bool)
```

### Tạo Migrations

```bash
# Sau khi thay đổi models.py
python manage.py makemigrations

# Kiểm tra SQL
python manage.py sqlmigrate [app_name] [migration_number]

# Áp dụng migrations
python manage.py migrate
```

### Reset/Khôi Phục Cơ Sở Dữ Liệu MySQL

```bash
# Xóa toàn bộ database
DROP DATABASE urbanvibe_db;

# Tạo lại database
CREATE DATABASE urbanvibe_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Chạy migrations
python manage.py makemigrations
python manage.py migrate

# Tạo superuser mới
python manage.py createsuperuser
```

**Hoặc từ dòng lệnh Django:**

```bash
# Xóa migrations (trừ 0001_initial.py)
# (Xóa các file .py trong migrations/, giữ lại __init__.py)

# Sau đó:
python manage.py makemigrations
python manage.py migrate
```

---

## 💳 Cấu Hình Thanh Toán VNPay

### 1. Đăng Ký Tài Khoản VNPay

1. Truy cập: https://www.vnpayment.vn
2. Đăng ký Merchant Account
3. Chờ phê duyệt từ VNPay
4. Nhận `TMN_CODE` và `HASH_SECRET_KEY`

### 2. Cấu Hình Settings

Sửa [ecom/settings.py](ecom/settings.py):

```python
# VNPay Configuration
VNPAY_TMN_CODE = 'your-tmn-code'  # VD: '2QXYZ123'
VNPAY_HASH_SECRET_KEY = 'your-hash-secret'  # VD: 'XXXXXXXXXXXXX'

# Sandbox (phát triển)
VNPAY_PAYMENT_URL = 'https://sandbox.vnpayment.vn/paygate'
VNPAY_RETURN_URL = 'http://localhost:8000/orders/payment-return/'

# Production (sản xuất)
# VNPAY_PAYMENT_URL = 'https://pay.vnpayment.vn/vpcpay.html'
# VNPAY_RETURN_URL = 'https://yourdomain.com/orders/payment-return/'
```

### 3. URL Thanh Toán

```
Trang Thanh Toán: http://localhost:8000/orders/checkout/
- Chọn địa chỉ giao hàng
- Xem tổng tiền
- Nhấp "Thanh Toán VNPay"

Gọi: orders.views.vnpay_payment()
- Tạo inputData với thông tin thanh toán
- Tính HMAC-SHA512 chữ ký bảo mật
- Chuyển hướng đến VNPay
```

### 4. Xử Lý Callback

```
URL Return: http://localhost:8000/orders/payment-return/
VNPay gửi response với vnp_ResponseCode:
- '00' → Thành công → Tạo Order + Payment
- Khác → Thất bại → Quay lại checkout
```

### 5. Test VNPay Sandbox

**Thẻ Tín Dụng Test:**

```
Số thẻ: 4111111111111111
CVV: 123
Ngày hết hạn: 12/25
OTP: 123456 (bất kỳ 6 số)
```

---

## 🔌 API & Serializers

### API Endpoints

#### **Sản Phẩm**

```
GET /api/products/              # Danh sách sản phẩm
GET /api/products/<id>/          # Chi tiết sản phẩm
GET /api/categories/             # Danh sách danh mục
GET /api/variants/<id>/          # Chi tiết biến thể
```

#### **Giỏ Hàng**

```
GET    /accounts/cart/            # Xem giỏ hàng
POST   /accounts/add-to-cart/     # Thêm vào giỏ
DELETE /accounts/remove-from-cart/ # Xóa khỏi giỏ
POST   /accounts/update-cart/      # Cập nhật số lượng
```

#### **Đơn Hàng**

```
GET /orders/                       # Danh sách đơn hàng
GET /orders/<order_id>/            # Chi tiết đơn hàng
POST /orders/checkout/             # Tạo đơn hàng mới
```

### Serializers

File: [products/serializers.py](products/serializers.py)

```python
# Ví dụ
class VariantSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.product_name')
    color_name = serializers.CharField(source='color.color_name')
    size_name = serializers.CharField(source='size.size_name')

    class Meta:
        model = Variant
        fields = ['uid', 'sku', 'price', 'stock', 'color_name', 'size_name']
```

---

## 📌 Những Điều Cần Lưu Ý

### 1. **UUID Primary Keys**

Model `BaseModel` cung cấp `uid` (UUID) làm primary key và `created_at` timestamp:

```python
from base.models import BaseModel

class MyModel(BaseModel):
    name = models.CharField(max_length=100)
    # uid và created_at tự động được thêm
```

### 2. **Slug Tự Động**

Các model Product, Category tự động slugify tên:

```python
# Tự động trong save()
product.product_name = "Áo Phông Nam"
# product.slug = "ao-phong-nam"
```

### 3. **Session-Based Cart & Coupons**

Cơ chế lưu trữ:

- `request.session['cart_id']` → Session cart
- `request.session['coupon_ids']` → List mã giảm giá
- Tự động merge khi user đăng nhập

### 4. **Middleware: ClearCouponOnLeaveMiddleware**

File: [accounts/middleware.py](accounts/middleware.py)

Xóa `coupon_ids` khi rời khỏi cart-related views:

```python
safe_view_names = ['checkout', 'cart', 'payment-return']
# Thêm tên view mới nếu tạo route cart khác
```

### 5. **Giá Sản Phẩm Theo Biến Thể**

```python
# Lấy giá sản phẩm theo size
product.get_product_price_by_size('M')
# = original_price + size_variant.price
```

### 6. **Email Activation**

Signal tự động tạo Profile và gửi email:

```python
# Khi User.objects.create_user() được gọi
# → Profile được tạo + email xác thực được gửi
```

### 7. **Bảo Mật**

⚠️ **TRƯỚC KHI DEPLOY:**

- Đổi `SECRET_KEY` trong settings
- Thiết lập `DEBUG = False`
- Cấu hình HTTPS
- Sử dụng biến môi trường (.env) cho mật khẩu
- Thay đổi mật khẩu admin mặc định

```python
# Sử dụng python-dotenv
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD')
```

---

## 🐛 Khắc Phục Sự Cố

### Lỗi: "ModuleNotFoundError: No module named 'django'"

```bash
pip install django==5.2.7
```

### Lỗi: "INSTALLED_APPS not found"

Đảm bảo thêm app vào `INSTALLED_APPS` trong [ecom/settings.py](ecom/settings.py):

```python
INSTALLED_APPS = [
    ...
    'products',
    'accounts',
    'orders',
    'home',
]
```

### Lỗi: "No such table: products_product"

```bash
# Chạy migrations
python manage.py migrate
```

### Lỗi: "Email không được gửi"

Kiểm tra cấu hình SMTP trong [ecom/settings.py](ecom/settings.py):

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# Ghi email ra console (dev)

# Hoặc dùng SMTP thực
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'app-password'  # Không phải mật khẩu Gmail
```

### Lỗi: "CSRF Token mismatch"

Đảm bảo form có `{% csrf_token %}`:

```html
<form method="POST">
  {% csrf_token %}
  <!-- form fields -->
</form>
```

### Lỗi: "VNPay: Invalid amount"

Đảm bảo số tiền nhân với 100:

```python
# ✓ Đúng
"vnp_Amount": str(int(total_amount) * 100)

# ✗ Sai
"vnp_Amount": str(total_amount)
```

### Lỗi: "Static files not found"

```bash
# Thu thập file tĩnh
python manage.py collectstatic --noinput

# Hoặc debug mode
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'public/static')]
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

---

## 📚 Tài Liệu Tham Khảo

- **Django Documentation**: https://docs.djangoproject.com/en/5.2/
- **VNPay Integration**: https://vnpayment.vn/
- **Django Allauth**: https://django-allauth.readthedocs.io/
- **Jazzmin Admin**: https://django-jazzmin.readthedocs.io/

---

## 📝 Logs & Debugging

### Enable Django Debug Toolbar

```bash
pip install django-debug-toolbar
```

Thêm vào `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'debug_toolbar',
]
```

Thêm vào `MIDDLEWARE`:

```python
MIDDLEWARE = [
    ...
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]
```

### View Django Logs

```python
import logging
logger = logging.getLogger(__name__)

logger.debug('Debug message')
logger.info('Info message')
logger.warning('Warning message')
logger.error('Error message')
```

---

## 🤝 Đóng Góp & Hỗ Trợ

Nếu gặp vấn đề:

1. Kiểm tra lại các bước cài đặt
2. Xem phần "Khắc Phục Sự Cố"
3. Xem logs Django (`python manage.py runserver` output)
4. Liên hệ nhóm phát triển

---

## 📄 License

Dự án này được phát triển cho mục đích học tập. Vui lòng tuân thủ các yêu cầu pháp lý cục bộ khi deploy.

---

## 👨‍💻 Thông Tin Dự Án

- **Phiên bản Django**: 5.2.7
- **Python**: 3.9+
- **Cơ sở dữ liệu**: MySQL 5.7+ / MariaDB
- **Thanh toán**: VNPay (Sandbox + Production)
- **Quản trị**: Jazzmin Admin
- **Xác thực**: Django Allauth (Email, Google, Facebook, GitHub)
- **REST API**: Django REST Framework + JWT

---

**Chúc bạn phát triển thành công! 🚀**

Cập nhật lần cuối: Tháng 12, 2025
