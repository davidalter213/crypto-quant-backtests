'''
This script is an example of how to use the backtesting library to backtest a strategy that uses the Alpha Trend indicator.

The Alpha Trend indicator is a trend-following indicator that uses a moving average to determine the direction of the trend. 
It is calculated by taking the average of the high and low prices over a specified period, and then adding or subtracting a 
multiple of the difference between the current price and the average price.

The strategy is defined as follows:
- If the price is above the Alpha Trend line, generate a buy signal.
- If the price is below the Alpha Trend line, generate a sell signal.

Use shorter term time frames like 1h.
'''

from backtesting import Strategy, Backtest
from backtesting.lib import crossover
import pandas as pd
import numpy as np

def AlphaTrend(data, multiplier, period):
    hl2 = (data['High'] + data['Low']) / 2
    alpha_trend = pd.Series(index=data.index, dtype=float)
    trend  = 1

    for i in range(1, len(hl2)):
        if trend == 1:
            alpha_trend[i] = hl2[i - period] + multiplier * (hl2[i] - hl2[i - period])
            if hl2[i] < alpha_trend[i]:
                trend = -1
        else:
            alpha_trend[i] = hl2[i - period] - multiplier * (hl2[i - period] - hl2[i])
            if hl2[i] > alpha_trend[i]:
                trend = 1
    
    return alpha_trend.ffill().bfill()

class AlphaTrendStrategy(Strategy):
    multiplier = 0.3
    period = 5

    def init(self):
       self.alpha_trend = self.I(AlphaTrend, self.data.df, self.multiplier, self.period)

    def next(self):
        price = self.data.Close[-1]
        trend = self.alpha_trend[-1]

        if not self.position:
            if price > trend and self.buy_signal(price, trend):
                self.buy()
            
            elif price < trend and self.sell_signal(price, trend):
                self.sell()

        elif self.position.is_long and price < trend:
            self.position.close()

        elif self.position.is_short and price > trend:
            self.position.close()

    def buy_signal(self, price, trend):
        return price > trend
    def sell_signal(self, price, trend):
        return price < trend
        
data = pd.read_csv('DOGE1h_2020-01-01_to_2025-01-01.csv', parse_dates=True, index_col='date')

bt = Backtest(data, AlphaTrendStrategy, cash=10000, commission=.002)

output = bt.run()

bt.plot()

print(output)

