'''
This script is an advanced example of how to use the backtesting library to backtest a strategy that uses the MACD and Stochastic indicators.

The strategy is defined as follows:
- If the MACD line is above the signal line, the %K line is above the %D line, and the MACD histogram is above 0, generate a buy signal.

Use longer term time frames like 4h.

'''

import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import talib

# Load the data
data = pd.read_csv('ETH4h_2022-01-01_to_2025-01-01.csv', parse_dates=True, index_col='datetime')

# Define the strategy
class AdvancedMACDLong(Strategy):
    def init(self):
        # MACD indicator
        self.macd_line, self.signal_line, self.hist = self.I(talib.MACD, self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9)
        
        # Stochastic indicator
        self.k, self.d = self.I(talib.STOCH, self.data.High, self.data.Low, self.data.Close)
        
    def next(self):
        # Entry criteria
        if self.macd_line[-1] > self.signal_line[-1] and self.k[-1] > self.d[-1] and self.hist[-1] > 0:
            if not self.position:
                self.buy(sl=self.data.Close[-1] * 0.98, tp=self.data.Close[-1] * 1.04)  # 2:1 Risk/Reward
        
        # Example exit criteria: MACD line crosses below signal line
        elif crossover(self.signal_line, self.macd_line):
            self.position.close()

# Setup backtest
bt = Backtest(data, AdvancedMACDLong, cash=10000, commission=.002, exclusive_orders=True)
output = bt.run()
print(output)

# Plot the results
bt.plot()