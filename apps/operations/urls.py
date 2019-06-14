from django.urls import path
from . import views


app_name = 'operations'
urlpatterns = [
    path('search/', views.search, name='search'),
    path('ajax_get_filter_result/', views.ajax_get_filter_result, name='ajax_get_filter_result'),
    path('ajax_get_prd_info/', views.ajax_get_prd_info, name='ajax_get_prd_info'),
    path('compare_prd/', views.compare_prd, name='compare_prd'),
]
