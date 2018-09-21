# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from stock.models import StockInfo, ChangeHistory, CapitalStockAmountHistory,\
                            FinanceHistory, StockBonusHistory, StockAllotmentHistory,\
                            TradeRecord
from scrapy.exceptions import DropItem
from datetime import date
import time

class StockInfoPipeline(object):

    def is_valid_date(self, strdate):
        '''''判断是否是一个有效的日期字符串'''
        try:
            if ":" in strdate:
                time.strptime(strdate, "%Y-%m-%d %H:%M:%S")
            else:
                time.strptime(strdate, "%Y-%m-%d")
            return True
        except:
            return False

    def dynamic_update(self, stock, key, item):
        if 'name' == key:
            if str(stock.name) != str(item[key]):
                ChangeHistory.objects.create(stock=stock, change_source=stock.name,\
                                                change_target=item[key], field=key,\
                                                generated_time=date.today())
                stock.name = item[key]

        if 'stock_exchange' == key:
            if str(stock.stock_exchange) != str(item[key]):
                ChangeHistory.objects.create(stock=stock, change_source=stock.stock_exchange,\
                                                change_target=item[key], field=key,\
                                                generated_time=date.today())
                stock.stock_exchange = item[key]

        if 'block' == key:
            if str(stock.block) != str(item[key]):
                ChangeHistory.objects.create(stock=stock, change_source=stock.block,\
                                                change_target=item[key], field=key,\
                                                generated_time=date.today())
                stock.block = item[key]

        if 'ownership' == key:
            if str(stock.ownership) != str(item[key]):
                ChangeHistory.objects.create(stock=stock, change_source=stock.ownership,\
                                                change_target=item[key], field=key,\
                                                generated_time=date.today())
                stock.ownership = item[key]

        if 'found_date' == key:
            if str(stock.found_date) != str(item[key]):
                if self.is_valid_date(item[key]):
                    ChangeHistory.objects.create(stock=stock, change_source=stock.found_date,\
                                                    change_target=item[key], field=key,\
                                                    generated_time=date.today())
                    stock.found_date = item[key]

        if 'market_list_date' == key:
            if str(stock.market_list_date) != str(item[key]):
                if self.is_valid_date(item[key]):
                    ChangeHistory.objects.create(stock=stock, change_source=stock.market_list_date,\
                                                    change_target=item[key], field=key,\
                                                    generated_time=date.today())
                    stock.market_list_date = item[key]

        if 'equity' == key:
            if float(stock.equity) != float(item[key]):
                ChangeHistory.objects.create(stock=stock, change_source=stock.equity,\
                                                change_target=item[key], field=key,\
                                                generated_time=date.today())
                stock.equity = float(item[key])

        if 'status' == key:
            if str(stock.status) != str(item[key]):
                ChangeHistory.objects.create(stock=stock, change_source=stock.status,\
                                                change_target=item[key], field=key,\
                                                generated_time=date.today())
                stock.status = item[key]

        if 'price' == key:
            stock.price = item[key]

        return stock

    def process_item(self, item, spider):

        stock_one,_ = StockInfo.objects.get_or_create(code=item['code'])

        kargs = {}
        for key in item.keys():
            if key == 'code':
                continue
            else:
                stock_one = self.dynamic_update(stock_one, key, item)
        stock_one.save()
        return item

class CapitalStockAmountHistoryPipeline(object):

    def dynamic_update(self, item):
        code = item['code']
        change_date = item['change_date']
        num = item['num']

        capital = CapitalStockAmountHistory.objects.filter(\
                                        code=code,\
                                        change_date=change_date,\
                                        num=num)
        if capital:
            return False
        else:
            return True

    def process_item(self, item, spider):
        result = self.dynamic_update(item)
        if result:
            stock_one,_ = StockInfo.objects.get_or_create(code=item['code'])
            item['stock'] =  stock_one
            item.save()
        return item

class FinanceHistoryPipeline(object):
 
    def dynamic_update(self, item):
        code = item['code']
        date = item['date']

        finance = FinanceHistory.objects.filter(\
                                        code=code,\
                                        date=date)
        if finance:
            return False
        else:
            return True

    def process_item(self, item, spider):
        result = self.dynamic_update(item)
        if result:
            stock_one,_ = StockInfo.objects.get_or_create(code=item['code'])
            item['stock'] =  stock_one
            item.save()
        return item

class TradeRecordPipeline(object):
    def dynamic_update(self, item):
        code = item['code']
        date = item['date']

        trade_record = TradeRecord.objects.filter(\
                                        code=code,\
                                        date=date)
        if trade_record:
            return False
        else:
            return True

    def process_item(self, item, spider):
        result = self.dynamic_update(item)
        if result:
            stock_one,_ = StockInfo.objects.get_or_create(code=item['code'])
            item['stock'] =  stock_one
            item.save()
        return item

class TradeRecordTaskPipeline(object):
    def dynamic_update(self, item):
        code = item['code']
        date = item['date']

        trade_record = TradeRecord.objects.filter(\
                                        code=code,\
                                        date=date)
        if trade_record:
            return False
        else:
            return True

    def process_item(self, item, spider):
        result = self.dynamic_update(item)
        if result:
            stock_one,_ = StockInfo.objects.get_or_create(code=item['code'])
            item['stock'] =  stock_one
            item.save()
        return item


class StockBonusHistoryPipeline(object):
    def dynamic_update(self, item):
        code = item['code']
        public_date = item['public_date']

        bonus = StockBonusHistory.objects.filter(\
                                        code=code,\
                                        public_date=public_date)
        if bonus:
            return False
        else:
            return True

    def process_item(self, item, spider):
        result = self.dynamic_update(item)
        if result:
            stock_one,_ = StockInfo.objects.get_or_create(code=item['code'])
            item['stock'] =  stock_one
            item.save()
        return item

class StockAllotmentHistoryPipeline(object):
    def dynamic_update(self, item):
        code = item['code']
        if 'public_date' in item:
            public_date = item['public_date']

            allotment = StockAllotmentHistory.objects.filter(\
                                            code=code,\
                                            public_date=public_date)
        else:
            exright_date = item['exright_date']
            allotment = StockAllotmentHistory.objects.filter(\
                                            code=code,\
                                            exright_date=exright_date)

        if allotment:
            return False
        else:
            return True

    def process_item(self, item, spider):
        result = self.dynamic_update(item)
        if result:
            stock_one,_ = StockInfo.objects.get_or_create(code=item['code'])
            item['stock'] =  stock_one
            item.save()
        return item
