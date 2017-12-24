# -*- coding: utf-8 -*-

import time
import threading
from abc import ABCMeta, abstractmethod
from bittrex import Bittrex

def threaded(func):
    def run(*k, **kw):
        t = threading.Thread(target=func, args=k, kwargs=kw)
        t.start()
    return run


class Analyzer(Bittrex):
    """Analyze the market following a specific algorithm"""

    def __init__(self, trader, **kwargs):
        Bittrex.__init__(self, None, None)
        self.__dict__.update(kwargs)
        self.trader = trader
        self.market = None
        self.busy = False
        self.price_tweet = None
        self.price_buy = None

    def get_market(self):
        return self.market

    def set_market(self, market):
        self.market = market

    def is_busy(self):
        return self.busy

    def set_busy(self, busy):
        self.busy = busy

    def set_price_tweet(self, price_tweet):
        self.price_tweet = price_tweet

    def set_price_buy(self, price_buy):
        self.price_buy = price_buy

    def accept_analysis(self, market, price_tweet, price_buy):
        '''return bool with the following meaning:
        bool is True if the request is accepted'''
        decision = False
        if self.is_busy() is False:
            self.set_busy(True)
            self.set_market(market)
            self.set_price_tweet(price_tweet)
            self.set_price_buy(price_buy)
            decision = True
        return decision

    @abstractmethod
    @threaded
    def apply_algorithm(self, market):
        return
