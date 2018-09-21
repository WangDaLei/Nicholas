from stock.models import StockInfo, TradeRecord, StockBonusHistory, StockAllotmentHistory

class Stock:
    def  __init__(self, code):
        self.code = code

    def get_all_trade_date(self, order=0):
        if self.check_stock_exists():
            stock_info = StockInfo.objects.get(code=self.code)
            market_list_date = stock_info.market_list_date
            # print(market_list_date)
            if order == 0:
               trade_record = TradeRecord.objects.filter(date__gte=market_list_date).\
                                                values('date').distinct().order_by('-date')
            else:
                trade_record = TradeRecord.objects.filter(date__gte=market_list_date).\
                                                values('date').distinct().order_by('date')
            date_list = list()
            for one in trade_record:
                date_list.append(one['date'])
            return date_list
        else:
            return []

    def check_stock_exists(self):
        '''
         True : exist
         False : not exist
        '''
        stock = StockInfo.objects.filter(code=self.code)
        if stock:
            return True
        else:
            return False

    def get_bonus_info(self):
        bonus = StockBonusHistory.objects.filter(code=self.code, status=True).order_by('exright_date')
        bonus_keys = list()
        for one in bonus:
            bonus_keys.append(one.exright_date)
        return bonus_keys, bonus

    def get_allotment_info(self):
        allotment = StockAllotmentHistory.objects.filter(code=self.code).order_by('exright_date')
        allotment_keys = list()
        for one in allotment:
            allotment_keys.append(one.exright_date)
        return allotment_keys, allotment

    def calculate_bonus_base(self, price, i, bonus):
        if i > len(price) - 1:
            return
        while i < len(price) - 1:
            if price[i + 1] != price[i]:
                break
            i += 1
        after_price = (price[i+1]*10.0 - bonus.stock_bonus)/(10 + bonus.stock_give + bonus.stock_transfer)
        if after_price == 0.0 or price[i+1] == 0.0:
            return
        base = after_price/price[i+1]

        x = i + 1
        while x < len(price):
            price[x] = round(price[x] * base, 2)
            x += 1

    def calculate_allotment_base(self, price, i, allotment):
        if i > len(price) - 1:
            return
        while i < len(price) - 1:
            if price[i + 1] != price[i]:
                break
            i += 1
        after_price = (price[i+1]*10.0 + allotment.allotment_num*allotment.allotment_price)/(10 + allotment.allotment_num)
        if after_price == 0.0 or price[i+1] == 0.0:
            return
        base = after_price/price[i+1]

        x = i + 1
        while x < len(price):
            price[x] = round(price[x] * base, 2)
            x += 1

    def calculate_bonus_allotment_base(self, price, i,  bonus, allotment):
        if i > len(price) - 1:
            return
        while i < len(price) - 1:
            if price[i + 1] != price[i]:
                break
            i += 1
        after_price = (price[i+1]*10.0 + allotment.allotment_num*allotment.allotment_price - bonus.stock_bonus)/\
                        (10 + bonus.stock_give + bonus.stock_transfer + allotment.allotment_num)
        if after_price == 0.0 or price[i+1] == 0.0:
            return
        base = after_price/price[i+1]
                       
        x = i + 1
        while x < len(price):
            price[x] = round(price[x] * base, 2)
            x += 1
    def get_from_date(self, date, obj):
        for one in obj:
            if one.exright_date == date:
                return one

    def get_daily_price_exright(self):
        '''
         get daily price  order by date  after ex-right based on current price
        '''
        bonus_keys, bonus = self.get_bonus_info()
        allotment_keys ,allotment = self.get_allotment_info()
        date_list = self.get_all_trade_date()
        price = self.get_daily_price_reality()

        lenth = len(date_list)
        for i in range(lenth):
            date = date_list[i]
            if date in bonus_keys and date in allotment_keys:
                bonus_one = self.get_from_date(date, bonus)
                allotment_one = self.get_from_date(date, allotment)
                self.calculate_bonus_allotment_base(price, i, bonus_one, allotment_one)
            elif date in bonus_keys:
                bonus_one = self.get_from_date(date, bonus)
                self.calculate_bonus_base(price, i, bonus_one)
            elif date in allotment_keys:
                allotment_one = self.get_from_date(date, allotment)
                self.calculate_allotment_base(price, i, allotment_one)
            else:
                pass
        for i in range(len(date_list)):
            if i < 1000:
                print(date_list[i], price[i])
        return 1

    def get_daily_price_reality(self):
        '''
         get daily price  order by date  not do ex-right
        '''
        date_list = self.get_all_trade_date()
        temp = 0.0
        reality_price_list = list()
        for date in date_list:
            trade_record = TradeRecord.objects.filter(code=self.code, date=date).first()
            if trade_record:
                reality_price_list.append(trade_record.close_price)
                temp = trade_record.close_price
            else:
                reality_price_list.append(temp)
        return reality_price_list
