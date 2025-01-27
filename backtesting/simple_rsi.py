'''

This is RSI strategy that sets the stop loss above the high and targets a 
1:3 RR ratio short. Can be convereted into a scaling stratgey by tweaking the code
1h timeframe 
'''

from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA
import pandas as pd
import numpy as np

data = pd.read_csv('XRP1h_2020-01-01_to_2025-01-01.csv', parse_dates=True, index_col='date')

print(data.head())

def RSI(series, period):
    series = pd.Series(series)
    delta = series.diff(1)
    up, down = delta.clip(lower=0), -delta.clip(upper=0)
    ma_up = up.rolling(period).mean()
    ma_down = down.rolling(period).mean()
    rsi = 100 - 100 / (1 + ma_up / ma_down)
    return rsi

class GoldenMomentumStrategy(Strategy):
    n1 = 14

    def init(self):
        self.rsi = self.I(RSI, self.data.Close, self.n1)
        self.close = self.data.Close
        self.low = self.data.Low
        self.high = self.data.High
        self.volume = self.data.Volume

    def buy_condition(self):
        return self.rsi[-1] < 30
    def sell_condition(self):
        return self.rsi[-1] > 70
    
    def next(self):
        if self.buy_condition():
            print('Buy signal Met.')
            self.buy()
        elif self.sell_condition():
            print('Sell signal Met.')
            self.sell()
        else:
            print('No signal Met.')

bt = Backtest(data, GoldenMomentumStrategy, commission=.002, cash=10000, trade_on_close=True)

stats = bt.run()

bt.plot()

print(stats)



        