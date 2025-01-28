import asyncio
import json
import os
from datetime import datetime
import pytz
from websockets import connect, connection
from termcolor import cprint

symbols = ['btcusdt', 'ethusdt', 'solusdt', 'xrpusdt', 'dogusdt', 'wifusdt']
websocket_url = 'wss://stream.binance.com:9443/ws'

class TradeAggregator:

    cprint('Hello, World!', 'white', 'on_blue', attrs=['bold'])

    def __init__(self, symbol):
        self.trades_buckets = {}

    async def add_trade(self, symbol, timestamp, usd_size, is_buyer_maker):
        trade_key = (symbol, timestamp, is_buyer_maker)
        self.trades_buckets[trade_key] = self.trades_buckets.get(trade_key, 0) + usd_size

    async def check_and_print_trades(self):
        timestamp_now = datetime.now(pytz.timezone('US/Eastern')).strftime('%H:%M:%S')

        deletions = []
        for trade_key, usd_size in self.trades_buckets.items():
            symbol, timestamp, is_buyer_maker = trade_key
            if timestamp < timestamp_now and usd_size > 500000:
                trade_type = 'BUY' if not is_buyer_maker else 'SELL'

                back_color = 'on_blue' if not is_buyer_maker else 'on_magenta'
                display_size = usd_size / 1000000
                attrs = ['bold']
                if usd_size > 3000000:
                    attrs.append('blink')
                    cprint(f'{trade_type} {symbol} {timestamp} ${display_size:.2f}m', 'white', back_color, attrs=attrs)

                else:
                    cprint(f'{trade_type} {symbol} {timestamp} ${display_size:.2f}m', 'white', back_color, attrs=attrs)

                    deletions.append(trade_key)

        for trade_key in deletions:
            del self.trades_buckets[trade_key]

trade_aggregator = TradeAggregator(symbols)

async def trade_handler(symbol, trade_aggregator):
    uri = f'{websocket_url}/{symbol.lower()}@aggTrade'

    async with connect(uri) as ws:
        while True:
            try:
                message = await ws.recv()
                print(message)
                trade = json.loads(message)
                timestamp = datetime.fromtimestamp(trade['T'] / 1000, pytz.timezone('US/Eastern')).strftime('%H:%M:%S')
                usd_size = float(trade['q']) * float(trade['p'])
                is_buyer_maker = trade['m']

                await trade_aggregator.add_trade(symbol.upper().replace('USDT',''), timestamp, usd_size, is_buyer_maker )

            except Exception as e:
                print(f'Error {e}')
                await asyncio.sleep(1)

async def print_aggregated_trades_every_second(trade_aggregator):
    while True:
        await asyncio.sleep(1)
        await trade_aggregator.check_and_print_trades()

async def main():
    tasks = [trade_handler(symbol, trade_aggregator) for symbol in symbols]
    tasks.append(print_aggregated_trades_every_second(trade_aggregator))

    await asyncio.gather(*tasks)

asyncio.run(main())

        