from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, CartItems, Variant
from .utils import calculate_cart_total


class CartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            cart_obj = Cart.get_or_create_active(request.user)
            cart_data = calculate_cart_total(cart_obj, user=request.user)

            items_data = []
            for item in cart_data['cart_items']:
                if not item.variant:
                    continue
                img_url = ""
                if item.variant.product.product_images.exists():
                    img_url = item.variant.product.product_images.first().image.url

                items_data.append({
                    'uid': item.uid,
                    'product_name': item.variant.product.product_name,
                    'quantity': item.quantity,
                    'price': item.variant.price,
                    'total_price': item.get_product_price,
                    'image': img_url,
                    'color': item.variant.color.color_name if item.variant.color else "",
                    'size': item.variant.size.size_name if item.variant.size else "",
                })

            response_data = {
                'status': 200,
                'subtotal': cart_data['subtotal'],
                'shipping_fee': cart_data['shipping_fee'],
                'tax': cart_data['tax'],
                'discount': cart_data['discount'],
                'total': cart_data['total'],
                'items': items_data,
            }
            return Response(response_data)
        except Exception as exc:
            return Response({'status': 500, 'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AddToCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            variant_uid = request.data.get('variant_uid')
            try:
                quantity = int(request.data.get('quantity', 1))
            except (TypeError, ValueError):
                return Response({'error': 'Số lượng không hợp lệ'}, status=status.HTTP_400_BAD_REQUEST)

            if not variant_uid:
                return Response({'error': 'Vui lòng cung cấp variant_uid'}, status=status.HTTP_400_BAD_REQUEST)
            if quantity < 1:
                return Response({'error': 'Số lượng phải lớn hơn hoặc bằng 1'}, status=status.HTTP_400_BAD_REQUEST)

            variant = get_object_or_404(Variant, uid=variant_uid)
            cart_obj = Cart.get_or_create_active(request.user)

            cart_item, created = CartItems.objects.get_or_create(
                cart=cart_obj,
                variant=variant,
            )
            new_quantity = quantity if created else cart_item.quantity + quantity

            if new_quantity > variant.stock:
                if created:
                    cart_item.delete()
                return Response(
                    {'error': f'Chỉ còn {variant.stock} sản phẩm'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cart_item.quantity = new_quantity
            cart_item.save()

            cart_data = calculate_cart_total(cart_obj, user=request.user)
            return Response({
                'message': 'Đã thêm vào giỏ hàng thành công.',
                'cart_count': cart_obj.get_cart_items_count(),
                'cart_total': cart_data['total'],
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
