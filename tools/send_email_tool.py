import traceback
from random import randrange

from django.core.mail import EmailMultiAlternatives
from django.db.models import Q

from iget.settings import EMAIL_FROM
from users.models import EmailVerification


def create_random_code(code_length):
    code_source = '2134567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'
    code = ''
    for i in range(code_length):
        e = code_source[randrange(0, len(code_source))]
        code += e
    return code


def send_email_code(email, verify_type):
    """发送邮箱验证：安全问题——可以随便伪造验证码。。。。
    问题：在发送的html格式的邮件中, text_content的内容并不会出现在邮箱正文中, 该如何处理text_content？
    """
    try:
        code = create_random_code(randrange(5, 9))
        subject, from_email, to_list = '', '', []
        text_content, html_content = '', ''
        if verify_type == -1:
            return False
        elif verify_type == 0:
            # 发送html格式邮件
            mail_list = [email, ]
            subject, from_email, to_list = '账号激活', EMAIL_FROM, mail_list
            text_content = '请点击激活链接完成账号注册：'
            html_content = '<p>请点击激活链接完成账号注册，链接在5分钟后或者完成相关操作后失效：' \
                           '<a href="http://127.0.0.1:8000/users/activate_account/' + code + '/?email=' + email  + \
                           '" target="_blank">激活账号</a></p>'
        elif verify_type == 1:
            mail_list = [email, ]
            subject, from_email, to_list = '重置密码', EMAIL_FROM, mail_list
            text_content = '请点击链接以重置密码：'
            html_content = '<p>请点击链接以重置密码，链接在5分钟后或者完成相关操作后失效：' \
                           '<a href="http://127.0.0.1:8000/users/resetpwd/' + code + '/?email=' + email + \
                           '" target="_blank">重置密码</a></p>'
        elif verify_type == 2:
            mail_list = [email, ]
            subject, from_email, to_list = '修改密码', EMAIL_FROM, mail_list
            text_content = '您好，请查收您的验证码：'
            html_content = '<div>这是您本次操作的验证码，验证码将在5分钟后或者完成相关操作后失效：' \
                           '<p style="color: black; font-size: 25px;">' + code + '</p></div>'
        elif verify_type == 3:
            mail_list = [email, ]
            subject, from_email, to_list = '换绑邮箱', EMAIL_FROM, mail_list
            text_content = '您好，请查收您的验证码：'
            html_content = '<div>这是您本次操作的验证码，验证码将在5分钟后或者完成相关操作后失效：' \
                           '<p style="color: black; font-size: 25px;">' + code + '</p></div>'
        else:
            return False

        # 前四个参数是必填项
        html_email = EmailMultiAlternatives(subject, text_content, from_email, to_list)
        html_email.attach_alternative(html_content, 'text/html')
        result = html_email.send()

        if result == 1:
            verify = EmailVerification()
            verify.to_email = email
            verify.verify_type = verify_type
            verify.code = code
            verify.save()
            _invalidate_code(email=email, code_type=verify_type, except_code=code)
        else:
            raise Exception
    except Exception:
        traceback.print_exc()
        return False
    else:
        return True

    # 发送纯文本邮件：
    # send_mail(
    #     subject=subject,
    #     message=message,
    #     from_email=EMAIL_FROM,
    #     recipient_list=mail_list,
    #     fail_silently=False,
    #     auth_user=EMAIL_HOST_USER,
    #     auth_password=EMAIL_HOST_PASSWORD,
    #     connection=None,
    # )


def _invalidate_code(email, code_type, except_code):
    codes = EmailVerification.objects.filter(
        Q(to_email=email) & Q(verify_type=code_type) & Q(is_valid=True) & ~Q(code=except_code)
    )
    for code in codes:
        code.is_valid = False
        code.save()
