from __future__ import absolute_import

from celery import shared_task

from dataStatistics.models import ViewStatistics


@shared_task
def async_write_prd_views(user_id, prd_serial_number):
    tar_prd_views_list = ViewStatistics.objects.filter(prd_serial_number=prd_serial_number)
    tar_prd_views = tar_prd_views_list[0] if tar_prd_views_list else None

    if tar_prd_views:
        tar_prd_views.view_num = tar_prd_views.view_num + 1
        if str(user_id) not in tar_prd_views.user_ids.split('#'):
            tar_prd_views.user_ids = tar_prd_views.user_ids + "#" + str(user_id)
        tar_prd_views.save()
    else:
        tar_prd_views = ViewStatistics()
        tar_prd_views.prd_serial_number = prd_serial_number
        tar_prd_views.user_ids = str(user_id)
        tar_prd_views.view_num = 1
        tar_prd_views.save()
