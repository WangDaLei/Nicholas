# coding=utf-8
import os
from celery import shared_task
from celery.decorators import periodic_task
from celery.task.schedules import crontab
from datetime import timedelta, datetime, date
from .controllers import get_stock_info, get_capital_amount,\
                            get_finance, get_bonus_allot, send_email,\
                            crawl_block_from_CSRC, parse_CRSC_PDF,\
                            repair_json_files, update_block


@periodic_task(run_every=crontab(hour=7, minute=35))
def crawl_stock_daily_info():
    os.system('cd stock_spider && scrapy crawl stock_info_spider')

    re, date, name = crawl_block_from_CSRC()
    if re:
        parse_CRSC_PDF(date, name)
        repair_json_files(date)
        update_block(date)

    os.system('cd stock_spider && scrapy crawl stock_block_spider')
    os.system('cd stock_spider && scrapy crawl stock_capital_amount_spider')
    os.system('cd stock_spider && scrapy crawl stock_finance_spider')
    os.system('cd stock_spider && scrapy crawl stock_bonus_spider')
    os.system('cd stock_spider && scrapy crawl stock_allotment_spider')

    info_list = list()

    info = get_stock_info()
    if info != "":
        info_list.append(info)

    info = get_capital_amount()
    if info != "":
        info_list.append(info)

    info = get_finance()
    if info != "":
        info_list.append(info)

    info = get_bonus_allot()
    if info != "":
        info_list.append(info)

    if info_list:
        send_email('\n'.join(info_list))

    os.system('cd stock_spider && scrapy crawl stock_trade_record_task_spider')
