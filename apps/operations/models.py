from django.db import models

from users.models import User


class UserFavorite(models.Model):
    """用户收藏记录表

    Attributes:
        :var price_when_fav: 收藏时的售价, 作为收藏后的价格变动的对比. 参考慢慢买
    """
    # 用户与收藏记录是一对多关系, 且需要用到用户字段数据, 故设为外键
    user_id = models.IntegerField(verbose_name='所属用户')
    # 通过字段favorite_id及favorite_type来确定收藏的类型
    # 之所以要确定收藏类型, 是因为需要显示不同的信息（产品和商品的价格描述不同, 电商平台信息不同等等）
    # 即：价格字段信息不同, 电商平台描述不同
    fav_prd_serial_number = models.CharField(verbose_name='产品编号', max_length=200)
    fav_type = models.IntegerField(verbose_name='收藏类型', choices=((0, 'goods'), (1, 'products')))
    price_when_fav = models.IntegerField(verbose_name='收藏时的售价')
    add_time = models.DateTimeField(verbose_name='添加收藏时的时间', auto_now_add=True)

    def __str__(self):
        user_list = User.objects.filter(pk=self.user_id)
        user_email = user_list[0].email if user_list else 'iget_admin@163.com'
        return user_email

    class Meta:
        ordering = ['user_id', ]
        verbose_name = '用户收藏记录'
        verbose_name_plural = verbose_name


class UserViewHistory(models.Model):
    """用户浏览记录表"""
    # 用户与浏览记录对应关系为一对多
    user_id = models.IntegerField(verbose_name='所属用户')
    # 同UserFavorite类似
    obj_id = models.IntegerField(verbose_name='商品/产品id')
    obj_type = models.IntegerField(verbose_name='类型', choices=((0, 'goods'), (1, 'products')))
    view_time = models.DateTimeField(verbose_name='查看时间', auto_now_add=True)

    def __str__(self):
        user_list = User.objects.filter(pk=self.user_id)
        user_email = user_list[0].email if user_list else 'iget_admin@163.com'
        return user_email

    class Meta:
        ordering = ['user_id', ]
        verbose_name = '用户浏览记录'
        verbose_name_plural = verbose_name
