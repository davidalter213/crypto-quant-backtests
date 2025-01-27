# Build next: liquidation data
# recent orders

import ccxt
import dontshare_config as ds

exchange = ccxt.kucoin({
    'enableRateLimit': True,
    'apiKey': ds.apiKey,
    'secret': ds.secret,
    'password': ds.password,
})

symbol = 'SOL/USDT'
order_type = 'market'
side = 'buy' #change to sell to short
amount = 10 

try: 
    balance = exchange.fetch_balance()

    print('Balances:')
    for currency, info in balance['total'].items():
        print(f'{currency} - {info:.2f}')

    print('\nPositions:')

    for position in balance['info']['data']['positions']:
        symbol = position['symbol']
        size = float(position['size'])
        avg_entry_price = float(position['avgEntryPrice'])
        mark_price = float(position['markPriceRp'])
        print(f'Symbol: {symbol}')
        print(f'Size: {size}')
        print(f'Average Entry Price: {avg_entry_price}')
        print(f'Mark Price: {mark_price}')
        print('------------')

except ccxt.BaseError as e:
    print(f'\n An error occurred: {e}')
        