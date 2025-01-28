'''
This script is a simple example of a backtesting strategy that uses two indicators to generate buy and sell signals.

The strategy is defined as follows:
- If the price crosses above the long-term indicator and the price is above the long-term indicator, generate a buy signal.
- If the price crosses below the short-term indicator and the price is below the short-term indicator, generate a sell signal.

Use longer term time frames like 1h.

'''

from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd

class twoIndicators(Strategy):
    def init(self):
        super().init()

    def next(self):
        current_price = self.data.Close[-1]
        if (crossover(self.data['Close'], self.data['ce_long']) and current_price > self.data['ce_long'][-1]):
            self.buy()

        if (crossover(self.data['Close'], self.data['ce_short']) and current_price < self.data['ce_short'][-1]):
            self.sell()

data = pd.read_csv('DOGE1h_2020-01-01_to_2025-01-01.csv', parse_dates= True, index_col='date')

atr_period = 57
atr_multiplier = 5
data['ce_long'] = data['Close'].rolling(window=atr_period).mean() - (data['Close'].rolling(window=atr_period).std() * atr_multiplier)
data['ce_short'] = data['Close'].rolling(window=atr_period).mean() + (data['Close'].rolling(window=atr_period).std() * atr_multiplier)

long_threshold = 80
short_threshold = 20

bt = Backtest(data, twoIndicators, cash=10000, commission=.002, exclusive_orders=True)

output = bt.run()

bt.plot()

print(output)

