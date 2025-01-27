'''
Simple EMA CrossOver Strategy that tells when to buy and sell
'''

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from backtesting import Strategy
from backtesting.lib import crossover
from backtesting import Backtest

data = pd.read_csv('DOGE1h_2020-01-01_to_2025-01-01.csv')
data['date'] = pd.to_datetime(data['date'])
data.set_index('date', inplace=True)

short_window = 5
medium_window = 8
long_window = 13

data['Short_MA'] = data['Close'].rolling(window=short_window, min_periods=1).mean()
data['Medium_MA'] = data['Close'].rolling(window=medium_window, min_periods=1).mean()
data['Long_MA'] = data['Close'].rolling(window=long_window, min_periods=1).mean()

signals = pd.DataFrame(index=data.index)
signals['Signal'] = 0.0

signals['Signal'][short_window:] = np.where(
    (data['Short_MA'][short_window:] > data['Medium_MA'][short_window:]) &
    (data['Medium_MA'][short_window:] > data['Long_MA'][short_window:]), 
    1.0, 0.0
)

signals['Signal'][short_window:] = np.where(
    (data['Short_MA'][short_window:] < data['Medium_MA'][short_window:]) &
    (data['Medium_MA'][short_window:] < data['Long_MA'][short_window:]), 
    -1.0,
    signals['Signal'][short_window:]
)

signals['Position'] = signals['Signal'].diff()
#Plotting

plt.figure(figsize=(14,7))
plt.plot(data['Close'], label='Close Price', alpha = 0.5)
plt.plot(data['Short_MA'], label = '5-day SMA', alpha = 0.5)
plt.plot(data['Medium_MA'], label = '8-day SMA', alpha = 0.5)
plt.plot(data['Long_MA'], label = '13-day SMA', alpha = 0.5)

plt.plot(signals[signals['Position'] == 1].index,
         data['Short_MA'][signals['Position'] == 1],
         '^', markersize=10, color='g', lw=0, label='Buy Signal')

plt.plot(signals[signals['Position'] == -1].index,
            data['Short_MA'][signals['Position'] == -1],
            'v', markersize=10, color='r', lw=0, label='Sell Signal')

plt.title('Most used Moving Average Crossover Strategy')
plt.legend(loc = 'best')
plt.show()

