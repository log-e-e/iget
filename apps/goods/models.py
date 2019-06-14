from django.db import models
from products.models import Product


class Mall(models.Model):
    """商城"""
    name = models.CharField(verbose_name='官网名称', max_length=20, unique=True)
    official_link = models.CharField(verbose_name='官网链接', max_length=200, unique=True)
    status = models.IntegerField(verbose_name='商城状态', choices=((-1, '停止服务'), (0, '服务中')), default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name', ]
        verbose_name = '商城'
        verbose_name_plural = verbose_name


# 使用对应产品提供的图片可以节约资源，本项目的目的在于提供比价信息
class Goods(models.Model):
    """商品. 即商城上在售的商品

    Attributes:
        :var buy_link: 购买链接的唯一性符合同种商品可在同一个商城上的不同商家销售的要求
    """
    name = models.CharField(verbose_name='名称', max_length=200)
    price = models.IntegerField(verbose_name='价格', default=0)
    # 关于商品图片：从产品中获取图片即可, 故可不必存储图片
    # gds_img = models.ImageField(verbose_name='商品图片', upload_to='goods/', max_length=1024, blank=True, null=True)

    # 商品链接：区分同一个商城的不同卖家. 注意：对于有unique约束的CharField()长度不超过255个字符
    buy_link = models.CharField(verbose_name='购买链接', max_length=254, unique=True)
    # 产品与商品属于一对多关系, 本应设为外键, 但是为了消除在数据迁移过程中外键约束带来的影响, 取消外键的使用
    # 产品与商城商品二者之间的存在关系属于弱相关：二者皆可独立存在（如果设置ForeignKey, 就会影响数据的存在）,
    # 但是商品的配置信息需要用到对应产品的配置信息及图片等, 故需要一个字段
    prd_serial_number = models.CharField(verbose_name='所属产品编号', max_length=254, unique=True)
    # 具体的商品是依赖于具体的商城的, 而一个商城中可以有多个商品（一对多）, 故为外键
    mall_id = models.IntegerField(verbose_name='所属商城')
    status = models.IntegerField(verbose_name='商品状态', choices=((-1, '已下架'), (0, '在售')), default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['prd_serial_number', ]
        verbose_name = '商品'
        verbose_name_plural = verbose_name
