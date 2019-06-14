import random

from django.db.models import Q
from django.shortcuts import render, redirect, reverse

from dataStatistics.models import PriceStatistics
from products.models import Product, ProductConfiguration, ProductSeries, ProductBrand
from products.tasks import async_write_prd_views


def get_product_detail(request):
    if request.method == 'GET':
        prd_serial_number = request.GET.get('prd_serial_number')
        product = Product.objects.get(prd_serial_number=prd_serial_number)
        productConfiguration = ProductConfiguration.objects.get(prd_serial_number=prd_serial_number)
        priceStatistics = PriceStatistics.objects.get(prd_serial_number=prd_serial_number)
        productSeries = ProductSeries.objects.get(pk=product.series_id)
        productBrand = ProductBrand.objects.get(pk=product.brand_id)
        # 同系列的其他产品
        other_same_series_prds = Product.objects.filter(Q(series_id=product.series_id)&(~Q(prd_serial_number=prd_serial_number)))
        other_same_series_prd_infos = []
        for other_prd in other_same_series_prds:
            other_productConfiguration = ProductConfiguration.objects.get(prd_serial_number=other_prd.prd_serial_number)
            other_priceStatistics = PriceStatistics.objects.get(prd_serial_number=other_prd.prd_serial_number)
            other_same_series_prd_infos.append({
                'product': other_prd,
                'productConfiguration': other_productConfiguration,
                'priceStatistics': other_priceStatistics,
            })
        # 按价格下降排序
        other_same_series_prd_infos = sorted(
            other_same_series_prd_infos,
            key=lambda prd_info: prd_info['priceStatistics'].lowest_price,
            reverse=True)
        # 同价位的其他产品
        min_price = priceStatistics.lowest_price - 500
        max_price = priceStatistics.lowest_price + 500
        other_same_price_prds = PriceStatistics.objects.filter(
            Q(lowest_price__gte=min_price)&Q(lowest_price__lte=max_price)&(~Q(prd_serial_number=product.prd_serial_number))).\
            values_list('prd_serial_number', flat=True)
        other_same_price_prds = list(other_same_price_prds)
        # 如果匹配到的数据过多，层层筛选
        if len(other_same_price_prds) > 1000:
            random_index_list = random.sample(range(0, len(other_same_price_prds)), 600)
            other_same_price_prds = [other_same_price_prds[i] for i in random_index_list]
        if len(other_same_price_prds) > 300:
            random_index_list = random.sample(range(0, len(other_same_price_prds)), 300)
            other_same_price_prds = [other_same_price_prds[i] for i in random_index_list]
        if len(other_same_price_prds) > 150 and len(other_same_price_prds) <= 300:
            random_index_list = random.sample(range(0, len(other_same_price_prds)), 100)
            other_same_price_prds = [other_same_price_prds[i] for i in random_index_list]
        if len(other_same_price_prds) > 8 and len(other_same_price_prds) <= 150:
            random_index_list = random.sample(range(0, len(other_same_price_prds)), 8)
            other_same_price_prds = [other_same_price_prds[i] for i in random_index_list]

        if request.user.is_authenticated:
            async_write_prd_views.delay(request.user.id, prd_serial_number)
        other_same_price_prd_infos = []
        for serial_number in other_same_price_prds:
            other_same_price_prd_infos.append({
                "product": Product.objects.get(prd_serial_number=serial_number),
                "priceStatistics": PriceStatistics.objects.get(prd_serial_number=serial_number)
            })

        return render(request, 'products/productDetail.html', context={
            'productBrand': productBrand,
            'productSeries': productSeries,
            'product': product,
            'productConfiguration': productConfiguration,
            'priceStatistics': priceStatistics,
            'other_same_series_prd_infos': other_same_series_prd_infos,
            'other_same_price_prd_infos': other_same_price_prd_infos
        })
    else:
        return redirect(reverse('forbidden_403'))


def get_product_config(request):
    if request.method == 'GET':
        prd_serial_number = request.GET.get('prd_serial_number')
        product = Product.objects.get(prd_serial_number=prd_serial_number)
        productConfiguration = ProductConfiguration.objects.get(prd_serial_number=prd_serial_number)

        return render(request, 'products/prdConfDetail.html', context={
            'product': product,
            'productConfiguration': productConfiguration
        })
    else:
        return redirect(reverse('forbidden_403'))
