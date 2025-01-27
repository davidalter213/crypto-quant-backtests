import pandas as pd
from backtesting import Backtest, Strategy

class EMAStrategy(Strategy):

    ema1_length = 11
    ema2_length = 17
    ema100_length = 44

    def init(self):
        self.pema1 = 0.0
        self.pema2 = 0.0
        self.pema100 = 0.0

        self.buy_signal = False

    def next(self):
        alpha1 = 2 / (self.ema1_length + 1)
        alpha2 = 2 / (self.ema2_length + 1)
        alpha100 = 2 / (self.ema100_length + 1)

        close = self.data.Close[-1]

        self.pema1 = alpha1 * close + (1 - alpha1) * self.pema1
        self.pema2 = alpha2 * close + (1 - alpha2) * self.pema2
        self.pema100 = alpha100 * close + (1 - alpha100) * self.pema100

        self.buy_signal = self.pema1 > self.pema2
        self.sell_signal = self.pema1 <= self.pema2

        if self.buy_signal:
            self.buy()

        if self.sell_signal:
            self.sell()

if __name__ == '__main__':
    data = pd.read_csv('DOGE1h_2020-01-01_to_2025-01-01.csv', parse_dates=True, index_col='date')
    data['Close'] = data['Close'].values.astype(float)

    EMAStrategy.ema1_length = 11
    EMAStrategy.ema2_length = 17
    EMAStrategy.ema100_length = 44

    bt = Backtest(data, EMAStrategy, cash=100000, commission=.001, exclusive_orders=True)
    stats = bt.run()
    bt.plot()
    print(stats)

