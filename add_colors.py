#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecom.settings')
django.setup()

from products.models import ColorVariant


colors = [
    {'color_name': 'Xanh', 'color_code': '#1E3A5F'},
    {'color_name': 'Nau', 'color_code': '#8B5A3C'},
    {'color_name': 'Den', 'color_code': '#000000'},
    {'color_name': 'Trang', 'color_code': '#FFFFFF'},
]

for color_data in colors:
    color, created = ColorVariant.objects.get_or_create(
        color_name=color_data['color_name'],
        defaults={'color_code': color_data['color_code']}
    )
    status = "tao moi" if created else "da ton tai"
    print(f"✓ {color.color_name} ({color.color_code}) - {status}")

for color in ColorVariant.objects.all():
    print(f"  {color.color_name}: {color.color_code}")
