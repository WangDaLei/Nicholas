
import os
import re
import json
import copy

from datetime import datetime, date, timedelta
import requests
import mistune
from django.db.models import Max
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.header import Header
from .models import \
    ChangeHistory, CapitalStockAmountHistory, FinanceHistory,\
    StockBonusHistory, StockAllotmentHistory, StockInfo,\
    TradeRecord, IndexRecord, CoinInfo, CoinRecord
from stock_project.config import \
    mail_hostname, mail_username, mail_password,\
    mail_encoding, mail_from, mail_to

from scrapy.selector import Selector
from PyPDF2 import PdfFileReader
from tabula import read_pdf


def get_stock_name_code(stock):
    return str(stock.name) + "(" + str(stock.code) + ") "


def get_stock_info():
    change_history = ChangeHistory.objects.filter(
        generated_time=date.today()).order_by('stock_id')

    info = ""
    str_name = "%s名字: 从%s变为%s\n"
    str_block = "%s板块: 从%s变为%s\n"
    str_property = "%s企业性质: 从%s变为%s\n"
    str_time = "%s上市时间: 从%s变为%s\n"
    str_capital = "%s股本: 从%s万股变为%s万股\n"
    str_status = "%s状态: 从%s变为%s\n"
    for one in change_history:
        if one.field == 'name':
            info += str_name % (
                get_stock_name_code(one.stock), str(one.change_source),
                str(one.change_target))
        elif one.field == 'block':
            info += str_block % (
                get_stock_name_code(one.stock), str(one.change_source),
                str(one.change_target))
        elif one.field == 'ownership':
            info += str_property % (
                get_stock_name_code(one.stock), str(one.change_source),
                str(one.change_target))
        elif one.field == 'market_list_date':
            info += str_time % (
                get_stock_name_code(one.stock), str(one.change_source),
                str(one.change_target))
        elif one.field == 'equity':
            info += str_capital % (
                get_stock_name_code(one.stock), str(one.change_source),
                str(one.change_target))
        elif one.field == 'status':
            info += str_status % (
                get_stock_name_code(one.stock), str(one.change_source),
                str(one.change_target))
        else:
            pass
    if info != "":
        return "### 股票状态变化\n```\n" + info + "```\n"
    else:
        return info


def get_pre_capital_amount(stock):
    pre_capital_amount = CapitalStockAmountHistory.objects.filter(
        stock=stock).order_by('-change_date')
    if pre_capital_amount.count() <= 1:
        return str(0)
    else:
        return str(pre_capital_amount[1].num)


def get_capital_amount():
    start_time = datetime.combine(date.today(), datetime.min.time())
    end_time = datetime.combine(
        date.today() + timedelta(days=1), datetime.min.time())
    capital_amount = CapitalStockAmountHistory.objects.filter(
        generated_time__range=[start_time, end_time]).order_by('stock_id')

    info = ""
    str_output = "%s由于%s 股本数量由%s万股变为%s万股, 改变的时间为:%s\n"
    for one in capital_amount:
        info += str_output % (
            get_stock_name_code(one.stock), str(one.reason),
            get_pre_capital_amount(one.stock), str(one.num),
            str(one.change_date))

    if info != "":
        return "### 股本变化\n```\n" + info + "```\n"
    else:
        return info


def get_pre_finance(stock):
    pre_capital_amount = FinanceHistory.objects.filter(stock=stock).order_by('-date')
    if pre_capital_amount.count() <= 1:
        return None
    else:
        return pre_capital_amount[1]


def get_finance():
    start_time = datetime.combine(date.today(), datetime.min.time())
    end_time = datetime.combine(date.today() + timedelta(days=1), datetime.min.time())
    finance = FinanceHistory.objects.filter(generated_time__range=[start_time, end_time])\
        .order_by('stock_id')

    info = ""
    str_compare = "%s发布财报: 每股净资产为%s 总资产为%s 总债务为%s 营业收入为%s" +\
                  " 总利润为%s 财报日期%s\n    其前值分别是: 每股净资产%s 总资产为%s 总债务为%s" +\
                  " 营业收入为%s 总利润为%s 财报日期%s\n"
    str_capital = "%s首次发布财报: 每股净资产为%s 总资产为%s 总债务为%s 营业收入为%s 总利润为%s\n"
    for one in finance:
        pre_capital_amount = get_pre_finance(one.stock)
        if pre_capital_amount:
            info += str_compare % (
                get_stock_name_code(one.stock), str(one.per_share_net_asset),
                str(one.total_asset), str(one.total_liabilities), str(one.business_income),
                str(one.net_profit), str(one.date), str(one.per_share_net_asset),
                str(one.total_asset), str(one.total_liabilities), str(one.business_income),
                str(one.net_profit), str(one.date))
        else:
            info += str_capital % (
                get_stock_name_code(one.stock), str(one.per_share_net_asset),
                str(one.total_asset), str(one.total_liabilities), str(one.business_income),
                str(one.net_profit))
    if info != "":
        return "### 公司财报\n```\n" + info + "```\n"
    else:
        return info


def get_bonus_allot():
    info = ""
    start_time = datetime.combine(date.today(), datetime.min.time())
    end_time = datetime.combine(date.today() + timedelta(days=1), datetime.min.time())
    bonus = StockBonusHistory.objects.filter(
        generated_time__range=[start_time, end_time], status=True).order_by('stock_id')
    allotment = StockAllotmentHistory.objects.filter(
        generated_time__range=[start_time, end_time]).order_by('stock_id')

    str_bonus = "%s分红: 送股(10股)%s 转股(10股)%s 派息%s 公布日期%s 除权日期%s\n"
    str_allotment = "%s配股: 数量(10股)%s 价格%s 基数(万股)%s 公布日期%s 除权日期%s 记录日期%s\n"
    for one in bonus:
        info += str_bonus % (
            get_stock_name_code(one.stock), str(one.stock_give), str(one.stock_transfer),
            str(one.stock_bonus), str(one.public_date), str(one.exright_date))
    for one in allotment:
        info += str_allotment % (
            get_stock_name_code(one.stock), str(one.allotment_num), str(one.allotment_price),
            str(one.allotment_capital_base), str(one.public_date), str(one.exright_date),
            str(one.record_date))
    if info != "":
        return "### 公司分红信息\n```\n" + info + "```\n"
    else:
        return info


def get_trade_amount_sum():
    today = date.today()
    shang_str = ""
    shen_str = ""
    big_block_str = ""
    for i in range(30):
        stocks = StockInfo.objects.filter(stock_exchange='上证交易所')
        one_date = today + timedelta(days=-1 * i)
        sum_amount = 0.0
        for one in stocks:
            trade_one = TradeRecord.objects.filter(date=one_date, code=one.code)
            if trade_one:
                sum_amount += trade_one.first().trade_amount
        # sum_amount = TradeRecord.objects.filter(date=one_date, stock__stock_exchange='上证交易所')\
        #                 .aggregate(num=Sum('trade_amount')).get('num') or 0
        sum_amount = round(sum_amount / 100000000, 2)
        if sum_amount:
            shang_str += '上证交易所:' + str(one_date) + " " + str(sum_amount) + "亿\n"

    for i in range(30):
        stocks = StockInfo.objects.filter(stock_exchange='深证交易所')
        one_date = today + timedelta(days=-1 * i)
        sum_amount = 0.0
        for one in stocks:
            trade_one = TradeRecord.objects.filter(date=one_date, code=one.code)
            if trade_one:
                sum_amount += trade_one.first().trade_amount
        # sum_amount = TradeRecord.objects.filter(date=one_date, stock__stock_exchange='深证交易所')\
        #                 .aggregate(num=Sum('trade_amount')).get('num') or 0
        sum_amount = round(sum_amount / 100000000, 2)
        if sum_amount:
            shen_str += '深证交易所:' + str(one_date) + " " + str(sum_amount) + "亿\n"

    big_block_list = StockInfo.objects.values_list('big_block').distinct()
    for one in big_block_list:
        if str(one[0]) == '':
            continue
        for i in range(7):
            one_date = today + timedelta(days=-1 * i)
            stocks = StockInfo.objects.filter(big_block=one[0])
            sum_amount = 0.0
            for one_stock in stocks:
                trade_one = TradeRecord.objects.filter(date=one_date, code=one_stock.code)
                if trade_one:
                    sum_amount += trade_one.first().trade_amount

            # sum_amount = TradeRecord.objects.filter(date=one_date, stock__big_block=one)\
            #                 .aggregate(num=Sum('trade_amount')).get('num') or 0
            sum_amount = round(sum_amount / 100000000, 2)
            if sum_amount:
                big_block_str += str(one[0]) + ':' + str(one_date) + " " + str(sum_amount) + "亿\n"
        big_block_str += '\n'

    if not shang_str and not shen_str and not big_block_str:
        return ""
    else:
        info = "### 交易量统计\n"
        if shang_str:
            info += "#### 上证\n```\n" + shang_str + "```\n"
        if shen_str:
            info += "#### 深证\n```\n" + shen_str + "```\n"
        if big_block_str:
            info += "#### 分模块统计\n```\n" + big_block_str + "```\n"
        return info


def send_email(info):
    info = mistune.markdown(info, escape=True, hard_wrap=True)

    mail_info = {
        "hostname": mail_hostname,
        "username": mail_username,
        "password": mail_password,
        "mail_encoding": mail_encoding
    }

    mail_info["from"] = mail_from
    mail_info["to"] = mail_to
    mail_info["mail_subject"] = "Daily Stock"
    mail_info["mail_text"] = info

    smtp = SMTP_SSL(mail_info["hostname"])
    smtp.ehlo(mail_info["hostname"])
    smtp.login(mail_info["username"], mail_info["password"])

    msg = MIMEText(mail_info["mail_text"], "html", mail_info["mail_encoding"])
    msg["Subject"] = Header(mail_info["mail_subject"], mail_info["mail_encoding"])
    msg["from"] = mail_info["from"]
    msg["to"] = ",".join(mail_info["to"])

    smtp.sendmail(mail_info["from"], mail_info["to"], msg.as_string())
    smtp.quit()


def crawl_block_from_CSRC():
    url_base = "http://www.csrc.gov.cn/pub/newsite/scb/ssgshyfljg/"
    req = requests.get(url_base)

    if req.encoding == 'ISO-8859-1':
        encodings = requests.utils.get_encodings_from_content(req.text)
        if encodings:
            encoding = encodings[0]
        else:
            encoding = req.apparent_encoding

        global encode_content
        # 如果设置为replace，则会用?取代非法字符；
        encode_content = req.content.decode(encoding, 'replace')

        sel = Selector(text=encode_content)
        name_list = sel.xpath('//div/div/div[re:test(text(), "上市公司行业分类结果")]\
                        /parent::*/following-sibling::*/ul/li/a//text()').extract()

        url_list = sel.xpath('//div/div/div[re:test(text(), "上市公司行业分类结果")]\
                        /parent::*/following-sibling::*/ul/li/a/@href').extract()

        date_list = sel.xpath('//div/div/div[re:test(text(), "上市公司行业分类结果")]\
                        /parent::*/following-sibling::*/ul/li/span//text()').extract()

        if len(date_list):
            sign = 0
            max_date = date_list[0]
            for i in range(len(date_list)):
                if date_list[i] > max_date:
                    max_date = date_list[i]
        else:
            return False, None, None

        name = name_list[sign]
        url = url_list[sign]

        if os.path.exists('CSRC/' + str(max_date)):
            return False, None, None
        else:
            os.makedirs('CSRC/' + str(max_date))
            url = url_base + url_list[sign][2:]
            req = requests.get(url)

            if req.encoding == 'ISO-8859-1':
                encodings = requests.utils.get_encodings_from_content(req.text)
                if encodings:
                    encoding = encodings[0]
                else:
                    encoding = req.apparent_encoding

                # 如果设置为replace，则会用?取代非法字符；
                encode_content1 = req.content.decode(encoding, 'replace')
                sel = Selector(text=encode_content1)
                pdf_list = sel.xpath('//a[re:test(text(), "%s")]//@href' % (name)).extract()
                pdf_name = pdf_list[0]
                pdf_url = url.rsplit('/', 1)[0] + pdf_name[1:]

                req = requests.get(pdf_url)
                file_pdf = open('CSRC/' + str(max_date) + "/" + pdf_name[2:], 'wb')
                file_pdf.write(req.content)
                file_pdf.close()
                return True, max_date, pdf_name[2:]
            return False, None, None


def parse_CRSC_PDF(date, name):

    pages = PdfFileReader(open('./CSRC/' + date + '/' + name, 'rb')).getNumPages()

    pre_block = ""
    pre_small_block = ""
    count = 0

    json_dict = {}

    for i in range(pages):
        content = read_pdf('./CSRC/' + date + '/' + name, pages=i + 1, multiple_tables=True)
        content_list = re.split(r'[ \n]+', str(content))

        for j in range(len(content_list)):
            if j < 12:
                continue
            if j % 6 == 1:
                if not content_list[j].endswith(')') and content_list[j] != 'NaN':
                    if j + 7 < len(content_list) and content_list[j + 7] == 'NaN' and\
                       content_list[j + 6] != 'NaN':
                        big_block = content_list[j] + content_list[j + 6]
                        m = 2
                        while not big_block.endswith(')'):
                            if j + 6 * m + 1 > len(content_list):
                                break
                            if content_list[6 * m + j + 1] == 'NaN' and\
                               content_list[6 * m + j] != 'NaN':
                                big_block += content_list[6 * m + j]
                            else:
                                break
                            m += 1
                    else:
                        big_block = content_list[j]
                    if pre_block.find(big_block) == -1:
                        if big_block.find(pre_block) != -1 and pre_block != "":
                            json_dict[big_block] = copy.deepcopy(json_dict[pre_block])
                            json_dict.pop(pre_block)
                            pre_block = big_block
                        else:
                            pre_block = big_block
                            json_dict[pre_block] = {}

                elif content_list[j].endswith(')'):
                    big_block = content_list[j]
                    if pre_block.find(big_block) == -1:
                        if big_block.find(pre_block) != -1 and pre_block != "":
                            json_dict[big_block] = copy.deepcopy(json_dict[pre_block])
                            json_dict.pop(pre_block)
                            pre_block = big_block
                        else:
                            pre_block = big_block
                            json_dict[pre_block] = {}

                else:
                    pass
            if j % 6 == 3:
                if content_list[j] != 'NaN':
                    if j + 5 < len(content_list) and content_list[j + 5] == 'NaN' and\
                       content_list[j + 6] != 'NaN':
                        small_block = content_list[j] + content_list[j + 6]
                        m = 2
                        while not big_block.endswith(')'):
                            if 6 * m + j > len(content_list):
                                break
                            if content_list[6 * m + j - 1] == 'NaN' and\
                               content_list[6 * m + j] != 'NaN':
                                small_block += content_list[6 * m + j]
                            else:
                                break
                            m += 1
                    else:
                        small_block = content_list[j]
                    if pre_small_block.find(small_block) == -1:
                        if small_block.find(pre_small_block) != -1 and pre_small_block != "":
                            json_dict[pre_block][small_block] = copy.deepcopy(
                                json_dict[pre_block][pre_small_block])
                            json_dict[pre_block].pop(pre_small_block)
                            pre_small_block = small_block
                        else:
                            pre_small_block = small_block
                            json_dict[pre_block][pre_small_block] = []
                else:
                    pass
            if j % 6 == 4:
                if content_list[j] != 'NaN':
                    code = content_list[j]
                    json_dict[pre_block][pre_small_block].append(code)
                    if code.startswith('6') or code.startswith('0'):
                        count += 1
                else:
                    pass

    with open('./CSRC/' + date + '/' + "re.json", 'w') as f:
        f.write(json.dumps(json_dict, ensure_ascii=False))


def repair_json_files(date):
    with open('./CSRC/' + date + '/' + "re.json", 'r') as f:
        content = json.loads(f.read())
    with open('./CSRC/base/template.json', 'r') as f:
        content_base = json.loads(f.read())

    base_big_block_list = []
    for key in content_base:
        base_big_block_list.append(key)

    for key in content:
        if key in base_big_block_list:
            continue
        else:
            for one in base_big_block_list:
                if one.find(key) != -1:
                    content[one] = content[key]
                    content.pop(key)
                    break
                else:
                    continue

    base_small_block_list = []
    for key in content_base:
        small_block = content_base[key]
        for one in small_block:
            base_small_block_list.append(one)

    for key in content:
        for one in content[key]:
            if one in base_small_block_list:
                continue
            else:
                for small in base_small_block_list:
                    if small.find(one) != -1:
                        content[key][small] = content[key][one]
                        content[key].pop(one)
                        break
    with open('./CSRC/' + date + '/' + "re.json", 'w') as f:
        f.write(json.dumps(content, ensure_ascii=False))


def update_block(file_date):
    with open('./CSRC/' + file_date + '/' + "re.json", 'r') as f:
        content = json.loads(f.read())

    for key in content:
        for small in content[key]:
            code_list = content[key][small]
            for code in code_list:
                stock_set = StockInfo.objects.filter(code=code)
                if stock_set:
                    one = stock_set.first()
                    if one.big_block != key:
                        ChangeHistory.objects.create(
                            stock=one, change_source=one.big_block,
                            change_target=key, field='big_block',
                            generated_time=date.today())
                        one.big_block = key
                        one.save()

                    if one.block != small:
                        ChangeHistory.objects.create(
                            stock=one, change_source=one.block,
                            change_target=small, field='block',
                            generated_time=date.today())
                        one.block = small
                        one.save()


def crawl_index_from_sohu():
    url_base = "http://q.stock.sohu.com/hisHq?code=zs_%s&start=%s&end=%s"

    index_code = ['000001', '399001']
    index_name = ['上证指数', '深证指数']

    for i, code in enumerate(index_code):
        max_date = IndexRecord.objects.filter(code=code).aggregate(Max('date'))['date__max']
        if max_date:
            start_date = max_date + timedelta(days=1)
            start_date = str(start_date).replace('-', '')
        else:
            start_date = '20000101'

        end_date = str(date.today()).replace('-', '')
        url = url_base % (code, start_date, end_date)

        req = requests.get(url)

        res_list = json.loads(req.content)

        if len(res_list):
            hq = res_list[0]['hq']
            for one in hq:
                index, _ = IndexRecord.objects.get_or_create(
                    code=code, name=index_name[i], date=one[0])
                index.open_index = one[1]
                index.highest_index = one[6]
                index.close_index = one[2]
                index.lowest_index = one[5]
                index.trade_volume = one[7]
                index.trade_amount = one[8]
                index.save()


def get_date_from_str(str):
    month_dict = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                  "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
    try:
        year = str.split(',')[1].strip()
        day = str.split(',')[0].split(' ')[1].strip()
        month = month_dict[str.split(',')[0].split(' ')[0].strip()]
        return date(int(year), int(month), int(day))
    except Exception as e:
        print(e)
        return date(2010, 1, 1)


def get_num_from_str(str):
    if str == '-':
        return 0
    return float(''.join(str.split(',')))


def craw_coin_from_coinmarket():
    """
    Crawl coin info.

        抓取币每天的交易信息.
    """
    all_coin_url = "https://s2.coinmarketcap.com/generated/search/quick_search.json"
    coin_trade_record_url = "https://coinmarketcap.com/currencies/%s/historical-data/" +\
                            "?start=20190101&end=20300101"

    req = requests.get(all_coin_url)
    res_list = json.loads(req.content)
    for one in res_list:
        name = one['name']
        symbol = one['symbol']
        slug = one['slug']
        rank = one['rank']
        coin, _ = CoinInfo.objects.get_or_create(name=name, symbol=symbol)
        if coin.slug != slug or coin.rank != rank:
            coin.slug = slug
            coin.rank = rank
            coin.save()

    coins = CoinInfo.objects.all().order_by('rank')
    for one in coins:
        print(one.symbol)
        slug = one.slug
        url = coin_trade_record_url % (slug)
        req = requests.get(url)
        sel = Selector(text=req.content)
        name_list = sel.xpath(
            '//div[re:test(@class, "table-responsive")]/' +
            'table[re:test(@class, "table")]/tbody/tr[re:test(@class, "text-right")]/td//text()')\
            .extract()
        lenth = len(name_list) // 7

        for i in range(lenth):
            date = get_date_from_str(name_list[i * 7])
            open_price = get_num_from_str(name_list[i * 7 + 1])
            high_price = get_num_from_str(name_list[i * 7 + 2])
            low_price = get_num_from_str(name_list[i * 7 + 3])
            close_price = get_num_from_str(name_list[i * 7 + 4])
            dollar_volume = get_num_from_str(name_list[i * 7 + 5])
            market_cap = get_num_from_str(name_list[i * 7 + 6])

            coin_record = CoinRecord.objects.filter(coin=one, date=date)
            if not coin_record:
                CoinRecord.objects.create(
                    coin=one, date=date, symbol=one.symbol, open_price=open_price,
                    hignest_price=high_price, lowest_price=low_price, close_price=close_price,
                    trade_volume=dollar_volume, market_cap=market_cap)


def analysis_coin_price_based_coin():
    coins = CoinInfo.objects.filter(rank__lt=50)
    total = 1000000
    coin_dict = {}
    average_lenth = 3
    for one in coins:
        # print(one.symbol)
        coin_records = CoinRecord.objects.filter(coin=one).order_by('date')[365:]
        if not coin_records:
            continue
        if len(coin_records) < average_lenth:
            continue

        x = average_lenth
        while(x < len(coin_records)):
            sum_volume = 0
            for i in range(average_lenth):
                sum_volume += coin_records[x - i - 1].trade_volume

            average_volume = sum_volume / average_lenth

            if coin_records[x].trade_volume / average_volume > 1.1:
                if one.symbol not in coin_dict and total > 0:
                    total -= 20000
                    coin_dict[one.symbol] = 20000 / coin_records[x].close_price
                    str1 = ''
                    for key in coin_dict:
                        str1 += key + ":" + str(round(coin_dict[key], 2)) + ' '
                    print(round(total, 2), str1)

            if coin_records[x].close_price < coin_records[x - 1].close_price:
                if one.symbol in coin_dict:
                    total += coin_dict[one.symbol] * coin_records[x].close_price
                    str1 = ''
                    coin_dict.pop(one.symbol)
                    for key in coin_dict:
                        str1 += key + ":" + str(round(coin_dict[key], 2)) + ' '
                    print(round(total, 2), str1)
            x += 1


def analysis_coin_price_based_date():
    """
    Analysis.

        根据币的交易信息决定买入卖出策略
    """
    coins = CoinInfo.objects.filter(rank__lte=50)
    date_dict = {}
    date_today = date.today()
    min_date = date_today
    average_lenth = 5
    total = 1000000
    coin_dict = {}
    output_str = ''

    huobi_coin_list = ['BTC', 'ETH', 'XRP', 'BCH', 'LTC', 'ETC', 'EOS', 'ADA', 'DASH', 'OMG',
                       'ZEC', 'BTM', 'ELA', 'ONT', 'IOST', 'QTUM', 'TRX', 'DTA', 'ZIL', 'ELF',
                       'RUFF', 'HC', 'NEO', 'BSV']

    for one in coins:
        if one.symbol == 'USDT' or one.symbol == 'TUSD':
            continue
        if one.symbol not in huobi_coin_list:
            continue
        min_coin = CoinRecord.objects.filter(coin=one).order_by('date').first()
        date_dict[one.symbol] = min_coin.date
        if min_coin.date < min_date:
            min_date = min_coin.date

    # min_date += timedelta(days=365)
    min_date = date.today() + timedelta(days=-5)

    while min_date < date_today:
        for key in date_dict:
            if date_dict[key] + timedelta(days=365) < min_date:
                coin_record = CoinRecord.objects.filter(
                    symbol=key, date__lte=min_date).order_by('-date')
                if len(coin_record) < average_lenth + 1:
                    continue
                sum_volume = 0.0
                for i in range(average_lenth):
                    sum_volume += coin_record[i + 1].trade_volume
                average_volume = sum_volume / average_lenth
                if coin_record[0].trade_volume / average_volume > 1.2 and key not in coin_dict\
                   and total >= 20000 and coin_record[0].trade_volume / coin_record[1].trade_volume\
                   > 1.2:
                    total -= 20000
                    coin_dict[key] = 20000 / coin_record[0].close_price
                if coin_record[0].close_price < coin_record[1].close_price and key in coin_dict:
                    total += coin_dict[key] * coin_record[0].close_price
                    coin_dict.pop(key)
            else:
                pass
        str1 = ''
        for key in coin_dict:
            str1 += key + ":" + str(round(coin_dict[key], 2)) + ' '
        output_str += str(str(min_date) + " " + str(round(total, 2)) + " " + str1 + '\n')
        min_date += timedelta(days=1)
    send_email(output_str)
