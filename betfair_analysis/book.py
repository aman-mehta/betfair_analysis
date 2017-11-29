import datetime as dt
import pandas as pd

class Side():

    def __init__(self, side):
        self.side = side
        self.depth = []
    
    def UpdateDepth(self, depth):
        self.depth = depth

    def GetTopPrice(self):
        prices = [float(price['price']) for price in self.depth]
        if self.side == 'back':
            return max(prices)
        elif self.side == 'lay':
            return min(prices)
        else:
            return -1
    
class Book():

    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.market = {'back': Side('back'), 'lay': Side('lay')}

    def UpdateSide(self, side, side_data):
        depth = []
        if isinstance(side_data[self.url + 'PriceSize'], list):
            for price in side_data[self.url + 'PriceSize']:
                level = {
                    'price': price[self.url + 'price'],
                    'size': price[self.url + 'size']
                }
                depth.append(level)
        elif isinstance(side_data[self.url + 'PriceSize'], dict):
            level = {
                'price': side_data[self.url + 'PriceSize'][self.url + 'price'],
                'size': side_data[self.url + 'PriceSize'][self.url + 'size']
            }
            depth.append(level)
        self.market[side].UpdateDepth(depth)

    def UpdateBook(self, exchange_data):
        back_data = exchange_data[self.url + 'availableToBack']
        lay_data = exchange_data[self.url + 'availableToLay']
        self.UpdateSide('back', back_data)
        self.UpdateSide('lay', lay_data)

    def GetTopPrice(self, side):
        return self.market[side].GetTopPrice()
        
    def GetPandasDepth(self):
        depth = {
            'timestamp' : dt.datetime.now(),
            'back_price': self.GetTopPrice('back'),
            'lay_price': self.GetTopPrice('lay')
        }
        return pd.DataFrame.from_records([depth], index='timestamp')
