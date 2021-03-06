# -*- coding: utf-8 -*-
from tweepy.streaming import StreamListener
import time
import threading

class Listener(StreamListener):
    '''Bot that constantly listen to the twitter account he is linked to
    It calls the Trader Bot when any followed Twitter account posted a tweet'''

    def __init__(self, follow, trader):
        super(Listener, self).__init__()
        self.followed_users = follow
        self.filtered_users = {}
        self.trader = trader

    def on_status(self, status):
        id = str(status.author.id)
        if id in self.followed_users.keys():
            print(threading.active_count())
            print(threading.enumerate())
            market = 'BTC-{MARKET}'.format(MARKET=self.followed_users[id])
            self.update_filter(5)  # update the filter if timeout ended
            if id not in self.filtered_users.keys():
                tweet = '::'.join([str(status.created_at), status.author.screen_name, status.text]) + '\n'
                with open('twitter_doc/tweet.txt', 'a') as db:
                    db.write('new tweet :' + market + ', created_at :' + str(status.created_at) + '\n')
                print('\n')
                print(tweet)
                print(market)
                self.notify_tweet(self.trader, market)
                self.filter(id, time.time()) # avoid to receive tweet from that id during 6 hours
            else:
                print('\n')
                print('The market {} already tweeted'.format(self.followed_users[id]))

    def on_error(self, status_code):
        if status_code == 420:
            print('Error while parsing twitter')

    def update_filter(self, timeout):
        for id in list(self.filtered_users.keys()):
            if time.time() > self.filtered_users[id] + timeout * 60:
                self.filtered_users.pop(id,None)

    def filter(self, id, time_in):
        self.filtered_users[id] = time_in

    def notify_tweet(self, trader, market):
        trader.on_tweet(market)