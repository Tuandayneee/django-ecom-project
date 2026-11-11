from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from orders.models import Order
from products.models import (
    Category,
    ColorVariant,
    Coupon,
    Product,
    Review,
    SizeVariant,
    Supplier,
    Variant,
)


class ProductModelAndViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='buyer@example.com',
            email='buyer@example.com',
            password='StrongPassword!1',
        )
        self.category = Category.objects.create(category_name='Áo Thun')
        self.product = Product.objects.create(
            product_name='Áo Thun Urban Basic',
            category=self.category,
            original_price=250000,
            price=200000,
        )
        self.color = ColorVariant.objects.create(color_name='Đen', color_code='#000000')
        self.size = SizeVariant.objects.create(size_name='M')

    def test_category_and_product_slug_auto_generation(self):
        self.assertEqual(self.category.slug, 'ao-thun')
        self.assertEqual(self.product.slug, 'ao-thun-urban-basic')

    def test_supplier_str_returns_name(self):
        supplier = Supplier.objects.create(
            name='Xưởng May ABC',
            contact_person='Nguyen Van A',
            email='supplier@example.com',
            phone='0901234567',
        )
        self.assertEqual(str(supplier), 'Xưởng May ABC')

    def test_variant_sku_auto_generation_with_and_without_color_size(self):
        v1 = Variant.objects.create(
            product=self.product,
            color=self.color,
            size=self.size,
            price=200000,
            stock=10,
        )
        self.assertEqual(v1.sku, 'AO-THUN-URBAN-BASIC-EN-M')

        v2 = Variant.objects.create(
            product=self.product,
            color=None,
            size=None,
            price=180000,
            stock=5,
        )
        self.assertEqual(v2.sku, 'AO-THUN-URBAN-BASIC-DEFAULT-DEFAULT')
        self.assertEqual(self.product.min_price, 180000)

    def test_coupon_is_valid_respects_active_and_expiry(self):
        now = timezone.now()
        active_coupon = Coupon.objects.create(
            coupon_code='ACTIVE20',
            discount_price=20000,
            minimum_amount=100000,
            is_active=True,
            valid_to=now + timedelta(days=1),
        )
        expired_coupon = Coupon.objects.create(
            coupon_code='EXPIRED20',
            discount_price=20000,
            minimum_amount=100000,
            is_active=True,
            valid_to=now - timedelta(minutes=1),
        )
        inactive_coupon = Coupon.objects.create(
            coupon_code='OFF20',
            discount_price=20000,
            minimum_amount=100000,
            is_active=False,
            valid_to=now + timedelta(days=1),
        )
        self.assertTrue(active_coupon.is_valid())
        self.assertFalse(expired_coupon.is_valid())
        self.assertFalse(inactive_coupon.is_valid())

    def test_product_list_api_returns_products_and_variants(self):
        Variant.objects.create(
            product=self.product,
            color=self.color,
            size=self.size,
            price=200000,
            stock=7,
        )
        response = self.client.get(reverse('api_products'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['product_name'], 'Áo Thun Urban Basic')
        self.assertEqual(len(data[0]['variants']), 1)
        self.assertEqual(data[0]['variants'][0]['stock'], 7)

    def test_submit_review_get_and_post_without_template_error(self):
        order = Order.objects.create(
            user=self.user,
            order_number='ORD-REV-001',
            full_name='Buyer',
            order_total=200000,
            status='completed',
            is_ordered=True,
        )
        self.client.force_login(self.user)
        url = reverse('submit_review', args=[order.order_number, self.product.uid])

        get_res = self.client.get(url)
        self.assertEqual(get_res.status_code, 200)

        post_res = self.client.post(url, {
            'subject': 'Rất tốt',
            'review': 'Chất vải dày dặn, mặc mát.',
            'rating': 5,
        })
        self.assertEqual(post_res.status_code, 302)
        self.assertEqual(Review.objects.filter(user=self.user, product=self.product, order=order).count(), 1)
