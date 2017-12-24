# -*- coding: utf-8 -*-

import time
from datetime import datetime
from Analyzer import Analyzer


class InAnalyzer(Analyzer):
    def __init__(self, trader, **kwargs):
        super(InAnalyzer, self).__init__(trader, **kwargs)

    def apply_algorithm(self, market):
        print('Buy analysis...')
        if self.get_marketsummary(market)['result'][0]['BaseVolume'] >= self.params['vol_th']:
            volumes = []  # chaque element = volume des 200 dernières transactions d achats
            rates = []
            time_tweet = datetime.now()
            timeout = time.time() + self.params['epoch'] * 60
            while True:
                market_history = self.get_market_history(market, 20)
                if market_history['success'] and time.time() < timeout:
                    results = market_history['result']
                    quantities = [result['Quantity'] for result in results if result['OrderType'] == 'BUY']
                    volumes.append(sum(quantities))
                    rates.append(self.get_ticker(market)['result']['Last'])

                    volume_growth = volumes[-1]/volumes[0] - 1.0
                    rate_growth = rates[-1]/rates[0] - 1.0

                    if volume_growth >= self.params['vol_growth'] and rate_growth >= self.params['rate_growth']:
                        self.send_buy_request(self.trader, market, rates[0], time_tweet)
                        break
                    time.sleep(5)
                elif time.time() > timeout:
                    break

            print('Analysis done')
            self.set_busy(False)

    def send_buy_request(self, trader, market, price_tweet, time_tweet):
        trader.add_buy_request(market, price_tweet, time_tweet)
