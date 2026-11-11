from rest_framework import serializers

from accounts.models import Cart, CartItems
from .models import Product, ProductImage, Variant


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['uid', 'image', 'is_thumbnail']


class VariantSerializer(serializers.ModelSerializer):
    variant_name = serializers.CharField(read_only=True)

    class Meta:
        model = Variant
        fields = ['uid', 'sku', 'variant_name', 'price', 'original_price', 'stock']


class ProductSerializer(serializers.ModelSerializer):
    product_images = ProductImageSerializer(many=True, read_only=True)
    variants = VariantSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.category_name', read_only=True, default=None)

    class Meta:
        model = Product
        fields = [
            'uid',
            'product_name',
            'slug',
            'category_name',
            'original_price',
            'price',
            'sold_count',
            'product_description',
            'product_images',
            'variants',
        ]


class CartItemSerializer(serializers.ModelSerializer):
    variant = VariantSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItems
        fields = ['uid', 'variant', 'quantity', 'total_price']

    def get_total_price(self, obj):
        return obj.get_product_price


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source='cart_items', many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['uid', 'is_paid', 'items']
