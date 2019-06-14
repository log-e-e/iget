from django.shortcuts import render

from tools import db_tool


def index(request):
    # 获取热门收藏的数据
    popular_fav_prd_info_list = db_tool.get_popular_fav()
    # 获取热门推荐的数据
    popular_rec_prd_info_list = db_tool.get_popular_rec()
    # 获取搭建在看的数据
    popular_view_prd_info_list = db_tool.get_popular_view()
    # 获取品牌排行榜前10的数据
    brand_rank_info_list = db_tool.get_brand_rank()[:10]
    # 获取热门笔记本排行榜前10数据
    popular_rank_prd_list = db_tool.get_popular_rank_prd()

    return render(request, 'index.html', context={
        'popular_fav_prd_infos': popular_fav_prd_info_list,
        'popular_rec_prd_infos': popular_rec_prd_info_list,
        'popular_view_prd_infos': popular_view_prd_info_list,
        'brand_rank_info_list': brand_rank_info_list,
        'popular_rank_prd_list': popular_rank_prd_list,
    })


def forbidden_403(request):
    return render(request, '403Forbidden.html')


def notfound_404(request):
    return render(request, '404notfound.html')
