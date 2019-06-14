from django.contrib.auth.middleware import MiddlewareMixin
from django.shortcuts import redirect, reverse


class pageAccessMD(MiddlewareMixin):
    # 游客用户页面请求受限名单、已登录用户页面请求受限名单
    anonymous_black = ['users/logout', 'users/user_info/', 'users/user_fav/', 'users/user_views/', 'users/user_msg/',
                       'users/ch_headimg/', 'users/chemail/', 'users/chpwd/', 'users/ajax_ch_nickname/',
                       'users/ajax_ch_gender/', 'users/ajax_ch_gender/', ]
    loggedIn_black = ['users/login', 'users/register/', 'users/activate_account/', 'users/forgetpwd/', 'users/resetpwd/', ]

    def process_request(self, request):
        # 不区分请求方式，直接检查
        request_url = request.path_info

        if request.user.is_authenticated:
            for black_item in self.loggedIn_black:
                if str(request_url).find(black_item) != -1:
                    return redirect(reverse('index'))
        else:
            for black_item in self.anonymous_black:
                if str(request_url).find(black_item) != -1:
                    return redirect(reverse('users:login'))
