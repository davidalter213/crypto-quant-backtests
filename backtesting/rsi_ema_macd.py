import pandas as pd
from backtesting import Backtest, Strategy
import ta

class RSIMACDxEMA(Strategy):

    def init(self):

        self.data['Close'] = pd.to_numeric(self.data['Close'], errors='coerce')

        # Check data after conversion
        print(self.data.head())

        # Initialize the RSI, MACD, and EMA using the 'ta' library
        self.rsi = ta.momentum.RSIIndicator(self.data.Close, 14).rsi()
        macd = ta.trend.MACD(self.data.Close, 12, 26, 9)
        self.fast_macd = macd.macd()
        self.slow_macd = macd.macd_signal()
        self.ema = ta.trend.EMAIndicator(self.data.Close, 20).ema_indicator()

    def next(self):
        # Define the trading signals
        is_long_signal = (
            self.rsi[-1] > 50 and
            self.fast_macd[-1] > self.slow_macd[-1] and
            self.data.Close[-1] > self.ema[-1]
        )

        is_short_signal = (
            self.rsi[-1] < 50 and
            self.fast_macd[-1] < self.slow_macd[-1] and
            self.data.Close[-1] < self.ema[-1]
        )

        # Execute trade orders based on the signals
        if is_long_signal:
            self.buy()
        elif is_short_signal:
            self.sell()

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

