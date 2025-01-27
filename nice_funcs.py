'''
ALL FUNCTIONS WE NEED AS ALGO TRADERS
'''

import ccxt
import json
import pandas as pd
import numpy as np
import dontshare_config as ds
from datetime import datetime, date, timezone, tzinfo
import time, schedule

#Account
kucoin = ccxt.kucoin({
    'enableRateLimit': True,
    'apiKey': ds.apiKey,
    'secret': ds.secret,
    'password': ds.password,
})

symbol = 'BTC/USDT'
index_pos = 0 # CHANGE BASED ON WHAT ASSET YOU WANT TO TRADE

# time between trades
pause_time = 60

# for volume cal, vol_repeat * vol_time == TIME of volume collection
vol_repeat = 11
vol_time = 5

pos_size = 100
params = {'timeinforce': 'PostOnly'}
target = 35
max_loss = -55
vol_decimal = .4

# for df
timeframe = '4h'
limit = 100
sma = 20

# GET BID AND ASK
# ask_bid()[0] = ask, [1] = bid
def ask_bid(symbol = symbol):

    ob = kucoin.fetch_order_book(symbol)

    bid = ob['bids'][0][0]
    ask = ob['asks'][0][0]

    print(f'this is the ask for {symbol} {ask} ')

    return ask, bid


#returns: df_sma with sma
#calls: daily_sma(symbol, timeframe, limit, sma) # if not passed, uses default
def df_sma(symbol = symbol, timeframe = timeframe, limit=limit, sma = sma):

    print('starting indis...')

    bars = kucoin.fetch_ohlcv(symbol, timeframe = timeframe, limit=limit)
    df_sma = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_sma['timestamp'] = pd.to_datetime(df_sma['timestamp'], unit='ms')

    #DAILY SMA 20 - 20 day
    df_sma[f'sma{sma}_{timeframe}'] = df_sma.close.rolling(sma).mean()

    # if bid < the 20 day sma, then  = BEARISH, if bid > 20 day sma, then = BULLISH
    bid = ask_bid(symbol)[1]

    #if sma > bid = SELL, if sma < bid = BUY
    df_sma.loc[df_sma[f'sma{sma}_{timeframe}'] > bid, 'sig'] = 'SELL'
    df_sma.loc[df_sma[f'sma{sma}_{timeframe}'] < bid, 'sig'] = 'BUY'

    df_sma['support'] = df_sma['close'].min()
    df_sma['resistance'] = df_sma['close'].max()

    print(df_sma)

    return df_sma

# open_positions, openpos_bool, openpos_size, long
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

    openpos_side = open_positions['side']
    openpos_size = open_positions['size']

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

    return open_positions, openpos_bool, openpos_size, long, index_pos

# returns: None
# kill_switch: pass in symbol, if no uses default
def kill_switch(symbol = symbol):

    print(f'kill switch engaged for {symbol}...')
    openposi = open_positions(symbol) [1] # t or f
    long = open_positions(symbol) [3] # t or f
    kill_size = open_positions(symbol) [2] # size that is open

    print(f'kill_switch... | openposi: {openposi} | long: {long} | kill_size: {kill_size}')

    while openposi == True:

        print('starting kill switch loop till limit fill..')
        temp_df = pd.DataFrame()
        print('just made a temp df')

        kucoin.cancel_all_orders(symbol)
        openposi = open_positions(symbol) [1]
        long = open_positions(symbol) [3]
        kill_size = open_positions(symbol) [2]
        kill_size = int(kill_size)

        ask = ask_bid(symbol)[0]
        bid = ask_bid(symbol)[1]

        if long == False:
            kucoin.create_limit_buy_order(symbol, kill_size, bid, params)
            print(f'just made a BUY to CLOSE order of {kill_size} {symbol} at ${bid}')
            print('sleeping for 30 seconds to see it it fills...')
            time.sleep(30)
        elif long == True:
            kucoin.create_limit_sell_order(symbol, kill_size, ask, params)
            print(f'just made a SELL to CLOSE order of {kill_size} {symbol} at ${ask}')
            print('sleeping for 30 seconds to see it it fills...')
            time.sleep(30)
        else: 
            print('+++++++++++ SOMETHING I DIDNT EXPECT IN KILL SWITCH +++++++++++')

        openposi = open_positions(symbol) [1]

# returns: None
# sleep_on_close: pass in symbol, if no uses default
def sleep_on_close(symbol = symbol, pause_time = pause_time):
    '''
    this function pulls closed orders, then if last close was in the last 59 mins
    then it sleeps for 1m
    sincelasttrade = minutes since last trade
    '''

    closed_orders = kucoin.fetch_closed_orders(symbol)

    for order in closed_orders[-1::-1]:

        sincelasttrade = pause_time - 1

        filled = False

        staus = order['info']['status']
        txttime = order['info']['transcatTimeNs']
        txttime = int(txttime)
        txttime = round(txttime / 1000000000)
        print(f'for {symbol} this is the status of the order {staus} with epoch time {txttime}')
        print('next iteration...')
        print('---------')

        if staus == 'Filled':
            print('FOUND the order with the last fill...')
            print(f'for {symbol} this is the time {txttime} this is the order status {staus}')
            orderbook = kucoin.fetch_order_book(symbol)
            ex_timestamp = orderbook['timestamp'] # in ms
            ex_timestamp = ex_timestamp / 1000
            print('------ below is the transaction time then exchange epoch time ------')
            print(txttime)
            print(ex_timestamp)

            time_spread = (ex_timestamp - txttime) / 60

            if time_spread < sincelasttrade:
                print('time since last trade is less than time spread')

                sleepy = round(sincelasttrade - time_spread) * 60
                sleepy_min = sleepy / 60

                print(f'the time spread is less than {sincelasttrade} mins its been {time_spread} mins.. so we SLEEP for {sleepy_min} mins')
                time.sleep(60)

            else:
                print(f'its been {time_spread} mins since last fill so we DONT SLEEP since last trade was {sincelasttrade} mins ago')
            break
        else:
            continue

def ob(symbol = symbol, vol_repeat=vol_repeat, vol_time=vol_time):

    print(f'fetching order book data for {symbol}...')

    df = pd.DataFrame()
    temp_df = pd.DataFrame()

    ob = kucoin.fetch_order_book(symbol)

    bids = ob['bids']
    asks = ob['asks']
    

    first_bid = bids[0]
    first_ask = asks[0]

    bid_vol_list = []
    ask_vol_list = []

    # if SELL vol > Buy vol AND profit target hit, exit

    # get last 1 min of volume.. and if sell > buy vol do x

    for x in range(vol_repeat):

        for set in bids:
        # print(set)
            price = set[0]
            vol = set[1]
            bid_vol_list.append(vol)
            #print(price)
            #print(vol)

            #print(bid_vol_list)
            sum_bid_vol = sum(bid_vol_list)
            #print(sum_bid_vol)
            temp_df['bid_vol'] = [sum_bid_vol]

        for set in asks:
            price = set[0]
            vol = set[1]
            ask_vol_list.append(vol)
            #print(price)
            #print(vol)

            #print(ask_vol_list)
            sum_askvol = sum(ask_vol_list)
            #print(sum_ask_vol)
            temp_df['ask_vol'] = [sum_askvol]

        #print(temp_df)
        time.sleep(vol_time)
        df = pd.concat([df, temp_df])
        print(df)
        print(' ')
        print('--------')
        print(' ')
    
    print('done collecting volume data for bids and asks...')
    print('calculating the sums...')
    total_bid_vol = df['bid_vol'].sum()
    total_ask_vol = df['ask_vol'].sum()
    print(f'last 1m this is total Bid Vol: {total_bid_vol} | asl vol: {total_ask_vol}')

    if total_bid_vol > total_ask_vol:
        control_dec = (total_ask_vol/total_bid_vol)
        print(f'Bulls are in control: {control_dec}...')
        #if bulls are in control, use regular targets
        bullish = True
    else:
        control_dec = (total_bid_vol / total_ask_vol)
        print(f'Bears are in control: {control_dec}...')
        bullish = False
    
    open_posi = open_positions(symbol)
    openpos_tf = open_posi[1]
    long = open_posi[3]
    print(f'openpos_tf: {openpos_tf} || long: {long}')

    #if target is hit, check book vol
    # if book vol < .4 .. stay in pos..sleep?
    #need to check to see if long or short

    if openpos_tf == True:
        if long == True:
            print('we are in a long position...')
            if control_dec < vol_decimal: # vol_decimal set to .4 at top
                vol_under_dec = True
                #print('going to sleep for a minute... cuz under vol decimal')
                #time.sleep(6)
            else:
                print('volume is not under dec so setting vol_under_dec to False')
                vol_under_dec = False
        else:
            print('we are in a short position...')
            if control_dec < vol_decimal: # vol_decimal set to .4 at top
                vol_under_dec = True
                #print('going to sleep for a minute... cuz under vol decimal')
                #time.sleep(6)
            else:
                print('volume is not under dec so setting vol_under_dec to False')
                vol_under_dec = False
    else:
        print('we are not in position...')

    print(vol_under_dec)

    return vol_under_dec

#[0] pnlclose and [1] in_position [2]size [3] long TF
def pnl_close(symbol):

    print('checking to see if its time to exit for {symbol}...')

    params = {'type': 'swap', 'code': 'USD'}
    pos_dict = kucoin.fetch_positions(params=params)

    index_pos = open_positions(symbol)[4]
    pos_dict = pos_dict[index_pos] # btc [0] eth [1] xrp [2]
    side = pos_dict['side']
    size = pos_dict['contracts']
    entry_price = float(pos_dict['entryPrice'])
    leverage = float(pos_dict['leverage'])

    current_price = ask_bid(symbol)[1]

    print(f'side {side} | entry price: {entry_price} | lev: {leverage}')

    # short or long

    if side == 'long':
        diff = current_price - entry_price
        long = True
    else:
        diff = entry_price - current_price
        long = False

    try:
        perc = round(((diff / entry_price) * leverage), 10)
    except:
        perc = 0
      
    perc = 100*perc
    print(f'for {symbol} this is our PNL percentage: {perc}%')

    pnl_close = False
    in_position = False

    if perc > 0:
        in_pos = True
        print(f'we are in a winning position for {symbol}...')
        if perc > target:
            print(':) :) We are in profit and hit target... checking volume :) :)')
            pnlclose = True
            vol_under_dec = ob(symbol)
            if vol_under_dec == True:
                print('going to sleep for a minute... cuz under vol decimal')
                time.sleep(30)
            else:
                print('starting kill switch, we hit our target...')
                kill_switch(symbol)
        else:
            print('we are in profit but havent hit target yet...')
    
    elif perc < 0: 

        in_pos = True

        if perc <= max_loss:
            print(':( :( We are in a losing position and hit our max loss... starting kill switch :( :(')
            kill_switch(symbol)
        else:
            print('we are in a losing position but havent hit max loss yet...')
        
    else:
        print('we are not in position...')

    if in_pos == True:
        
        #if breaks over .8% over 15m sma, then close pos (STOP LOSS)
        timeframe = '15m'
        df_f = df_sma(symbol, timeframe, 100, 20)
        last_sma15 = df_f.iloc[-1][f'sma{sma}_{timeframe}']
        last_sma15 = int(last_sma15)

        curr_bid = ask_bid(symbol)[1]
        curr_bid = int(curr_bid)

        sl_val = last_sma15 * 1.008
    else: 
        print('we are not in position...')
    
    print(f'for {symbol} just finished checking PNL close...')

    return pnl_close, in_position, size, long

    



df_sma(symbol, '15m', 100, 20)


