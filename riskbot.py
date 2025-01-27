
import ccxt
import json
import pandas as pd
import numpy as np
import dontshare_config as ds
import nice_funcs as n
import time, schedule
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

####### INPUTS #######
size = 10
#size_1 = size * .2 
#size_2_3 = size * .4
symbol = 'BTC/USDT'
perc_from_lh = .35
close_seconds = 60*47
max_lh = 500
timeframe = '5m' # 5 *180 = 15 hours 
num_bars = 180
max_risk = 100 #$100
sl_perc = 0.1
exit_perc = 0.002
max_tr = 550
quartile = 0.33
time_limit = 120 
sleep = 30
######################

#Account
kucoin = ccxt.kucoin({
    'enableRateLimit': True,
    'apiKey': ds.apiKey,
    'secret': ds.secret,
    'password': ds.password,
})

def size_kill(symbol = symbol):

    max_risk = 110

    print('Starting size kill checker...')
    params = {'type': 'swap', 'code': 'USD'}

    balance = kucoin.fetch_balance(params)

    open_positions = balance['info']['data']['positions']
    pos_df = pd.DataFrame.from_dict(open_positions)

    pos_cost = pos_df.loc[pos_df['symbol'] == symbol , 'cost'][0] #getting margin
    pos_cost = float(pos_cost)
    pos_side = pos_df.loc[pos_df['symbol'] == symbol , 'side'][0] #getting side
    pos_size = pos_df.loc[pos_df['symbol'] == symbol , 'size'][0] #getting size
    pos_size = float(pos_size)

    if pos_cost > max_risk:
        print(f'🚨EMERGENCY KILL SWITCH - MAX RISK TOO HIGH FOR {symbol} size: {pos_size} cost: {pos_cost}')

        kucoin.cancel_all_orders(symbol)
        kucoin.cancel_all_orders(symbol = symbol, params = {'untriggered': True})
        print('just cancelled all orders and conditional orders...')

        if pos_side == 'Sell':
            kucoin.create_market_buy_order(symbol, pos_size, params = {'reduceOnly': True})
            print(f'just created a market buy order for {pos_size} {symbol} cuz were short... sleeping for 72 hrs')
            time.sleep(60*60*72)
        elif pos_side == 'Buy':
            kucoin.create_market_sell_order(symbol, pos_size, params = {'reduceOnly': True})
            print(f'just created a market sell order for {pos_size} {symbol} cuz were long... sleeping for 72 hrs')
            time.sleep(60*60*72)
        else:
            print('no position found... noting to submit to the market')
    else:
        print(f'size kill check: current position {symbol} cost: {pos_cost} is below max risk of {max_risk}%')



def pnl_close(symbol = symbol):

    '''
    this is the first thing we check evert loop of any algo its gonna look 
    for the DD max,a and also the wnning % ex, if max dd is 5% and we hit
    that amount- it would close, if hits target of 10% close

    1. Check total PNL across all exchanges, if max loss kill
    2. Volatility index 
    '''
    ######Inputs######

    target = 10
    max_dd = 5

    print('Starting PNL close...')   

    params = {'type': 'swap', 'code': 'USD'}

    pos_dict = kucoin.fetch_positions(params)
    pos_df = pd.DataFrame.from_dict(pos_dict)


    ### GET DATA FROM POSITION DICTIONARY DF ###
    side = pos_df.loc[pos_df['symbol'] == symbol , 'side'][0]

    leverage = pos_df.loc[pos_df['symbol'] == symbol , 'leverage'][0]

    leverage = float(leverage)
    size = pos_df.loc[pos_df['symbol'] == symbol , 'size'][0]
    size = float(size)

    entry_price = pos_df.loc[pos_df['symbol'] == symbol , 'avgEntryprice'][0]
    entry_price = float(entry_price)

    print(f'symbol: {symbol} | side: {side} | size: {size} | entry price: {entry_price} | leverage: {leverage}')

def balances():

    pheposinfo = n.open_positions()
    phe_balance = pheposinfo[5]

    phe_bal = phe_balance['total']['USD']
    phe_used = phe_balance['used']['USD']

    # time
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('')
    print('Time: ', dt_string)
    print(f'balance on Phemex: {round(phe_bal, 2)} and we have {round(phe_used, 2)} in trades')
    print('')
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')


    print('Phemex balance: ', phe_bal)

    return phe_bal, phe_used, now 

# LOCKOUT - IF ever down 30% in a day, close all positions, and sleep all accounts

def lockout():

    print('Lockout Checker initiated...')
    max_loss = -0.3
    all_bal_info = balances()

    start_bal = all_bal_info[0]
    used_bal = all_bal_info[1]
    


print(kucoin.fetch_balance())