from django.contrib import admin
from .models import User


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'nickname', 'gender', 'head_img', 'is_active', 'create_time', 'update_time')

admin.site.register(User, UserAdmin)
