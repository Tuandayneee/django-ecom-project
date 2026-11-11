from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.api_views import AddToCartAPIView, CartAPIView
from home.views import index
from products.views import ProductListAPIView

urlpatterns = [
    path('', index, name='home'),
    path('admin/', admin.site.urls),
    path('product/', include('products.urls')),
    path('accounts/', include('accounts.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/products/', ProductListAPIView.as_view(), name='api_products'),
    path('api/cart/', CartAPIView.as_view(), name='api_cart'),
    path('api/cart/add/', AddToCartAPIView.as_view(), name='api_add_to_cart'),
    path('accounts/', include('allauth.urls')),
    path('orders/', include('orders.urls')),
    path('', include('home.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += staticfiles_urlpatterns()
