'''
Shorter timeframe, use 15m data to create Chandelier Exit indicator

If price action is above the Chandelier Exit line, go long
If price action is below the Chandelier Exit line, go short
'''

import pandas as pd
from backtesting import Backtest, Strategy
import numpy as np

class MagicIndicator(Strategy):
    ce_period = 14
    ce_multiplier = 1
    risk_reward_ratio = 2

    def init(self):
        self.atr = self.I(self.ATR, self.data.High, self.data.Low, self.data.Close, period=self.ce_period)
    
    def ATR(self, high, low, close, period):
        tr1 = high - low
        tr2 = np.abs(high[1:] - close[:-1])
        tr3 = np.abs(low[1:] - close[:-1])

        tr = np.max([tr1[1:], tr2, tr3], axis=0)
        tr = np.insert(tr, 0, tr1[0])

        atr = pd.Series(tr).rolling(period).mean().values
        return atr
    
    def next(self):
        atr_value = self.atr[-1]
        ce = self.data.Close[-1] - self.ce_multiplier * atr_value

        if not self.position:
            if ce > self.data.Close[-1]:
                entry_price = self.data.Close[-1]
                stop_loss = entry_price - atr_value
                take_profit = entry_price + atr_value * self.risk_reward_ratio
                self.buy(sl=stop_loss, tp=take_profit)
            elif ce < self.data.Close[-1]:
                entry_price = self.data.Close[-1]
                stop_loss = entry_price + atr_value
                take_profit = entry_price - atr_value * self.risk_reward_ratio

# Load your hourly Bitcoin data
data = pd.read_csv('DOGE1h_2020-01-01_to_2025-01-01.csv',parse_dates= True, index_col='date')
data.drop(data.columns[0], axis=1, inplace=True)

# Debugging: Print the DataFrame columns to verify
print(data.head())
print(data.columns)

# Run the backtest
bt = Backtest(data, MagicIndicator, cash=100000, commission=.001)
stats = bt.run()
bt.plot()

print(stats)