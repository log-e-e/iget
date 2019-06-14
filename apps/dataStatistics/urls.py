from django.urls import path
from . import views


app_name = 'dataStatistics'
urlpatterns = [
    path('allRankList/', views.all_rank_list, name='allRankList'),
    path('certainRankList/', views.certain_rank_list, name='certainRankList'),
    path('popular_fav/', views.ajax_get_popular_fav, name='ajax_get_popular_fav'),
    path('popular_rec/', views.ajax_get_popular_rec, name='ajax_get_popular_rec'),
    path('people_view/', views.ajax_get_people_view, name='ajax_get_people_view'),
    path('add_prd_to_fav/', views.ajax_add_prd_to_fav, name='ajax_add_prd_to_fav'),
    path('ajax_delete_fav_prd/', views.ajax_delete_fav_prd, name='ajax_delete_fav_prd'),
    path('ajax_delete_all_fav_prd/', views.ajax_delete_all_fav_prd, name='ajax_delete_all_fav_prd'),
]
