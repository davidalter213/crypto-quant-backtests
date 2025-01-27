'''
Market Maker Bot
'''

import ccxt
import pandas as pd
import dontshare_config
import time, schedule
import dontshare_config as ds
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

############## INPUTS ########################
size = 3
symbol = 'BTC/USDT'
perc_from_lh = .35
close_seconds = 60*47
max_lh = 800
timeframe = '1m'
num_bars = 100
max_risk = 1000
sl_perc = 0.1
exit_perc = 0.002
max_tr = 550
quartile = 0.33
time_limit = 60
sleep = 30
##############################################


#Account
kucoin = ccxt.kucoin({
    'enableRateLimit': True,
    'apiKey': ds.apiKey,
    'secret': ds.secret,
    'password': ds.password,
})

def open_positions(symbol = symbol):

    # what is the position index for the symbol
    if symbol == 'BTC/USDT':
        index_pos = 0
    elif symbol == 'ETH/USDT':
        index_pos = 1
    elif symbol == 'XRP/USDT':
        index_pos = 2
    else: 
        index_pos = None
    

    params = {'type': 'main', 'code': 'USD'}
    kubal = kucoin.fetch_balance(params=params)
    open_positions = kubal['info']['data']

    openpos_side = open_positions[index_pos]['side']
    openpos_size = open_positions[index_pos]['size']

    if openpos_side == ('Buy'):
        openpos_bool = True
        long = True
    elif openpos_side == ('Sell'):
        openpos_bool = True
        long = False
    else:
        openpos_bool = False
        long = None
    
    print(f'open_positions... | openpos_bool {openpos_bool} |  openpos_size: {openpos_size} | long: {long},')

    return open_positions, openpos_bool, openpos_size, long

def ask_bid(symbol = symbol):

    ob = kucoin.fetch_order_book(symbol)

    bid = ob['bids'][0][0]
    ask = ob['asks'][0][0]

    print(f'this is the ask for {symbol} {ask} ')

    return ask, bid

def kill_switch():

    #my main kill function that works as a taker instead of maker
    # make sure the kill function reports clearly on excel
    # sleep after killing, needs a breather whenever possible

    openposi = open_positions()[1] # this returns T/F for open pos yes or no
    long = open_positions()[3] # this sets long to T/F

    print('KILL SWITCH ACTIVATED... going to loop till limit close...')
    print(f'open position is set to {openposi} if true we continue to kill')

    btc_kill_size = open_positions()[2] #this gets the open_position size
    btc_kill_size = int(btc_kill_size) # puts into int format

    while openposi == True:

        print('starting kill switch loop again till Limit fill...')
        temp_df = pd.DataFrame()
        print('just made a new temp_df for the kill switch, cancelling orders')

        # this cancels all orders
        kucoin.cancel_all_orders(symbol)
        # this cancels the condiitonal order
        kucoin.cancel_all_orders(symbol=symbol, params= {'untriggered': True})

        openposi = open_positions()[1] # T/F for open_positions
        long = open_positions()[3] # this sets long to T/F

        btc_kill_size = open_positions()[2] #this gets the open_position size
        btc_kill_size = int(btc_kill_size) # puts into int format

        now = datetime.now()
        dt_string = now.strftime("%m/%d/%Y %H:%M:%S")
        comptime = int(time.time())

        ask = ask_bid()[0] 
        bid = ask_bid()[1]

        if long == False:
            kucoin.cancel_all_orders(symbol)
            kucoin.cancel_all_orders(symbol=symbol, params={'untriggered': True})
            params = {'timeInForce': 'PostOnly'}
            kucoin.create_limit_buy_order(symbol, btc_kill_size, bid, params)
            temp_df['desc'] = ['kill switch']
            temp_df['open_time'] = [comptime]
            print(f'just made a BUY to CLOSE order of {btc_kill_size} {symbol} at ${bid}')
            print('sleeping for 30 seconds to see it it fills...')
            time.sleep(30)
        elif long == True:
            kucoin.cancel_all_orders(symbol)
            kucoin.cancel_all_orders(symbol=symbol, params={'untriggered': True})
            params = {'timeInForce': 'PostOnly'}
            kucoin.create_limit_sell_order(symbol, btc_kill_size, ask, params)
            temp_df['desc'] = ['kill switch']
            temp_df['open_time'] = [comptime]
            print(f'just made a SELL to CLOSE order of {btc_kill_size} {symbol} at ${ask}')
            print('sleeping for 30 seconds to see it it fills...')
            time.sleep(30)
        else: 
            print('+++++++++++ SOMETHING I DIDNT EXPECT IN KILL SWITCH +++++++++++')

        openposi = open_positions(symbol) [1]

def size_kill():

    params = {'type':"swap", "code": "USD"}
    all_ku_balance = kucoin.fetch_balance(params=params)
    open_positions = all_ku_balance['info']['data']['positions']

    pos_cost = open_positions[2]['posCost']
    pos_cost = float(pos_cost)
    print(f'position cost: {pos_cost}')

    openpos_side = open_positions[2]['side']



