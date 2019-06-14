from __future__ import absolute_import
from .celery import app as celery_app

# 用于确保启动django的同时启动celery
__all__ = ['celery_app']
