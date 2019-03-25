from stock.models import StockInfo, CapitalStockAmountHistory, TradeRecord, IndexRecord
from django.db.models import Max
from stock.controllers import send_email


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


def get_capital_by_date(symbol, date, close_price=1):
    try:
        capital = CapitalStockAmountHistory.objects.filter(code=symbol, change_date__lte=date)\
            .order_by('-change_date').first()
        if capital:
            capital = capital.num
        else:
            stock = StockInfo.objects.get(code=symbol)
            capital = stock.equity
        price = TradeRecord.objects.filter(code=symbol, date__lte=date)\
            .order_by('-date').first()
        if price:
            if close_price:
                price = price.close_price
            else:
                price = price.open_price
        else:
            price = 0
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
    block_dict = {}
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
            if not capital:
                capital = get_capital_by_date(one.code, max_date, 0)
            sum2_block += capital
        percent = round(sum_block / sum2_block, 6) if sum2_block else 0
        block_dict[block] = percent
    shang_index = IndexRecord.objects.filter(name='上证指数', date=max_date).first()
    shang_index2 = IndexRecord.objects.filter(name='上证指数', date=max2_date).first()
    if shang_index and shang_index2:
        index = round((shang_index.close_index / shang_index2.close_index - 1) * 100, 4)
    else:
        index = 0
    block_dict = {k: round(100 * (v - 1), 2) for k, v in block_dict.items() if v > 0.5}
    sorted_dict = sorted(block_dict.items(), key=lambda item: -1 * item[1])

    top_dict = sorted_dict[:5]
    low_dict = sorted_dict[-5:]
    top_dict = [(one[0], str(one[1]) + '%') for one in top_dict]
    low_dict = [(one[0], str(one[1]) + '%') for one in low_dict]

    str_all = "## Shang Index: " + str(index) + '%\n'
    str_all += "## Top5: " + str(top_dict) + "\n"
    str_all += "## Low5: " + str(low_dict) + "\n"
    top_stocks = {}
    low_stocks = {}
    for one in top_dict:
        stock_list = StockInfo.objects.filter(
            status__in=['正常', '停牌'], block=one[0]).values_list('name', 'code')
        top_stocks[one[0]] = stock_list
    for one in low_dict:
        stock_list = StockInfo.objects.filter(
            status__in=['正常', '停牌'], block=one[0]).values_list('name', 'code')
        low_stocks[one[0]] = stock_list
    str_all += "## Top stocks: " + str(top_stocks) + "\n"
    str_all += "## Low stocks: " + str(low_stocks) + "\n"
    send_email(str_all, title='Block by Index')
    return str_all
