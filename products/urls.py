from django.urls import path
from products.views import get_product, submit_review


urlpatterns = [
    path('<slug>/', get_product, name='product'),
    path('submit_review/<str:order_id>/<uuid:product_id>/',submit_review, name='submit_review'),
]