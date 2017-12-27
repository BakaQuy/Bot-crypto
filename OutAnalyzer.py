# -*- coding: utf-8 -*-

import time
import requests
import numpy as np
from talib import SMA, EMA
from Analyzer import Analyzer


class OutAnalyzer(Analyzer):

    def __init__(self, trader, **kwargs):
        super(OutAnalyzer, self).__init__(trader, **kwargs)

    def apply_algorithm(self, market):
        print('Sell analysis...')
        url = "https://bittrex.com/Api/v2.0/pub/market/GetTicks?tickInterval=oneMin&marketName={}".format(market) # change this request after api bittrex v2
        market_history = requests.get(url)
        period = max(self.params['period_sma'], self.params['period_ema'])
        data = market_history.json()['result'][-(period + 2): -1]
        historic = np.array([item['C'] for item in data]) # close price for the last period data

        while True:
            if self.params['period_sma'] is not None and self.params['period_ema'] is not None:
                # compute intersection between the two last data of historic
                sma = SMA(historic, timeperiod=self.params['period_sma'])
                ema = EMA(historic, timeperiod=self.params['period_ema'])
                # sma[-2] and ema[-2] evaluated in t = t0 = 0 (rescaled)
                # sma[-1] and ema[-1] evaluated in t = t0 + tick_time
                r = np.array([self.params['tick_time']*60.0, sma[-1]]) - np.array([0.,sma[-2]]) # p -> p + t r
                s = np.array([self.params['tick_time']*60.0, ema[-1]]) - np.array([0.,ema[-2]]) # q -> q + u s
                cross = np.cross(r, s)

                if cross != 0:
                    t = np.cross((np.array([0.,ema[-2]]) - np.array([0.,sma[-2]])), s)/cross
                    u = np.cross((np.array([0.,ema[-2]]) - np.array([0.,sma[-2]])), r)/cross

                    if u >= 0 and u <= 1 and t >= 0 and t <= 1 and r[1] > s[1]:
                        # intersection detected
                        self.send_sell_request(self.trader, market)
                        break

                time.sleep(self.params['tick_time']*60)
                last_price = self.get_ticker(market)['result']['Last']
                historic = np.append(historic, last_price) # add new data
                historic = np.delete(historic, 0) # remove the oldest data (useless)

            if self.params['take_profit'] is not None and self.params['stop_loss'] is not None:
                last_price = self.get_ticker(market)['result']['Last']
                rate_growth = last_price/self.price_buy - 1.0

                if rate_growth >= self.params['take_profit']:
                    print ('take profit, sold at :' + str(last_price) + 'profit of :' + str(rate_growth))
                    self.send_sell_request(self.trader, market)
                    break

                if last_price < self.price_tweet:
                    print ('stop loss, sold at :' + str(last_price) + 'loss of :' + str(rate_growth))
                    self.send_sell_request(self.trader, market)
                    break

        print('Sell analysis done')
        self.set_busy(False)

    def send_sell_request(self, trader, market):
        trader.add_sell_request(market)
