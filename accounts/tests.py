from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Address, Cart, CartItems
from accounts.utils import calculate_cart_total
from products.models import (
    Category,
    ColorVariant,
    Coupon,
    CouponUsage,
    Product,
    SizeVariant,
    Variant,
)


class CartCouponAndAccountTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='alice@example.com',
            email='alice@example.com',
            password='StrongPassword!1',
        )
        self.other_user = User.objects.create_user(
            username='bob@example.com',
            email='bob@example.com',
            password='StrongPassword!1',
        )
        self.cat_shirts = Category.objects.create(category_name='Áo')
        self.cat_pants = Category.objects.create(category_name='Quần')

        self.shirt = Product.objects.create(product_name='Áo Sơ Mi', category=self.cat_shirts, price=300000)
        self.pants = Product.objects.create(product_name='Quần Jeans', category=self.cat_pants, price=500000)
        color = ColorVariant.objects.create(color_name='Trắng')
        size = SizeVariant.objects.create(size_name='L')

        self.shirt_variant = Variant.objects.create(
            product=self.shirt,
            color=color,
            size=size,
            price=300000,
            stock=5,
        )
        self.pants_variant = Variant.objects.create(
            product=self.pants,
            color=color,
            size=size,
            price=500000,
            stock=5,
            sku='QUAN-JEANS-TRANG-L',
        )
        Address.objects.create(
            user=self.user,
            full_name='Alice',
            phone='0900000001',
            address_line='123 Pho Hue',
            city='Hà Nội',
            is_default=True,
        )

    def test_context_processor_handles_multiple_unpaid_carts_safely(self):
        Cart.objects.create(user=self.user, is_paid=False)
        Cart.objects.create(user=self.user, is_paid=False)

        self.client.force_login(self.user)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_add_to_cart_requires_post_and_validates_quantity_and_stock(self):
        self.client.force_login(self.user)
        url = reverse('add_to_cart', args=[self.shirt.slug])

        get_res = self.client.get(f"{url}?variant={self.shirt_variant.uid}&quantity=1")
        self.assertEqual(get_res.status_code, 405)

        bad_qty = self.client.post(url, {'variant': str(self.shirt_variant.uid), 'quantity': 0})
        self.assertEqual(bad_qty.status_code, 302)
        self.assertEqual(CartItems.objects.count(), 0)

        over_stock = self.client.post(url, {'variant': str(self.shirt_variant.uid), 'quantity': 99})
        self.assertEqual(over_stock.status_code, 302)
        self.assertEqual(CartItems.objects.count(), 0)

        ok_res = self.client.post(url, {'variant': str(self.shirt_variant.uid), 'quantity': 2})
        self.assertEqual(ok_res.status_code, 302)
        cart = Cart.objects.get(user=self.user, is_paid=False)
        self.assertEqual(cart.get_cart_items_count(), 2)

    def test_apply_coupon_validation_and_calculate_cart_total(self):
        now = timezone.now()
        cart = Cart.objects.create(user=self.user, is_paid=False)
        CartItems.objects.create(cart=cart, variant=self.shirt_variant, quantity=1)  # 300,000
        CartItems.objects.create(cart=cart, variant=self.pants_variant, quantity=1)  # 500,000

        cat_coupon = Coupon.objects.create(
            coupon_code='SHIRT10',
            category=self.cat_shirts,
            coupon_type='percent',
            discount_price=10,
            minimum_amount=200000,
            usage_limit_per_user=1,
            is_active=True,
            valid_to=now + timedelta(days=2),
        )
        expired_coupon = Coupon.objects.create(
            coupon_code='OLD50',
            coupon_type='amount',
            discount_price=50000,
            minimum_amount=100000,
            is_active=True,
            valid_to=now - timedelta(days=1),
        )

        self.client.force_login(self.user)
        self.client.post(reverse('apply_coupon'), {'coupon_code': 'OLD50'})
        self.assertFalse(cart.coupons.filter(coupon_code='OLD50').exists())

        self.client.post(reverse('apply_coupon'), {'coupon_code': 'SHIRT10'})
        self.assertTrue(cart.coupons.filter(coupon_code='SHIRT10').exists())

        # Attach expired coupon directly to confirm calculate_cart_total also guards expiry & usage limit
        cart.coupons.add(expired_coupon)
        totals = calculate_cart_total(cart, user=self.user)
        # 10% of 300,000 shirt = 30,000; shipping Hanoi = 25,000; subtotal = 800,000 -> total = 795,000
        self.assertEqual(totals['subtotal'], 800000)
        self.assertEqual(totals['shipping_fee'], 25000)
        self.assertEqual(totals['discount'], 30000)
        self.assertEqual(totals['total'], 795000)

        # Exhaust coupon usage limit
        CouponUsage.objects.create(user=self.user, coupon=cat_coupon, used_count=1)
        totals_after_limit = calculate_cart_total(cart, user=self.user)
        self.assertEqual(totals_after_limit['discount'], 0)

    def test_delete_address_requires_post_and_ownership(self):
        addr = Address.objects.create(
            user=self.other_user,
            full_name='Bob',
            phone='0900000002',
            address_line='456 Le Loi',
            city='HCM',
        )
        self.client.force_login(self.user)
        url = reverse('delete_address', args=[addr.uid])

        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertTrue(Address.objects.filter(uid=addr.uid).exists())

        self.client.force_login(self.other_user)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertFalse(Address.objects.filter(uid=addr.uid).exists())

    def test_profile_addresses_and_change_password_flows(self):
        self.client.force_login(self.user)
        addr = Address.objects.get(user=self.user)

        self.assertEqual(self.client.get(reverse('user_profile')).status_code, 200)
        self.assertEqual(self.client.get(reverse('user_orders')).status_code, 200)
        self.assertEqual(self.client.get(reverse('address_list')).status_code, 200)

        edit_url = reverse('edit_address', args=[addr.uid])
        self.assertEqual(self.client.get(edit_url).status_code, 200)
        edit_res = self.client.post(edit_url, {
            'full_name': 'Alice Updated',
            'phone': '0900000001',
            'address_line': '123 Pho Hue, Hai Ba Trung',
            'city': 'Hà Nội',
            'is_default': True,
        })
        self.assertEqual(edit_res.status_code, 302)
        addr.refresh_from_db()
        self.assertEqual(addr.full_name, 'Alice Updated')

        save_res = self.client.post(reverse('save_address'), {
            'full_name': 'Alice Office',
            'phone': '0900000099',
            'city': 'Đà Nẵng',
            'district': 'Hải Châu',
            'ward': 'Thạch Thang',
            'address_line': '10 Bach Dang',
            'province_id': '',
            'district_id': '',
            'ward_code': '',
        })
        self.assertEqual(save_res.status_code, 302)
        self.assertTrue(Address.objects.filter(user=self.user, full_name='Alice Office').exists())

        pw_res = self.client.post(reverse('change_password'), {
            'old_password': 'StrongPassword!1',
            'new_password1': 'NewStrongPass!2',
            'new_password2': 'NewStrongPass!2',
        })
        self.assertRedirects(pw_res, reverse('user_profile'))

    def test_cart_api_and_add_to_cart_api(self):
        api_client = APIClient()
        unauth_res = api_client.get(reverse('api_cart'))
        self.assertEqual(unauth_res.status_code, 401)

        api_client.force_authenticate(user=self.user)
        add_res = api_client.post(
            reverse('api_add_to_cart'),
            {'variant_uid': str(self.shirt_variant.uid), 'quantity': 2},
            format='json',
        )
        self.assertEqual(add_res.status_code, 200)
        self.assertEqual(add_res.json()['cart_count'], 2)

        bad_res = api_client.post(
            reverse('api_add_to_cart'),
            {'variant_uid': str(self.shirt_variant.uid), 'quantity': 10},
            format='json',
        )
        self.assertEqual(bad_res.status_code, 400)

        get_res = api_client.get(reverse('api_cart'))
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()['subtotal'], 600000)
