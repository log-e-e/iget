from __future__ import absolute_import, unicode_literals
import os
from django.conf import settings
from celery import Celery

# 设置 Django 的配置文件
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iget.settings')

# 创建 celery 实例
app = Celery('iget')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')

# 搜索所有 app 中的 tasks
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
