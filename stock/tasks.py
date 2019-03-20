from __future__ import absolute_import, unicode_literals
from celery import shared_task
import os
from .controllers import \
    get_stock_info, get_capital_amount,\
    get_finance, get_bonus_allot, send_email,\
    crawl_block_from_CSRC, parse_CRSC_PDF,\
    repair_json_files, update_block, get_trade_amount_sum,\
    crawl_index_from_sohu, craw_coin_from_coinmarket,\
    analysis_coin_price_based_date


@shared_task
def crawl_stock_daily_info():
    os.system('cd stock_spider && scrapy crawl stock_info_spider')

    re, date, name = crawl_block_from_CSRC()
    if re:
        parse_CRSC_PDF(date, name)
        repair_json_files(date)
        update_block(date)

    crawl_index_from_sohu()

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

    info = get_trade_amount_sum()
    if info:
        send_email(info)


@shared_task
def craw_coin_from_coinmarket_task():
    craw_coin_from_coinmarket()


@shared_task
def analysis_coin_price_based_date_task():
    analysis_coin_price_based_date()
