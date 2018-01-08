# -*- coding: utf-8 -*-

from tweepy import OAuthHandler, Stream, API
from Trader import Trader
from Listener import Listener
from InAnalyzer import InAnalyzer
from OutAnalyzer import OutAnalyzer
import threading
import csv
import sys

# TWITTER ACCOUNT
CONSUMER_KEY = "hs14fkRYcc2cG9AQc878v4nM8"
CONSUMER_SECRET = "7DPdNqq1Ij1e5akNuoLAc5gAQXDHxdQRytD25pC9z0h2lzo1gO"

ACCESS_TOKEN = "1289245472-bsF2NmZDVg9hXVpxHV3XfZTBn8osyu9JPXxrZzE"
ACCESS_TOKEN_SECRET = "keHL91ANXYi6TT2eLK86crnUjwxMd7bKEyCdQUUUxGOGX"

# BITTREX ACCOUNT
API_KEY = ''
API_SECRET = ''

# SLACK TOKEN
SLACK_TOKEN = "xoxp-290505432145-290505432193-290948857171-ef909d3a120c45cfc5a218ebf77987a2"

# FILES
FOLLOWED_USERS_FILE = 'twitter_doc/twitter_id.csv'
def csv_to_dict(filename):
    with open(filename) as f:
        reader = csv.reader(f)
        data = [row[0].split(';') for row in reader]
    dico = {item[1]:item[2] for item in data}
    return dico

# MAIN
# params_in = [{'epoch':3, 'vol_th':50, 'rate_growth':0.02, 'vol_growth':2},
#             {'epoch':3, 'vol_th':50, 'rate_growth':0.01, 'vol_growth':2},
#             {'epoch':3, 'vol_th':50, 'rate_growth':0.03, 'vol_growth':2}]

params_in = [{'epoch':3, 'vol_th':10, 'rate_growth':0.01, 'vol_growth':0.05}]

params_out = [{'period_sma': 14, 'period_ema': 9, 'tick_time': 1, 'period_time':60,
            'take_profit': None, 'stop_loss': None}]


if __name__ == '__main__':
    trader = Trader(API_KEY, API_SECRET, SLACK_TOKEN)
    in_analyzers = [InAnalyzer(trader, params=params_in[i]) for i in range(len(params_in))]
    out_analyzers = [OutAnalyzer(trader, params=params_out[i]) for i in range(len(params_out))]
    trader.hire(in_analyzers, out_analyzers)

    follow_dict = csv_to_dict(FOLLOWED_USERS_FILE)
    listener = Listener(follow_dict, trader)
    auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    try:
        followed_users_id = follow_dict.keys()
        tracked_words = [] # words you are looking for
        stream = Stream(auth, listener)
        stream.filter(follow=followed_users_id, track=tracked_words, async=True)

        trader.slackclient.api_call(
            "chat.postMessage",
            channel='#bot-python',
            text="Bot init"
        )

    except KeyboardInterrupt:
        trader.slackclient.api_call(
            "chat.postMessage",
            channel='#bot-python',
            text="Bot killed"
                )
        print('Process ended by User')
        sys.exit(0)
