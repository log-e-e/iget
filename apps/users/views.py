import os
import time
import traceback

from cryptography.fernet import Fernet
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, reverse, redirect
from django.utils import timezone

from dataStatistics.models import ViewStatistics
from iget import settings
from operations.models import UserFavorite
from tools import db_tool
from tools.send_email_tool import send_email_code
from users.models import User
from .tasks import async_send_email

key_bytes = Fernet.generate_key()
f= Fernet(key_bytes)


def ajax_check_email_registered_activated(request):
    if request.method == 'GET':
        email = str(request.GET.get("email"))
        user_list = User.objects.filter(Q(email=email))
        registered, activated = "false", "false"

        if user_list:
            registered = "true"
            activated = "true" if user_list[0].is_active else activated

        return JsonResponse(data={
            "registered": registered,
            "activated": activated,
        })
    else:
        pass


def ajax_validate_account(request):
    if request.method == 'POST':
        email = str(request.POST.get('email'))
        password = str(request.POST.get('password'))
        user = authenticate(username=email, password=password)
        is_valid = "true" if user else "false"

        return JsonResponse(data={
            "is_valid": is_valid,
        })
    else:
        pass


def ajax_send_email(request):
    if request.method == 'GET':
        email = str(request.GET.get("email"))
        # 此处的邮件类型直接转为int可能会抛异常：request.GET.get("verify_type")的值不合法时会抛异常
        verify_type_str = request.GET.get("verify_type")
        verify_type = int(verify_type_str) if verify_type_str else -1
        send_success = send_email_code(email=email, verify_type=verify_type)
        if send_success:
            return JsonResponse({
                "completed": "true",
                "msg": "邮件已发送至邮箱，请查收",
            })
        else:
            return JsonResponse({
                "completed": "false",
                "msg": "邮件发送失败，请重试！",
            })
    else:
        return redirect(reverse('forbidden_403'))


def ajax_ch_nickname(request):
    if request.method == 'POST':
        try:
            nickname = request.POST.get("nickname")
            request.user.nickname = nickname
            request.user.save()
        except Exception:
            return JsonResponse({
                "completed": "false",
                "msg": "昵称修改失败，请重试！",
            })
        else:
            return JsonResponse({
                "completed": "true",
                "msg": "昵称修改成功",
            })
    else:
        pass


def ajax_ch_gender(request):
    if request.method == 'POST':
        try:
            gender = request.POST.get("gender")
            request.user.gender = 0 if gender == "male" else 1
            request.user.save()
        except Exception:
            traceback.print_exc()
            return JsonResponse({
                "completed": "false",
                "msg": "性别修改失败，请重试！",
            })
        else:
            return JsonResponse({
                "completed": "true",
                "msg": "性别修改成功",
            })
    else:
        pass


def ajax_check_code(request):
    if request.method == 'GET':
        code = str(request.GET.get("code"))
        email = str(request.GET.get("email"))
        # 检测code的有效性并从数据中获取对应的email_ver对象
        # 值得注意的是，如果在15分钟内发送了多个验证码，那么如何保证只有最新的验证码是有效的呢？
        # 解决办法：暂时只能想到的是———在每次发送新的验证码的同时，将最近15分钟内的验证码全部设置为无效即可
        code_valid, email_ver = db_tool.is_valid_code(email, code)
        return JsonResponse(data={
            "code_valid": "true" if code_valid else "false",
        })
    else:
        pass


def register(request):
    # 如果是GET请求，则是请求注册页面
    if request.method == 'GET':
        response = render(request, 'users/register.html')
        # 设置注册提交cookie标识，用于防止在跳转到notification页面后刷新页面时重复提交表单
        response.set_signed_cookie("registerPostToken", "allow", salt="RECONSTRUCTION_IS_PAINFUL")

        return response
    # 如果是POST请求，则是提交注册信息
    elif request.method == 'POST':
        email = request.POST.get('email')
        # 查询邮箱对应的登录url
        mail_website = db_tool.get_mail_site(email)
        # 检查registerPostToken，如果registerPostToken的cookie存在则执行用户数据录入
        if request.get_signed_cookie("registerPostToken", default=None, salt="RECONSTRUCTION_IS_PAINFUL"):
            # 数据输入的校验在前台由jquery validate完成，后台不再进行校验
            password = request.POST.get('password1')

            # 设置并将用户数据写入数据库
            new_user = User()
            new_user.username = email
            new_user.email = email
            new_user.set_password(password)
            new_user.nickname = email
            new_user.head_img = 'users/head_img_sys.jpeg'
            new_user.status = 0
            new_user.save()

            # 发送邮箱验证,改用celery异步发送邮件
            async_send_email.delay(email=email, verify_type=0)

            response = render(request, 'users/notification.html', context={
                'title': '邮箱激活',
                'msg': '恭喜您, 只差一步就注册成功啦！请前往邮箱' +
                       email + '激活账号，未激活的账号将无法正常登陆'
                               '（激活链接将在以下情况失效：5分钟内未完成激活操作、重新发送激活邮件、完成激活操作）。请',
                'notify_type': 'login_email',
                'mail_website': mail_website,
                'target_email': email,
                'send_email_type': '0',
            })
            # 删除注册cookie，处理页面刷新导致表单重复提交的结果
            response.delete_cookie("registerPostToken")

            return response
        # registerPostToken的cookie不存在时则只刷新页面不提交数据
        else:
            response = render(request, 'users/notification.html', context={
                'title': '邮箱激活',
                'msg': '恭喜您, 只差一步就注册成功啦！请前往邮箱' +
                       email + '激活账号，未激活的账号将无法正常登陆'
                               '（激活链接将在以下情况失效：5分钟内未完成激活操作、重新发送激活邮件、完成激活操作）。请',
                'notify_type': 'login_email',
                'mail_website': mail_website,
                'target_email': email,
                'send_email_type': '0',
            })
            # 删除注册cookie，处理页面刷新导致表单重复提交的结果
            response.delete_cookie("registerPostToken")

            return response
    else:
        pass


def activate_account(request, code):
    if request.method == 'GET':
        # 检测code的有效性并从数据中获取对应的email_ver对象
        code_valid, email_ver = db_tool.is_valid_code(request.GET.get('email'), code)
        # 如果code有效
        if code_valid:
            # 点击链接后设置is_valid为False，避免重复点击链接
            email_ver.is_valid = False
            email_ver.save()

            email = email_ver.to_email
            user_list = User.objects.filter(email=email)
            if user_list:
                user = user_list[0]
                user.is_active = True
                user.save()

                return render(request, 'users/notification.html', context={
                    'title': '完成注册',
                    'msg': '恭喜, 账号激活成功！请',  # '登录'二字作为链接
                    'notify_type': 'login_iget',
                })
            else:
                return redirect(reverse('forbidden_403'))
        else:
            return redirect(reverse('forbidden_403'))
    else:
        pass


def login_email(request, mail_site):
    if request.method == 'GET' and mail_site != '#':
        site_link = 'https://' + mail_site
        return redirect(site_link, permanent=True)
    else:
        return redirect(reverse('forbidden_403'))


def login(request):
    if request.method == 'GET':
        response = render(request, 'users/login.html')
        response.set_signed_cookie("loginPostToken", "allow", salt="RECONSTRUCTION_IS_PAINFUL")
        return response
    elif request.method == 'POST':
        email = request.POST.get("email")
        # 查询邮箱
        mail_website = db_tool.get_mail_site(email)
        if request.get_signed_cookie("loginPostToken", default=None, salt="RECONSTRUCTION_IS_PAINFUL"):
            password = request.POST.get("password")
            user = authenticate(username=email, password=password)
            if user.is_active:
                # 更新登录时间
                user.last_login = timezone.datetime.now()
                django_login(request, user)
                return redirect(reverse('index'))
            else:
                # 发送激活邮件
                async_send_email.delay(email=email, verify_type=0)
                response = render(request, 'users/notification.html', context={
                    'title': '邮箱激活',
                    'msg': '非常抱歉！您的账号尚未激活，请前往邮箱激活账号（链接在5分钟后或者完成相关操作后失效），'
                           '激活邮件已发送至邮箱' + email + '，请',
                    'notify_type': 'login_email',
                    'mail_website': mail_website,
                    'target_email': email,
                    'send_email_type': '0',
                })
                response.delete_cookie("loginPostToken")
                return response
        else:
            return redirect(reverse('forbidden_403'))
    else:
        return redirect(reverse('forbidden_403'))


@login_required(login_url='/users/login/')
def logout(request):
    if request.method == 'GET':
        django_logout(request)
        return redirect(reverse('index'))
    else:
        return redirect(reverse('forbidden_403'))


def forgetpwd(request):
    if request.method == 'GET':
        response = render(request, 'users/forgetpwd.html', context={
            'title': '找回密码',
        })
        response.set_signed_cookie("forgetpwdPostToken", "allow", salt="RECONSTRUCTION_IS_PAINFUL", max_age=600)
        return response
    elif request.method == 'POST':
        email = request.POST.get("email")
        # 查询邮箱
        mail_website = db_tool.get_mail_site(email)
        if request.get_signed_cookie("forgetpwdPostToken", default=None, salt="RECONSTRUCTION_IS_PAINFUL"):
            # 异步发送重置密码邮箱链接
            async_send_email.delay(email=email, verify_type=1)

            response = render(request, 'users/notification.html', context={
                'title': '重置密码',
                'msg': '请前往邮箱重置密码（激活链接将在以下情况失效：5分钟内未完成重置密码操作、重新发送重置密码邮件、完成重置密码操作）, '
                       '邮件已发送至邮箱' + email + '，请',
                'notify_type': 'login_email',
                'mail_website': mail_website,
                'target_email': email,
                'send_email_type': '1',
            })
            response.delete_cookie("forgetpwdPostToken")

            return response
        else:
            response = render(request, 'users/notification.html', context={
                'title': '重置密码',
                'msg': '请前往邮箱重置密码（激活链接将在以下情况失效：5分钟内未完成重置密码操作、重新发送重置密码邮件、完成重置密码操作）, '
                       '邮件已发送至邮箱' + email + '，请',
                'notify_type': 'login_email',
                'mail_website': mail_website,
                'target_email': email,
                'send_email_type': '1',
            })
            response.delete_cookie("forgetpwdPostToken")

            return response
    else:
        return redirect(reverse('forbidden_403'))


def resetpwd(request, code):
    # 该get请求是邮件中的，因此需要验证请求携带的验证码是否有效
    if request.method == 'GET':
        email = request.GET.get('email')
        code_valid, email_ver = db_tool.is_valid_code(email, code)
        # 如果验证码有效
        if code_valid:
            response = render(request, 'users/resetpwd.html', context={
                'email': email,
                'verify_type': 1,
            })
            response.set_signed_cookie("resetpwdPostToken", "allow", salt="RECONSTRUCTION_IS_PAINFUL", max_age=600)
            # 为了安全，在设置允许重置密码提交的同时还需要验证get请求验证码的有效性
            code_time = code + "@time_" + str(int(time.time()))
            code_byte = bytes(code_time, encoding="utf8")
            token = str(f.encrypt(code_byte), encoding='utf8')
            response.set_signed_cookie("resetpwdAuthPostToken", token, salt="RECONSTRUCTION_IS_PAINFUL", max_age=420)

            return response
        # 如果验证码已失效
        else:
            return redirect(reverse('forbidden_403'))
    # 对于该post请求，只有在来自get请求的验证码有效的情况下才能够进行提交
    elif request.method == 'POST':
        email = request.POST.get('email')
        verify_type = request.POST.get('verify_type')
        new_password = request.POST.get('password1')
        resetpwdPostToken = request.get_signed_cookie("resetpwdPostToken", default=None, salt="RECONSTRUCTION_IS_PAINFUL")
        resetpwdAuthPostToken = request.get_signed_cookie("resetpwdAuthPostToken", default=None, salt="RECONSTRUCTION_IS_PAINFUL")

        # 如果允许提交
        if resetpwdPostToken and resetpwdAuthPostToken:
            # 校验get请求验证码的有效性
            token_bytes = bytes(resetpwdAuthPostToken, encoding='utf8')
            code_time = str(f.decrypt(token_bytes), encoding='utf8')
            resetpwd_code = code_time[:code_time.find("@time_")]
            code_valid = db_tool.is_valid_code(email, resetpwd_code)[0]
            # 如果get请求的验证码有效
            if code_valid:
                user = User.objects.filter(Q(email=email))[0]
                user.set_password(new_password)
                user.save()
                response = render(request, 'users/notification.html', context={
                    'title': '完成重置',
                    'msg': '恭喜, 重置密码成功！请',  # '登录'二字作为链接
                    'notify_type': 'login_iget',
                })
                response.delete_cookie("resetpwdPostToken")
                response.delete_cookie("resetpwdAuthPostToken")
                # 使用完get请求的验证码后立即使其失效
                db_tool.set_code_invalid(email, verify_type, resetpwd_code)

                return response
            else:
                return redirect(reverse('forbidden_403'))
        else:
            return redirect(reverse('forbidden_403'))
    else:
        return redirect(reverse('forbidden_403'))


def get_user_info(request):
    if request.method == 'GET':
        return render(request, 'users/usercenter_info.html')
    else:
        return redirect(reverse('forbidden_403'))


def get_user_fav(request):
    if request.method == 'GET':
        # 获取收藏的数据
        fav_prd_serial_number_list = UserFavorite.objects.filter(user_id=request.user.id).values_list('fav_prd_serial_number', flat=True)
        products = db_tool._get_products_by_serial_number(fav_prd_serial_number_list)
        products_info = db_tool._get_product_dict_info_list(products)

        return render(request, 'users/usercenter_fav.html', context={
            "products_info": products_info,
            "products_length": len(products_info),
        })
    else:
        return redirect(reverse('forbidden_403'))


def get_user_views(request):
    views_list = ViewStatistics.objects.all()
    serial_number_list = []

    for views in views_list:
        print(views.user_ids)
        if len(str(views.user_ids)) == 1 and str(views.user_ids) == str(request.user.id):
            serial_number_list.append(views.prd_serial_number)
        elif request.user.id in views.user_ids.split('#'):
            serial_number_list.append(views.prd_serial_number)
        else:
            print("not in")
    products = db_tool._get_products_by_serial_number(serial_number_list)
    product_info_list = db_tool._get_product_dict_info_list(products)
    print(len(product_info_list))

    return render(request, 'users/usercenter_views.html', context={
        'product_info_list': product_info_list
    })


def get_user_msg(request):
    if request.method == 'GET':
        return render(request, 'users/usercenter_msg.html')
    else:
        return redirect(reverse('forbidden_403'))


def ch_headimg(request):
    if request.method == 'POST':
        img = request.FILES.get("img_file")
        path = str(request.user.head_img).split('/')
        # 用于更换头像后删除原有头像文件
        old_headimg_path = settings.MEDIA_ROOT + "/" + "/".join(path)
        # 新头像路径：用于在上传文件的过程中抛出异常时进行回滚
        new_headimg_path = ''
        path[-1] = request.POST.get("img_name")
        path = "/".join(path)
        url = settings.MEDIA_ROOT + "/" + path

        try:
            with open(url, "wb") as f:
                for chunk in img.chunks():
                    f.write(chunk)
            # 对新头像进行重命名
            avatar_suffix = "." + path.split(".")[1]
            path_dir = settings.MEDIA_ROOT + "/" + path[0: path.find('/')]
            new_name = "id_" + str(request.user.id) + "_" + \
                       str(time.strftime("%Y%m%d_%H%M%S", time.localtime())) + avatar_suffix
            new_url = os.path.join(path_dir, new_name)
            new_headimg_path = new_url
            os.rename(url, new_url)

            request.user.head_img = path[0: path.find('/') + 1] + new_name
            request.user.save()
        except Exception:
            traceback.print_exc()
            os.remove(new_headimg_path)
            return JsonResponse({
                "completed": "false",
                "msg": "头像上传失败，请重试！",
            })
        else:
            # 确认将新头像保存到数据库后，再删除旧头像。需要注意的是，如果是系统默认头像则不删除
            img_name = old_headimg_path.split('/')[-1]
            if os.path.exists(new_headimg_path) and img_name != 'head_img_sys.jpeg':
                os.remove(os.path.join(settings.MEDIA_ROOT, old_headimg_path))
            return JsonResponse({
                "completed": "true",
                "msg": "头像上传成功",
            })
    else:
        return redirect(reverse('index'))


def chemail(request):
    if request.method == 'GET':
        response = render(request, 'users/chemail.html', context={
            "verify_type": 3,
        })
        response.set_signed_cookie("oldemailPostToken", "allow", salt="RECONSTRUCTION_IS_PAINFUL", max_age=600)

        return response
    # 对于验证旧邮箱及提交新邮箱的post请求均由该部分的代码处理
    elif request.method == 'POST':
        code = request.POST.get("verifycode")
        verify_type = request.POST.get("verify_type")
        old_email = request.POST.get("old_email")
        new_email = request.POST.get("new_email")
        is_check_old = True if (old_email and (not new_email)) else False
        oldemailPostToken = request.get_signed_cookie("oldemailPostToken", default=None, salt="RECONSTRUCTION_IS_PAINFUL")
        newemailPostToken = request.get_signed_cookie("newemailPostToken", default=None, salt="RECONSTRUCTION_IS_PAINFUL")

        # 提交旧邮箱请求
        if is_check_old and oldemailPostToken:
            # 数据库校验验证码。实际上并不需要再进行校验（提交之前已经进行了ajax校验），但为了安全可以再执行一次校验
            # 执行相应的跳转
            response = render(request, 'users/chemail_newemail.html', context={
                "verify_type": 3,
            })
            # 删除名为oldemailPostToken的cookie
            response.delete_cookie("oldemailPostToken")
            # 此处解决一个问题：在请求'users/chemail_newemail.html'页面时，需要有对应的有效验证码，用以防止用户直接访问'users/chemail_newemail.html'页面
            # 思路如下：对通过了post请求的验证码进行加密处理通过cookie传给'users/chemail_newemail.html'页面请求，然后对cookie进行相应的解密得到
            # 验证码，然后再从数据库中进行验证码校验，若验证码存在，则可以访问'users/chemail_newemail.html'页面，否则重定向到原页面
            code_time = code + "@time_" + str(int(time.time()))
            code_byte = bytes(code_time, encoding="utf8")
            token = str(f.encrypt(code_byte), encoding='utf8')
            response.set_signed_cookie("newemailPostToken", token, salt="RECONSTRUCTION_IS_PAINFUL", max_age=420)

            return response
        # 提交新邮箱请求
        elif (not is_check_old) and newemailPostToken:
            # 在使用新邮箱的验证码后立即将验证码设为无效
            db_tool.set_code_invalid(
                email=new_email,
                code_type=verify_type,
                code=code
            )
            # 旧邮箱
            replace_email = request.POST.get('replace_email')
            token_bytes = bytes(newemailPostToken, encoding='utf8')
            code_time = str(f.decrypt(token_bytes), encoding='utf8')
            old_code = code_time[:code_time.find("@time_")]
            code_valid = db_tool.is_valid_code(replace_email, old_code)[0]
            # 旧邮箱验证码有效则执行提交
            if code_valid:
                request.user.email = new_email
                request.user.username = new_email
                request.user.save()

                response = render(request, 'users/usercenter_info.html')
                response.delete_cookie("newemailPostToken")
                # 在使用完旧邮箱验证码后立即使其失效
                db_tool.set_code_invalid(
                    email=replace_email,
                    code_type=verify_type,
                    code=old_code
                )

                return response
            # 旧邮箱验证码无效则回到旧邮箱提交页面
            else:
                response = render(request, 'users/chemail.html', context={
                    "verify_type": 3,
                })
                response.set_signed_cookie("oldemailPostToken", "allow", salt="RECONSTRUCTION_IS_PAINFUL", max_age=600)
                response.delete_cookie("newemailPostToken")

                return response
        # 如果不是以上两种情况，那么回到旧邮箱验证页面页面
        else:
            response = render(request, 'users/chemail.html', context={
                "verify_type": 3,
            })
            response.set_signed_cookie("oldemailPostToken", "allow", salt="RECONSTRUCTION_IS_PAINFUL", max_age=600)
            response.delete_cookie("newemailPostToken")

            return response


def chpwd(request):
    if request.method == 'GET':
        response = render(request, 'users/chpwd.html', context={
            'verify_type': 2,
        })
        response.set_signed_cookie("chpwdPostToken", "allow", salt="RECONSTRUCTION_IS_PAINFUL")
        return response
    elif request.method == 'POST':
        chpwdPostToken = request.get_signed_cookie("chpwdPostToken", default=None, salt="RECONSTRUCTION_IS_PAINFUL")
        new_password = request.POST.get('password1')
        email = request.user.email
        code = request.POST.get('verifycode')
        verify_type = 2

        if chpwdPostToken:
            request.user.set_password(new_password)
            request.user.save()
            db_tool.set_code_invalid(email, verify_type, code)
            # 修改成功后注销登录
            django_logout(request)
            response = render(request, 'users/notification.html', context={
                'title': '密码修改',
                'msg': '恭喜, 密码修改成功！请',  # '登录'二字作为链接
                'notify_type': 'login_iget',
            })
            response.delete_cookie("chpwdPostToken")
            return response
        else:
            response = render(request, 'users/notification.html', context={
                'title': '密码修改',
                'msg': '恭喜, 密码修改成功！请',  # '登录'二字作为链接
                'notify_type': 'login_iget',
            })
            response.delete_cookie("chpwdPostToken")
            return response
    else:
        return redirect(reverse('forbidden_403'))


def get_notification(request, context):
    return render(request, 'users/notification.html', context=context)


class CustomBackend(ModelBackend):
    """自定义用户验证"""
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 使用用户名或邮箱均可登录
        try:
            user = User.objects.get(Q(username=username) | Q(email=username))
            if user.check_password(password):
                return user
        except Exception:
            return None
