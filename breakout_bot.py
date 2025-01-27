'''

calc last 3 days of data
find the resistance and support on 15m, on retest place order
'''

import ccxt
import json
import pandas as pd
import numpy as np
import dontshare_config as ds
from datetime import datetime, date, timezone, tzinfo
import time, schedule
import nice_funcs as n

#Account
kucoin = ccxt.kucoin({
    'enableRateLimit': True,
    'apiKey': ds.apiKey,
    'secret': ds.secret,
    'password': ds.password,
})


symbol = 'BTC/USDT'
pos_size = 10
target = 3
max_loss = -2
index_pos = 0 # CHANGE BASED ON WHAT ASSET YOU WANT TO TRADE

# time between trades
pause_time = 10 

# for volume cal, vol_repeat * vol_time == TIME of volume collection
vol_repeat = 11
vol_time = 5


params = {'timeinforce': 'PostOnly'}
vol_decimal = .4


def open_positions():
    params = {'type': 'swap', 'code': 'USD'}
    phebal = kucoin.fetch_balance(params=params)
    open_positions = phebal['info']['data`']['positions']
    openpos_side = open_positions[0]['side']
    openpos_size = open_positions[0]['size']

    if openpos_side == ('Buy'):
        openpos_bool = True
        long = True
    elif openpos_side == ('Sell'):
        openpos_bool = True
        long = False
    else: 
        openpos_bool = False
        long = None

    return open_positions, openpos_bool, openpos_size, long



askbid = n.ask_bid(symbol)
ask = askbid[0]
bid = askbid[1]
print(f'for {symbol}... ask: {ask}, bid: {bid}')

#PULL IN THE DF_SMA 
df_sma = n.df_sma(symbol, '15m', 289, 20)


#PULL in OPEN POSITIONS
open_pos = open_positions(symbol)


#CALC SUPPORT & RESISTANCE BASED ON CLOSE
curr_support = df_sma['close'].min()
curr_resistance = df_sma['close'].max()
print(f'support: {curr_support}, resistance: {curr_resistance}')


# Calc the retest, where we put orders

def retest():

    print('creating retest number...')

    '''
    if support breaks - SHORT, place asks right below (.1% == 0.01)
    if resistance breaks - LONG, place bids right above resistance
    '''

    time.sleep(5)

    df2 = n.df_sma(symbol, '15m', 289, 20)

    if df_sma['close'].iloc[-1] > df_sma['close'].iloc[-2]:
        print('last close is bigger than 2nd to last')
    else:
        print('last close is smaller than 2nd to last')
        

    

#PULL IN PNL CLOSE
#pnl_close() [0] pnlclose and [1] in_pos and [2] size [3] long TF
pnl_close = n.pnl_close(symbol)


#PULL IN KILL FUNCTION
kill_switch = n.kill_switch(symbol)

# FUNCTION SLEEP ON CLOSE
sleep_on_close = n.sleep_on_close(symbol, pause_time)

#RUN BOT

def bot():
    print('bot running...')


schedule.every(28).minutes.do(bot)

while True:
    try:
        schedule.run_pending()
    except:
        print('something went wrong, INTERNET PROBLEM OR SOMETHING...')
        time.sleep(30)
