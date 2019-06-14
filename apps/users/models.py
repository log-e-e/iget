from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """用户信息表. 用于存储用户信息.

    Attributes:
        :var email: 邮箱. 用于账号注册, 登录, 找回密码, 修改密码, 邮箱换绑时的邮箱账号验证
        :var pwd: 密码. 账号登录所需
        :var nickname: 用户昵称. 默认为邮箱, 可在用户中心自行修改
        :var head_img: 用户头像. 默认为系统头像, 修改同上
        :var gender: 用户性别. 默认为男性, 可在用户中心自行修改
        :var create_time: 创建时间. 用户注册账号的时间, 一旦用户创建完成则时间不再改变
        :var update_time: 最后修改时间. 用户对于用户信息表中的任意字段的修改都会引起该字段的变动
    """
    # 在继承了AbstractUser后email与password字段则课不必要, AbstractUser中已存在, 当然也可进行覆盖

    # 最大长度为100个字符; 约束条件：unique
    # email = models.EmailField(verbose_name='绑定邮箱', max_length=100, unique=True)
    # 加密
    # password = models.CharField(verbose_name='登录密码', max_length=254)

    # 账号状态：之所以增加离线及在线状态, 是因为在系统的站内消息功能上需要：当系统需要发送消息时, 只对在线的用户会直接发送消息
    # 在线用户如何检测新消息未读？

    # 原本想实现单点登录, 但是时间不允许，以后再做，而且实现单点登录并不是通过字段记录登录状态
    # 判断用户登录方法之一：在网页中嵌入： {% if user.is_authenticated %} 条件判断即可,该方法只是判断用户登录状态, 并未实现单点登录
    # status = models.IntegerField(verbose_name='账号状态',
    #                              choices=((0, '账号未激活'), (1, '离线'), (2, '在线')))

    # 覆盖AbstractUser的is_active字段, 值设为False
    is_active = models.BooleanField(verbose_name='是否激活', default=False)
    # 昵称长度不超过10个字符, default='user_(随机字母、数字组合)'. blank取消填写验证, null设置数据库字段可为空
    nickname = models.CharField(verbose_name='昵称', max_length=20, blank=True, null=True)

    # 用户的初始头像：暂时不知道如何在此处设置默认图像, 默认图像的问题在注册输入数据时进行解决
    # head_img = models.ImageField(verbose_name='头像', width_field=50, height_field=50, upload_to='users/',
    # max_length=1024, default='system_default/head_img_sys.jpg')

    # 注：在ImageField()中，如果设置width_field和height_field，在admin后台添加图片时会报错：getattr(): attribute name must be string
    # head_img = models.ImageField(
    # verbose_name='头像', width_field=70, height_field=70, upload_to='users/', blank=True, null=True)
    # 正确的做法应为如下：
    head_img = models.ImageField(verbose_name='头像', upload_to='users/', blank=True, null=True)

    gender = models.IntegerField(verbose_name='性别', choices=((0, '男'), (1, '女'),), default=0)
    create_time = models.DateTimeField(verbose_name='注册时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name='最后修改时间', auto_now=True)

    def __str__(self):
        return self.email

    class Meta(AbstractUser.Meta):
        ordering = ['create_time', ]
        verbose_name = '用户账号'
        verbose_name_plural = verbose_name


# 消息字段实现的功能是：1.系统向全体用户发送消息 2.系统向某个用户发送特定消息
# 问题来了：如何检查公共消息和私有消息？
# 公共消息检查：登录时遍历所有全员消息；在线时通过实时消息检查
# 私有消息检查：无论是否在线，都会在MessageLog表中插入消息数据并标记为未读状态。用户在线时则实时消息检查，登录时则遍历未读消息即可。
# 为何分为两张表？答：为了解决公共消息发送问题，最大程度提升公共消息发送的有效性，同时解决了公共消息的读取状态问题
# 对于MessageReadLog表，它可以认为是消息阅读记录表，用户记录用户对消息的阅读状态
class MessageReadLog(models.Model):
    user_id = models.IntegerField(verbose_name='消息接收者id')
    msg_id = models.IntegerField(verbose_name='消息id')
    # 境况：用户登录时检测未读消息, 用户在使用系统过程中更新未读消息(即在系统有新通知时，向所有在线用户发送消息、对于离线用户则在其下次登录时发送)
    status = models.IntegerField(verbose_name='消息状态', choices=((-1, '删除'), (0, '未读'), (1, '已读')), default=0)

    def __str__(self):
        user_list = User.objects.filter(pk=self.user_id)
        user_email = user_list[0].email if user_list else 'iget_admin@163.com'
        return user_email

    class Meta:
        ordering = ['user_id', ]
        verbose_name = '消息阅读日志'
        verbose_name_plural = verbose_name


class Message(models.Model):
    title = models.CharField(verbose_name='消息标题', max_length=100)
    content = models.TextField(verbose_name='消息内容')
    # # 消息发送者id：默认为系统发送, 实际上对于本项目而言, 该字段可以不要
    # send_id = models.IntegerField(verbose_name='消息发送者id', default=0)
    send_type = models.IntegerField(verbose_name='消息发送类型', choices=((0, '公共消息'), (1, '个人消息')), default=0)
    send_time = models.DateField(verbose_name='消息发送时间', auto_now_add=True)
    # 设置消息的时效性截止时间：如果用户在有效时间内未登录, 则该消息不会发送给用户
    end_time = models.DateField(verbose_name='消息有效性截止时间')

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title', ]
        verbose_name = '消息阅读日志'
        verbose_name_plural = verbose_name


class EmailVerification(models.Model):
    """邮箱验证表. 用于用户操作之前的邮箱安全验证

    Attributes:
        :var target_email: 目标邮箱
        :var verify_type: 验证码类型. 包括：注册, 密码修改, 邮箱换绑
        :var code: 验证码链接. 点击链接后则通过验证从而进入下一步操作
        :var send_time: 发送时间
    """
    to_email = models.EmailField(verbose_name='目标邮箱', max_length=100)
    # 激活邮箱(注册及登录验证账号未激活时发送邮箱激活邮件), 修改密码（忘记密码以修改密码, 个人中心修改密码）, 修改邮箱
    verify_type = models.IntegerField(verbose_name='验证类型',
                                      choices=((0, 'activate'), (1, 'reset_pwd'), (2, 'ch_pwd'), (3, 'che_email')))
    # 统一为链接, 验证码加密问题
    code = models.CharField(verbose_name='邮箱验证码', max_length=254)
    send_time = models.DateTimeField(verbose_name='发送时间', auto_now_add=True)
    # is_valid与failure_time都是用于限制重复点击链接请求, 保证账号安全
    # 点击后失效
    is_valid = models.BooleanField(verbose_name='验证码是否有效', default=True)

    def __str__(self):
        return self.code

    class Meta:
        ordering = ['send_time', ]
        verbose_name = '邮箱验证码'
        verbose_name_plural = verbose_name


class MailWebSite(models.Model):
    """邮箱信息表"""
    mail_site = models.CharField(verbose_name='邮箱登录链接', max_length=100)
