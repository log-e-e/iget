"""iget URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.views import serve

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # 说明：此处的图标格式.ico不是必须的，理论上只要是张图片就ok
    path('favicon.ico', serve, {'path': 'media/system_default/favicon.png'}),
    path('', views.index, name='index'),
    path('forbidden_403/', views.forbidden_403, name='forbidden_403'),
    path('notfound_404/', views.notfound_404, name='notfound_404'),
    path('users/', include('users.urls')),
    path('products/', include('products.urls')),
    path('goods/', include('goods.urls')),
    path('operations/', include('operations.urls')),
    path('dataStatistics/', include('dataStatistics.urls'))
]
