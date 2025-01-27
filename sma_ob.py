'''

based on ob data, determine the close
using stat of sma if daily 20 sma > bid bear
if daily 20 sma < bid bull
orders placed around 15m sma 

# strategy: determine the trend with 20 day sma / based off trend,
buy/sell to open around the 15m sma 20 day - .1% under and .3% over
'''


import ccxt
import pandas as pd
import dontshare_config
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
pos_size = 50
params = {'timeinforce': 'PostOnly'}
target = 25

# GET BID AND ASK
# ask_bid()[0] = ask, [1] = bid
def ask_bid():

    ob = kucoin.fetch_order_book(symbol)

    bid = ob['bids'][0][0]
    ask = ob['asks'][0][0]

    return ask, bid

# FIND DAILY SMA 20
#daily_sma()[0] = df_d,
def daily_sma():

    print('starting indis...')

    timeframe = '1d'
    num_bars = 100

    bars = kucoin.fetch_ohlcv(symbol, timeframe, limit=num_bars)
    df_d = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_d['timestamp'] = pd.to_datetime(df_d['timestamp'], unit='ms')

    #DAILY SMA 20 - 20 day
    df_d['sma20_d'] = df_d.close.rolling(20).mean()

    # if bid < the 20 day sma, then  = BEARISH, if bid > 20 day sma, then = BULLISH
    bid = ask_bid()[1]

    #if sma > bid = SELL, if sma < bid = BUY
    df_d.loc[df_d['sma20_d'] > bid, 'sig'] = 'SELL'
    df_d.loc[df_d['sma20_d'] < bid, 'sig'] = 'BUY'

    return df_d
    

# FIND 15 MIN SMA 20 
#f15_sma()[0] = df_d,
def f15_sma():

    print('starting 15 min sma...')

    timeframe = '15m'
    num_bars = 100

    bars = kucoin.fetch_ohlcv(symbol, timeframe, limit=num_bars)
    df_f = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_f['timestamp'] = pd.to_datetime(df_f['timestamp'], unit='ms')

    #DAILY SMA 20 - 20 day
    df_f['sma20_15'] = df_f.close.rolling(20).mean()

    # BUY PRICE 1+2 AND SELL PRICE 1+2 (then later figure out which i choose)
    # buy/sell to open around the 15m sma 20 day - .1% under and .3% over
    df_f['bp_1'] = df_f['sma20_15']*1.001
    df_f['bp_2'] = df_f['sma20_15']*.997
    df_f['sp_1'] = df_f['sma20_15']*.999
    df_f['sp_2'] = df_f['sma20_15']*1.003


    return df_f



# open_positions() open_positions, openpos_bool, openpos_size, long
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





def kill_switch():

    # gracefully limit close us

    print('KILL SWITCH INITIATED')

    open_posi = open_positions()[1]
    long = open_positions()[3]
    kill_size = pnl_close()[2]

    while open_posi == True:

        print('starting kill switch loop til limit fill...')
        temp_df = pd.DataFrame()
        print('just made a temp df...')

        kucoin.cancel_all_orders(symbol)
        open_posi = open_positions()[1]
        long = open_positions()[3]
        kill_size = pnl_close()[2]
        kill_size = int(kill_size)

        now = datetime.now()
        ask = ask_bid()[0]
        bid = ask_bid()[1]

        if long == False:
            kucoin.create_limit_buy_order(symbol, kill_size, bid, params)
            print(f'just made a BUY order to CLOSE order of {kill_size} {symbol} at {bid} ')
            print('sleeping for 30 secs to see if it fills...')
            time.sleep(30)
        elif long == True:
            kucoin.create_limit_sell_order(symbol, kill_size, ask, params)
            print(f'just made a SELL order to CLOSE order of {kill_size} {symbol} at {ask} ')
            print('sleeping for 30 secs to see if it fills...')
            time.sleep(30)
        else:
            print('SOMETHING UNEXPECTED :(')

        open_posi = open_positions()[1]


def ob(symbol = symbol):

    print('fetching order book...')

    df = pd.DataFrame()
    temp_df = pd.DataFrame()

    ob = kucoin.fetch_order_book(symbol)

    bids = ob['bids']
    asks = ob['asks']

    first_bid = bids[0][0]
    first_ask = asks[0][0]

    bid_vol_list = []

    ask_vol_list = []

    for x in range(11):

        for set in bids:
            price = set[0]
            vol = set[1]
            bid_vol_list.append(vol) # list of buyers

            sum_bidvol = sum(bid_vol_list)
            temp_df['bid_vol'] = [sum_bidvol]

        for set in asks:
            price = set[0]
            vol = set[1]
            ask_vol_list.append(vol) # list of buyers

            sum_askvol = sum(ask_vol_list)
            temp_df['ask_vol'] = [sum_askvol]
        

        print(temp_df)
        time.sleep(5) # change to 5
        df_merged = pd.concat([df, temp_df], ignore_index=True)
        print(df_merged)
        print(' ')
        print('-------------')
        print(' ')

    print('finished fetching order book for bids and asks...')
    print('calculating the sums...')
    print(' ')
    print('-------------')
    total_bidvol = df_merged['bid_vol'].sum()
    total_askvol = df_merged['ask_vol'].sum()
    print(f'total bid vol: {total_bidvol} | total ask vol: {total_askvol} in the last 1min')

    # get last one min of vol of sell > buy do x
    if total_bidvol > total_askvol:
        control_dec = (total_askvol / total_bidvol)
        print(f'✅📈Bulls are in control in the last 1 min: {control_dec}')
        bullish  = True
        # if bulls are in control, use regular target
    else:
        control_dec = (total_bidvol / total_askvol)
        print(f'🚨📉Bears are in control in the last 1 min {control_dec}')
        bullish = False
    
    # if target is hit, check book vol
    # if book vol < .4, then stay in pos...
    # need to check to see if long or short

    open_posi = open_positions()
    openpos_tf = open_posi[1]
    long = open_posi[3]
    print(f'open pos: {openpos_tf} | long: {long}')

    

ob('BTC/USDT')

# [0] is PNLCLOSE, [1] is IN POSITION, [2] is SIZE, [3] is LONG
def pnl_close():

    print('Checking to see if its time to close...')

    params = {'type': 'swap', 'code': 'USD'}
    pos_dict = kucoin.fetch_positions(params)
    pos_dict = pos_dict[0]

    side = pos_dict['side']
    size = pos_dict['contracts']
    entry_price = float(pos_dict['avgEntryPrice'])
    leverage = float(pos_dict['leverage'])

    current_price = ask_bid()[1]

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

    print(f'diff: {diff} | perc: {perc}')

    perc = 100*perc
    print(f'this is our PNL percentage: {perc}%')

    pnl_close = False
    in_position = False

    if perc > 0:
        print('We are in profit, checking to see if we should close...')
        if perc > target:
            print(f' :) :) :) starting the kill switch because we hit our profit target of {target}% :) :) :)')
            pnlclose = True
            kill_switch()
        else:
            print('We are in profit but not enough to close')
            pnlclose = False

    elif perc < 0:
        print('We are in a loss, but holding on...')
        in_position = True

    else:
        print('we are not in position ')


    print('just finished checking PNL close...')

    return pnl_close, in_position, size, long


def bot():

    pnl_close() # close positions if we hit pnl 

    df_d = daily_sma() # determine log / short
    df_f = f15_sma() # provides prices bp_1, bp_2, sp_1, sp_2
    ask = ask_bid()[0]
    bid = ask_bid()[1]

    sig = df_d.iloc[-1]['sig']

    open_size = pos_size / 2

    # ONLY RUN IF NOT IN POSITION

    in_position = pnl_close()[1]

    if in_position == False:

        if sig == 'BUY':
            print('making an opening order as a BUY')
            bp_1 = df_f.iloc[-1]['bp_1']
            bp_2 = df_f.iloc[-1]['bp_2']
            print(f'this is bp_1: {bp_1} and this is bp_2: {bp_2}')
            kucoin.cancel_all_orders(symbol)
            kucoin.create_limit_buy_order(symbol, open_size, bp_1, params)
            kucoin.create_limit_buy_order(symbol, open_size, bp_2, params)

            print('just made opening order so going to sleep for 2 mins...')
            time.sleep(120)
        else:
            print('making an opening order as a SELL')
            sp_1 = df_f.iloc[-1]['sp_1']
            sp_2 = df_f.iloc[-1]['sp_2']
            print(f'this is sp_1: {sp_1} and this is sp_2: {sp_2}')
            kucoin.cancel_all_orders(symbol)
            kucoin.create_limit_sell_order(symbol, open_size, sp_1, params)
            kucoin.create_limit_sell_order(symbol, open_size, sp_2, params)

            print('just made opening order so going to sleep for 2 mins...')
            time.sleep(120)

    else:
        print('we are in position already, not making any new orders... ')


schedule.every(28).minutes.do(bot)

while True:
    try:
        schedule.run_pending()
    except:
        print('something went wrong, INTERNET PROBLEM OR SOMETHING...')
        time.sleep(30)


