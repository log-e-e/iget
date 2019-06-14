from django.db import models
from products.models import Product, ProductBrand


# 说明：外键的使用场景是对存在强关系的两个实体间的约束
class PriceStatistics(models.Model):
    """产品售价信息统计. 用于统计各大商城中对应的商品的价格信息

    Attributes:
        :var products: unique, 外键设置须重新考虑
    """
    # 一条数据对应一款产品, 故该表需要用到Product类中的字段并且在表中唯一, 因此不宜用ForeignKey()而应用OneToOneField()
    # products = models.ForeignKey(Product, verbose_name='所属产品', on_delete=models.CASCADE, unique=True)
    prd_serial_number = models.CharField(verbose_name='产品编号', max_length=254, unique=True)
    official_price = models.IntegerField(verbose_name='官方报价', default=0)
    lowest_price = models.IntegerField(verbose_name='最低售价', default=0)
    highest_price = models.IntegerField(verbose_name='最高售价', default=0)
    mall_num = models.IntegerField(verbose_name='在售商城数', default=0)
    update_date = models.DateField(verbose_name='信息更新时间', auto_now=True)

    def __str__(self):
        product_list = Product.objects.filter(prd_serial_number=self.prd_serial_number)
        product_name = product_list[0].name if product_list else 'null'

        return product_name

    class Meta:
        ordering = ['prd_serial_number', ]
        verbose_name = '产品售价信息统计'
        verbose_name_plural = verbose_name


class FavoriteStatistics(models.Model):
    """产品收藏次数统计. 针对用户的收藏操作做出的次数统计, 以此数据作为依据为用户推荐产品"""
    # products = models.ForeignKey(Product, verbose_name='所属产品', on_delete=models.CASCADE, unique=True)
    prd_serial_number = models.CharField(verbose_name='产品编号', max_length=254, unique=True)
    user_ids = models.CharField(verbose_name='用户id字符串', max_length=1600)
    # 如果是第一次收藏产品, 那么默认的收藏次数为1
    fav_num = models.IntegerField(verbose_name='收藏次数', default=1)
    update_date = models.DateField(verbose_name='信息更新时间', auto_now=True)

    def __str__(self):
        product_list = Product.objects.filter(prd_serial_number=self.prd_serial_number)
        product_name = product_list[0].name if product_list else 'null'

        return product_name

    class Meta:
        ordering = ['fav_num', ]
        verbose_name = '产品收藏次数统计'
        verbose_name_plural = verbose_name


class ViewStatistics(models.Model):
    """产品详情页浏览次数统计. 同收藏统计作用一样"""
    # products = models.ForeignKey(Product, verbose_name='所属产品', on_delete=models.CASCADE, unique=True)
    prd_serial_number = models.CharField(verbose_name='产品编号', max_length=254, unique=True)
    user_ids = models.CharField(verbose_name='用户id字符串', max_length=1600)
    view_num = models.IntegerField(verbose_name='详情查看次数', default=1)
    update_date = models.DateField(verbose_name='信息更新时间', auto_now=True)

    def __str__(self):
        product_list = Product.objects.filter(prd_serial_number=self.prd_serial_number)
        product_name = product_list[0].name if product_list else 'null'

        return product_name

    class Meta:
        ordering = ['view_num', ]
        verbose_name = '产品详情查看次数统计'
        verbose_name_plural = verbose_name


class ProductRank(models.Model):
    """各种笔记本排行榜. 参照：http://top.zol.com.cn/compositor/notebook.html """
    ranking = models.IntegerField(verbose_name='排名')
    # products = models.ForeignKey(Product, verbose_name='产品', on_delete=models.CASCADE)
    prd_serial_number = models.CharField(verbose_name='产品编号', max_length=254, unique=True)
    composite_score = models.FloatField(verbose_name='综合评分')
    update_date = models.DateField(verbose_name='信息更新时间', auto_now=True)
    ranking_type = models.IntegerField(
        verbose_name='所属排行榜',
        choices=((0, '热门笔记本电脑排行榜'), (1, '上升最快的笔记本电脑排行榜'),
                 # 品牌排行榜
                 (2, '联想笔记本电脑排行榜'), (3, '戴尔笔记本电脑排行榜'),
                 (4, 'ThinkPad笔记本电脑排行榜'), (5, '惠普笔记本电脑排行榜'),
                 (6, '华为笔记本电脑排行榜'), (7, '苹果笔记本电脑排行榜'),
                 (8, '华硕笔记本电脑排行榜'), (9, '雷神笔记本电脑排行榜'),
                 (10, 'Alienware笔记本电脑排行榜'),
                 # 产品特性排行榜
                 (11, '游戏本排行榜'), (12, '商务办公本排行榜'), (13, '轻薄本排行榜'), (14, '超极本排行榜'),
                 (15, '二合一笔记本排行榜'), (16, '校园学生本排行榜'), (17, '17英寸笔记本电脑排行榜'),
                 (18, 'i9处理器笔记本排行榜'), (19, 'i7处理器笔记本排行榜'),
                 (20, 'i5处理器笔记本排行榜'), (21, '发烧级显卡笔记本排行榜'),
                 (22, '性能级显卡笔记本排行榜'), (23, '8G内存笔记本排行榜'),
                 (24, '4G内存笔记本排行榜'), (25, '全高清笔记本排行榜'),
                 (26, '固态硬盘笔记本排行榜'), (27, '混合硬盘笔记本排行榜'),
                 # 价格区间
                 (28, '3500-3999元笔记本排行榜'), (29, '4000-4999元笔记本排行榜'), (30, '5000-5999元笔记本排行榜'),
                 (31, '6000-7999元笔记本排行榜'), (32, '8000元笔记本排行榜'), ))

    def __str__(self):
        product_list = Product.objects.filter(prd_serial_number=self.prd_serial_number)
        product_name = product_list[0].name if product_list else 'null'

        return product_name

    class Meta:
        ordering = ['ranking_type', ]
        verbose_name = '产品各类排行榜'
        verbose_name_plural = verbose_name


class BrandRank(models.Model):
    """笔记本品牌排行榜"""
    ranking = models.IntegerField(verbose_name='排名')
    # brand = models.ForeignKey(ProductBrand, verbose_name='笔记本品牌id', on_delete=models.CASCADE, unique=True)
    brand_id = models.IntegerField(verbose_name='对应的品牌')
    composite_score = models.FloatField(verbose_name='综合评分')
    brand_occupancy = models.FloatField(verbose_name='品牌占有率')
    positive_rate = models.FloatField(verbose_name='好评率')
    lowest_price = models.IntegerField(verbose_name='最低价', default=0)
    highest_price = models.IntegerField(verbose_name='最高价', default=0)
    product_num = models.IntegerField(verbose_name='产品数', default=0)
    update_date = models.DateField(verbose_name='信息更新时间', auto_now=True)

    def __str__(self):
        brand_list = ProductBrand.objects.filter(pk=self.brand_id)
        brand_name = brand_list[0].name_cn if brand_list else 'null'
        return brand_name

    class Meta:
        ordering = ['ranking', ]
        verbose_name = '品牌排行榜'
        verbose_name_plural = verbose_name
