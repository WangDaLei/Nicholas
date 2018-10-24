
import math
from datetime import date
from stock.models import IndexRecord

def get_covariance(x, y):
	avg_x = sum(x)/len(x)
	avg_y = sum(y)/len(y)

	sum_all = 0.0
	for i in range(len(x)):
		sum_all += (x[i]-avg_x)*(y[i]-avg_y)
	return round(sum_all/len(x), 2)

def get_standard_deviation(x):
	avg_x = sum(x)/len(x)
	sum_all = 0.0
	for i in range(len(x)):
		sum_all += (x[i]-avg_x)**2

	re = (sum_all/len(x))**0.5
	return round(re, 2)


def get_correlation_coefficient(name='上证指数',start_date='2010-01-01', end_date=date.today()):
	'''
		交易量使用亿作为单位，涨跌幅采用采用去除百分号的小数
	'''
	records = IndexRecord.objects.filter(name=name, date__range=[start_date, end_date]).order_by('date')
	trade_amount_list = []
	change_percent_list = []
	for i, record in enumerate(records):
		if not i:
			continue
		else:
			trade_amount_list.append(round(record.trade_amount, 2))
			rate = round((record.close_index - records[i-1].close_index)/records[i-1].close_index*100, 2)
			change_percent_list.append(rate)
	rate = get_covariance(trade_amount_list, change_percent_list)/(get_standard_deviation(trade_amount_list)*\
			get_standard_deviation(change_percent_list))
	return rate

if __name__ == "__main__":
	rate = get_correlation_coefficient()
	print(rate)