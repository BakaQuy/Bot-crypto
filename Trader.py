# -*- coding: utf-8 -*-

from bittrex import Bittrex
from slackclient import SlackClient
from datetime import datetime
import threading
import csv
import copy

BET = 0.05 

def threaded(func):
    def run(*k, **kw):
        t = threading.Thread(target=func, args=k, kwargs=kw)
        t.start()
    return run

class Trader(Bittrex):
    """Responsible of the wallet and manage the Analyzer"""

    def __init__(self, api_key, api_secret, slack_token):
        super(Trader, self).__init__(api_key, api_secret)
        self.moves = 'database' # change to real database
        self.in_analyzers = []
        self.out_analyzers = []
        self.buy_trade = []
        self.sell_trade = []
        self.balances = self.get_all_balances('twitter_doc/twitter_id.csv') #creer protefeuille virtuel de tous les coins etudies
        self.balances['BTC'] = 10.0 #creer un portefeuille virtuel de 50 BTC 
        self.slack_token = slack_token
        self.slackclient = SlackClient(self.slack_token)
        try:
            self.wallet = self.get_balance('BTC')['result']['Available']
        except:
            self.wallet = None
        self.check_order()

    @threaded
    def on_tweet(self, market):
        print(threading.active_count())
        print(threading.enumerate())
        if len(self.in_analyzers) > 0:
            analyzer_found = False
            for analyzer in self.in_analyzers:
                if analyzer.accept_analysis(market, None, None):
                    analyzer_found = True
                    analyzer.apply_algorithm(market)
                    break

            if analyzer_found == False:
                print ('Not enough In-analyzers')
                print('Number of In-analyzers:', len(self.in_analyzers))
                if len(self.in_analyzers) < 5:
                    new_analyzer = copy.copy(self.in_analyzers[0])
                    self.in_analyzers.append(new_analyzer)
                    print('New In-analyzer added!')
                    new_analyzer.set_busy(False)
                    new_analyzer.accept_analysis(market, None, None)
                    new_analyzer.apply_algorithm(market)
        else:
            print ('No In-analyzer instantiated')

    @threaded
    def on_buy(self, market, price_tweet, price_buy):
        if len(self.out_analyzers) > 0:
            analyzer_found = False
            for analyzer in self.out_analyzers:
                if analyzer.accept_analysis(market, price_tweet, price_buy):
                    analyzer_found = True
                    analyzer.apply_algorithm(market)
                    break

            if analyzer_found == False:
                print ('Not enough Out-analyzers')
                print('Number of Out-analyzers:', len(self.out_analyzers))
                if len(self.out_analyzers) < 5:
                    new_analyzer = copy.copy(self.out_analyzers[0])
                    self.out_analyzers.append(new_analyzer)
                    print('New Out-analyzer added!')
                    new_analyzer.set_busy(False)
                    new_analyzer.accept_analysis(market, price_tweet, price_buy)
                    new_analyzer.apply_algorithm(market)
        else:
            print ('No Out-analyzer instantiated')

    def hire(self, in_analyzers, out_analyzers):
        self.in_analyzers = self.in_analyzers + in_analyzers
        self.out_analyzers = self.out_analyzers + out_analyzers

    def add_buy_request(self, market, price_tweet, time_tweet):
        self.buy_trade.append((market, price_tweet, time_tweet))

    def add_sell_request(self, market):
        self.sell_trade.append(market)

    def buy(self):
        if len(self.buy_trade) > 0:
            for trade in self.buy_trade:
                self.buy_orderbook(trade, BET)
                self.buy_trade.remove(trade)
                self.on_buy(trade[0], trade[1], None)

    def buy_orderbook(self, trade, bet_btc):
        #if self.get_balance('BTC') >= bet_btc:     #vrai
        if self.balances['BTC'] >= bet_btc:         #simulation
            bet = bet_btc
            orderbook = self.get_orderbook(trade[0], 'sell', 50)
            if orderbook['success']:
                quantity = 0
                orders = orderbook['result']
                for order in orders:
                    if (bet - order['Quantity']*order['Rate']) > 0:
                        bet -= order['Quantity']*order['Rate']
                        quantity += order['Quantity']

                    elif (bet - order['Quantity']*order['Rate']) <= 0:
                        quantity_left = bet/order['Rate']
                        quantity += quantity_left
                        #self.buy_limit(market, quantity, order['Rate'])
                        #print('Buy on: ' + market + '(' + str(bet_btc/quantity) + ')')
                        self.add_balance(trade[0][4:], quantity, bet_btc)
                        self.send_buy_move_slack(trade, str(bet_btc/quantity))                       
                        break

    def sell(self):
        if len(self.sell_trade) > 0:
            for trade in self.sell_trade:
                self.sell_orderbook(trade)
                self.sell_trade.remove(trade)

    def sell_orderbook(self, market):
        #balance = self.get_balance(market[4:])['result']['Balance'] #vrai balance sur Bittrex
        balance = self.balances[market[4:]]
        if balance > 0:
            quantity = balance
            gain = 0
            orderbook = self.get_orderbook(market, 'buy', 50)
            while True:
                if orderbook['success']:
                    orders = orderbook['result']
                    for order in orders:
                        if (balance - order['Quantity']) > 0:
                            balance -= order['Quantity']
                            gain += order['Quantity']*order['Rate']

                        elif (balance - order['Quantity']) <= 0:
                            #self.sell_limit(market, quantity, order['Rate'])
                            gain += balance*order['Rate']
                            #print('Sell on: ' + market + '(' + str(gain/quantity) + ')')
                            self.remove_balance(market[4:], quantity, gain)
                            self.send_sell_move_slack(market[4:], str(gain/quantity))
                            break
                    break

    def get_all_balances(self, filename):
        with open(filename) as f:
            reader = csv.reader(f)
            data = [row[0].split(';') for row in reader]
        dico = {item[2]:0.0 for item in data}
        return dico

    def add_balance(self, market, quantity, bet):
        self.balances[market] += quantity
        self.balances['BTC'] -= bet
        #print('Balances:\n' + 'BTC = ' + str(self.balances['BTC']) + '\n' + market + ' = ' + str(self.balances[market]))

    def remove_balance(self, market, quantity, gain):
        if self.balances[market] >= quantity:
            self.balances[market] -= quantity
            self.balances['BTC'] += gain

        elif self.balances[market] < quantity:
             self.balances[market] = 0.0
             self.balances['BTC'] += gain
        #print('Balances:\n' + 'BTC = ' + str(self.balances['BTC']) + '\n' + market + ' = ' + str(self.balances[market]))

    def send_buy_move_slack(self, trade, price_buy):
        move_1 = 'Buy done on : ' + trade[0][4:] +'\n' # trade[0] = market
        move_2 = 'Price tweet : ' + str(trade[1]) + '\n' # trade[1] = price_tweet
        move_3 = 'Time tweet : ' + str(trade[2]) + '\n'
        move_4 = 'Price buy : ' + price_buy + '\n'
        move_5 = 'Time buy : ' + str(datetime.now()) + '\n'
        move_6 = 'BTC : ' + str(self.balances['BTC']) + '\n'
        move_7 = trade[0][4:] + ' : ' + str(self.balances[trade[0][4:]])

        move = move_1 + move_2 + move_3 + move_4 + move_5 + move_6 + move_7
        print(move)

        with open('twitter_doc/tweet.txt', 'a') as db:
            db.write(move)
        self.slackclient.api_call(
            "chat.postMessage",
            channel='#bot-python',
            text=move
        )

    def send_sell_move_slack(self, market, price_sell):
        move_1 = 'Sell done on : ' + market + '\n'
        move_2 = 'Price sell : ' + price_sell + '\n'
        move_3 = 'Time sell : ' + str(datetime.now()) + '\n'
        move_4 = 'BTC : ' + str(self.balances['BTC']) + '\n'
        move_5 = market + ' : ' + str(self.balances[market])

        move = move_1 + move_2 + move_3 + move_4 + move_5
        print(move)

        with open('twitter_doc/tweet.txt', 'a') as db:
            db.write(move)
        self.slackclient.api_call(
            "chat.postMessage",
            channel='#bot-python',
            text=move
        )

    @threaded
    def check_order(self):
        while True:
            self.buy()
            self.sell()