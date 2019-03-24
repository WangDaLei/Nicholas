from datetime import timedelta
from stock.models import StockInfo, CapitalStockAmountHistory, TradeRecord
from django.db.models import Max


def get_covariance(x, y):
    avg_x = sum(x) / len(x)
    avg_y = sum(y) / len(y)

    sum_all = 0.0
    for i in range(len(x)):
        sum_all += (x[i] - avg_x) * (y[i] - avg_y)
    return round(sum_all / (len(x) - 1), 2)


def get_standard_deviation(x):
    avg_x = sum(x) / len(x)
    sum_all = 0.0
    for i in range(len(x)):
        sum_all += (x[i] - avg_x)**2

    re = (sum_all / (len(x) - 1))**0.5
    return round(re, 2)


def get_unarg_parameter(x, y):
    avg_x = sum(x) / len(x)
    avg_y = sum(y) / len(y)

    sum_xy = 0.0
    for i in range(len(x)):
        sum_xy += (x[i] - avg_x) * (y[i] - avg_y)

    sum_x = 0.0
    for i in range(len(x)):
        sum_x += (x[i] - avg_x)**2

    b1 = sum_xy / sum_x
    b0 = avg_y - b1 * avg_x

    return round(b1, 4), round(b0, 4)


def get_capital_by_date(symbol, date):
    try:
        capital = CapitalStockAmountHistory.objects.filter(change_date__lte=date)\
            .order_by('-change_date').first()
        if capital:
            capital = capital.num
        else:
            stock = StockInfo.objects.get(code=symbol)
            capital = stock.equity
        price = TradeRecord.objects.get(code=symbol, date=date).close_price
        total = price * capital
        return total
    except Exception as e:
        print(e)
        return 0


def get_increase_by_block():
    blocks = StockInfo.objects.exclude(block='').values_list('block').distinct()
    max_date = TradeRecord.objects.aggregate(Max('date'))
    max2_date = TradeRecord.objects.exclude(date=max_date['date__max']).aggregate(Max('date'))
    max_date = max_date['date__max']
    max2_date = max2_date['date__max']
    print(max_date)
    print(max2_date)
    max_date = max2_date + timedelta(days=-1)
    for block in blocks:
        block = block[0]
        block_stocks = StockInfo.objects.filter(status__in=['正常', '停牌'], block=block)
        sum_block = 0.0
        for one in block_stocks:
            capital = get_capital_by_date(one.code, max_date)
            sum_block += capital
        sum2_block = 0.0
        for one in block_stocks:
            capital = get_capital_by_date(one.code, max2_date)
            sum2_block += capital
        percent = round(sum_block / sum2_block, 6) if sum2_block else 0
        print(block, sum_block, sum2_block, percent, '\n')
