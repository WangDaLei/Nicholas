# -*-coding:utf8-*-

import os
import re
import json

from datetime import datetime, date, timedelta
import requests
import smtplib
import mistune
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.header import Header
from dateutil.relativedelta import relativedelta
from .models import  ChangeHistory, CapitalStockAmountHistory, FinanceHistory,\
                        StockBonusHistory, StockAllotmentHistory, StockInfo,\
                        TradeRecord
from stock_project.config import mail_hostname, mail_username, mail_password,\
                                mail_encoding, mail_from, mail_to
from django.db.models import Sum

from scrapy.selector import Selector
from PyPDF2 import PdfFileReader
from tabula import read_pdf

def get_stock_name_code(stock):
    return str(stock.name) + "(" + str(stock.code) + ") "

def get_stock_info():
    change_history = ChangeHistory.objects.filter(generated_time=date.today()).order_by('stock_id')

    info = ""
    for one in change_history:
        if one.field == 'name':
            info += (get_stock_name_code(one.stock) + "名字: 从" + str(one.change_source) + "变为" +\
                    str(one.change_target) + "\n")
        elif one.field == 'block':
            info += (get_stock_name_code(one.stock) + "板块: 从" + str(one.change_source) + "变为" +\
                    str(one.change_target) + "\n")
        elif one.field == 'ownership':
            info += (get_stock_name_code(one.stock) + "企业性质: 从" + str(one.change_source) + "变为" +\
                    str(one.change_target) + "\n")
        elif one.field == 'market_list_date':
            info += (get_stock_name_code(one.stock) + "上市时间: 从" + str(one.change_source) + "变为" +\
                    str(one.change_target) + "\n")
        elif one.field == 'equity':
            info += (get_stock_name_code(one.stock) + "股本: 从" + str(one.change_source) + "万股变为" +\
                    str(one.change_target) + "万股\n")
        elif one.field == 'status':
            info += (get_stock_name_code(one.stock) + "状态: 从" + str(one.change_source) + "变为" +\
                    str(one.change_target) + "\n")
        else:
            pass
    if info != "":
        return "### 股票状态变化\n```\n" + info + "```\n"
    else:
        return info

def get_pre_capital_amount(stock):
    pre_capital_amount = CapitalStockAmountHistory.objects.filter(stock=stock).order_by('-change_date')
    if pre_capital_amount.count() <= 1:
        return str(0)
    else:
        return str(pre_capital_amount[1].num)

def get_capital_amount():
    start_time = datetime.combine(date.today(), datetime.min.time())
    end_time = datetime.combine(date.today() + timedelta(days=1), datetime.min.time())
    capital_amount = CapitalStockAmountHistory.objects.filter(generated_time__range=[start_time, end_time])\
                        .order_by('stock_id')

    info = ""
    for one in capital_amount:
        info += (get_stock_name_code(one.stock) + "由于" + str(one.reason) + " 股本数量由" +\
                    get_pre_capital_amount(one.stock) + "万股变为" + str(one.num) +"万股, 改变的时间为:"\
                    + str(one.change_date) + "\n")
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
    for one in finance:
        pre_capital_amount = get_pre_finance(one.stock)
        if pre_capital_amount:
            info += (get_stock_name_code(one.stock) + "发布财报: 每股净资产为" + str(one.per_share_net_asset)\
                        + " 总资产为" + str(one.total_asset) + " 总债务为" + str(one.total_liabilities)\
                        + " 营业收入为" + str(one.business_income) + " 总利润为" + str(one.net_profit)\
                        + " 财报日期" + str(one.date) + "\n    其前值分别是: 每股净资产" + str(one.per_share_net_asset)
                        + " 总资产为" + str(one.total_asset) + " 总债务为" + str(one.total_liabilities)\
                        + " 营业收入为" + str(one.business_income) + " 总利润为" + str(one.net_profit)\
                        + " 财报日期" + str(one.date) + "\n")
        else:
            info += (get_stock_name_code(one.stock) + "首次发布财报: 每股净资产为" + str(one.per_share_net_asset)\
                        + " 总资产为" + str(one.total_asset) + " 总债务为" + str(one.total_liabilities)\
                        + " 营业收入为" + str(one.business_income) + " 总利润为" + str(one.net_profit) + "\n")
    if info != "":
        return "### 公司财报\n```\n" + info + "```\n"
    else:
        return info
def get_bonus_allot():
    info = ""
    start_time = datetime.combine(date.today(), datetime.min.time())
    end_time = datetime.combine(date.today() + timedelta(days=1), datetime.min.time())
    bonus = StockBonusHistory.objects.filter(generated_time__range=[start_time, end_time],status=True)\
                        .order_by('stock_id')
    allotment = StockAllotmentHistory.objects.filter(generated_time__range=[start_time, end_time])\
                        .order_by('stock_id')

    for one in bonus:
        info += (get_stock_name_code(one.stock) + "分红: 送股(10股)" + str(one.stock_give)\
                    + " 转股(10股)" + str(one.stock_transfer) + " 派息" + str(one.stock_bonus)\
                    + " 公布日期" + str(one.public_date) + " 除权日期" + str(one.exright_date) + "\n")
    for one in allotment:
        info += (get_stock_name_code(one.stock) + "配股: 数量(10股)" + str(one.allotment_num)\
                    + " 价格" + str(one.allotment_price) + " 基数(万股)" + str(one.allotment_capital_base)\
                    + " 公布日期" + str(one.public_date) + " 除权日期" + str(one.exright_date)\
                    + "记录日期" + str(one.record_date) + "\n")
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
        one_date = today + timedelta(days=-1*(i+1))
        sum_amount = TradeRecord.objects.filter(date=one_date, stock__stock_exchange='上证交易所')\
                        .aggregate(num=Sum('trade_amount')).get('num') or 0
        sum_amount = round(sum_amount/100000000, 2)
        if sum_amount:
            shang_str += '上证交易所:' + str(one_date) + " " + str(sum_amount) + "亿\n"

    for i in range(30):
        one_date = today + timedelta(days=-1*(i+1))
        sum_amount = TradeRecord.objects.filter(date=one_date, stock__stock_exchange='深证交易所')\
                        .aggregate(num=Sum('trade_amount')).get('num') or 0
        sum_amount = round(sum_amount/100000000, 2)
        if sum_amount:
            shang_str += '深证交易所:' + str(one_date) + " " + str(sum_amount) + "亿\n"

    big_block_list = StockInfo.objects.values_list('big_block').distinct()
    for one in big_block_list:
        for i in range(7):
            one_date = today + timedelta(days=-1*(i+1))
            sum_amount = TradeRecord.objects.filter(date=one_date, stock__big_block=one)\
                            .aggregate(num=Sum('trade_amount')).get('num') or 0
            sum_amount = round(sum_amount/100000000, 2)
            if sum_amount:
                big_block_str += str(one) + ':' + str(one_date) + " " + str(sum_amount) + "亿\n"
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
        encode_content = req.content.decode(encoding, 'replace') #如果设置为replace，则会用?取代非法字符；


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

                encode_content1 = req.content.decode(encoding, 'replace') #如果设置为replace，则会用?取代非法字符；
                sel = Selector(text=encode_content1)
                pdf_list = sel.xpath('//a[re:test(text(), "%s")]//@href'%(name)).extract()
                pdf_name = pdf_list[0]
                pdf_url = url.rsplit('/',1)[0] + pdf_name[1:]

                req =  requests.get(pdf_url)
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

    code_list = []
    small_block_dict = {}

    for i in range(pages):
        content = read_pdf('./CSRC/' + date + '/' + name, pages=i+1, multiple_tables=True)
        content_list = re.split(r'[ \n]+', str(content))

        for j in range(len(content_list)):
            if j < 12:
                continue
            if j % 6 == 1:
                if not content_list[j].endswith(')') and content_list[j] != 'NaN':
                    if content_list[j+7] == 'NaN' and content_list[j+6] != 'NaN':
                        big_block = content_list[j] + content_list[j+6]
                        m = 2
                        while not big_block.endswith(')'):
                            if content_list[6*m +j + 1] == 'NaN' and content_list[6*m + j] != 'NaN':
                                big_block += content_list[6*m + j]
                            else:
                                break
                            m += 1
                    else:
                        big_block = content_list[j]
                    if pre_block.find(big_block) == -1:
                        pre_block = big_block
                        json_dict[pre_block] = {}

                elif content_list[j].endswith(')'):
                    big_block = content_list[j]
                    if pre_block.find(big_block) == -1:
                        pre_block = big_block
                        json_dict[pre_block] = {}

                else:
                    pass
            if j % 6 == 3:
                if content_list[j] != 'NaN':
                    if content_list[j+5] == 'NaN' and content_list[j+6] != 'NaN':
                        small_block = content_list[j] + content_list[j+6]
                        m = 2
                        while not big_block.endswith(')'):
                            if content_list[6*m +j - 1] == 'NaN' and content_list[6*m + j] != 'NaN':
                                small_block += content_list[6*m + j]
                            else:
                                break
                            m += 1
                    else:
                        small_block = content_list[j]
                    if pre_small_block.find(small_block) == -1:
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
                        ChangeHistory.objects.create(stock=one, change_source=one.big_block,\
                                                change_target=key, field='big_block',\
                                                generated_time=date.today())
                        one.big_block = key
                        one.save()

                    if one.block != small:
                        ChangeHistory.objects.create(stock=one, change_source=one.block,\
                                                change_target=small, field='block',\
                                                generated_time=date.today())
                        one.block = small
                        one.save()


