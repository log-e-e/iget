import traceback

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse

from dataStatistics.models import FavoriteStatistics, ViewStatistics, PriceStatistics
from operations.models import UserFavorite
from products.models import Product
from tools import db_tool


def ajax_get_popular_fav(request):
    product_info_list = db_tool.get_popular_fav()

    return JsonResponse(product_info_list, safe=False)


def ajax_get_popular_rec(request):
    # 暂时不要任何数据，直接从指定的数据范围内取即可
    product_info_list = db_tool.get_popular_rec()

    return JsonResponse(product_info_list, safe=False)


def ajax_get_people_view(request):
    product_info_list = db_tool.get_popular_view()

    return JsonResponse(product_info_list, safe=False)


def ajax_add_prd_to_fav(request):
    if request.method == 'GET':
        is_completed, already_added, is_login = "false", "false", "true"
        try:
            # 检查是否登录，未登录用户不能收藏
            if request.user.is_authenticated:
                user_id = request.user.id
                prd_serial_number = request.GET.get('prd_serial_number')
                # 检查是否早已添加了收藏
                fav_list = UserFavorite.objects.filter(Q(user_id=user_id)&Q(fav_prd_serial_number=prd_serial_number))
                if fav_list:
                    already_added = "true"
                else:
                    priceStatistics = PriceStatistics.objects.get(prd_serial_number=prd_serial_number)
                    userFavorite = UserFavorite()
                    userFavorite.user_id = user_id
                    userFavorite.fav_prd_serial_number = prd_serial_number
                    userFavorite.fav_type = 1
                    userFavorite.price_when_fav = priceStatistics.lowest_price
                    userFavorite.save()
                    is_completed = "true"
            else:
                is_login = "false"
        except:
            traceback.print_exc()
        finally:
            return JsonResponse({
                "is_completed": is_completed,
                "already_added": already_added,
                "is_login": is_login,
        })
    else:
        return redirect(reverse('forbidden_403'))


def ajax_delete_fav_prd(request):
    if request.method == 'GET':
        is_completed = "false"
        try:
            user_id = request.user.id
            prd_serial_number = request.GET.get('prd_serial_number')
            UserFavorite.objects.filter(Q(user_id=user_id)&Q(fav_prd_serial_number=prd_serial_number)).delete()
            is_completed = "true"
        except:
            traceback.print_exc()
        finally:
            return JsonResponse({
                "is_completed": is_completed
            })
    else:
        pass


def ajax_delete_all_fav_prd(request):
    if request.method == 'GET':
        is_completed = "false"
        try:
            user_id = request.user.id
            UserFavorite.objects.filter(Q(user_id=user_id)).delete()
            is_completed = "true"
        except:
            traceback.print_exc()
        finally:
            return JsonResponse({
                "is_completed": is_completed
            })
    else:
        pass


def all_rank_list(request):
    return render(request, 'dataStatistics/allRankList.html')


def certain_rank_list(request):
    return render(request, 'dataStatistics/certainRankList.html')
