'''
This script is a simple example of how to use the backtesting library to backtest a strategy that uses the RSI, EMA, and MACD indicators.
Using the backtesting library, we can easily backtest a strategy that uses the RSI, EMA, and MACD indicators to generate buy and sell signals.

The strategy is defined as follows:
- If the RSI is above 50, the fast MACD is above the slow MACD, and the close price is above the fast EMA, generate a buy signal.
- If the RSI is below 50, the fast MACD is below the slow MACD, and the close price is below the fast EMA, generate a sell signal.

Use longer term time frames like 12h.
'''

import pandas as pd
from backtesting import Backtest, Strategy
from talib import RSI, EMA, MACD

class RSIMACDxEMA(Strategy):

    def init(self):

        self.rsi = self.I(RSI, self.data.Close, timeperiod =11)
        self.fast_macd, self.slow_macd, _ = self.I(MACD, self.data.Close, fastperiod=11, slowperiod=30)
        self.ema_fast = self.I(EMA, self.data.Close, timeperiod=22)
        self.ema_slow = self.I(EMA, self.data.Close, timeperiod=75)

    def next(self):

        is_long_signal = (
            self.rsi > 50 and
            self.fast_macd > self.slow_macd and
            self.data.Close > self.ema_fast
        )

        is_short_signal = (
            self.rsi < 50 and
            self.fast_macd < self.slow_macd and
            self.data.Close < self.ema_fast
        )

        if is_long_signal:
            self.buy()
        elif is_short_signal:
            self.sell()

# Load data

data = pd.read_csv('/Users/davidalter/market_maker_botv1/ETH6h_2019-01-01_to_2025-01-01.csv', parse_dates=True, index_col='date')

# Convert the 'datetime' column to a datetime type if it's not already
data['datetime'] = pd.to_datetime(data['datetime'], unit='ms')

# Set the 'datetime' as the index of the dataframe
data.set_index('datetime', inplace=True)

# Drop the duplicate date column if present
if 'date' in data.columns:
    data.drop(columns=['date'], inplace=True)

# Rename columns to ensure they are compatible with the backtesting library
data.rename(columns={
    'Open': 'Open',
    'High': 'High',
    'Low': 'Low',
    'Close': 'Close',
    'Volume': 'Volume'
}, inplace=True)

# Verify everything is correct
print(data.head())

bt = Backtest(data, RSIMACDxEMA, cash=10000, commission=.002)

stats = bt.run()

bt.plot()

print(stats)

