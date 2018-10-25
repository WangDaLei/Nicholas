
from datetime import date
from stock.models import IndexRecord
from .controllers import get_unarg_parameter

def get_unary_linear_regression(name='上证指数',start_date='2010-01-01', end_date=date.today()):
	'''
	    计算 指数变化的百分比 和 交易量的相关系数
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
			rate = abs(round((record.close_index - records[i-1].close_index)/records[i-1].close_index*100, 2))
			change_percent_list.append(rate)

	b1, b0 = get_unarg_parameter(trade_amount_list, change_percent_list)
	return b1, b0

def get_unary_linear_regression_of_index(start_date='2010-01-01', end_date=date.today()):
	'''
		计算 两个指数之间的一元回归
	'''
	shang_records = IndexRecord.objects.filter(name='上证指数', date__range=[start_date, end_date]).order_by('date')
	shen_records = IndexRecord.objects.filter(name='深证指数', date__range=[start_date, end_date]).order_by('date')
	
	shang_list = []
	shen_list = []
	
	for i, record in enumerate(shang_records):
		shang_list.append(round(record.close_index, 2))

	for i, record in enumerate(shen_records):
		shen_list.append(round(record.close_index, 2))

	b1, b0 = get_unarg_parameter(shang_list, shen_list)
	return b1, b0

def get_unary_linear_regression_of_index_percent(start_date='2010-01-01', end_date=date.today()):
	'''
		计算 两个指数变化率的一元回归
	'''
	shang_records = IndexRecord.objects.filter(name='上证指数', date__range=[start_date, end_date]).order_by('date')
	shen_records = IndexRecord.objects.filter(name='深证指数', date__range=[start_date, end_date]).order_by('date')
	
	shang_list = []
	shen_list = []
	
	for i, record in enumerate(shang_records):
		if not i:
			continue
		else:
			rate = round((record.close_index - shang_records[i-1].close_index)/shang_records[i-1].close_index*100, 2)
			shang_list.append(round(rate, 2))

	for i, record in enumerate(shen_records):
		if not i:
			continue
		else:
			rate = round((record.close_index - shen_records[i-1].close_index)/shen_records[i-1].close_index*100, 2)
			shen_list.append(round(rate, 2))

	b1, b0 = get_unarg_parameter(shang_list, shen_list)
	return b1, b0