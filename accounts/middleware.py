# accounts/middleware.py (SỬA LẠI)

class ClearCouponOnLeaveMiddleware:
    
    
    def __init__(self, get_response): 
        self.get_response = get_response
        
        
        self.safe_view_names = [
            'cart',           
            'apply_coupon',   
            'update_cart',    
            'remove_item',    
            # 'checkout',     
        ]

    def __call__(self, request):
        
        response = self.get_response(request)
        
        
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