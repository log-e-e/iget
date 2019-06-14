import json

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse

from dataStatistics.models import PriceStatistics
from products.models import Product, ProductConfiguration, ProductBrand
from tools import db_tool


# 数据库查找规则
def search(request):
    # 搜索
    """
    关于搜索：
        1. 首先对关键词进行通过结果集查询过滤，过滤掉没有查询结果的关键词
        2. 然后根据关键词查询结果集的大小进行分层筛选，直至查找到最小结果集为止
        3. 如何判断结果集最小：当前搜索的结果集list长度为0时，则意味着上一次搜索的结果集是最小结果集
    关于搜索与筛选：
        1. 搜索框：一般而言，搜索框搜索的是产品型号或名称（只支持该类搜索词）。因此该功能可以直接通过数据库匹配产品名称即可获取数据
        2. 筛选框：与搜索框不同的是，需要记录每次筛选后的筛选条件
        3. 异同：搜索与筛选功能均需要进行分页；搜索功能在结果出来后可以在筛选框中设置产品品牌（如果有索索结果的话）
    :param request:
    :return:
    """
    if request.method == 'GET':
        # 搜索类型：1.搜索框搜索——ordinary；2.筛选框筛选——filter；3.结果内搜索——withinResults
        searchType = str(request.GET.get('searchType')).strip()
        sort = str(request.GET.get('sort') if request.GET.get('sort') else 'default')
        page_number = int(request.GET.get('page'))
        searchKey = str(request.GET.get('searchKey'))
        # 分词处理，提取有效关键词
        search_keywords = db_tool._get_search_keywords(searchKey)
        if searchType == 'ordinary':
            if search_keywords:
                # 数据库检索规则：1. 首先搜索全部关键词，若是全部关键词搜索不到结果则减少关键词重试
                # 1. 过滤掉无查询结果的关键词，并将有结果的关键词及其查询结果保留下来
                prd_list = []
                for key in search_keywords:
                    queryset = Product.objects.filter(Q(name__icontains=key))
                    if queryset:
                        prd_list.append((key, queryset))
                    else:
                        pass
                # 如果有查询结果，则进行相应的筛选处理
                if prd_list:
                    # 按照各个关键词的搜索结果进行降序排序
                    prd_list = sorted(prd_list, key=lambda result: len(result[1]), reverse=True)

                    # 首先假设最大结果集为最小非空结果集，然后进行分层筛选，获取最小非空结果集
                    min_result = prd_list[0][1]
                    for result in prd_list[1:]:
                        cur_result = min_result.filter(Q(name__icontains=result[0]))
                        if cur_result:
                            min_result = cur_result
                        else:
                            break
                    #获取排序后的结果
                    # 排序处理结果: [{"product": product_dict,"priceStatistics": price_dict}, {"product": product_dict,"priceStatistics": price_dict}]
                    sorted_product_info_list = db_tool._get_sorted_products_info(db_tool._get_product_dict_info_list(min_result), sort)
                    # 获取排序后的最小非空结果集后，对结果接进行分页处理
                    # 需要注意的是，当搜索结果小于20时，只显示１页及其相关结果
                    print(len(sorted_product_info_list))
                    if len(sorted_product_info_list) < 20:
                        print("小于２０")
                        page_info_dict = db_tool._get_page_info(sorted_product_info_list, len(sorted_product_info_list), page_number)
                    else:
                        page_info_dict = db_tool._get_page_info(sorted_product_info_list, 20, page_number)
                    page_info_dict['searchKey'] = searchKey
                    page_info_dict['sort'] = sort
                    page_info_dict['searchType'] = searchType

                    return render(request, 'operations/search.html', context=page_info_dict)
                # 如果没有查询结果，则返回相应的空结果页面
                else:
                    return render(request, 'operations/search.html', context={
                        "searchKey": searchKey
                    })
            else:
                return render(request, 'operations/search.html', context={
                        "searchKey": searchKey
                    })
    else:
        return redirect(reverse('forbidden_403'))


def ajax_get_filter_result(request):
    if request.method == 'GET':
        sorted_by = str(request.GET.get('sort') if request.GET.get('sort') else 'default')
        cur_page_number = int(request.GET.get('page'))
        filter_list = []

        for k, v in request.GET.items():
            # 获取以 k 开头的参数值: k0=_1-21,首先要去除开头的下划线
            if str(k).startswith('k'):
                v_str = str(v)[1:]
                k_v_list = v_str.split('-')
                filter_list.append(v_str)
        # 获取请求分页数据

        page_info_dict = dict(db_tool._get_paging_data(filter_list, sorted_by, cur_page_number, 20))
        page_info_dict_json = json.dumps(page_info_dict, indent=4, ensure_ascii=False)
        # return JsonResponse(page_info_dict)
        return JsonResponse(page_info_dict_json, safe=False)
    else:
        pass


def ajax_get_prd_info(request):
    if request.method == 'GET':
        prd_serial_number = request.GET.get('prd_serial_number')
        product_info = {}

        if prd_serial_number:
            product = Product.objects.get(prd_serial_number=prd_serial_number)
            product_info = db_tool._get_product_dict_info_list([product, ])[0]

        return JsonResponse(product_info, safe=True)
    else:
        pass


def compare_prd(request):
    if request.method == 'GET':
        params = request.GET.keys()
        prd_serial_num_list = [request.GET.get(param) for param in params if str(param).startswith('prd_')]

        product_info_list = []
        for serial_number in prd_serial_num_list:
            product = Product.objects.get(prd_serial_number=serial_number)
            brand = ProductBrand.objects.get(pk=product.brand_id)
            config = ProductConfiguration.objects.get(prd_serial_number=serial_number)
            priceStatistics = PriceStatistics.objects.get(prd_serial_number=serial_number)
            product_info_list.append({
                'brand': brand,
                'product': product,
                'config': config,
                'priceStatistics': priceStatistics
            })

        return render(request, 'operations/compare.html', context={
            'product_info_list': product_info_list
        })
    else:
        return redirect(reverse('forbidden_403'))
