from django.urls import path
from . import views


app_name = 'products'
urlpatterns = [
    path('product_detail/', views.get_product_detail, name='get_product_detail'),
    path('product_config/', views.get_product_config, name='get_product_config'),
]
