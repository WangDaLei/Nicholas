from .app import Stock
from stock.models import StockInfo

def main():
	stock = StockInfo.objects.all()


if __name__ == '__main__':
	main()