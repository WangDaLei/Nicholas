# -*- coding: UTF-8 -*-
import scrapy
import time
import math
from django.db.models import Max
from datetime import date, timedelta
from scrapy.selector import Selector
from scrapy_splash import SplashRequest
from stock_spider.items import StockInfoItem, CapitalStockAmountHistoryItem,\
                                FinanceHistoryItem, TradeRecordItem,\
                                StockBonusHistoryItem, StockAllotmentHistoryItem
from stock.models import StockInfo, CapitalStockAmountHistory, FinanceHistory

class StochInfoSpider(scrapy.Spider):
    name = "stock_info_spider"
    all_stock_code = []

    custom_settings = {
        'ITEM_PIPELINES': {
            'stock_spider.pipelines.StockInfoPipeline': 1
        }
    }

    def start_requests(self):
        stock_set = StockInfo.objects.all()
        for one in stock_set:
            self.all_stock_code.append(one.code)
        url = "http://quote.eastmoney.com/stocklist.html"
        yield SplashRequest(url, self.parse, args={'wait': 3})

    def parse(self, response):
        sel = Selector(response)
        stock_list = sel.xpath('//div[re:test(@class,"qox")]/div/div/ul/li/a[re:test(@href, "/sz|/sh")]/text()').extract()

        for stock in stock_list:
            sset = stock.split('(')
            if str(sset[1]).startswith("000") or str(sset[1]).startswith("001") or str(sset[1]).startswith("002"):
                stock_code = sset[1].split(')')[0]
                stock_name = sset[0]
                if stock_code not in self.all_stock_code:
                    stock_info = StockInfoItem()
                    stock_info['code'] = stock_code
                    stock_info['name'] = stock_name
                    stock_info['stock_exchange'] = u'深证交易所'
                    yield stock_info
            if sset[1].startswith("600") or sset[1].startswith("601") or sset[1].startswith("603"):
                stock_code = sset[1].split(')')[0]
                stock_name = sset[0]
                if stock_code not in self.all_stock_code:
                    stock_info = StockInfoItem()
                    stock_info['code'] = stock_code
                    stock_info['name'] = stock_name
                    stock_info['stock_exchange'] = u'上证交易所'
                    yield stock_info


class StochBlockSpider(scrapy.Spider):
    name = "stock_block_spider"
    all_stock_code = []

    custom_settings = {
        'ITEM_PIPELINES': {
            'stock_spider.pipelines.StockInfoPipeline': 1
        }
    }

    def get_time_stamp(self):
        return (int(round(time.time() * 1000)))

    def start_requests(self):
        stock_set = StockInfo.objects.all()
        for one in stock_set:
            self.all_stock_code.append(one.code)
        for one in self.all_stock_code:
            stock_one = StockInfo.objects.get(code=one)
            if stock_one.block == "":
                url_block = "http://vip.stock.finance.sina.com.cn/corp/go.php/vCI_CorpOtherInfo/stockid/%s/menu_num/2.phtml"%(str(one))
                yield scrapy.Request(url_block, self.parse_block)
            
            url_pro = "http://vip.stock.finance.sina.com.cn/corp/go.php/vCI_CorpInfo/stockid/%s.phtml"%(str(one))
            yield scrapy.Request(url_pro, self.parse_pro)
            
            url_equity = "http://vip.stock.finance.sina.com.cn/corp/go.php/vCI_StockStructure/stockid/%s.phtml"%(str(one))
            yield scrapy.Request(url_equity, self.parse_equity)
            
            # if one.startswith("6"):
            #     s = "sh" + one
            # else:
            #     s = "sz" + one
            # time_stamp = self.get_time_stamp()
            # url_price = "http://hq.sinajs.cn/rn=%s&list=%s"%(str(time_stamp), str(s))
            # yield scrapy.Request(url_price, self.parse_price)

    def parse_block(self, response):

        sel = Selector(response)
        codelist = sel.xpath('//meta[re:test(@name,"Keywords")]/@content').extract()
        code = str(codelist[0]).split(')')[0].split('(')[-1]
        stock_info = StockInfoItem()
        stock_info['code'] = code
        sel = Selector(response)
        name = u"所属行业板块"
        stock_list = sel.xpath('//div/table/tr/th[re:test(text(),"%s")]/parent::*/following-sibling::*[1]/td/text()'%(name)).extract()

        block =""
        for stock in stock_list:
            block += str(stock.strip())
        if block != "":
            stock_info['block'] = block
        yield stock_info

    def parse_pro(self, response):

        sel = Selector(response)
        codelist = sel.xpath('//meta[re:test(@name,"Keywords")]/@content').extract()
        code = str(codelist[0]).split(')')[0].split('(')[-1]

        stock_info = StockInfoItem()
        stock_info['code'] = code

        name = u"组织形式"
        stock_list = sel.xpath('//div/table/tr/td[re:test(text(),"%s")]/following-sibling::*/text()'%(name)).extract()

        ownership =""
        for stock in stock_list:
            ownership += str(stock.strip())
        if ownership != "":
            stock_info['ownership'] = ownership

        name = u"成立日期"
        stock_date = sel.xpath('//div/table/tr/td[re:test(text(),"%s")]/following-sibling::*[1]//text()'%(name)).extract()
        found_date = ""
        for date in stock_date:
            found_date += date.strip()
        if found_date != "":
            stock_info['found_date'] = found_date

        name = u"上市日期"
        market_list_date = ""
        stock_date = sel.xpath('//div/table/tr/td[re:test(text(),"%s")]/following-sibling::*[1]//text()'%(name)).extract()
        for date in stock_date:
            market_list_date += date.strip()
        if market_list_date != "":
            stock_info['market_list_date'] = market_list_date

        yield stock_info

    def parse_equity(self, response):
        sel = Selector(response)
        codelist = sel.xpath('//meta[re:test(@name,"Keywords")]/@content').extract()
        code = str(codelist[0]).split(')')[0].split('(')[-1]

        stock_info = StockInfoItem()
        stock_info['code'] = code

        name = u".总股本"
        stock_list = sel.xpath('//div/table[re:test(@id,"StockStructureNewTable0")]/tbody/tr/td[re:test(text(),"%s")]/following-sibling::*[1]//text()'%(name)).extract()
        stock_equity = ""
        for stock in stock_list:
            stock_equity += str(stock.strip().split('万股')[0].strip())
        if stock_equity != "":
            stock_info['equity'] = stock_equity

        yield stock_info

    def parse_price(self, response):

        stock = response.text
        sset = stock.strip().split("=")
        
        code = str(sset[0].split("_")[-1][2:])
        sign = sset[1].split(",")[-1].split('"')[0]
        today = sset[1].split(",")[3]
        yesterday = sset[1].split(",")[2]

        status = ""
        price = 0.0

        if sign == "-3":
            status = "退市"
            price = 0.0
        elif sign == "-2":
            status = "未上市"
            price = 0.0
        elif sign == "03":
            status = "停牌"
            price = float(yesterday)
        elif sign == "00":
            status = "正常"
            price = float(today)
        else:
            status = "未知错误"
            price = 0.0

        stock_info = StockInfoItem()
        stock_info['code'] = code
        stock_info['status'] = status
        stock_info['price'] = price

        yield stock_info

class StochCapitalAmountSpider(scrapy.Spider):
    name = "stock_capital_amount_spider"
    all_stock_code = []

    custom_settings = {
        'ITEM_PIPELINES': {
            'stock_spider.pipelines.CapitalStockAmountHistoryPipeline': 1
        }
    }

    def start_requests(self):
        stock_set = StockInfo.objects.all()
        for one in stock_set:
            self.all_stock_code.append(one.code)
        for one in self.all_stock_code:
            url_capital_amount = "http://vip.stock.finance.sina.com.cn/corp/go.php/vCI_StockStructure/stockid/%s.phtml"%(str(one))
            yield scrapy.Request(url_capital_amount, self.parse_capital_amount)

    def parse_capital_amount(self, response):

        sel = Selector(response)
        codelist = sel.xpath('//meta[re:test(@name,"Keywords")]/@content').extract()
        stock_code = str(codelist[0]).split(')')[0].split('(')[1]

        name = u".公告日期"
        public_date_str = ""
        stock_list = sel.xpath('//table[re:test(@id,"StockStructureNewTable")]/tbody/tr/td[re:test(text(),"%s")]/following-sibling::*//text()'%(name)).extract()
        for stock in stock_list:
            public_date_str += str(stock.strip()) + " "

        name = u".变动日期"
        change_date_str = ""
        stock_list = sel.xpath('//table[re:test(@id,"StockStructureNewTable")]/tbody/tr/td[re:test(text(),"%s")]/following-sibling::*//text()'%(name)).extract()
        for stock in stock_list:
            change_date_str += str(stock.strip()) + " "

        name = u".变动原因"
        reason_str = ""
        stock_list = sel.xpath('//table[re:test(@id,"StockStructureNewTable")]/tbody/tr/td[re:test(text(),"%s")]/following-sibling::*'%(name)).extract()
        for stock in stock_list:
            temp =stock.strip().split("<td>")[1].split("</td>")[0]
            if temp == "":
                temp = "None"
            reason_str += str(temp) + " "

        name = u".总股本"
        captital_amount_str = ""
        stock_list = sel.xpath('//table[re:test(@id,"StockStructureNewTable")]/tbody/tr/td[re:test(text(),"%s")]/following-sibling::*//text()'%(name)).extract()
        for stock in stock_list:
            captital_amount_str += str(stock.strip().split("万股")[0].strip()) + " "

        lenth = len(change_date_str.strip().split(' '))
        public_date = public_date_str.strip().split(' ')
        change_date = change_date_str.strip().split(' ')
        reason = reason_str.strip().split(' ')
        captital_amount = captital_amount_str.strip().split(' ')


        # assert change_date is now lost, To do publish_time will be 1970-1-1
        max_date = CapitalStockAmountHistory.objects.filter(code=stock_code).aggregate(Max('change_date'))['change_date__max']
        items = list()
        for i in range(lenth):
            captial_item = CapitalStockAmountHistoryItem()
            captial_item['code'] = stock_code
            captial_item['change_date'] = change_date[i]
            if i < len(public_date):
                if not public_date[i] and public_date[i] != '': 
                    captial_item['public_date'] = public_date[i]
            if i < len(reason):
                captial_item['reason'] = reason[i]
            if i < len(captital_amount):
                captial_item['num'] = float(captital_amount[i])
            items.append(captial_item)
            if not max_date is None and str(captial_item['change_date']) > str(max_date):
                yield captial_item
            else:
                continue

class StockFinanceSpider(scrapy.Spider):
    name = "stock_finance_spider"
    all_stock_code = []

    custom_settings = {
        'ITEM_PIPELINES': {
            'stock_spider.pipelines.FinanceHistoryPipeline': 1
        }
    }

    def start_requests(self):
        stock_set = StockInfo.objects.all()
        for one in stock_set:
            self.all_stock_code.append(one.code)
        for one in self.all_stock_code:
            # one = "000735"
            url_finance = "http://vip.stock.finance.sina.com.cn/corp/go.php/vFD_FinanceSummary/stockid/%s.phtml"%(str(one))
            yield scrapy.Request(url_finance, self.parse_finance)
            # break

    def parse_finance(self, response):

        sel = Selector(response)
        codelist = sel.xpath('//meta[re:test(@name,"Keywords")]/@content').extract()
        stock_code = str(codelist[0]).split(')')[0].split('(')[1]
        name = u"截止日期"
        deadline_str = ""
        stock_list = sel.xpath('//table[re:test(@id,"FundHoldSharesTable")]/tr/td/strong[re:test(text(),"%s")]/parent::*/following-sibling::*//text()'%(name)).extract()
        for stock in stock_list:
            deadline_str += str(stock.strip().split("元")[0].strip()) + " "

        name = u"每股净资产"
        per_share_net_asset_str = ""
        stock_list = sel.xpath('//table[re:test(@id,"FundHoldSharesTable")]/tr/td[re:test(text(),"%s")]/following-sibling::*//text()'%(name)).extract()
        for stock in stock_list:
            per_share_net_asset_str += str(stock.strip().split("元")[0].strip()) + " "

        name = u"资产总计"
        total_asset_str = ""
        stock_list = sel.xpath('//table[re:test(@id,"FundHoldSharesTable")]/tr/td[re:test(text(),"%s")]/following-sibling::*//text()'%(name)).extract()
        for stock in stock_list:
            total_asset_str += str(stock.strip().split("元")[0].strip()) + " "

        name = u"长期负债合计"
        total_liabilities_str = ""
        stock_list = sel.xpath('//table[re:test(@id,"FundHoldSharesTable")]/tr/td[re:test(text(),"%s")]/following-sibling::*//text()'%(name)).extract()
        for stock in stock_list:
            total_liabilities_str += str(stock.strip().split("元")[0].strip()) + " "

        name = u"主营业务收入"
        business_income_str = ""
        stock_list = sel.xpath('//table[re:test(@id,"FundHoldSharesTable")]/tr/td[re:test(text(),"%s")]/following-sibling::*//text()'%(name)).extract()
        for stock in stock_list:
            business_income_str += str(stock.strip().split("元")[0].strip()) + " "

        name = u"净利润"
        net_profit_str = ""
        stock_list = sel.xpath('//table[re:test(@id,"FundHoldSharesTable")]/tr/td[re:test(text(),"%s")]/following-sibling::*//text()'%(name)).extract()
        for stock in stock_list:
            net_profit_str += str(stock.strip().split("元")[0].strip()) + " "

        lenth = len(deadline_str.split(' ')) - 1
        deadline_set = deadline_str.split(' ')
        per_share_net_asset_set = per_share_net_asset_str.split(' ')
        total_asset_set = total_asset_str.split(' ')
        total_liabilities_set = total_liabilities_str.split(' ')
        business_income_set = business_income_str.split(' ')
        net_profit_set = net_profit_str.split(' ')
        FinanceHistory
        max_date = FinanceHistory.objects.filter(code=stock_code).aggregate(Max('date'))['date__max']
        for i in range(lenth):
            ai = bi = ci = di = ei = fi = "-1"
            if(deadline_set[i] != ''):
                ai = deadline_set[i].strip()
            if(per_share_net_asset_set[i] != ''):
                bi = ''.join(per_share_net_asset_set[i].strip().split(','))
            if(total_asset_set[i] != ''):
                ci = ''.join(total_asset_set[i].strip().split(','))
            if(total_liabilities_set[i] != ''):
                di = ''.join(total_liabilities_set[i].strip().split(','))
            if(business_income_set[i] != ''):
                ei = ''.join(business_income_set[i].strip().split(','))
            if(net_profit_set[i] != ''):
                fi = ''.join(net_profit_set[i].strip().split(','))

            item = FinanceHistoryItem()
            item['code'] = stock_code
            item['date'] = ai
            item['per_share_net_asset'] = bi
            item['total_asset'] = ci
            item['total_liabilities'] = di
            item['business_income'] = ei
            item['net_profit'] = fi
            if not max_date is None and str(item['date']) > str(max_date):
                yield item
            else:
                continue

class StockTradeRecordSpider(scrapy.Spider):
    name = "stock_trade_record_spider"
    all_stock_code = []
    stock_market_list_date = []

    custom_settings = {
        'LOG_FILE' : "scrapy_spider_trade_record.log",
        'DOWNLOAD_DELAY' : 2,
        'DOWNLOAD_TIMEOUT' : 100,
        'CONCURRENT_REQUESTS_PER_IP' : 5,
        'ITEM_PIPELINES': {
            'stock_spider.pipelines.TradeRecordPipeline': 1
        }
    }

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

    def get_year_seazon(self, strdate):
        if self.is_valid_date(strdate):
            year = int(strdate.split('-')[0])
            month = strdate.split('-')[1]
            seazon = int(math.ceil(int(month)/3))
            return True, year, seazon
        else:
            return False, "", ""

    def start_requests(self):
        stock_set = StockInfo.objects.all().order_by('-id')
        for one in stock_set:
            self.all_stock_code.append(one.code)
            self.stock_market_list_date.append(one.market_list_date)
        for i, element in enumerate(self.all_stock_code):
            # element = "000735"
            market_date = self.stock_market_list_date[i]
            re, year, seazon = self.get_year_seazon(str(market_date))
            if not re :
                continue
            today = date.today()
            re, today_year, today_seazon = self.get_year_seazon(str(today))
            while year <= today_year:
                if year == today_year and seazon > today_seazon:
                    break

                if seazon % 4 == 0:
                    url_trade_record = "http://vip.stock.finance.sina.com.cn/corp/go.php/vMS_MarketHistory/stockid/%s.phtml?year=%s&jidu=4"%(element, year)
                    seazon = 0
                    year += 1
                else:
                    url_trade_record = "http://vip.stock.finance.sina.com.cn/corp/go.php/vMS_MarketHistory/stockid/%s.phtml?year=%s&jidu=%s"%(element, year, seazon)
                seazon += 1
                yield scrapy.Request(url_trade_record, self.parse_trade_record)
            # break

    def parse_trade_record(self, response):

        sel = Selector(response)
        codelist = sel.xpath('//meta[re:test(@name,"Keywords")]/@content').extract()
        stock_code = str(codelist[0]).split(')')[0].split('(')[1]

        name = sel.xpath('//table[re:test(@id,"FundHoldSharesTable")]/thead/tr//th//text()').extract()
        if name == []:
            return
        stock_list = sel.xpath('//table[re:test(@id,"FundHoldSharesTable")]/tr//td//text()').extract()
        count = 0
        item = TradeRecordItem()
        for stock in stock_list:
            if stock.strip() == "":
                continue
            if count < 7:
                count += 1
                continue
            temp = count % 7
            count += 1
            if temp == 0:
                if not self.is_valid_date(stock.strip()):
                    count -= 1
                    continue
                item = TradeRecordItem()
                item['code'] = stock_code
                item['date'] = stock.strip()
            elif temp == 1:
                item['open_price'] = stock.strip()
            elif temp == 2:
                item['hignest_price'] = stock.strip()
            elif temp == 3:
                item['close_price'] = stock.strip()
            elif temp == 4:
                item['lowest_price'] = stock.strip()
            elif temp == 5:
                item['trade_volume'] = stock.strip()
            else:
                item['trade_amount'] = stock.strip()
                yield item

class StockBonusHistorySpider(scrapy.Spider):
    name = "stock_bonus_spider"
    all_stock_code = []

    custom_settings = {
        'ITEM_PIPELINES': {
            'stock_spider.pipelines.StockBonusHistoryPipeline': 1
        }
    }

    def start_requests(self):
        stock_set = StockInfo.objects.all()
        for one in stock_set:
            self.all_stock_code.append(one.code)
        for one in self.all_stock_code:
            url = "http://vip.stock.finance.sina.com.cn/corp/go.php/vISSUE_ShareBonus/stockid/%s.phtml"%(str(one))
            yield scrapy.Request(url, self.parse_stock_bonus)

    def parse_stock_bonus(self, response):

        sel = Selector(response)
        codelist = sel.xpath('//meta[re:test(@name,"Keywords")]/@content').extract()
        stock_code = str(codelist[0]).split(')')[0].split('(')[1]

        stock_list = sel.xpath('//div/table[re:test(@id,"sharebonus_1")]/tbody/tr/td[1]//text()').extract()
        public_date_str = ""
        sign = 0
        for stock in stock_list:
            if stock.strip() == "暂时没有数据！":
                sign = 1
                break
            else:
                public_date_str += (str(stock.strip()) + " ")
        if sign != 1:
            stock_give_str = ""
            stock_list = sel.xpath('//div/table[re:test(@id,"sharebonus_1")]/tbody/tr/td[2]//text()').extract()
            for stock in stock_list:
                stock_give_str += (str(stock.strip()) + " ")

            stock_transfer_str = ""
            stock_list = sel.xpath('//div/table[re:test(@id,"sharebonus_1")]/tbody/tr/td[3]//text()').extract()
            for stock in stock_list:
                stock_transfer_str += (str(stock.strip()) + " ")

            stock_bonus_str = ""
            stock_list = sel.xpath('//div/table[re:test(@id,"sharebonus_1")]/tbody/tr/td[4]//text()').extract()
            for stock in stock_list:
                stock_bonus_str += (str(stock.strip()) + " ")

            status_str = ""
            stock_list = sel.xpath('//div/table[re:test(@id,"sharebonus_1")]/tbody/tr/td[5]//text()').extract()
            for stock in stock_list:
                status_str += (str(stock.strip()) + " ")

            exright_date_str = ""
            stock_list = sel.xpath('//div/table[re:test(@id,"sharebonus_1")]/tbody/tr/td[6]//text()').extract()
            for stock in stock_list:
                exright_date_str += (str(stock.strip()) + " ")

            lenth = len(public_date_str.split(' ')) - 1
            public_date = public_date_str.split(' ')
            stock_give = stock_give_str.split(' ')
            stock_transfer = stock_transfer_str.split(' ')
            stock_bonus = stock_bonus_str.split(' ')
            status = status_str.split(' ')
            exright_date = exright_date_str.split(' ')

            for i in range(lenth):
                item = StockBonusHistoryItem()
                item['code'] = stock_code
                if public_date[i] != '--':
                    item['public_date'] = public_date[i]
                if exright_date[i] != '--':
                    item['exright_date'] = exright_date[i]
                if status[i] == "实施":
                    item['status'] = True
                else:
                    item['status'] = False
                item['stock_give'] = stock_give[i]
                item['stock_transfer'] = stock_transfer[i]
                item['stock_bonus'] = stock_bonus[i]
                yield item

class StockAllotmentHistorySpider(scrapy.Spider):
    name = "stock_allotment_spider"
    all_stock_code = []

    custom_settings = {
        'ITEM_PIPELINES': {
            'stock_spider.pipelines.StockAllotmentHistoryPipeline': 1
        }
    }

    def start_requests(self):
        stock_set = StockInfo.objects.all()
        for one in stock_set:
            self.all_stock_code.append(one.code)
        for one in self.all_stock_code:
            url = "http://vip.stock.finance.sina.com.cn/corp/go.php/vISSUE_ShareBonus/stockid/%s.phtml"%(str(one))
            yield scrapy.Request(url, self.parse_stock_allotment)

    def parse_stock_allotment(self, response):
        sel = Selector(response)
        codelist = sel.xpath('//meta[re:test(@name,"Keywords")]/@content').extract()
        stock_code = str(codelist[0]).split(')')[0].split('(')[1]

        sign = 0
        public_date_str = ""
        stock_list = sel.xpath('//div/table[re:test(@id,"sharebonus_2")]/tbody/tr/td[1]//text()').extract()
        for stock in stock_list:
            if stock.strip() == "暂时没有数据！":
                sign = 1
                break
            else:
                public_date_str += (str(stock.strip()) + " ")
        if sign != 1:
            allotment_num_str = ""
            stock_list = sel.xpath('//div/table[re:test(@id,"sharebonus_2")]/tbody/tr/td[2]//text()').extract()
            for stock in stock_list:
                allotment_num_str += (str(stock.strip()) + " ")

            allotment_price_str = ""
            stock_list = sel.xpath('//div/table[re:test(@id,"sharebonus_2")]/tbody/tr/td[3]//text()').extract()
            for stock in stock_list:
                allotment_price_str += (str(stock.strip()) + " ")

            allotment_capital_base_str = ""
            stock_list = sel.xpath('//div/table[re:test(@id,"sharebonus_2")]/tbody/tr/td[4]//text()').extract()
            for stock in stock_list:
                allotment_capital_base_str += (str(stock.strip()) + " ")

            exright_date_str = ""
            stock_list = sel.xpath('//div/table[re:test(@id,"sharebonus_2")]/tbody/tr/td[5]//text()').extract()
            for stock in stock_list:
                exright_date_str += (str(stock.strip()) + " ")

            record_date_str = ""
            stock_list = sel.xpath('//div/table[re:test(@id,"sharebonus_2")]/tbody/tr/td[6]//text()').extract()
            for stock in stock_list:
                record_date_str += (str(stock.strip()) + " ")

            lenth = len(public_date_str.split(' ')) - 1

            public_date = public_date_str.split(' ')
            allotment_num = allotment_num_str.split(' ')
            allotment_price = allotment_price_str.split(' ')
            allotment_capital_base = allotment_capital_base_str.split(' ')
            exright_date = exright_date_str.split(' ')
            record_date = record_date_str.split(' ')

            for i in range(lenth):
                item = StockAllotmentHistoryItem()
                item['code'] = stock_code
                if public_date[i] != '--':
                    item['public_date'] = public_date[i]
                if exright_date[i] != '--':
                    item['exright_date'] = exright_date[i]
                if record_date[i] != '--':
                    item['record_date'] = record_date[i]
                item['allotment_num'] = allotment_num[i]
                item['allotment_price'] = allotment_price[i]
                item['allotment_capital_base'] = allotment_capital_base[i]
                yield item

class StockTradeRecordTaskSpider(scrapy.Spider):
    name = "stock_trade_record_task_spider"
    all_stock_code = []

    custom_settings = {
        'ITEM_PIPELINES': {
            'stock_spider.pipelines.TradeRecordTaskPipeline': 1
        }
    }

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

    def get_year_seazon(self, strdate):
        if self.is_valid_date(strdate):
            year = int(strdate.split('-')[0])
            month = strdate.split('-')[1]
            seazon = int(math.ceil(int(month)/3))
            return True, year, seazon
        else:
            return False, "", ""

    def start_requests(self):
        stock_set = StockInfo.objects.all()
        for one in stock_set:
            self.all_stock_code.append(one.code)

        for i, element in enumerate(self.all_stock_code):
            today = date.today()
            last_day = today + timedelta(days=-10)
            re, year, seazon = self.get_year_seazon(str(last_day))
            re, today_year, today_seazon = self.get_year_seazon(str(today))
            while year <= today_year:
                if year == today_year and seazon > today_seazon:
                    break

                if seazon % 4 == 0:
                    url_trade_record = "http://vip.stock.finance.sina.com.cn/corp/go.php/vMS_MarketHistory/stockid/%s.phtml?year=%s&jidu=4"%(element, year)
                    seazon = 0
                    year += 1
                else:
                    url_trade_record = "http://vip.stock.finance.sina.com.cn/corp/go.php/vMS_MarketHistory/stockid/%s.phtml?year=%s&jidu=%s"%(element, year, seazon)
                seazon += 1
                yield scrapy.Request(url_trade_record, self.parse_trade_record)
            # break

    def parse_trade_record(self, response):

        sel = Selector(response)
        codelist = sel.xpath('//meta[re:test(@name,"Keywords")]/@content').extract()
        stock_code = str(codelist[0]).split(')')[0].split('(')[1]

        name = sel.xpath('//table[re:test(@id,"FundHoldSharesTable")]/thead/tr//th//text()').extract()
        if name == []:
            return
        stock_list = sel.xpath('//table[re:test(@id,"FundHoldSharesTable")]/tr//td//text()').extract()
        count = 0
        item = TradeRecordItem()
        for stock in stock_list:
            if stock.strip() == "":
                continue
            if count < 7:
                count += 1
                continue
            temp = count % 7
            count += 1
            if temp == 0:
                if not self.is_valid_date(stock.strip()):
                    count -= 1
                    continue
                item = TradeRecordItem()
                item['code'] = stock_code
                item['date'] = stock.strip()
            elif temp == 1:
                item['open_price'] = stock.strip()
            elif temp == 2:
                item['hignest_price'] = stock.strip()
            elif temp == 3:
                item['close_price'] = stock.strip()
            elif temp == 4:
                item['lowest_price'] = stock.strip()
            elif temp == 5:
                item['trade_volume'] = stock.strip()
            else:
                item['trade_amount'] = stock.strip()
                yield item

class TestSpider(scrapy.Spider):
    name = "test_spider"

    start_url = [
        "http://beemp3s.org/artists/"
    ]

    name_list = []

    a = ord('a')
    for i in range(26):
        c = chr(a + i)
        name_list.append(c)

    a = ord('0')
    for i in range(10):
        c = chr(a + i)
        name_list.append(c)

    name_list = ['a']

    def start_requests(self):
        for url_base in self.start_url:
            for name in self.name_list:
                url = url_base + name
                yield SplashRequest(url, self.parse_artist, args={'wait': 3})

    def parse_artist(self, response):
        print("+++++")
        sel = Selector(response)
        popular_artist_list = sel.xpath(
            '//div[re:test(@class,"container bg_yellow padding_20px")]' +
            '/div[re:test(@class,"row margin-bottom30")]/div//text()'
        ).extract()
        for one in popular_artist_list:
            print(one)
