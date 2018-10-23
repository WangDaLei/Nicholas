
from datetime import date
from django.db import models

# Create your models here.

class StockInfo(models.Model):
    STOCK_EXCHANGE_CHOICES = (
        (u'上证交易所', u'上证交易所'),
        (u'深证交易所', u'深证交易所')
    )
    name = models.CharField(max_length=20, default="")
    code = models.CharField(max_length=10)
    stock_exchange = models.CharField(choices=STOCK_EXCHANGE_CHOICES, max_length=16)
    big_block = models.CharField(max_length=40, default="")
    block = models.CharField(max_length=40, default="")
    ownership = models.CharField(max_length=30, default="")
    found_date = models.DateField(null=True, blank=True)
    market_list_date = models.DateField(null=True, blank=True)
    equity = models.FloatField(default=0.0)
    price = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, default="")

    class Meta:
        app_label = 'stock'

class CapitalStockAmountHistory(models.Model):
    stock = models.ForeignKey('StockInfo', on_delete=models.CASCADE)
    code = models.CharField(max_length=10)
    change_date = models.DateField(blank=True)
    public_date = models.DateField(blank=True, default="1970-1-1")
    generated_time =models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=100, default="")
    num = models.FloatField(default=0.0)

class FinanceHistory(models.Model):
    stock = models.ForeignKey('StockInfo', on_delete=models.CASCADE)
    code = models.CharField(max_length=10)
    date = models.DateField(blank=True)
    per_share_net_asset = models.FloatField(default=0.0)
    total_asset = models.FloatField(default=0.0)
    total_liabilities = models.FloatField(default=0.0)
    business_income = models.FloatField(default=0.0)
    net_profit = models.FloatField(default=0.0)
    generated_time =models.DateTimeField(auto_now_add=True)


class TradeRecord(models.Model):
    stock = models.ForeignKey('StockInfo', on_delete=models.CASCADE)
    code = models.CharField(max_length=10)
    date = models.DateField(blank=True)
    open_price = models.FloatField(default=0.0)
    hignest_price = models.FloatField(default=0.0)
    close_price = models.FloatField(default=0.0)
    lowest_price = models.FloatField(default=0.0)
    trade_volume = models.FloatField(default=0.0)
    trade_amount = models.FloatField(default=0.0)
    generated_time =models.DateTimeField(auto_now_add=True)


class StockBonusHistory(models.Model):
    stock = models.ForeignKey('StockInfo', on_delete=models.CASCADE)
    code = models.CharField(max_length=10)
    public_date = models.DateField(blank=True, default="1970-1-1")
    stock_give = models.FloatField(default=0.0)
    stock_transfer = models.FloatField(default=0.0)
    stock_bonus = models.FloatField(default=0.0)
    status = models.BooleanField(default=False)
    exright_date = models.DateField(blank=True, default="1970-1-1")
    generated_time =models.DateTimeField(auto_now_add=True)


class StockAllotmentHistory(models.Model):
    stock = models.ForeignKey('StockInfo', on_delete=models.CASCADE)
    code = models.CharField(max_length=10)
    public_date = models.DateField(blank=True, default="1970-1-1")
    allotment_num = models.FloatField(default=0.0)
    allotment_price = models.FloatField(default=0.0)
    allotment_capital_base = models.FloatField(default=0.0)
    exright_date = models.DateField(blank=True, default="1970-1-1")
    record_date = models.DateField(blank=True, default="1970-1-1")
    generated_time =models.DateTimeField(auto_now_add=True)

class ChangeHistory(models.Model):
    stock = models.ForeignKey('StockInfo', on_delete=models.CASCADE)
    change_source = models.TextField(null=True, default="")
    change_target = models.TextField(null=True, default="")
    field = models.CharField(max_length=20, default="")
    generated_time = models.DateField()

    class Meta:
        app_label = 'stock'

class IndexRecord(models.Model):
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=20)
    date = models.DateField()
    open_index = models.FloatField(default=0.0)
    highest_index = models.FloatField(default=0.0)
    close_index = models.FloatField(default=0.0)
    lowest_index = models.FloatField(default=0.0)
    trade_volume = models.FloatField(default=0.0)
    trade_amount = models.FloatField(default=0.0)
    generated_time =models.DateTimeField(auto_now_add=True)
