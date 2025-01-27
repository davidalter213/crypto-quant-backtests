'''
Get Liquidations from Binance
'''

import asyncio
import json
import os
from datetime import datetime
import pytz
from websockets import connect
from termcolor import cprint

websocket_url_base = 'wss://fstream.binance.com/ws/!forceOrder@arr'
filename = 'binance_liquidations.csv'

if not os.path.isfile(filename):
    with open(filename, 'w') as f:
        f.write(",".join([
            'symbol', 'side', 'order_type', 'time_in_force',
            'orig_qty', 'price', 'average_price', 'order_status',
            'order_last_filled_qty', 'order_filled_accumulated_qty',
            'order_trade_time', 'usd_size'
        ]) + '\n')

async def binance_liquidation_stream(uri, filename):
    async with connect(uri) as websocket:
        print("Connected to WebSocket")
        cprint("Liquidation Bot LIVE🚨", 'red', 'on_white')
        while True:
            try:
                message = await websocket.recv()
                order_data = json.loads(message)['o']

                symbol = order_data['s'].replace('USDT', '')
                side = order_data['S']
                timestamp = order_data['T']
                filled_qty = float(order_data['z'])
                price = float(order_data['p'])
                usd_size = filled_qty * price
                est = pytz.timezone('US/Eastern')
                time_est = datetime.fromtimestamp(timestamp / 1000, est).strftime('%Y-%m-%d %H:%M:%S')



                if usd_size > 3000:
                    liquidation_type = 'L LIQ' if side == 'SELL' else 'S LIQ'
                    symbol = symbol[:4]
                    output = f'{symbol} {liquidation_type} ${usd_size:,.2f} {time_est}'
                    color = 'red' if side == 'SELL' else 'green'
                    attrs = ['bold'] if usd_size >= 10000 else []

                    
                    if usd_size >= 250000:
                       stars = '*' * 3
                       attrs.append('blink')
                       output = f'{stars} {output}'
                       for _ in range(4):
                            cprint(output, 'white', f'on_{color}', attrs=attrs)  # Changed colors for visibility

                    elif usd_size >= 100000:
                        stars = '*' * 1
                        attrs.append('blink')
                        output = f'{stars} {output}'
                        for _ in range(2):
                            cprint(output, 'white', f'on_{color}', attrs=attrs)
                    
                    elif usd_size >= 25000:
                        cprint(output, 'white', f'on_{color}', attrs=attrs)

                    else:
                        cprint(output, 'white', f'on_{color}', attrs=attrs)
                    
                    print('')

                msg_values = [str(order_data.get(k, '')) for k in [ 's', 'S', 'o', 'f', 'q', 'p', 'ap', 'X', 'l', 'Z', 'T', 'usd_size']]
                msg_values.append(str(usd_size))
                with open(filename, 'a') as f:
                   trade_info = ','.join(msg_values) + '\n'
                   trade_info = trade_info.replace("USDT", "")
                   f.write(trade_info)

                        

            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(5)


async def main():
    uri = 'wss://fstream.binance.com/ws/!forceOrder@arr'
    await binance_liquidation_stream(uri, filename)

if __name__ == '__main__':
    asyncio.run(main())
