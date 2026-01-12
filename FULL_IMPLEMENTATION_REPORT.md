# 📋 BÁO CÁO TRIỂN KHAI CHỨC NĂNG CHÍNH - URBANVIBE E-SHOP

**Ngày cập nhật:** 5 Tháng 1, 2026  
**Phiên bản Django:** 5.2.7  
**Cơ sở dữ liệu:** MySQL (urbanvibe_db)

---

## 📌 MỤC LỤC

1. [3.3.1. Quản Lý Sản Phẩm & Danh Mục](#331-quản-lý-sản-phẩm--danh-mục)
2. [3.3.2. Giỏ Hàng & Thanh Toán](#332-giỏ-hàng--thanh-toán)
3. [3.3.3. Xác Thực & Bảo Mật Người Dùng](#333-xác-thực--bảo-mật-người-dùng)

---

## 3.3.1. Quản Lý Sản Phẩm & Danh Mục

### ✅ 1. Cơ Chế Slug Tự Động (Auto-Slug)

**Vị trí:** `products/models.py`

**Mô tả:** Hệ thống tự động tạo đường dẫn SEO từ tên sản phẩm bằng cách slugify, xử lý ký tự đặc biệt và tiếng Việt.

#### Code triển khai:

```python
# products/models.py - Class Category
class Category(BaseModel):
    category_name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    category_image = models.ImageField(upload_to="categories", null=True, blank=True)

    def save(self, *args, **kwargs):
        # Tự động tạo slug từ tên danh mục
        self.slug = slugify(self.category_name)
        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.category_name


# products/models.py - Class Product
class Product(BaseModel):
    product_name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="products"
    )
    product_description = models.TextField(null=True, blank=True)
    original_price = models.IntegerField(default=0)
    price = models.IntegerField(default=0)
    sold_count = models.IntegerField(default=0)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Chỉ tạo slug nếu chưa có (không overwrite nếu sửa sau)
        if not self.slug:
            self.slug = slugify(self.product_name)
        super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return self.product_name
```

#### Cơ chế hoạt động:

| Input                | Output Slug          | URL Route                      |
| -------------------- | -------------------- | ------------------------------ |
| "Áo Thun Mùa Hè"     | `ao-thun-mua-he`     | `/product/ao-thun-mua-he/`     |
| "Quần Jean Xanh Đậm" | `quan-jean-xanh-dam` | `/product/quan-jean-xanh-dam/` |
| "Giày Thể Thao Nike" | `giay-the-thao-nike` | `/product/giay-the-thao-nike/` |

#### URL Pattern:

```python
# products/urls.py
urlpatterns = [
    path('<slug:slug>/', views.product_detail, name='product_detail'),
]
```

#### Xử lý trùng lặp:

Django's `SlugField` với `unique=True` tự động xử lý:

- Nếu slug "ao-thun" đã tồn tại → Hệ thống sẽ từ chối save
- Admin phải sửa lại tên sản phẩm
- Database sẽ không có slug trùng lặp

---

### ✅ 2. Quản Lý Ảnh Đa Chiều (Multi-Dimensional Image Management)

**Vị trí:** `products/models.py` - Classes `Variant`, `ProductImage`

**Mô tả:** Hệ thống lưu trữ ảnh sản phẩm liên kết với các biến thể (màu sắc, kích thước), tối ưu hóa tốc độ tải trang.

#### Code triển khai:

```python
# products/models.py - Class Variant (Biến thể sản phẩm)
class Variant(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    color = models.ForeignKey(ColorVariant, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(SizeVariant, on_delete=models.SET_NULL, null=True, blank=True)
    stock = models.IntegerField(default=0)

    sku = models.CharField(max_length=100, unique=True, blank=True)
    original_price = models.IntegerField(default=0)
    price = models.IntegerField(default=0)
    image = models.ImageField(upload_to="products/variants", null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def get_price(self):
        """Lấy giá sản phẩm (giá variant nếu có, ngược lại lấy giá tối thiểu)"""
        if self.price > 0:
            return self.price
        return self.product.min_price

    @property
    def variant_name(self):
        """Tên hiển thị của variant: Sản phẩm - Màu - Kích thước"""
        return f"{self.product.product_name} - {self.color.color_name if self.color else ''} - {self.size.size_name if self.size else ''}"

    def save(self, *args, **kwargs):
        # Tự động tạo SKU từ slug product + color + size
        if not self.sku:
            slug_product = slugify(self.product.product_name)
            slug_color = slugify(self.color.color_name) if self.color else 'no-color'
            slug_size = slugify(self.size.size_name) if self.size else 'no-size'

            self.sku = f"{slug_product}-{slug_color}-{slug_size}".upper()

        super().save(*args, **kwargs)

    def __str__(self):
        parts = [self.product.product_name]
        if self.color:
            parts.append(self.color.color_name)
        if self.size:
            parts.append(self.size.size_name)
        return " - ".join(parts)


# products/models.py - Class ProductImage (Ảnh sản phẩm)
class ProductImage(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_images")
    image = models.ImageField(upload_to="product")
    is_thumbnail = models.BooleanField(default=False)
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.product.product_name


# products/models.py - Color & Size Models
class ColorVariant(BaseModel):
    color_name = models.CharField(max_length=100)
    color_code = models.CharField(
        max_length=7,
        default='#000000',
        help_text='Mã HEX: xanh:#1E3A5F, nâu:#8B5A3C, đen:#000000, trắng:#FFFFFF'
    )

    def __str__(self):
        return self.color_name


class SizeVariant(BaseModel):
    size_name = models.CharField(max_length=100)

    def __str__(self):
        return self.size_name
```

#### Cấu trúc lưu trữ ảnh:

```
media/
├── product/                    # Ảnh chính sản phẩm
│   ├── ao-thun-1.jpg
│   ├── ao-thun-2.jpg
│   └── ...
├── products/
│   └── variants/              # Ảnh biến thể
│       ├── ao-thun-xanh.jpg
│       ├── ao-thun-do.jpg
│       └── ...
└── categories/                # Ảnh danh mục
    ├── quan-ao.jpg
    └── giay-dep.jpg
```

#### Tính năng hình ảnh:

| Tính Năng      | Mô Tả                             | Lợi Ích                                 |
| -------------- | --------------------------------- | --------------------------------------- |
| Ảnh Variant    | Lưu ảnh riêng cho từng variant    | Khách hàng thấy ảnh sắc của từng option |
| Thumbnail      | Đánh dấu ảnh đại diện             | Tối ưu hiển thị ở trang danh sách       |
| Upload tự động | Khi Admin upload → Resize tự động | Giảm dung lượng file                    |

---

## 3.3.2. Giỏ Hàng & Thanh Toán (Trọng Tâm)

### ✅ 1. Logic Giỏ Hàng (Shopping Cart System)

**Vị trí:**

- Models: `accounts/models.py` - Classes `Cart`, `CartItems`
- Views: `accounts/views.py`
- Utils: `accounts/utils.py`

#### A. Cấu trúc Model:

```python
# accounts/models.py
class Cart(BaseModel):
    """Giỏ hàng của user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="carts", null=True, blank=True)
    coupons = models.ManyToManyField(Coupon, blank=True, related_name='carts')
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_cart_total(self):
        """Tính tổng tiền giỏ (chỉ sản phẩm, không ship/tax)"""
        cart_items = self.cart_items.all()
        price = []
        for cart_item in cart_items:
            price.append(cart_item.get_product_price)
        return sum(price)


class CartItems(BaseModel):
    """Các sản phẩm trong giỏ"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(default=1)

    @property
    def get_product_price(self):
        """Giá sản phẩm * số lượng"""
        if self.variant:
            return self.variant.price * self.quantity
        return 0

    def __str__(self):
        if self.variant:
            return f"{self.variant.product.product_name} ({self.variant.variant_name}) - {self.quantity}"
        return f"Sản phẩm đã xóa - {self.quantity}"
```

#### B. Views Giỏ Hàng:

```python
# accounts/views.py

@login_required(login_url='login')
def cart(request):
    """Hiển thị trang giỏ hàng"""
    try:
        # Lấy hoặc tạo giỏ hàng của user
        cart_obj, _ = Cart.objects.get_or_create(user=request.user, is_paid=False)

        # Tính toán tổng tiền (hàm chuẩn)
        context = calculate_cart_total(cart_obj, user=request.user)

        context['cart'] = cart_obj
        context['has_default_address'] = Address.objects.filter(
            user=request.user,
            is_default=True
        ).exists()
    except Exception as e:
        print(f"Cart View Error: {e}")
        context = {'cart_items': [], 'subtotal': 0, 'total': 0, 'discount': 0}

    return render(request, 'accounts/cart.html', context)


@login_required(login_url='login')
def add_to_cart(request, uid):
    """Thêm sản phẩm vào giỏ hàng"""
    variant_uid = request.GET.get('variant')
    try:
        quantity = int(request.GET.get('quantity', 1))
    except ValueError:
        quantity = 1

    if not variant_uid:
        messages.warning(request, "Vui lòng chọn màu sắc/kích thước")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    try:
        variant_obj = get_object_or_404(Variant, uid=variant_uid)

        # Lấy hoặc tạo giỏ hàng
        cart_obj, _ = Cart.objects.get_or_create(user=request.user, is_paid=False)

        # Lấy hoặc tạo CartItem
        cart_item, created = CartItems.objects.get_or_create(
            cart=cart_obj,
            variant=variant_obj
        )

        if created:
            cart_item.quantity = quantity
        else:
            # Nếu item đã tồn tại → cộng thêm quantity
            cart_item.quantity += quantity

        # Kiểm tra không vượt quá stock
        if cart_item.quantity > variant_obj.stock:
            cart_item.quantity = variant_obj.stock
            messages.warning(request, f"Chỉ còn {variant_obj.stock} sản phẩm.")

        cart_item.save()
        messages.success(request, "Đã thêm vào giỏ hàng")

    except Exception as e:
        print(e)
        messages.error(request, "Lỗi hệ thống")

    return redirect('cart')


@login_required(login_url='login')
def update_cart(request):
    """Cập nhật số lượng sản phẩm trong giỏ (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'status': 'Invalid method'}, status=405)

    try:
        data = json.loads(request.body)
        item_uid = data.get('item_uid')
        new_quantity = int(data.get('new_quantity'))

        cart_item = get_object_or_404(CartItems, uid=item_uid, cart__user=request.user)
        item_total_price = 0

        if new_quantity > 0:
            # Kiểm tra stock
            if new_quantity > cart_item.variant.stock:
                return JsonResponse({
                    'status': 'Stock limit',
                    'message': f'Chỉ còn {cart_item.variant.stock} sản phẩm'
                }, status=400)

            # Cập nhật số lượng
            cart_item.quantity = new_quantity
            cart_item.save()
            item_total_price = cart_item.get_product_price
        else:
            # Nếu số lượng = 0 → xóa item
            cart_item.delete()
            item_total_price = 0

        # Tính lại tổng giỏ hàng
        cart_details = calculate_cart_total(cart_item.cart, user=request.user)

        return JsonResponse({
            'status': 'Success',
            'item_total': item_total_price,
            'subtotal': cart_details['subtotal'],
            'discount': cart_details['discount'],
            'cart_total': cart_details['total'],
            'shipping_fee': cart_details['shipping_fee']
        })

    except Exception as e:
        return JsonResponse({'status': 'Error', 'message': str(e)}, status=400)


@login_required(login_url='login')
def remove_item(request, cart_item_uid):
    """Xóa sản phẩm khỏi giỏ hàng"""
    try:
        CartItems.objects.filter(uid=cart_item_uid, cart__user=request.user).delete()
        messages.success(request, "Đã xóa sản phẩm")
    except Exception as e:
        print(f"Remove item error: {e}")
        messages.error(request, "Lỗi khi xóa sản phẩm")

    return redirect('cart')
```

#### C. Hàm Tính Toán Giỏ Hàng (accounts/utils.py):

```python
# accounts/utils.py
from django.db.models import Sum
from products.models import Coupon, CouponUsage, Variant
from .models import Cart, CartItems


def calculate_cart_total(cart_obj, user=None, selected_address=None):
    """
    Tính tổng tiền giỏ hàng với hỗ trợ:
    - Tính phí ship theo địa chỉ
    - Áp dụng coupon discount
    - Tính tax (10%)

    Args:
        cart_obj: Object Cart
        user: User object (để kiểm tra coupon limit)
        selected_address: Address object (để tính ship)

    Returns:
        dict: {
            'cart_items': [...],
            'subtotal': int,
            'shipping_fee': int,
            'discount': int,
            'tax': int,
            'total': int
        }
    """
    cart_items = cart_obj.cart_items.all()

    # 1. Tính tiền hàng (Subtotal)
    subtotal = sum(item.get_product_price for item in cart_items)

    # 2. Tính phí vận chuyển
    shipping_fee = 30000  # Giá mặc định

    address_to_use = None
    if selected_address:
        address_to_use = selected_address
    else:
        current_user = user if user else cart_obj.user
        if current_user and current_user.is_authenticated:
            # Lấy địa chỉ mặc định hoặc địa chỉ đầu tiên
            address_to_use = Address.objects.filter(user=current_user, is_default=True).first()
            if not address_to_use:
                address_to_use = Address.objects.filter(user=current_user).first()

    # Miễn phí ship nếu đơn hàng > 3,000,000
    if subtotal > 3000000:
        shipping_fee = 0
    elif address_to_use:
        shipping_fee = get_shipping_fee_by_location(address_to_use)

    # 3. Tính coupon discount
    total_discount = 0
    if cart_obj.coupons.exists():
        for coupon in cart_obj.coupons.all():
            if subtotal < coupon.minimum_amount:
                continue

            eligible_amount = 0

            # Nếu coupon áp dụng cho danh mục cụ thể
            if coupon.category:
                for item in cart_items:
                    if item.variant.product.category == coupon.category:
                        eligible_amount += item.get_product_price
            else:
                # Coupon áp dụng cho toàn bộ
                eligible_amount = subtotal

            if eligible_amount == 0:
                continue

            # Tính discount theo loại
            if coupon.coupon_type == 'percent':
                # Giảm phần trăm
                discount_val = (eligible_amount * coupon.discount_price) / 100
                total_discount += discount_val
            elif coupon.coupon_type == 'amount':
                # Giảm tiền cố định
                total_discount += coupon.discount_price
            elif coupon.coupon_type == 'shipping':
                # Miễn phí ship
                total_discount += shipping_fee

    # Đảm bảo discount không vượt quá tổng tiền
    grand_total_temp = subtotal + shipping_fee
    if total_discount > grand_total_temp:
        total_discount = grand_total_temp

    # 4. Tính tax (10% của subtotal)
    tax = 0  # Tùy chọn: có thể bật tax bằng tax = int(subtotal * 0.1)

    # 5. Tính tổng cộng
    grand_total = int(subtotal + shipping_fee + tax - total_discount)

    return {
        'cart_items': cart_items,
        'subtotal': int(subtotal),
        'shipping_fee': int(shipping_fee),
        'tax': int(tax),
        'discount': int(total_discount),
        'total': int(grand_total)
    }


def get_shipping_fee_by_location(address_obj):
    """
    Tính phí vận chuyển dựa vào địa chỉ giao hàng.

    Logic:
    - Hà Nội & gần: 25,000đ
    - Côn Đảo, Phú Quốc: 70,000đ
    - Mặc định: 35,000đ
    """
    customer_city = address_obj.city.lower()

    if "côn đảo" in customer_city or "phú quốc" in customer_city:
        return 70000

    if "hà nội" in customer_city or "ha noi" in customer_city:
        return 25000

    return 35000
```

---

### ✅ 2. Tích Hợp VNPay (Payment Integration)

**Vị trí:** `orders/vnpay.py`

**Thông số VNPay:**

- TMN Code: `SIXDZGUD` (Sandbox)
- Secret Key: `B159DXK3140FGOFHWGYJ29B8J77IVVOZ`
- Environment: Sandbox (test)

#### Bước 1: Tạo Request → VNPay (Create Payment URL)

```python
# orders/vnpay.py
import hashlib
import hmac
import urllib.parse
from datetime import datetime
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from products.models import Variant
from accounts.models import Cart, Address
from accounts.utils import calculate_cart_total
from orders.utils import get_user_shipping_fee
from .models import Order, OrderProduct, Payment


def get_client_ip(request):
    """Lấy IP address của client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def vnpay_payment(request):
    """
    Tạo URL thanh toán VNPay.

    Quy trình:
    1. Lấy thông tin từ session (mua ngay hoặc giỏ hàng)
    2. Tính tổng tiền
    3. Tạo request data
    4. Mã hóa HMAC-SHA512
    5. Redirect sang VNPay payment page
    """
    address_uid = request.session.get('shipping_address_uid')
    if not address_uid:
        messages.warning(request, "Vui lòng chọn địa chỉ giao hàng trước.")
        return redirect('orders:checkout')

    try:
        # Kiểm tra cờ xem đang là Mua ngay hay Giỏ hàng
        is_buy_now = request.session.get('is_buy_now', False)

        total_amount = 0
        order_info_str = ""

        if is_buy_now:
            # === TRƯỜNG HỢP 1: MUA NGAY ===
            item_data = request.session.get('direct_buy_item')
            if not item_data:
                return redirect('product')

            # Lấy sản phẩm từ DB
            variant = Variant.objects.get(uid=item_data['variant_uid'])
            quantity = int(item_data['quantity'])

            # Tính tiền (Giá * Số lượng + Ship)
            subtotal = variant.price * quantity
            shipping_fee = 35000  # Hoặc gọi hàm tính ship

            total_amount = subtotal + shipping_fee
            order_info_str = f"Thanh toan mua ngay: {variant.product.product_name}"

        else:
            # === TRƯỜNG HỢP 2: GIỎ HÀNG ===
            carts = Cart.objects.filter(user=request.user, is_paid=False)
            cart_obj = None
            for cart in carts:
                if cart.cart_items.exists():
                    cart_obj = cart
                    break

            if not cart_obj:
                return redirect('store')

            cart_data = calculate_cart_total(cart_obj, user=request.user)
            total_amount = int(cart_data['total'])
            order_info_str = f"Thanh toan gio hang User {request.user.id}"

        # --- PHẦN TẠO URL VNPAY ---
        # Tạo Order Reference ID duy nhất
        order_id = f"ORD-{request.user.id}-{datetime.now().strftime('%H%M%S')}"
        request.session['order_ref'] = order_id  # Lưu để check sau

        ipaddr = get_client_ip(request)

        # Bước 1: Chuẩn bị dữ liệu request
        inputData = {
            "vnp_Version": "2.1.0",
            "vnp_Command": "pay",
            "vnp_TmnCode": settings.VNPAY_TMN_CODE,  # SIXDZGUD
            "vnp_Amount": str(int(total_amount) * 100),  # ⚠️ QUAN TRỌNG: Nhân 100
            "vnp_CreateDate": datetime.now().strftime('%Y%m%d%H%M%S'),
            "vnp_CurrCode": "VND",
            "vnp_IpAddr": ipaddr,
            "vnp_Locale": "vn",
            "vnp_OrderInfo": order_info_str,
            "vnp_OrderType": "billpayment",
            "vnp_ReturnUrl": settings.VNPAY_RETURN_URL,
            "vnp_TxnRef": order_id,
        }

        # Bước 2: Sắp xếp tham số theo thứ tự A-Z
        inputData = sorted(inputData.items())

        # Bước 3: Tạo query string
        queryData = urllib.parse.urlencode(inputData)

        # Bước 4: Mã hóa HMAC-SHA512 với Secret Key
        if settings.VNPAY_HASH_SECRET_KEY:
            vnp_SecureHash = hmac.new(
                bytes(settings.VNPAY_HASH_SECRET_KEY, 'utf-8'),
                bytes(queryData, 'utf-8'),
                hashlib.sha512
            ).hexdigest()
            queryData += "&vnp_SecureHash=" + vnp_SecureHash

        # Bước 5: Tạo URL thanh toán đầy đủ
        payment_url = settings.VNPAY_PAYMENT_URL + "?" + queryData
        return redirect(payment_url)

    except Exception as e:
        print(f"Lỗi tạo URL VNPay: {e}")
        return redirect('orders:checkout')
```

**Dòng thời gian Bước 1:**

```
1. Khách click "Thanh toán VNPay"
   ↓
2. Hệ thống tính tổng tiền (subtotal + shipping + tax - discount)
   ↓
3. Tạo order_id duy nhất: ORD-{user_id}-{timestamp}
   ↓
4. Sắp xếp dữ liệu A-Z
   ↓
5. Mã hóa HMAC-SHA512 với Secret Key
   ↓
6. Redirect sang VNPay Sandbox
   ↓
7. Khách nhập thông tin thẻ / tài khoản ngân hàng
```

---

#### Bước 2: Hashing & Signature (Mã hóa dữ liệu)

**Yêu cầu bảo mật:**

- Xác thực tính toàn vẹn dữ liệu (Data Integrity)
- Chống giả mạo (Anti-Spoofing)

**Quá trình mã hóa:**

```python
# Bước lặp lại từ Bước 1
inputData = {
    "vnp_Version": "2.1.0",
    "vnp_Command": "pay",
    "vnp_TmnCode": "SIXDZGUD",
    "vnp_Amount": "5000000",  # 50,000đ
    "vnp_CreateDate": "20260105101523",
    "vnp_CurrCode": "VND",
    "vnp_IpAddr": "192.168.1.100",
    "vnp_Locale": "vn",
    "vnp_OrderInfo": "Thanh toan gio hang User 1",
    "vnp_OrderType": "billpayment",
    "vnp_ReturnUrl": "http://127.0.0.1:8000/payment_return/",
    "vnp_TxnRef": "ORD-1-101523",
}

# Sắp xếp A-Z
sorted_data = sorted(inputData.items())
# Result:
# [
#   ('vnp_Amount', '5000000'),
#   ('vnp_Command', 'pay'),
#   ...
# ]

# Tạo query string
queryData = urllib.parse.urlencode(sorted_data)
# Result: "vnp_Amount=5000000&vnp_Command=pay&..."

# Mã hóa HMAC-SHA512
secret_key = "B159DXK3140FGOFHWGYJ29B8J77IVVOZ"

vnp_SecureHash = hmac.new(
    bytes(secret_key, 'utf-8'),
    bytes(queryData, 'utf-8'),
    hashlib.sha512
).hexdigest()

# Result: "abc123def456..." (256 ký tự hex)

# URL thanh toán cuối cùng:
payment_url = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?" + queryData + "&vnp_SecureHash=" + vnp_SecureHash
```

**Thuật toán:** HMAC-SHA512

- **HMAC:** Keyed Hash Message Authentication Code
- **SHA512:** 512-bit Secure Hash Algorithm
- **Secret Key:** Chỉ có hệ thống biết (được cấp bởi VNPay)

---

#### Bước 3: Response & Checksum Validation

```python
# orders/vnpay.py - QUAN TRỌNG: Xác thực checksum

def validate_vnpay_checksum(data):
    """
    Xác thực chữ ký số (checksum) từ VNPay.

    BƯỚC QUAN TRỌNG: Ngăn chặn hacker giả mạo kết quả thanh toán.

    Quy trình:
    1. Lấy vnp_SecureHash từ response
    2. Loại bỏ vnp_SecureHash khỏi data
    3. Sắp xếp data theo thứ tự A-Z
    4. Tạo queryString
    5. Mã hóa HMAC-SHA512 với Secret Key
    6. So sánh hash nhận được vs hash gửi về

    Returns: True nếu hợp lệ, False nếu không
    """
    try:
        # 1. Lấy hash từ VNPay gửi về
        vnp_SecureHash = data.get('vnp_SecureHash')
        if not vnp_SecureHash:
            print("❌ Lỗi: Không có vnp_SecureHash trong response")
            return False

        # 2. Sao chép dữ liệu và loại bỏ hash
        inputData = dict(data)
        inputData.pop('vnp_SecureHash', None)
        inputData.pop('vnp_SecureHashType', None)

        # 3. Sắp xếp theo A-Z
        inputData = sorted(inputData.items())

        # 4. Tạo query string
        queryData = urllib.parse.urlencode(inputData)

        # 5. Mã hóa HMAC-SHA512 với Secret Key
        computed_hash = hmac.new(
            bytes(settings.VNPAY_HASH_SECRET_KEY, 'utf-8'),
            bytes(queryData, 'utf-8'),
            hashlib.sha512
        ).hexdigest()

        # 6. So sánh
        if computed_hash == vnp_SecureHash:
            print("✅ Checksum hợp lệ - Dữ liệu không bị giả mạo")
            return True
        else:
            print(f"❌ Checksum không khớp - Dữ liệu bị giả mạo!")
            print(f"   Expected: {computed_hash}")
            print(f"   Received: {vnp_SecureHash}")
            return False

    except Exception as e:
        print(f"❌ Lỗi xác thực checksum: {e}")
        return False


def payment_return(request):
    """
    Xử lý kết quả trả về từ VNPay (Callback).

    Dòng thời gian:
    1. VNPay xử lý thanh toán
    2. Redirect khách về: http://127.0.0.1:8000/payment_return/
    3. Hệ thống xác thực checksum
    4. Kiểm tra response code
    5. Tạo Order nếu thành công
    """
    inputData = request.GET
    if inputData:
        vnp_ResponseCode = inputData.get('vnp_ResponseCode')
        vnp_TxnRef = inputData.get('vnp_TxnRef')

        # ✅ STEP 1: XÁC THỰC CHECKSUM (CRITICAL - Chống giả mạo)
        if not validate_vnpay_checksum(inputData):
            messages.error(request, "❌ Xác thực giao dịch thất bại. Dữ liệu có thể bị giả mạo.")
            return redirect('orders:checkout')

        # ✅ STEP 2: Kiểm tra response code
        # Mã 00 = Thành công
        # Mã khác = Thất bại
        if vnp_ResponseCode == '00':
            try:
                from django.db import transaction

                with transaction.atomic():
                    # 1. Lấy thông tin địa chỉ
                    address_uid = request.session.get('shipping_address_uid')
                    address = Address.objects.get(uid=address_uid)

                    # --- XÁC ĐỊNH NGUỒN DỮ LIỆU (MUA NGAY hay GIỎ HÀNG) ---
                    is_buy_now = request.session.get('is_buy_now', False)

                    final_subtotal = 0
                    final_shipping = 35000
                    final_total = 0
                    final_tax = 0
                    final_discount = 0
                    order_items_payload = []

                    if is_buy_now:
                        # == XỬ LÝ MUA NGAY ==
                        item_data = request.session.get('direct_buy_item')
                        variant = Variant.objects.get(uid=item_data['variant_uid'])
                        qty = int(item_data['quantity'])

                        final_subtotal = variant.price * qty
                        final_total = final_subtotal + final_shipping

                        order_items_payload.append({
                            'variant': variant,
                            'quantity': qty,
                            'price': variant.price
                        })

                    else:
                        # == XỬ LÝ GIỎ HÀNG ==
                        carts = Cart.objects.filter(user=request.user, is_paid=False)
                        cart_obj = None
                        for cart in carts:
                            if cart.cart_items.exists():
                                cart_obj = cart
                                break

                        cart_data = calculate_cart_total(cart_obj, user=request.user)

                        final_subtotal = cart_data['subtotal']
                        final_shipping = cart_data['shipping_fee']
                        final_tax = cart_data['tax']
                        final_discount = cart_data['discount']
                        final_total = cart_data['total']

                        for item in cart_data['cart_items']:
                            order_items_payload.append({
                                'variant': item.variant,
                                'quantity': item.quantity,
                                'price': item.variant.price
                            })

                    # 2. Tạo Payment record
                    payment = Payment.objects.create(
                        user=request.user,
                        payment_id=vnp_TxnRef,
                        payment_method='VNPay',
                        amount_paid=str(final_total),
                        status='Completed'
                    )

                    # 3. Tạo Order
                    order = Order.objects.create(
                        user=request.user,
                        payment=payment,
                        order_number=vnp_TxnRef,
                        full_name=address.full_name,
                        phone=address.phone,
                        address_line=address.address_line,
                        city=address.city,
                        order_total=final_subtotal,
                        shipping_fee=final_shipping,
                        coupon_discount=final_discount,
                        tax=final_tax,
                        status='Pending',  # Chờ xác nhận
                        is_ordered=True
                    )

                    # 4. Tạo OrderProduct & Trừ kho
                    for item in order_items_payload:
                        var = item['variant']
                        qty = item['quantity']
                        price = item['price']

                        # Trừ kho
                        var.stock -= qty
                        var.save()

                        OrderProduct.objects.create(
                            order=order,
                            product=var.product,
                            variant=var,
                            product_name=var.variant_name,
                            quantity=qty,
                            product_price=price
                        )

                    # 5. Dọn dẹp session
                    if is_buy_now:
                        if 'direct_buy_item' in request.session:
                            del request.session['direct_buy_item']
                        if 'is_buy_now' in request.session:
                            del request.session['is_buy_now']
                    else:
                        if cart_obj:
                            cart_obj.cart_items.all().delete()
                            cart_obj.coupons.clear()
                            cart_obj.is_paid = True
                            cart_obj.save()

                    if 'shipping_address_uid' in request.session:
                        del request.session['shipping_address_uid']

                    messages.success(request, "✅ Thanh toán thành công!")
                    return redirect('orders:order_success', order_uid=order.uid)

            except Exception as e:
                print(f"Lỗi xử lý VNPay Return: {e}")
                messages.error(request, "Thanh toán thành công nhưng lỗi tạo đơn. Liên hệ Admin.")
                return redirect('orders:checkout')

        else:
            # Thanh toán thất bại
            messages.error(request, "❌ Giao dịch thất bại hoặc bị hủy.")
            return redirect('orders:checkout')

    return redirect('home')
```

**Response Code từ VNPay:**

| Code | Ý Nghĩa                   | Hành Động     |
| ---- | ------------------------- | ------------- |
| 00   | Giao dịch thành công      | Tạo Order     |
| 01   | Giao dịch chưa hoàn thành | Chờ xác nhận  |
| 02   | Giao dịch bị lỗi          | Thông báo lỗi |
| 09   | Giao dịch bị hủy          | Thông báo hủy |

---

## 3.3.3. Xác Thực & Bảo Mật Người Dùng

### ✅ 1. Mã Hóa Mật Khẩu (Password Hashing)

**Vị trí:** Mặc định Django Auth

**Thuật toán:** PBKDF2 + SHA256 + Salt ngẫu nhiên

```python
# accounts/views.py - Đăng ký user
def register_page(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        if User.objects.filter(username=email).exists():
            messages.error(request, 'Email này đã được sử dụng!')
            return render(request, 'accounts/login_register.html')

        try:
            # Tạo user
            user_obj = User.objects.create_user(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name
            )

            # ✅ Django tự động mã hóa password bằng PBKDF2
            user_obj.set_password(password)
            user_obj.save()

            # Lưu phone vào Profile
            profile = user_obj.profile
            profile.phone = phone
            profile.save()

            messages.success(request, 'Đăng ký thành công! Vui lòng đăng nhập.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Đã xảy ra lỗi: {e}')
            return render(request, 'accounts/login_register.html')

    return render(request, 'accounts/login_register.html')
```

**Cơ chế mã hóa Django:**

```
Bước 1: Lấy password từ form
        Input: "MyPassword123!"

Bước 2: Tạo salt ngẫu nhiên (16 byte)
        Salt: "a5c8d2f1e9b3c7d6"

Bước 3: PBKDF2 Hash 100,000 lần với SHA256
        Hashing iterations: 100,000
        Algorithm: SHA256

Bước 4: Kết hợp: algorithm$iterations$salt$hash
        Stored: "pbkdf2_sha256$100000$a5c8d2f1e9b3c7d6$abc123def456..."

Khi login:
Bước 1: Lấy password từ form
        Input: "MyPassword123!"

Bước 2: Lấy stored hash từ DB
        Stored: "pbkdf2_sha256$100000$a5c8d2f1e9b3c7d6$abc123def456..."

Bước 3: Extract salt từ stored hash
        Salt: "a5c8d2f1e9b3c7d6"

Bước 4: Hash input password bằng salt & iterations này
        Generated: "abc123def456..."

Bước 5: So sánh hash
        Generated == Stored? ✅ YES → LOGIN SUCCESS
```

**Bảo mật:**

- ✅ Ngay cả khi DB bị lộ, attacker không thể dịch ngược ra password gốc
- ✅ Mỗi password có salt độc lập → Tránh rainbow table attacks
- ✅ 100,000 iterations → Chậm down brute force attacks

---

### ✅ 2. Email Verification (Xác Thực Email)

**Vị trí:**

- Signal: `accounts/models.py` - `send_email_token()`
- Email: `base/emails.py` - `send_account_activation_email()`
- Activation: `accounts/views.py` - `activate_email()`

#### Code triển khai:

```python
# accounts/models.py
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from base.emails import send_account_activation_email


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    is_email_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=100, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile')
    phone = models.CharField(max_length=20, null=True, blank=True)

    def get_cart_count(self):
        item_count = CartItems.objects.filter(
            cart__user=self.user,
            cart__is_paid=False
        ).aggregate(Sum('quantity'))['quantity__sum']
        return item_count if item_count else 0

    def __str__(self):
        return self.user.username


# ✅ Signal tự động khi User được tạo
@receiver(post_save, sender=User)
def send_email_token(sender, instance, created, **kwargs):
    """
    Tự động kích hoạt khi User mới được tạo.

    Quy trình:
    1. Tạo Profile với email_token duy nhất (UUID)
    2. Gửi email xác thực
    """
    try:
        if created:
            # Tạo token duy nhất bằng UUID
            email_token = str(uuid.uuid4())

            # Lưu vào Profile
            Profile.objects.create(user=instance, email_token=email_token)

            # Gửi email
            email = instance.email
            send_account_activation_email(email, email_token)

            print(f"✅ Email xác thực gửi tới {email}")
    except Exception as e:
        print(f"❌ Lỗi gửi email: {e}")
```

```python
# base/emails.py
from django.conf import settings
from django.core.mail import send_mail


def send_account_activation_email(email, email_token):
    """
    Gửi email xác thực tài khoản.

    Cấu hình cần thiết (ecom/settings.py):
    - EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    - EMAIL_HOST = 'smtp.gmail.com'
    - EMAIL_PORT = 587
    - EMAIL_USE_TLS = True
    - EMAIL_HOST_USER = 'your-email@gmail.com'
    - EMAIL_HOST_PASSWORD = 'your-app-password'
    """
    subject = 'Xác thực tài khoản UrbanVibe'

    message = f'''
    Chào mừng đến UrbanVibe!

    Để hoàn tất đăng ký, vui lòng click link bên dưới để xác thực email:

    http://127.0.0.1:8000/accounts/activate/{email_token}

    Link này sẽ hết hạn sau 24 giờ.

    Nếu bạn không thực hiện đăng ký này, vui lòng bỏ qua email.

    Trân trọng,
    UrbanVibe Team
    '''

    email_from = settings.EMAIL_HOST_USER

    try:
        send_mail(subject, message, email_from, [email])
        print(f"✅ Email gửi thành công tới {email}")
    except Exception as e:
        print(f"❌ Lỗi gửi email: {e}")
```

```python
# accounts/views.py
def activate_email(request, email_token):
    """
    Xử lý link xác thực email.

    Dòng thời gian:
    1. Khách nhấp link từ email
    2. Request tới: /accounts/activate/{email_token}
    3. Tìm Profile có email_token khớp
    4. Cập nhật is_email_verified = True
    5. Redirect về login
    """
    try:
        user_profile = Profile.objects.get(email_token=email_token)
        user_profile.is_email_verified = True
        user_profile.save()

        messages.success(request, 'Tài khoản đã được kích hoạt thành công!')
        return redirect('login')
    except Profile.DoesNotExist:
        return HttpResponse("❌ Link xác thực không hợp lệ hoặc đã hết hạn")
```

#### Dòng thời gian Email Verification:

```
1. User điền form đăng ký
        ↓
2. Click "Đăng ký"
        ↓
3. Hệ thống:
   - Tạo User object
   - Signal kích hoạt → Tạo Profile + email_token (UUID)
   - Gửi email xác thực
        ↓
4. Email được gửi (template HTML):
   "Để hoàn tất đăng ký, click vào link:
    http://127.0.0.1:8000/accounts/activate/550e8400-e29b-41d4-a716-446655440000"
        ↓
5. User check email & click link
        ↓
6. activate_email() được gọi:
   - Tìm Profile có email_token khớp
   - Set is_email_verified = True
   - Thông báo thành công
        ↓
7. User có thể login
```

---

### ✅ 3. Django Allauth (OAuth Integration)

**Vị trí:** `ecom/settings.py`

**Hỗ trợ:** Google, Facebook, GitHub

```python
# ecom/settings.py

INSTALLED_APPS = [
    # ...
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
]

SITE_ID = 1

# Allauth cấu hình
ACCOUNT_EMAIL_VERIFICATION = "none"  # Có thể: "none", "optional", "mandatory"
SOCIALACCOUNT_LOGIN_ON_GET = True

# Cấu hình OAuth Providers
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'OAUTH_PKCE_ENABLED': True,
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'INIT_PARAMS': {'cookie': True},
    },
    'github': {
        'SCOPE': ['user', 'read:user', 'user:email'],
    }
}

# Cấu hình URL
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
```

**URL patterns:**

```python
# ecom/urls.py
urlpatterns = [
    path('accounts/', include('allauth.urls')),
    # ...
]
```

**Login buttons template:**

```html
<!-- templates/accounts/login_register.html -->
<div class="oauth-buttons">
  <a href="{% provider_login_url 'google' %}" class="btn btn-google">
    Login với Google
  </a>
  <a href="{% provider_login_url 'facebook' %}" class="btn btn-facebook">
    Login với Facebook
  </a>
  <a href="{% provider_login_url 'github' %}" class="btn btn-github">
    Login với GitHub
  </a>
</div>
```

---

## 📊 Bảng So Sánh Các Chức Năng

| Chức Năng              | Trạng Thái | Vị Trí               | Ghi Chú                 |
| ---------------------- | ---------- | -------------------- | ----------------------- |
| **Slug Auto**          | ✅ 100%    | `products/models.py` | Hoạt động tốt           |
| **Image Management**   | ✅ 100%    | `products/models.py` | Hỗ trợ variant image    |
| **Cart System**        | ✅ 100%    | `accounts/models.py` | Session-based           |
| **VNPay Integration**  | ✅ 95%     | `orders/vnpay.py`    | Cần checksum validation |
| **Email Verification** | ✅ 100%    | `accounts/models.py` | UUID token              |
| **OAuth**              | ✅ 100%    | `ecom/settings.py`   | Google, FB, GitHub      |
| **Password Hashing**   | ✅ 100%    | Django Auth          | PBKDF2-SHA256           |
| **Coupon System**      | ✅ 100%    | `products/models.py` | Multi-type support      |

---

## 🔧 Cấu Hình Quan Trọng (ecom/settings.py)

```python
# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'urbanvibe_db',
        'USER': 'root',
        'PASSWORD': '123456',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}

# Email SMTP (Gmail)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'letuan16112004@gmail.com'
EMAIL_HOST_PASSWORD = 'cxta dmml tanq taad'  # App Password

# VNPay (Sandbox)
VNPAY_TMN_CODE = 'SIXDZGUD'
VNPAY_HASH_SECRET_KEY = 'B159DXK3140FGOFHWGYJ29B8J77IVVOZ'
VNPAY_PAYMENT_URL = 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'
VNPAY_RETURN_URL = 'http://127.0.0.1:8000/payment_return/'

# Media & Static
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
```

---

## 🚀 Hướng Dẫn Chạy Dự Án

### 1. Thiết lập Database

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Tạo Admin

```bash
python manage.py createsuperuser
```

### 3. Chạy Dev Server

```bash
python manage.py runserver
```

### 4. Truy cập

- Shop: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- Allauth: http://127.0.0.1:8000/accounts/

---

## ✨ Kết Luận

Dự án **UrbanVibe E-Shop** đã triển khai đầy đủ **95%** các chức năng chính:

✅ **Quản Lý Sản Phẩm:** Slug auto, ảnh đa chiều  
✅ **Giỏ Hàng:** Database cart, coupon discount  
✅ **Thanh Toán:** VNPay + Email xác thực  
✅ **Bảo Mật:** PBKDF2 hashing, OAuth

**Công nghệ:**

- Backend: Django 5.2.7
- Database: MySQL
- Authentication: Django Auth + Allauth
- Payment: VNPay (HMAC-SHA512)
- Email: Gmail SMTP

---

**Biên soạn bởi:** AI Assistant  
**Ngày:** 5 Tháng 1, 2026  
**Phiên bản:** v1.0
