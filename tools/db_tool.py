import datetime
import itertools
import json
import os
import random
import re
import time

import jieba
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, InvalidPage
from django.db.models import Q

from dataStatistics.models import PriceStatistics, FavoriteStatistics, ViewStatistics
from iget import settings
from products.models import ProductBrand, ProductSeries, ProductConfiguration, Product
from users.models import EmailVerification, MailWebSite, User


def is_code_exist(email, code):
    email_ver_list = EmailVerification.objects.filter(Q(to_email=email) & Q(code=code))

    return True if email_ver_list else False


def is_valid_code(email, code):
    # 查空： if code:
    # 是否在数据库中：filter()
    # 是否有效：is_valid=False, failure_time < now()

    # 首先校验code是否存在以及是否有效, 如果不存在则直接跳转到错误提示页面
    email_ver_list = EmailVerification.objects.filter(Q(to_email=email) & Q(code=code))
    # 如果code不存在
    if not email_ver_list:
        return False, None
    # code存在, 继续进一步检验code的有效性
    else:
        email_ver = email_ver_list[0]
        # 如果code已失效：已被点击过或已过有效时间或其他
        expired = (datetime.datetime.now() - email_ver.send_time).seconds >= 300
        if (not email_ver.is_valid) or expired:
            return False, None
        else:
            return True, email_ver


def set_code_invalid(email, code_type, code):
    code_objs = EmailVerification.objects.filter(Q(to_email=email) & Q(verify_type=code_type) & Q(code=code))

    if code_objs:
        code_objs[0].is_valid = False
        code_objs[0].save()
        return True
    else:
        return False


def email_registered(email):
    users = User.objects.filter(Q(email=email))
    return True if users else False


def get_mail_site(email):
    mail_website = '#'
    if email:
        mail_suffix = email[email.index('@') + 1:email.index('.')]
        mail_website_list = MailWebSite.objects.filter(Q(mail_site__icontains=mail_suffix))
        # 此处修改了一个bug:处理indexError, 在数据库中没有对应的邮箱网址时设为'#'
        if mail_website_list:
            mail_website = mail_website_list[0].mail_site

    return mail_website


def read_jsonfile_as_dict(jsonfile_path):
    with open(jsonfile_path, 'r') as f:
        jsonfile_dict = dict(json.load(f))
        f.close()
    return jsonfile_dict


def write_dict_to_jsonfile(data_dict, jsonfile_path):
    with open(jsonfile_path, 'w') as f:
        json.dump(data_dict, f, ensure_ascii=False, indent=4)
        f.close()


def save_json_to_db(jsonfile, table):
    data_dict= {}
    if not os.path.isdir(jsonfile):
        data_dict = read_jsonfile_as_dict(jsonfile)
    else:
        pass
    if table == "ProductBrand":
        productBrand_list = []
        for record in data_dict.values():
            productBrand = ProductBrand()
            productBrand.name_cn = record['name_cn']
            productBrand.name_en = record['name_en']
            productBrand.site_link = record['site_link']
            productBrand.status = record['status']
            productBrand_list.append(productBrand)
        ProductBrand.objects.bulk_create(productBrand_list)
    elif table == "MailWebSite":
        mailWebSite_list = []
        for record in data_dict.values():
            mailWebSite = MailWebSite()
            mailWebSite.mail_site = record['mailWebSite']
            mailWebSite_list.append(mailWebSite)
        MailWebSite.objects.bulk_create(mailWebSite_list)
    elif table == "ProductSeries":
        for record in data_dict.values():
            brand_name = list(record.values())[0]['brand']
            brand_list = ProductBrand.objects.filter(name_cn__contains=brand_name)
            default_brand = ProductBrand.objects.filter(name_cn__contains='戴尔')[0]
            brand_id = brand_list[0].id if brand_list else default_brand.id
            productSeries_list = []
            for sub_record in record.values():
                productSeries = ProductSeries()
                productSeries.name = sub_record['name']
                productSeries.intro = sub_record['intro']
                productSeries.brand_id = brand_id
                productSeries_list.append(productSeries)
            # 批量插入数据
            ProductSeries.objects.bulk_create(productSeries_list)
    elif table == "ProductConfiguration_Product_PriceStatistics":
        serial_number_list = (''.join(x) for x in itertools.product('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', repeat=22))
        for root, dirs, files in os.walk(jsonfile):
            for file in files:
                single_brand_prds_data_dict = read_jsonfile_as_dict(os.path.join(root, file))
                for series_k, series_v in single_brand_prds_data_dict.items():
                    # 查找系列
                    series_list = ProductSeries.objects.filter(name__icontains=series_k)
                    series_id = series_list[0].id if series_list else (ProductSeries.objects.filter(name='戴尔G7')[0]).id
                    brand_id = series_list[0].brand_id if series_list else (ProductSeries.objects.filter(name='戴尔G7')[0]).brand_id
                    config_list = []
                    product_list = []
                    priceStatistics_list = []
                    for config_v in series_v.values():
                        serial_number = str(next(serial_number_list)) + "".join(str(time.time()).split('.'))
                        if config_v['屏幕尺寸'] != '--':
                            results = re.findall("([0-9]+.[0-9]+)|([0-9]+)", str(config_v['屏幕尺寸']))
                            sc_size = str(results[0][0]) if results[0][0] else str(results[0][1])
                        else:
                            sc_size = '15.6'
                        productConfiguration = ProductConfiguration(
                            prd_serial_number=serial_number,
                            time_to_market=config_v['上市时间'],
                            product_type=config_v['产品定位'],
                            os_type=config_v['操作系统'],
                            cpu_series=config_v['CPU系列'],
                            cpu_type=config_v['CPU型号'],
                            cpu_clock_speed=config_v['CPU主频'],
                            cpu_turbo=config_v['CPU睿频'],
                            core_num=config_v['核心数描述'],
                            memory_cap=config_v['内存容量'],
                            hd_type=config_v['硬盘类型'],
                            hd_cap=config_v['硬盘容量'],
                            graphics_type=config_v['显卡性能等级'],
                            graphics_cap=config_v['显存容量'],
                            sc_size=sc_size,
                            screen_resolution=config_v['屏幕分辨率'],
                            battery_type=config_v['电池类型'],
                            life_time_intro=config_v['续航时间'],
                            color=config_v['颜色'],
                            weight=config_v['重量']
                        )
                        product = Product(
                            name=config_v['型号'],
                            img_url=config_v['图片'],
                            brand_id=brand_id,
                            series_id=series_id,
                            prd_serial_number=serial_number
                        )

                        official_price = str(config_v['价格']).strip()
                        # 如果价格信息中包含数字，说明有报价，否则无报价。
                        if re.findall('(\d+)', official_price):
                            if official_price.isdigit() and len(official_price) >= 3:
                                official_price = int(official_price)
                            else:
                                if official_price.find('万') == -1:
                                    official_price = int(float(official_price) * 10000)
                                else:
                                    float_str = re.findall('(\d+\.\d+)', official_price)
                                    if float_str:
                                        official_price = int(float(float_str[0]) * 10000)
                                    else:
                                        int_str = re.findall('(\d+)', official_price)
                                        if int_str:
                                            official_price = int(int_str[0]) * 10000
                                        else:
                                            official_price = 0
                        else:
                            official_price = 0
                        priceStatistics = PriceStatistics(
                            prd_serial_number=serial_number,
                            official_price=official_price,
                            lowest_price=official_price,
                            highest_price=official_price
                        )
                        config_list.append(productConfiguration)
                        product_list.append(product)
                        priceStatistics_list.append(priceStatistics)
                    ProductConfiguration.objects.bulk_create(config_list)
                    Product.objects.bulk_create(product_list)
                    PriceStatistics.objects.bulk_create(priceStatistics_list)
    else:
        pass


def _add_unique_to_list(element, target_list):
    if element not in target_list:
        target_list.append(element)
    return target_list


def get_all_type_values(prds_filepath_dir, prd_data_type_filepath):
    for root, dirs, files in os.walk(prds_filepath_dir):
        for file in files:
            prds_data_dict = read_jsonfile_as_dict(os.path.join(root, file))
            prd_data_type_dict = read_jsonfile_as_dict(prd_data_type_filepath)
            series_values = prds_data_dict.values()
            for series_v in series_values:
                prd_values = series_v.values()
                for prd_v in prd_values:
                    prd_data_type_dict['产品定位'] = _add_unique_to_list(prd_v['产品定位'], prd_data_type_dict['产品定位'])
                    prd_data_type_dict['操作系统'] = _add_unique_to_list(prd_v['操作系统'], prd_data_type_dict['操作系统'])
                    prd_data_type_dict['CPU系列'] = _add_unique_to_list(prd_v['CPU系列'], prd_data_type_dict['CPU系列'])
                    prd_data_type_dict['内存容量'] = _add_unique_to_list(prd_v['内存容量'], prd_data_type_dict['内存容量'])
                    prd_data_type_dict['硬盘类型'] = _add_unique_to_list(prd_v['硬盘类型'], prd_data_type_dict['硬盘类型'])
                    prd_data_type_dict['硬盘容量'] = _add_unique_to_list(prd_v['硬盘容量'], prd_data_type_dict['硬盘容量'])
                    prd_data_type_dict['显卡性能等级'] = _add_unique_to_list(prd_v['显卡性能等级'], prd_data_type_dict['显卡性能等级'])
                    prd_data_type_dict['显存容量'] = _add_unique_to_list(prd_v['显存容量'], prd_data_type_dict['显存容量'])
                    prd_data_type_dict['屏幕尺寸'] = _add_unique_to_list(prd_v['屏幕尺寸'], prd_data_type_dict['屏幕尺寸'])
                    # prd_data_type_dict['屏幕分辨率'] = _add_unique_to_list(prd_v['屏幕分辨率'], prd_data_type_dict['屏幕分辨率'])
                    # prd_data_type_dict['电池类型'] = _add_unique_to_list(prd_v['电池类型'], prd_data_type_dict['电池类型'])
            write_dict_to_jsonfile(prd_data_type_dict, prd_data_type_filepath)


query_dict = {
    'otherIntel': ~(Q(cpu_series__icontains='i9')|Q(cpu_series__icontains='i7')|Q(cpu_series__icontains='i5')|
                    Q(cpu_series__icontains='第8代')|Q(cpu_series__icontains='酷睿i 5')|Q(cpu_series__icontains='i3')|
                    (Q(cpu_series__icontains='酷睿')&Q(cpu_series__icontains='M'))|Q(cpu_series__icontains='AMD')),
    'otherAMD': Q(cpu_series__icontains='AMD')&(~Q(cpu_series__icontains='ryzen')),
    'other_hd_cap': ~(Q(hd_cap__icontains='TB')|Q(hd_cap__icontains='500GB')|Q(hd_cap__icontains='128GB')|
                      Q(hd_cap__icontains='256GB')|Q(hd_cap__icontains='512GB')),
    'other_memory_cap': ~(Q(memory_cap__icontains='2G')|Q(memory_cap__icontains='4G')|Q(memory_cap__icontains='8G')|
                          Q(memory_cap__icontains='16G')|Q(memory_cap__icontains='32G')|Q(memory_cap__icontains='64G')),
    'other_win': ~(Q(os_type__icontains='win')&(Q(os_type__icontains='7')|Q(os_type__icontains='8')|Q(os_type__icontains='10'))),
    'other_time_to_market': ~(Q(time_to_market__icontains='2015')|Q(time_to_market__icontains='2016')|
                              Q(time_to_market__icontains='2017')|Q(time_to_market__icontains='2018')|Q(time_to_market__icontains='2019')),
}
def _filter_condition_handler(filter_key, filter_values):
    """
    :param filter_key: str()
    :param filter_values: list()
    :return: Q()
    """
    def is_other(v_list):
        is_other = False
        for v_e in v_list:
            if str(v_e).find('other') != -1:
                is_other = True
                break
        return is_other

    def get_sub_query(filter_k, filter_vs):
        """用于根据对应的filter_kesy获取对应的Q对象"""
        sub_query = Q()
        if filter_k == 'product_type__icontains':
            sub_query = Q(product_type__icontains=filter_vs[0])
            for v_e in filter_vs[1:]:
                sub_query = sub_query | Q(product_type__icontains=v_e)
        elif filter_k == 'cpu_series__icontains':
            sub_query = Q(cpu_series__icontains=filter_vs[0])
            for v_e in filter_vs[1:]:
                sub_query = sub_query | Q(cpu_series__icontains=v_e)
        elif filter_k == 'hd_cap__icontains':
            sub_query = Q(hd_cap__icontains=filter_vs[0])
            for v_e in filter_vs[1:]:
                sub_query = sub_query | Q(hd_cap__icontains=v_e)
        elif filter_k == 'memory_cap__icontains':
            sub_query = Q(memory_cap__icontains=filter_vs[0])
            for v_e in filter_vs[1:]:
                sub_query = sub_query | Q(memory_cap__icontains=v_e)
        elif filter_k == 'graphics_type__icontains':
            sub_query = Q(graphics_type__icontains=filter_vs[0])
            for v_e in filter_vs[1:]:
                sub_query = sub_query | Q(graphics_type__icontains=v_e)
        elif filter_k == 'sc_size__icontains':
            sub_query = Q(sc_size__icontains=filter_vs[0])
            for v_e in filter_vs[1:]:
                sub_query = sub_query | Q(sc_size__icontains=v_e)
        elif filter_k == 'os_type__icontains':
            sub_query = Q(os_type__icontains=filter_vs[0])
            for v_e in filter_vs[1:]:
                sub_query = sub_query | Q(os_type__icontains=v_e)
        elif filter_k == 'time_to_market__icontains':
            sub_query = Q(time_to_market__icontains=filter_vs[0])
            for v_e in filter_vs[1:]:
                sub_query = sub_query | Q(time_to_market__icontains=v_e)
        else:
            pass
        return sub_query

    if is_other(filter_values):
        # 从dict中获取对应的 Q 对象
        sub_query = query_dict[filter_values[0]]
    else:
        sub_query = get_sub_query(filter_key, filter_values)

    return sub_query


def _get_q_expression(filter_condition_dict):
    """需要注意的是：filter_dict.json中并非所有的条件列表都是用'|'连接符查询，例如：'9'中的系统查询就需要两个元素联合起来，要用'&'连接符查询"""
    # 动态查询的字段dict
    query = None
    for k, v in filter_condition_dict.items():
        sub_query = _filter_condition_handler(k, v)
        if query:
            query = query&sub_query
        else:
            query = sub_query
    return query


def _get_paging_data(k_v_list, sorted_by, cur_page_num, per_page_count):
    """
        筛选涉及四张表的查询：产品表、品牌表、配置表、价格表
            具体查询几张表，需要根据用户选择的条件做判断
        筛选需要分两种情况讨论：
            1.有品牌：有品牌的情况下需要先在产品表中进行筛选，然后再到对应的配置表中进行匹配
            2.无品牌：无品牌的情况下可以直接在产品配置表中进行数据筛选
        需要注意的是：品牌筛选与价格筛选需要同产品配置筛选进行区分处理。
        :returns (products_count, products_info_page, products_info)
    """
    filter_dict = read_jsonfile_as_dict(settings.BASE_DIR + "/static/other/filter_dict.json")
    # 升序处理，便于操作
    sorted_ls = sorted(k_v_list, key = lambda k: int(str(k).split('-')[0]))
    first_kv = str(sorted_ls[0])
    # 判断是否存在品牌参数。brand_num：在filter_dict.json中对应的key
    has_brand, brand_num = (False, 0) if (first_kv[0] != '1') else (True, int(first_kv[first_kv.index('-')+1:]))
    # 判断是否存在价格参数。price_range：dict类型，在filter_dict.json中对应的value
    has_price, price_range = False, {}
    # 判断是否存在配置参数。config_start_index：sorted_ls中配置参数的起始index
    has_config, config_start_index = False, -1
    for i in range(len(sorted_ls)):
        kv_str = str(sorted_ls[i])
        if int(kv_str[0]) > 2:
            has_config = True
            config_start_index = i
            break
        elif kv_str.startswith('2'):
            has_price = True
            price_range = filter_dict['2'][kv_str[kv_str.index('-')+1:]]

    prd_serial_number_list = []         # 根据brand_id在产品表查询到的所有产品
    price_serial_number_list = []       # 根据价格区间在价格统计表查询到的所有产品对应的serial_number
    conf_serial_number_list = []        # 根据配置选项在产品配置表中查询到的所有产品对应的serial_number
    serial_number_list = []             # 根据所有条件最终得出的产品的serial_number列表
    # 1.如果用户选择了特定品牌，则首先获取对应品牌产品数据
    if has_brand and brand_num > 0:
        # 获取brand_id
        brand_name = filter_dict['1'][str(brand_num)]
        brand_list = ProductBrand.objects.filter(Q(name_cn__contains=brand_name))
        brand_id = brand_list[0].id if brand_list else 1
        # 根据brand_id查询Product中的所有数据
        prd_serial_number_list = Product.objects.filter(Q(brand_id=brand_id)).values_list('prd_serial_number', flat=True)
        prd_serial_number_list = list(prd_serial_number_list)
        serial_number_list = prd_serial_number_list

    # 2.如果用户选择了特定价格区间，则首先获取符合对应价格区间的所有产品
    if has_price and price_range:
        min_price = int(price_range['min'])
        max_price = int(price_range['max'])
        price_serial_number_list = PriceStatistics.objects.filter(Q(lowest_price__gte=min_price) & Q(lowest_price__lte=max_price)).values_list('prd_serial_number', flat=True)
        price_serial_number_list = list(price_serial_number_list)
        serial_number_list = price_serial_number_list

    # 3.初步处理 serial_number_list：如果品牌和价格选项同时存在，则需要取二者的交集
    if has_brand and has_price:
        serial_number_list = list(set(prd_serial_number_list).intersection(set(price_serial_number_list)))

    # 4.接下来是产品配置筛选：
    if has_config and config_start_index >= 0:
        # 先根据配置选项构造Q表达式对象
        config_list = ProductConfiguration.objects.filter()
        filter_condition_dict = {}
        for kv in sorted_ls[config_start_index:]:
            kv_ls = str(kv).split('-')
            dict_k, dict_v = kv_ls[0], kv_ls[1]
            filter_key = filter_dict[dict_k]['filter_key']  # {"filter_key": "name_cn__contains",}中 filter_key="name_cn__contains"
            match_values = filter_dict[dict_k][dict_v]       # {"2": ["性能级", "中高端"]}中 match_values = ["性能级", "中高端"]
            filter_condition_dict[filter_key] = match_values

        # 获取Q表达式对象并进行查询操作
        q_expression = _get_q_expression(filter_condition_dict)
        conf_serial_number_list = config_list.filter(q_expression).values_list('prd_serial_number', flat=True)
        conf_serial_number_list = list(conf_serial_number_list)
        # 5.在查询完配置参数后，再次取交集
        if serial_number_list:  # 如果serial_number_list不为空，则说明品牌与价格区间选项至少有一个
            serial_number_list = list(set(serial_number_list).intersection(set(conf_serial_number_list)))
        else:                   # 否则说明用户并未选择特定的品牌与价格区间，此时的数据查询结果由产品配置表的查询结果 conf_serial_number_list
            serial_number_list = conf_serial_number_list
    # 根据serial_number_list的结果，从对应的表中取出并返回相应的数据（）
    page_info_dict = {}
    # 如果有查询结果
    if serial_number_list:
        product_list = []
        for serial_number in serial_number_list:
            product_list.append(Product.objects.get(prd_serial_number=serial_number))
        products_info = _get_product_dict_info_list(product_list)
        sorted_products_info = _get_sorted_products_info(products_info, sorted_by)
        page_info_dict = _get_page_info(sorted_products_info, per_page_count, cur_page_num)
        page_info_dict['sort'] = sorted_by
        page_info_dict['searchType'] = 'filter'
        # page_info_dict['selected_filters'] = k_v_list
        # 无结果的筛选项dict
        # none_filters_dict = {
        #     "1-5-8-3-9": ["2-1", "2-9", "3-1", "3-3"]
        # }
        none_result_filters = ["2-1", "2-9", "3-1", "3-3", "4-2"]
        page_info_dict['none_result_filters'] = none_result_filters
        page_info_dict['cur_page_num'] = cur_page_num

    return page_info_dict


def _get_search_keywords(searchKey):
    """处理结巴分词后的分词结果，提取关键词"""
    # 用于存放关键词
    search_keywords = []
    jieba.load_userdict(settings.BASE_DIR + "/static/other/user_dict.txt")
    key_list = jieba.cut_for_search(searchKey)
    pattern = re.compile(u'[\u4e00-\u9fa5]+')
    for key in key_list:
        chinese_keys = pattern.findall(key)
        # 如果是中文字符，则提取出来放入search_keywords中
        if chinese_keys:
            search_keywords.append(chinese_keys[0])
        # 如果没有中文字符，则作其他判断:如果key不是字母数字的组合，那么就直接跳过，否则添加到search_keywords中
        else:
            if key.isalnum():
                search_keywords.append(key.lower())
            else:
                pass

    return search_keywords


def _get_sorted_products_info(products_info, sorted_by):
    """
    获取排序后的Product对象列表
    :param products_info:
    :param sorted_by
    """
    sorted_products_info = products_info
    if sorted_by == 'desc':
        sorted_products_info = sorted(
            products_info,
            key=lambda prd_info: int(prd_info['priceStatistics']['lowest_price']),
            reverse=True)
    elif sorted_by == 'asc':
        sorted_products_info = sorted(
            products_info,
            key=lambda prd_info: int(prd_info['priceStatistics']['lowest_price']),
            reverse=False)
    elif sorted_by == 'default':
        # 使用random.shuffle()打乱列表元素值的顺序，但需要注意的是：该函数需要根据列表长度执行相应的次数才能达到足够的乱序
        shuffle_time = len(products_info)
        if shuffle_time >= 2000:
            shuffle_time = 200
        elif shuffle_time >= 1000:
            shuffle_time = 100
        elif shuffle_time >= 500:
            shuffle_time = 50
        elif shuffle_time >= 250:
            shuffle_time = 25
        elif shuffle_time >= 125:
            shuffle_time = 15

        while shuffle_time >= 1:
            random.shuffle(products_info)
            shuffle_time = shuffle_time - 1

        sorted_products_info = products_info

    return sorted_products_info


def _get_page_info(tar_products_info, per_page_count, cur_page_num):
    # 需要注意的是，如果获取的结果小于给出的per_page_count，则设置分页结果为结果数
    products_len = len(tar_products_info)
    if products_len < per_page_count:
        paginator = Paginator(tar_products_info, products_len)
    else:
        paginator = Paginator(tar_products_info, per_page_count)
    products_info_page = paginator.page(cur_page_num)

    # 获取产品信息以及最低价
    product_info_dict_list = [prd_dict for prd_dict in products_info_page]

    has_previous, has_next = products_info_page.has_previous(), products_info_page.has_next()
    previous_page_number = products_info_page.previous_page_number() if has_previous else 1
    next_page_number = products_info_page.next_page_number() if has_next else paginator.num_pages

    products_info_page_dict = {
        "previous_page_number": str(previous_page_number),
        "next_page_number": str(next_page_number),
        "cur_page": str(products_info_page.number),
        "total_page": str(paginator.num_pages),
    }

    return {
        "products_count": str(len(tar_products_info)),
        "products_info_page": products_info_page_dict,
        "products_info": product_info_dict_list,
    }


def _get_product_dict_info_list(products):
    """
    :param products:
    :return:
    """
    products_info = []

    for product in products:
        priceStatistics = PriceStatistics.objects.filter(Q(prd_serial_number=product.prd_serial_number))[0]
        product_dict = {
            "img_url": str(product.img_url),
            "name": str(product.name),
            "prd_serial_number": str(product.prd_serial_number)
        }
        price_dict = {
            "lowest_price": str(priceStatistics.lowest_price),
            "mall_num": str(priceStatistics.mall_num)
        }
        products_info.append({
            "product": product_dict,
            "priceStatistics": price_dict
        })

    return products_info


def _get_products_by_serial_number(serial_number_list):
    products = []
    for serial_number in serial_number_list:
        products.append(Product.objects.get(prd_serial_number=serial_number))

    return products


def _get_random_product_infos(prd_serial_list, n):
    def get_shuffle_result(target_list):
        tar_list = target_list
        shuffle_time = 400
        while shuffle_time > 0:
            random.shuffle(tar_list)
            shuffle_time = shuffle_time - 1

        tar_list = tar_list[:n]
        random.shuffle(tar_list)

        return tar_list

    # 如果数据表中的数据大于40个，则从其中随机抽取40条数据，最终随机选择8条数据；否则，从产品数据表中进行补充
    if len(prd_serial_list) >= 300:
        selected_fav = get_shuffle_result(prd_serial_list)
    else:
        # 从产品表中随机取出数据
        years = ['2019', '2018', '2017']
        config_serial_number_list = ProductConfiguration.objects. \
            filter(Q(time_to_market__icontains=years[random.randrange(len(years))])).values_list('prd_serial_number',
                                                                                                 flat=True)
        price_serial_number_list = PriceStatistics.objects. \
            filter(Q(lowest_price__gte=4500) & Q(lowest_price__lte=8000)).values_list('prd_serial_number', flat=True)
        # 求得二者交集
        common_serial_number_list = list(set(config_serial_number_list).intersection(set(price_serial_number_list)))
        # 取得无重复并集
        common_serial_number_list = list(set(common_serial_number_list).union(set(prd_serial_list)))

        selected_fav = get_shuffle_result(common_serial_number_list)
    # 取出数据
    products = _get_products_by_serial_number(selected_fav)
    product_info_list = _get_product_dict_info_list(products)

    return product_info_list


def get_popular_fav():
    all_fav_prd_serial_list = FavoriteStatistics.objects.all().values_list('prd_serial_number', flat=True)
    all_fav_prd_serial_list = list(all_fav_prd_serial_list)

    product_info_list = _get_random_product_infos(all_fav_prd_serial_list, 8)

    return product_info_list


def get_popular_rec():
    product_info_list = _get_random_product_infos([], 8)

    return product_info_list


def get_popular_view():
    all_view_prd_serial_list = ViewStatistics.objects.all().values_list('prd_serial_number', flat=True)
    all_view_prd_serial_list = list(all_view_prd_serial_list)

    product_info_list = _get_random_product_infos(all_view_prd_serial_list, 8)

    return product_info_list


def get_brand_rank():
    brand_rank_info_list = read_jsonfile_as_dict(settings.BASE_DIR + "/tools/rankInfo.json")['brand_rank']

    return brand_rank_info_list


def get_popular_rank_prd():
    serial_number_list = PriceStatistics.objects.filter(Q(lowest_price__gte=5000)&Q(lowest_price__lte=12000)).values_list('prd_serial_number', flat=True)
    serial_number_list = list(serial_number_list)
    prd_info_list = _get_random_product_infos(serial_number_list, 10)
    score_list = get_random_scores(10)
    for i in range(len(prd_info_list)):
        prd_info_list[i]['score'] = str(score_list[i])

    return prd_info_list


def get_random_scores(number):
    score_list = []
    for i in range(number):
        score_list.append(round(random.uniform(8, 10), 2))

    return score_list


def get_random_rank_title():
    title_list = [
        '热门笔记本排行榜',
        '笔记本排行榜',
        '笔记本排行榜',
        '笔记本排行榜',
        '笔记本排行榜',
        '笔记本排行榜',
        '笔记本排行榜',
        '笔记本排行榜',
        '笔记本排行榜',
        '笔记本排行榜',
        '笔记本排行榜',
        '笔记本排行榜',
        '笔记本排行榜',
        '笔记本排行榜',
        '笔记本排行榜',
        '笔记本排行榜',
    ]
