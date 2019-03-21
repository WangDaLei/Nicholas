from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_project.settings')

app = Celery('stock_tasks')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.timezone = 'Asia/Shanghai'
app.conf.update(enable_utc=False)
app.conf.update(CELERY_TIMEZONE='Asia/Shanghai')
# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'crawl_stock_daily_info': {
        'task': 'stock.tasks.crawl_stock_daily_info',
        'schedule': crontab(hour=15, minute=35),
        'args': ()
    },
    'craw_coin_from_coinmarket_task': {
        'task': 'stock.tasks.craw_coin_from_coinmarket_task',
        'schedule': crontab(hour=9, minute=10),
        'args': ()
    },
    'analysis_coin_price_based_date_task': {
        'task': 'stock.tasks.analysis_coin_price_based_date_task',
        'schedule': crontab(hour=9, minute=25),
        'args': ()
    },
    'crawl_block_from_CSRC_task': {
        'task': 'stock.tasks.crawl_block_from_CSRC_task',
        'schedule': crontab(hour=12, minute=1),
        'args': ()
    },
    # 'check_new_subscriber': {
    #     'task': 'notice.tasks.check_new_subscriber',
    #     'schedule': 60 * 60.0,
    #     'args': ()
    # },
}
