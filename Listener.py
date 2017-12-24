# -*- coding: utf-8 -*-

from tweepy.streaming import StreamListener
from termcolor import colored
import time


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
            market = 'BTC-{MARKET}'.format(MARKET=self.followed_users[id])
            self.update_filter(6)  # update the filter if timeout ended
            if id not in self.filtered_users.keys():
                tweet = '::'.join([str(status.created_at), status.author.screen_name, status.text]) + '\n'
                with open('twitter_doc/tweet.txt', 'a') as db:
                    db.write('new tweet :' + market + ', created_at :' + str(status.created_at) + '\n')
                print(tweet)
                print(market + '\n')
                self.notify_tweet(self.trader, market)
                self.filter(id, time.time()) # avoid to receive tweet from that id during 6 hours
            else:
                print('The market {} already tweeted'.format(self.followed_users[id]))

    def on_error(self, status_code):
        if status_code == 420:
            print('Error while parsing twitter')

    def update_filter(self, timeout):
        for id in self.filtered_users:
            if time.time() > self.filtered_users[id] + timeout * 3600:
                del self.filtered_users[id]

    def filter(self, id, time_in):
        self.filtered_users[id] = time_in

    def notify_tweet(self, trader, market):
        trader.on_tweet(market)
