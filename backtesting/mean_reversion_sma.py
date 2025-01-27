'''
Longer term timeframe, simple mean reversion strategy + SMA crossover

The idea is that when price is overextended, it will revert back to the mean.
and when the price is below the mean, it will revert back to the mean.
You are looking for a crossover between the lines. Setting the stop loss as last low or high. 
'''

import pandas as pd 
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA

data  = pd.read_csv('1d_2023-01-01_to_2025-01-01.csv', parse_dates= True, index_col='date')

print(data.head())


class SmaCross(Strategy):
    def init(self):
        self.short_sma = self.I(SMA, self.data.Close, 20)
        self.long_sma = self.I(SMA, self.data.Close, 50)
    
    def next(self):
        if crossover(self.short_sma, self.long_sma):
            self.buy()
        elif crossover(self.long_sma, self.short_sma):
            self.sell()

bt = Backtest(data, SmaCross, cash=10000, commission=.002)

output = bt.run()

bt.plot()

print(output)