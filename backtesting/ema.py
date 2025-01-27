import pandas as pd
import numpy as np
from backtesting import Strategy
from backtesting.lib import crossover
from backtesting import Backtest

data = pd.read_csv('DOGE1h_2020-01-01_to_2025-01-01.csv',parse_dates= True, index_col='date')

class EMAStrategy(Strategy):

    n1 = 24
    n2 = 72

    def init(self):
        close_series = pd.Series(self.data['Close'])

        self.ema = self.I(self.EMA, close_series, self.n1)
        self.smma = self.I(self.SMMA, close_series, self.n2)

    def next(self):
        if crossover(self.ema, self.smma) and not self.position.is_long:
            self.buy(sl = self.smma[-1])
        elif crossover(self.smma, self.ema):
            self.sell(sl = self.smma[-1])

    @staticmethod
    def EMA(series, period):
        return series.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def SMMA(series, period):
        return series.ewm(alpha=1/period, adjust=False).mean()
    
bt = Backtest(data, EMAStrategy, cash=100000, commission=.001)

stats = bt.run()

bt.plot()

print(stats)



