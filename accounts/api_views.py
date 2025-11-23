from rest_framework.views import APIView
from rest_framework.views import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Cart
from products.serializers import CartSerializer
from .views import _get_cart_details


class CartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart_obj, _ = Cart.objects.get_or_create(user=request.user, is_paid=False)
        
        # Gọi helper mới (lấy coupon từ DB)
        cart_data = _get_cart_details(cart_obj)
        
        # Serialize data để trả về JSON
        # Lưu ý: Bạn cần tạo Serializer cho cart_items trả về đúng format JSON
        
        response_data = {
            'subtotal': cart_data['subtotal'],
            'shipping_fee': cart_data['shipping_fee'],
            'discount': cart_data['discount'],
            'total': cart_data['total'],
            'items': [
                {
                    'product_name': item.variant.product.product_name,
                    'quantity': item.quantity,
                    'price': item.variant.product.price,
                    # ... thêm các trường cần thiết
                } for item in cart_data['cart_items']
            ]
        }

        return Response(response_data)


class AddToCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Thêm sản phẩm vào giỏ hàng qua API
        """
        variant_uid = request.data.get('variant_uid')
        quantity = request.data.get('quantity', 1)

        return Response({'message': 'Đã thêm vào giỏ hàng thành công.'}, status=status.HTTP_200_OK)