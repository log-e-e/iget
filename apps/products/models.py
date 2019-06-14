from django.db import models


class ProductBrand(models.Model):
    """产品品牌

    Attributes:
        :var name_cn: 品牌的中文名称
        :var name_en: 品牌的英文名称
        :var site_link: 品牌的官网链接
    """
    name_cn = models.CharField(verbose_name='中文名称', max_length=20, unique=True)
    name_en = models.CharField(verbose_name='英文名称', max_length=20, unique=True)
    site_link = models.CharField(verbose_name='官网链接', max_length=254, unique=True)
    status = models.IntegerField(verbose_name='品牌状态', choices=((0, '停售'), (1, '在售')), default=1)

    def __str__(self):
        return self.name_cn

    class Meta:
        ordering = ['name_cn', ]
        verbose_name = '品牌'
        verbose_name_plural = verbose_name


class ProductSeries(models.Model):
    """产品系列. 主要用于一系列具有相同特性的产品, 也是对应系列的卖点

    Attributes:
        :var product_brand: 所属的品牌
        :var name: 系列名称
        :var introduction: 系列的特性简介
    """
    # 系列与品牌是一对多关系, 同时还需要使用品牌字段数据, 因此设为外键
    brand_id = models.IntegerField(verbose_name='所属品牌')
    name = models.CharField(verbose_name='系列名称', max_length=254, unique=True)
    intro = models.CharField(verbose_name='系列简介', max_length=254, blank=True, null=True)
    status = models.IntegerField(verbose_name='系列状态', choices=((0, '停售'), (1, '在售')), default=1)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name', ]
        verbose_name = '产品系列'
        verbose_name_plural = verbose_name


class ProductConfiguration(models.Model):
    """产品配置. 一种配置对应一种产品"""
    # 产品编号
    prd_serial_number = models.CharField(verbose_name='产品编号', max_length=254, unique=True)
    # 基本参数
    time_to_market = models.CharField(verbose_name='上市时间', max_length=64)
    product_type = models.CharField(verbose_name='产品定位类型', max_length=256)
    os_type = models.CharField(verbose_name='操作系统', max_length=254)
    # 处理器
    cpu_series = models.CharField(verbose_name='CPU系列', max_length=128)
    cpu_type = models.CharField(verbose_name='CPU型号', max_length=128)
    cpu_clock_speed = models.CharField(verbose_name='CPU主频', max_length=20)
    cpu_turbo = models.CharField(verbose_name='CPU睿频', max_length=20)
    core_num = models.CharField(verbose_name='核心数描述', max_length=50)
    # 存储
    memory_cap = models.CharField(verbose_name='内存容量', max_length=32)
    hd_type = models.CharField(verbose_name='硬盘类型', max_length=128)
    hd_cap = models.CharField(verbose_name='硬盘容量', max_length=128)
    # 显卡
    graphics_type = models.CharField(verbose_name='显卡性能等级', max_length=64)
    graphics_cap = models.CharField(verbose_name='显存容量', max_length=32)
    # 显示屏
    sc_size = models.CharField(verbose_name='屏幕尺寸', max_length=20)
    screen_resolution = models.CharField(verbose_name='分辨率', max_length=32)
    # 电源：电池类型分为锂电池、聚合物电池（镍镉电池、镍氢电池）
    battery_type = models.CharField(verbose_name='电池类型', max_length=128)
    life_time_intro = models.CharField(verbose_name='续航时间描述', max_length=100)
    # 外观
    color = models.CharField(verbose_name='颜色', max_length=64)
    weight = models.CharField(verbose_name='重量', max_length=64)

    def __str__(self):
        return '配置_' + str(self.id)

    class Meta:
        ordering = ['id', ]
        verbose_name = '配置'
        verbose_name_plural = verbose_name


class Product(models.Model):
    """产品. 产品 = 品牌 + 系列 + 配置"""
    prd_serial_number = models.CharField(verbose_name='产品编号', max_length=254, unique=True)
    name = models.CharField(verbose_name='产品名称', max_length=256)
    img = models.ImageField(verbose_name='产品图片', width_field=70, height_field=70, upload_to='products/',
                            blank=True, null=True)
    img_url = models.URLField(verbose_name='产品图片链接', max_length=254,
                              default='https://2d.zol-img.com.cn/product/190_80x60/227/ce8Ml2FxDOZE.jpg')
    brand_id = models.IntegerField(verbose_name='所属品牌')
    series_id = models.IntegerField(verbose_name='所属系列')
    feature_desc = models.CharField(verbose_name='特性描述', max_length=200, blank=True, null=True)
    status = models.IntegerField(verbose_name='产品状态', choices=((0, '停售'), (1, '在售')), default=1)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name', ]
        verbose_name = '产品'
        verbose_name_plural = verbose_name
