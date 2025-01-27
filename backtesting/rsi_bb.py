'''
full breakdown https://www.youtube.com/watch?v=Vv3eqU_0pho&ab_channel=MoonDev
'''

import pandas as pd
import matplotlib.pyplot as plt
from backtesting import Backtest, Strategy
import numpy as np
from backtesting.lib import crossover
import ta

#Bollinger Band Breakout Strategy (Short Only)
class BollingerBandBreakoutShort(Strategy):
    rsi_period = 14
    bollinger_period = 20
    rsi_lower = 40
    rsi_upper = 60
    take_profit = 0.05 # 5%
    stop_loss = 0.03 # 3%

    def init(self):
        self.rsi = self.data['RSI']
        self.upper_bb = self.data['UpperBB']
        self.lower_bb = self.data['LowerBB']

    def next(self):
        if not self.position and self.rsi < self.rsi_lower and self.data['Close'][-1] < self.lower_bb:
            self.buy()
        elif self.position and self.data['Close'] > self.upper_bb:
            self.sell()


data = pd.read_csv('ETH6h_2019-01-01_to_2025-01-01.csv', parse_dates=True, index_col='date')
# Drop the first column
data.drop(data.columns[0], axis=1, inplace=True)

#Ensure necessary columns are present and rename correctly
data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

data['RSI'] = ta.momentum.RSIIndicator(data['Close'], 14).rsi()
upper_bb, lower_bb = ta.volatility.BollingerBands(data['Close'], 20).bollinger_lband(), ta.volatility.BollingerBands(data['Close'], 20).bollinger_hband()
data['UpperBB'] = upper_bb
data['LowerBB'] = lower_bb

bt = Backtest(data, BollingerBandBreakoutShort, cash=10000, commission=.002)

stats_default = bt.run()
print('Default Parameter Results:')
print(stats_default)


#Run the backtest with the best parameters
bt = Backtest(data, BollingerBandBreakoutShort, cash=10000, commission=.002)
stats_optimized = bt.run()

print('Optimized Results:')
print(stats_optimized)

#Plot the backtest results
bt.plot()


plt.figure()
plt.plot(data.index, data['Close'], label='Close Price')
plt.plot(data.index, data['RSI'], label='14-Period RSI')
plt.plot(data.index, data['UpperBB'], label='Upper Bollinger Band')
plt.plot(data.index, data['LowerBB'], label='Lower Bollinger Band')

plt.xlabel('Date')
plt.ylabel('Price')
plt.title('Bollinger Band RSI Breakout Strategy')
plt.legend()
plt.show()

