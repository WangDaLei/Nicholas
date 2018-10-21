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

def get_stock_name_code(stock):
    return str(stock.name) + "(" + str(stock.code) + ") "

def get_trade_amount_sum():
    today = date.today()
    for i in range(30):
        one_date = today + timedelta(days=-1*(i+1))
        sum_amount = TradeRecord.objects.filter(date=one_date, stock__stock_exchange='上证交易所')\
                        .aggregate(num=Sum('trade_amount')).get('num') or 0
        sum_amount = round(sum_amount/100000000, 2)
        if sum_amount:
            print('上证交易所', one_date, sum_amount)

    for i in range(30):
        one_date = today + timedelta(days=-1*(i+1))
        sum_amount = TradeRecord.objects.filter(date=one_date, stock__stock_exchange='深证交易所')\
                        .aggregate(num=Sum('trade_amount')).get('num') or 0
        sum_amount = round(sum_amount/100000000, 2)
        if sum_amount:
            print('深证交易所', one_date, sum_amount)

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

# def crawl_stock_trade_info():
#     stock_all = StockInfo.objects.all()
#     url = 'https://query2.finance.yahoo.com/v8/finance/chart/%s.%s?period1=946656000&period2=1536768000&interval=1d'
#     for one in stock_all:
#         code = one.code
#         print(code)
#         if code.startswith('6'):
#             url_real = url%(code, 'SS')
#         else:
#             url_real = url%(code, 'SZ')
#         res = requests.get(url_real)
#         file = open('data/'+str(code) + ".txt", 'w')
#         file.write(res.text)
#         file.close()
