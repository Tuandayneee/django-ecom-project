from urllib.parse import parse_qs, urlparse

from django.contrib.auth.models import User
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import Address, Cart, CartItems
from orders.models import Order, OrderProduct, Payment
from orders.vnpay import build_vnpay_query_and_hash, validate_vnpay_checksum
from products.models import Category, ColorVariant, Product, SizeVariant, Variant


class OrderAndVNPayTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='customer@example.com',
            email='customer@example.com',
            password='StrongPassword!1',
        )
        self.other_user = User.objects.create_user(
            username='attacker@example.com',
            email='attacker@example.com',
            password='StrongPassword!1',
        )
        category = Category.objects.create(category_name='Giày')
        self.product = Product.objects.create(product_name='Sneaker Pro', category=category, price=500000)
        color = ColorVariant.objects.create(color_name='Đen')
        size = SizeVariant.objects.create(size_name='42')
        self.variant = Variant.objects.create(
            product=self.product,
            color=color,
            size=size,
            price=500000,
            stock=10,
        )
        self.address = Address.objects.create(
            user=self.user,
            full_name='Nguyen Van A',
            phone='0912345678',
            address_line='100 Nguyen Trai',
            city='Hà Nội',
            is_default=True,
        )
        self.other_address = Address.objects.create(
            user=self.other_user,
            full_name='Attacker',
            phone='0999999999',
            address_line='999 Hacker St',
            city='Hà Nội',
            is_default=True,
        )

    def _fill_user_cart(self, qty=2):
        cart = Cart.objects.create(user=self.user, is_paid=False)
        CartItems.objects.create(cart=cart, variant=self.variant, quantity=qty)
        return cart

    def test_vnpay_checksum_validation_rejects_tampered_or_missing_hash(self):
        secret = 'TESTVNPAYSECRET123456'
        params = {
            'vnp_Amount': '102500000',
            'vnp_ResponseCode': '00',
            'vnp_TxnRef': 'ORD-TEST-001',
        }
        _, valid_hash = build_vnpay_query_and_hash(params, secret)
        signed = {**params, 'vnp_SecureHash': valid_hash}

        self.assertTrue(validate_vnpay_checksum(signed, secret))
        self.assertFalse(validate_vnpay_checksum(params, secret))
        self.assertFalse(validate_vnpay_checksum(signed, ''))

        tampered = {**signed, 'vnp_Amount': '100'}
        self.assertFalse(validate_vnpay_checksum(tampered, secret))

    def test_cod_checkout_deducts_stock_and_creates_order(self):
        self._fill_user_cart(qty=3)
        mail.outbox.clear()
        self.client.force_login(self.user)

        checkout_get = self.client.get(reverse('orders:checkout'))
        self.assertEqual(checkout_get.status_code, 200)
        self.assertContains(checkout_get, 'Nguyen Van A')

        res = self.client.post(reverse('orders:checkout'), {
            'selected_address': str(self.address.uid),
            'payment_method': 'cod',
        })
        self.assertEqual(res.status_code, 302)

        order = Order.objects.get(user=self.user)
        self.assertEqual(order.status, 'Pending')
        self.assertFalse(order.is_ordered)
        self.assertEqual(order.order_total, 1500000)
        self.assertEqual(order.shipping_fee, 25000)
        self.assertEqual(order.order_products.count(), 1)

        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 7)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(order.order_number, mail.outbox[0].subject)

        success_res = self.client.get(reverse('orders:order_success', args=[order.uid]))
        self.assertEqual(success_res.status_code, 200)
        self.assertContains(success_res, '100 Nguyen Trai')

        detail_res = self.client.get(reverse('order_detail', args=[order.order_number]))
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, reverse('product', args=[self.product.slug]))

    def test_cod_checkout_blocks_other_user_address_idor(self):
        self._fill_user_cart(qty=1)
        self.client.force_login(self.user)

        res = self.client.post(reverse('orders:checkout'), {
            'selected_address': str(self.other_address.uid),
            'payment_method': 'cod',
        })
        self.assertEqual(res.status_code, 404)
        self.assertEqual(Order.objects.count(), 0)

    def test_order_success_and_remove_order_enforce_ownership_and_post(self):
        self._fill_user_cart(qty=2)
        self.client.force_login(self.user)
        self.client.post(reverse('orders:checkout'), {
            'selected_address': str(self.address.uid),
            'payment_method': 'cod',
        })
        order = Order.objects.get(user=self.user)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 8)

        # Other user cannot view success page or cancel order
        self.client.force_login(self.other_user)
        self.assertEqual(
            self.client.get(reverse('orders:order_success', args=[order.uid])).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(reverse('orders:remove_order', args=[order.uid])).status_code,
            404,
        )

        # Owner cannot cancel via GET
        self.client.force_login(self.user)
        self.assertEqual(
            self.client.get(reverse('orders:remove_order', args=[order.uid])).status_code,
            405,
        )

        # Owner cancels via POST -> status changes to 'cancelled' and stock is restored
        cancel_res = self.client.post(reverse('orders:remove_order', args=[order.uid]))
        self.assertEqual(cancel_res.status_code, 302)
        order.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(order.status, 'cancelled')
        self.assertEqual(self.variant.stock, 10)

    @override_settings(
        VNPAY_TMN_CODE='TESTTMN',
        VNPAY_HASH_SECRET_KEY='TESTSECRETKEY123456',
        VNPAY_PAYMENT_URL='https://sandbox.vnpayment.vn/paymentv2/vpcpay.html',
        VNPAY_RETURN_URL='http://127.0.0.1:8000/orders/payment/return/',
    )
    def test_vnpay_flow_creates_pending_order_rejects_bad_checksum_and_confirms_valid_return(self):
        self._fill_user_cart(qty=2)  # subtotal = 1,000,000 + ship 25,000 = 1,025,000
        self.client.force_login(self.user)

        session = self.client.session
        session['shipping_address_uid'] = str(self.address.uid)
        session['is_buy_now'] = False
        session.save()

        pay_res = self.client.get(reverse('orders:vnpay_payment'))
        self.assertEqual(pay_res.status_code, 302)

        parsed = urlparse(pay_res['Location'])
        query_params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        txn_ref = query_params['vnp_TxnRef']

        # Pending Order and Payment are created before redirecting to VNPay
        order = Order.objects.get(order_number=txn_ref)
        self.assertEqual(order.status, 'Pending')
        self.assertFalse(order.is_ordered)
        self.assertEqual(order.payment.status, Payment.PaymentStatus.PENDING)
        self.assertEqual(OrderProduct.objects.filter(order=order).count(), 1)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 10)

        return_url = reverse('orders:payment_return')

        # 1) Invalid checksum must be rejected
        bad_return = self.client.get(return_url, {
            'vnp_TxnRef': txn_ref,
            'vnp_Amount': str(int(order.grand_total) * 100),
            'vnp_ResponseCode': '00',
            'vnp_SecureHash': 'deadbeef',
        })
        self.assertEqual(bad_return.status_code, 302)
        order.refresh_from_db()
        self.assertFalse(order.is_ordered)
        self.assertEqual(order.status, 'Pending')

        # 2) Valid checksum but mismatched amount must be rejected
        tampered_amount_params = {
            'vnp_TxnRef': txn_ref,
            'vnp_Amount': '100',
            'vnp_ResponseCode': '00',
        }
        _, amt_hash = build_vnpay_query_and_hash(tampered_amount_params, 'TESTSECRETKEY123456')
        tampered_amount_params['vnp_SecureHash'] = amt_hash
        self.client.get(return_url, tampered_amount_params)
        order.refresh_from_db()
        self.assertFalse(order.is_ordered)

        # 3) Valid checksum and valid amount confirms payment & deducts stock
        valid_params = {
            'vnp_TxnRef': txn_ref,
            'vnp_Amount': str(int(order.grand_total) * 100),
            'vnp_ResponseCode': '00',
            'vnp_TransactionStatus': '00',
        }
        _, valid_hash = build_vnpay_query_and_hash(valid_params, 'TESTSECRETKEY123456')
        valid_params['vnp_SecureHash'] = valid_hash

        ok_res = self.client.get(return_url, valid_params)
        self.assertRedirects(ok_res, reverse('orders:order_success', args=[order.uid]))

        order.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(order.status, 'paid')
        self.assertTrue(order.is_ordered)
        self.assertEqual(order.payment.status, Payment.PaymentStatus.COMPLETED)
        self.assertEqual(self.variant.stock, 8)

    @override_settings(
        VNPAY_TMN_CODE='TESTTMN',
        VNPAY_HASH_SECRET_KEY='TESTSECRETKEY123456',
    )
    def test_vnpay_ipn_without_session_confirms_order_by_txn_ref(self):
        payment = Payment.objects.create(
            user=self.user,
            payment_id='ORD-IPN-001',
            payment_method='VNPay',
            amount_paid='525000',
            status=Payment.PaymentStatus.PENDING,
        )
        order = Order.objects.create(
            user=self.user,
            payment=payment,
            order_number='ORD-IPN-001',
            full_name='Nguyen Van A',
            order_total=500000,
            shipping_fee=25000,
            status='Pending',
            is_ordered=False,
        )
        OrderProduct.objects.create(
            order=order,
            product=self.product,
            variant=self.variant,
            product_name=self.product.product_name,
            quantity=1,
            product_price=500000,
        )

        params = {
            'vnp_TxnRef': 'ORD-IPN-001',
            'vnp_Amount': '52500000',
            'vnp_ResponseCode': '00',
            'vnp_TransactionStatus': '00',
        }
        _, sig = build_vnpay_query_and_hash(params, 'TESTSECRETKEY123456')
        params['vnp_SecureHash'] = sig

        anon_client = Client()
        res = anon_client.get(reverse('orders:payment_return'), params)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['RspCode'], '00')

        order.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(order.status, 'paid')
        self.assertTrue(order.is_ordered)
        self.assertEqual(self.variant.stock, 9)

    def test_buy_now_requires_post_and_validates_stock(self):
        self.client.force_login(self.user)
        url = reverse('orders:buy_now')

        self.assertEqual(self.client.get(url).status_code, 405)

        bad_res = self.client.post(
            url,
            {'variant_uid': str(self.variant.uid), 'quantity': 999},
            content_type='application/json',
        )
        self.assertEqual(bad_res.status_code, 400)

        ok_res = self.client.post(
            url,
            {'variant_uid': str(self.variant.uid), 'quantity': 2},
            content_type='application/json',
        )
        self.assertEqual(ok_res.status_code, 200)

    def test_order_admin_search_does_not_raise_field_error(self):
        Order.objects.create(
            user=self.user,
            order_number='ORD-ADMIN-001',
            full_name='Nguyen Van A',
            phone='0912345678',
            order_total=100000,
        )
        admin_user = User.objects.create_superuser(
            username='admin@example.com',
            email='admin@example.com',
            password='StrongPassword!1',
        )
        self.client.force_login(admin_user)
        res = self.client.get('/admin/orders/order/?q=Nguyen')
        self.assertEqual(res.status_code, 200)
