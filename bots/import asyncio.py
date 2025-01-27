import asyncio
import json
import os
from datetime import datetime
import pytz
from websockets import connect
from termcolor import cprint

symbols = ['btcusdt', 'ethusdt', 'xrpusdt', 'solusdt', 'wifusdt']
websocket_url_base = 'wss://fstream.binance.com/ws/'
trades_filename = 'binance_trades.csv'
significant_trade_threshold = 10000  # Set your threshold here

if not os.path.isfile(trades_filename):
    with open(trades_filename, 'w') as f:
        f.write('Event Time, Symbol, Aggregate Trade ID, Price, Quantity, First Trade ID, Trade Time, Is Buyer Maker\n')

async def binance_trade_stream(uri, symbol, filename):
    async with connect(uri) as websocket:
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)

                event_time = datetime.fromtimestamp(data['E'] / 1000, pytz.UTC)
                agg_trade_id = data['a']
                price = float(data['p'])
                quantity = float(data['q'])
                first_trade_id = data['f']
                trade_time = datetime.fromtimestamp(data['T'] / 1000, pytz.UTC)
                is_buyer_maker = data['m']

                usd_size = price * quantity
                display_symbol = symbol.upper().replace('USDT', '')

                if usd_size >= significant_trade_threshold:
                    trade_type = 'SELL' if is_buyer_maker else 'BUY'
                    color = 'red' if trade_type == 'SELL' else 'green'
                    time_est = trade_time.strftime('%Y-%m-%d %H:%M:%S')

                    if usd_size >= 250000:
                        stars = '*' * 3
                        attrs = ['bold', 'blink']
                        output = f'{stars} {display_symbol} {trade_type} ${usd_size:,.2f} {time_est} {stars}'
                        for _ in range(4):
                            cprint(output, 'yellow', f'on_{color}', attrs=attrs)

                    elif usd_size >= 100000:
                        stars = '*' * 1
                        attrs = ['bold', 'blink']
                        output = f'{stars} {display_symbol} {trade_type} ${usd_size:,.2f} {time_est} {stars}'
                        for _ in range(2):
                            cprint(output, 'yellow', f'on_{color}', attrs=attrs)
                    
                    elif usd_size >= 25000:
                        attrs = ['bold']
                        output = f'{display_symbol} {trade_type} ${usd_size:,.2f} {time_est}'
                        cprint(output, 'yellow', f'on_{color}', attrs=attrs)
                    
                    print('')

                    with open(filename, 'a') as f:
                        f.write(f'{event_time}, {symbol}, {agg_trade_id}, {price}, {quantity}, '
                                f'{first_trade_id}, {trade_time}, {is_buyer_maker}\n')
            
            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(5)

async def main():
    filename = 'binance_trades.csv'
    tasks = []
    for symbol in symbols:
        uri = f"{websocket_url_base}{symbol}@aggTrade"
        tasks.append(binance_trade_stream(uri, symbol, filename))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())