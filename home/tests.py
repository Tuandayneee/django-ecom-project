from django.test import Client, TestCase
from django.urls import reverse

from products.models import Category, Product


class HomeViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat = Category.objects.create(category_name='Áo Khoác')
        Product.objects.create(product_name='Áo Khoác Bomber', category=self.cat, price=450000)

    def test_home_about_contact_and_filters(self):
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)
        self.assertEqual(self.client.get(reverse('about')).status_code, 200)
        self.assertEqual(self.client.get(reverse('contact')).status_code, 200)

        search_res = self.client.get(reverse('home'), {'search': 'Bomber'})
        self.assertEqual(search_res.status_code, 200)
        self.assertContains(search_res, 'Áo Khoác Bomber')

        cat_res = self.client.get(reverse('home'), {'category': self.cat.slug})
        self.assertEqual(cat_res.status_code, 200)
        self.assertContains(cat_res, 'Áo Khoác Bomber')
