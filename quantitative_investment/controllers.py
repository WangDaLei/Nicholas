'''
'''

def get_covariance(x, y):
	avg_x = sum(x)/len(x)
	avg_y = sum(y)/len(y)

	sum_all = 0.0
	for i in range(len(x)):
		sum_all += (x[i]-avg_x)*(y[i]-avg_y)
	return round(sum_all/(len(x)-1), 2)

def get_standard_deviation(x):
	avg_x = sum(x)/len(x)
	sum_all = 0.0
	for i in range(len(x)):
		sum_all += (x[i]-avg_x)**2

	re = (sum_all/(len(x)-1))**0.5
	return round(re, 2)