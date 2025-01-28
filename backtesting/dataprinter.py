import ccxt 
import pandas as pd
import datetime as datetime 

def fetch_and_save_historical_data(symbol, timeframe, start_date, end_date, filename):

    binance = ccxt.binance()

    start_timestamp = int(datetime.datetime.strptime(start_date, '%Y-%m-%d').timestamp()) * 1000
    end_timestamp = int(datetime.datetime.strptime(end_date, '%Y-%m-%d').timestamp()) * 1000

    all_ohlcv = []
    current_timestamp = start_timestamp

    while current_timestamp < end_timestamp:
        limit = min(1000, (end_timestamp - current_timestamp) // (60 * 1000))
        ohlcv = binance.fetch_ohlcv(symbol, timeframe, since=current_timestamp, limit=limit)

        if not ohlcv:
            break

        all_ohlcv.extend(ohlcv)

        current_timestamp = (ohlcv[-1][0] + 60000)  # Add 1 millisecond to avoid duplicates

        df = pd.DataFrame(all_ohlcv, columns=['datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])

    df['date'] = pd.to_datetime(df['datetime'], unit='ms')

    df.to_csv(filename, index=False)
    print(f"Saved {len(df)} rows to {filename}")

symbol = 'ETH/USDT'
timeframe = '4h'
start_date = '2022-01-01'
end_date = '2025-01-01'

filename = f'{timeframe}_{start_date}_to_{end_date}.csv'

fetch_and_save_historical_data(symbol, timeframe, start_date, end_date, filename)

#Drop /USDT from symbol so that we can add it to the filename and rename the filename
symbol = symbol.replace('/', '') 
