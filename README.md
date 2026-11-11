# Django E-Commerce (Urban Vibe)

Ứng dụng web thương mại điện tử xây dựng bằng **Django 5.2**, **Django REST Framework** và **MySQL / SQLite**, hỗ trợ quản lý sản phẩm theo biến thể, giỏ hàng, mã giảm giá, thanh toán COD / VNPay và quản lý đơn hàng.

## Tính Năng Chính

- **Sản phẩm & Biến thể (`products`)**: Danh mục, slug tự động, biến thể màu sắc/kích cỡ với SKU tự động, tồn kho, đánh giá sản phẩm theo đơn hàng.
- **Tài khoản & Giỏ hàng (`accounts`)**: Đăng ký/đăng nhập (kèm xác thực email và OAuth qua `django-allauth`), sổ địa chỉ giao hàng, giỏ hàng theo người dùng, áp dụng mã giảm giá theo loại (`amount`, `percent`, `shipping`) và theo danh mục.
- **Đặt hàng & Thanh toán (`orders`)**: Hỗ trợ mua ngay (`buy-now`) hoặc thanh toán từ giỏ hàng qua **COD** hoặc **VNPay** (tạo đơn `Pending` trước khi chuyển hướng, xác thực chữ ký `HMAC-SHA512`, kiểm tra số tiền và trừ tồn kho nguyên tử trong `transaction.atomic()`), hủy đơn hoàn tồn kho.
- **REST API (`rest_framework` + JWT)**:
  - `POST /api/token/` — Lấy JWT access/refresh token
  - `POST /api/token/refresh/` — Làm mới JWT access token
  - `GET /api/products/` — Danh sách sản phẩm và biến thể
  - `GET /api/cart/` — Xem giỏ hàng hiện tại (yêu cầu JWT)
  - `POST /api/cart/add/` — Thêm biến thể vào giỏ hàng (yêu cầu JWT)
- **Admin Dashboard**: Tùy biến với `django-jazzmin`.

## Yêu Cầu Hệ Thống

- Python 3.10+ (đã kiểm thử với Python 3.12 / Django 5.2.7)
- SQLite (mặc định khi chạy local/test) hoặc MySQL 5.7+ / MariaDB

## Cài Đặt & Chạy Local

### 1. Clone repository

```bash
git clone https://github.com/Tuandayneee/django-ecom-project.git
cd django-ecom-project
```

### 2. Tạo virtual environment & cài dependencies

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Cấu hình biến môi trường

Sao chép file mẫu `.env.example` thành `.env` và điền thông tin phù hợp:

```bash
cp .env.example .env
```

Mặc định dự án dùng SQLite (`DB_ENGINE=sqlite`) và in email xác thực ra console nếu chưa cấu hình SMTP, giúp chạy thử và kiểm thử nhanh chóng. Để dùng MySQL, đặt `DB_ENGINE=mysql` và điền `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` trong `.env`.

### 4. Khởi tạo database & chạy server

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Truy cập:
- Trang chủ: `http://127.0.0.1:8000/`
- Trang quản trị: `http://127.0.0.1:8000/admin/`

## Chạy Automated Tests

```bash
python manage.py check
python manage.py test -v 2
```

## Cấu Trúc Thư Mục

```text
├── accounts/           # Tài khoản, hồ sơ, địa chỉ, giỏ hàng & Cart API
├── base/               # BaseModel (UUID PK) & helper gửi email
├── ecom/               # Settings, root URLs, context processors
├── home/               # Trang chủ, giới thiệu, liên hệ
├── orders/             # Checkout, COD, tích hợp VNPay & quản lý đơn hàng
├── products/           # Sản phẩm, danh mục, biến thể, coupon, đánh giá
├── public/static/      # Static assets (CSS, JS, images, fonts)
├── templates/          # Django HTML templates
├── .env.example        # Mẫu biến môi trường
├── requirements.txt    # Danh sách thư viện Python
└── manage.py
```

## Routes Chính

- `/` — Trang chủ, tìm kiếm và lọc theo danh mục
- `/about/`, `/contact/` — Giới thiệu và liên hệ
- `/product/<slug>/` — Chi tiết sản phẩm
- `/product/submit_review/<order_id>/<product_id>/` — Đánh giá sản phẩm
- `/accounts/login/`, `/accounts/register/`, `/accounts/logout/` — Xác thực tài khoản
- `/accounts/cart/` — Giỏ hàng và áp dụng coupon
- `/accounts/profile/`, `/accounts/profile/orders/`, `/accounts/profile/addresses/` — Hồ sơ, đơn hàng và sổ địa chỉ
- `/orders/checkout/` — Thanh toán (COD / VNPay)
- `/orders/payment/vnpay/`, `/orders/payment/return/` — Luồng thanh toán & callback VNPay
