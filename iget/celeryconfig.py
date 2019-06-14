import djcelery

djcelery.setup_loader()

# 设置队列，将任务队列分为定时任务队列与普通任务队列
CELERY_QUEUES = {
    # 定时任务
    'beat_tasks': {
        'exchange': 'beat_tasks',
        'exchange_type': 'direct',
        'binding_key': 'beat_tasks',
    },
    # 普通任务
    'work_queue': {
        'exchange': 'work_queue',
        'exchange_type': 'direct',
        'binding_key': 'work_queue',
    }
}

# 设置默认队列
CELERY_DEFAULT_QUEUE = 'work_queue'

# 导入各个app的tasks.py中的任务
# 说明：此处不用再导入各个应用下的tasks，在celery.py中已经设置了自动扫描：app.autodiscover_tasks()
# CELERY_IMPORTS = (
#     'users.tasks',
# )

# 防止某些情况下的死锁，在启动worker后出现了相应的warning，此行先不用
# CELERYD_FORCE_EXECV = True

# 设置并发的worker数量
CELERYD_CONCURRENCY = 4

# 允许重试
CELERY_ACKS_LATE = True

# 每个worker最多执行100个任务后就立即被销毁，可以防止内存泄漏
CELERYD_MAX_TASKS_PER_CHILD = 100

# 单个任务的最大运行时间
CELERYD_TASK_TIME_LIMIT = 12 * 30

# 接受的内容格式设为json
CELERY_ACCEPT_CONTENT = ['json']

# 任务序列化后的数据格式为json
CELERY_TASK_SERIALIZER = 'json'

# 执行结果序列化后的数据格式为json
CELERY_RESULT_SERIALIZER = 'json'

# 设置时区
CELERY_ENABLE_UTC = True
TIME_ZONE = 'Asia/Shanghai'
CELERY_TIMEZONE = TIME_ZONE
