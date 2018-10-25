
import math
from datetime import date
from stock.models import IndexRecord
from .controllers import get_covariance, get_standard_deviation

def get_correlation_coefficient(name='上证指数',start_date='2010-01-01', end_date=date.today()):
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
	rate = get_covariance(trade_amount_list, change_percent_list)/(get_standard_deviation(trade_amount_list)*\
			get_standard_deviation(change_percent_list))
	return rate

def get_correlation_coefficient_of_index(start_date='2010-01-01', end_date=date.today()):
	'''
		计算 两个指数之间的相关系数
	'''
	shang_records = IndexRecord.objects.filter(name='上证指数', date__range=[start_date, end_date]).order_by('date')
	shen_records = IndexRecord.objects.filter(name='深证指数', date__range=[start_date, end_date]).order_by('date')
	
	shang_list = []
	shen_list = []
	
	for i, record in enumerate(shang_records):
		shang_list.append(round(record.close_index, 2))

	for i, record in enumerate(shen_records):
		shen_list.append(round(record.close_index, 2))

	rate = get_covariance(shang_list, shen_list)/(get_standard_deviation(shang_list)*\
			get_standard_deviation(shen_list))
	return rate

def get_correlation_coefficient_of_index_percent(start_date='2010-01-01', end_date=date.today()):
	'''
		计算 两个指数变化率的相关系数
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

	rate = get_covariance(shang_list, shen_list)/(get_standard_deviation(shang_list)*\
			get_standard_deviation(shen_list))
	return rate
