from django.urls import path
from . import views


app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login_email/<mail_site>/', views.login_email, name='login_email'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('activate_account/<code>/', views.activate_account, name='activate_account'),
    path('forgetpwd/', views.forgetpwd, name='forgetpwd'),
    path('resetpwd/<code>/', views.resetpwd, name='resetpwd'),
    path('user_info/', views.get_user_info, name='user_info'),
    path('user_fav/', views.get_user_fav, name='user_fav'),
    path('user_views/', views.get_user_views, name='user_views'),
    path('user_msg/', views.get_user_msg, name='user_msg'),
    path('ch_headimg/', views.ch_headimg, name='ch_headimg'),
    path('chemail/', views.chemail, name='chemail'),
    path('chpwd/', views.chpwd, name='chpwd'),
    path('ajax_check_email_registered_activated/', views.ajax_check_email_registered_activated,
         name='ajax_check_email_registered_activated'),
    path('ajax_validate_account/', views.ajax_validate_account, name='ajax_validate_account'),
    path('ajax_send_email/', views.ajax_send_email, name='ajax_send_email'),
    path('ajax_ch_nickname/', views.ajax_ch_nickname, name='ajax_ch_nickname'),
    path('ajax_ch_gender/', views.ajax_ch_gender, name='ajax_ch_gender'),
    path('ajax_check_code/', views.ajax_check_code, name='ajax_check_code'),
]
