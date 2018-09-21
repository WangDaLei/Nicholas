# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy_djangoitem import DjangoItem
from stock.models import StockInfo, CapitalStockAmountHistory,\
                            FinanceHistory, TradeRecord, StockBonusHistory,\
                            StockAllotmentHistory


class StockInfoItem(DjangoItem):
    django_model = StockInfo

class CapitalStockAmountHistoryItem(DjangoItem):
    django_model = CapitalStockAmountHistory

class FinanceHistoryItem(DjangoItem):
    django_model = FinanceHistory

class TradeRecordItem(DjangoItem):
    django_model = TradeRecord
    
class StockBonusHistoryItem(DjangoItem):
    django_model = StockBonusHistory

class StockAllotmentHistoryItem(DjangoItem):
    django_model = StockAllotmentHistory
