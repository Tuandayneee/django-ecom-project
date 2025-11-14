# accounts/middleware.py (SỬA LẠI)

class ClearCouponOnLeaveMiddleware:
    
    # SỬA LẠI: Tên hàm đúng là __init__
    def __init__(self, get_response): 
        self.get_response = get_response
        
        # Danh sách các "view name" an toàn
        self.safe_view_names = [
            'cart',           
            'apply_coupon',   
            'update_cart',    
            'remove_item',    
            # 'checkout',     
        ]

    def __call__(self, request):
        # Dòng 12 (response = self.get_response(request)) sẽ hết lỗi
        # vì self.get_response đã được tạo ở hàm __init__
        response = self.get_response(request)
        
        # Logic xóa coupon (tôi đã đổi 'coupon_id' thành 'coupon_ids'
        # để hỗ trợ nhiều mã giảm giá như bạn yêu cầu)
        if 'coupon_ids' in request.session: 
            
            resolver_match = request.resolver_match
            current_view_name = None
            
            if resolver_match:
                current_view_name = resolver_match.view_name
                
            if current_view_name not in self.safe_view_names:
                try:
                    del request.session['coupon_ids'] 
                except KeyError:
                    pass
        return response