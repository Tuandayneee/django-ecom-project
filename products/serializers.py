from rest_framework import serializers
from .models import Product,Variant,ProductImage
from accounts.models import CartItems,Cart


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image']



class VariantSerializer(serializers.ModelSerializer):
    Product = ProductImageSerializer(many=True, read_only=True)
    class Meta:
        model = Variant
        fields = ['id', 'name', 'price']


class ProductSerializer(serializers.ModelSerializer):
    product_image = ProductImageSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = ['uid', 'product_name', 'price', 'product_description', 'product_images']

class CartItemSerializer(serializers.ModelSerializer):
    variant = VariantSerializer()
    total_price = serializers.SerializerMethodField(source='get_total_price' )

    class Meta:
        model = CartItems
        fields = ['uid', 'variant', 'quantity', 'total_price']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source='cart_items', many=True)
    class Meta:
        model = Cart
        fields = ['uid', 'is_paid', 'items']