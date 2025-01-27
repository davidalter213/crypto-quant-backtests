'''

HMMs can predict hidden states and market regimes...

HMMs assume markets have hiddent states (regimes) that we cant directly observe
These hidden states influence observable market features (price, volume, ect)
Hidden states: bull, bear, sideways
Observanle feautrs: market data we can measure
Transition probabailities: likelihood of moving between states

HMM process:
define possible market regimes 
slect relevant observable features
train model on historical data
use model to infer current regime

'''


import pandas as pd
import numpy as np
from hmmlearn import hmm
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
import time

print('Starting Bitcoin HMM analysis..')

def load_and_preprocess_data(file_path):
    # Load the data

    print(f'Loading data from {file_path}')
    df = pd.read_csv(file_path)

    df.drop(df.columns[-1], axis=1, inplace=True)

    print('Creating datetime index...')
    df.index = pd.date_range(start='2019-01-01', periods=len(df), freq='h')

    #rename columns to DATETIMEOHLCV
    df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']

    print('Calculating returns and volatility...')
    df['returns'] = df['close'].pct_change()
    df['volatility'] = df['returns'].rolling(window = 24).std()

    print('Calculating volume change...')
    df['volume_change'] = df['volume'].pct_change()

    print('Dropping NaN values...')
    df.dropna(inplace=True)

    print(f'Data loaded and preprocessed. Shape: {df.shape}')
    return df

def train_hmm(data, n_components=3):
    print(f'Training HMM with {n_components} components...')
    features = ['returns', 'volatility', 'volume_change']
    X = data[features].values

    print('Normalizing features...')
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print('Training HMM...')
    model = hmm.GaussianHMM(n_components=n_components, covariance_type='full', n_iter=100, random_state=42)
    model.fit(X_scaled)

    print('HMM trained.')
    return model, scaler

# predict states
def predict_states(model, data, scaler):
    print('Predicting states...')
    features = ['returns', 'volatility', 'volume_change']
    X = data[features].values
    X_scaled = scaler.transform(X)

    states = model.predict(X_scaled)
    print(f'States predicted. Unique states: {np.unique(states)}')
    return states

#analyze states
def analyze_states(data, states):
    print('Analyzing states...')
    df_analysis = data.copy()
    df_analysis['state'] = states

    for state in range(model.n_components):
        print(f'Analyzing State {state}')
        state_data = df_analysis[df_analysis['state'] == state]
        print(state_data[['returns', 'volatility', 'volume_change']].describe())
        print(f'Number of periods in state: {state} {len(state_data)}')

def plot_results(data, states):
    print('Plotting results...')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

    ax1.plot(data.index, data['close'])
    ax1.set_title('Bitcoin Price and HMM States')
    ax1.set_ylabel('Price')

    for state in range(model.n_components):
        mask = (states == state)
        ax1.fill_between(data.index, data['close'].min(), data['close'].max(), 
                         where=mask, alpha=0.3, label=f'State {state}')
        
    ax1.legend()

    ax2.plot(data.index, data['returns'])
    ax2.set_title('Bitcoin Returns')
    ax2.set_ylabel('returns')
    ax2.set_xlabel('date')

    plt.tight_layout()
    print('Showing plot...')
    #save the plot to my data folder in this directory as a plot
    plt.savefig('data/plot.png')
    plt.show()


print('Starting main execution...')
file_path = '/Users/davidalter/market_maker_botv1/src/btc_1h.csv'
data = load_and_preprocess_data(file_path)
print(data.head())

print('Training HMM model...')
model, scaler = train_hmm(data, n_components=3)

print('Predicting states...')
states = predict_states(model, data, scaler)

print('Analyzing states...')
analyze_states(data, states)

print('Plotting results...')
plot_results(data, states)

print('Printing transition matrix...')
print('Transition matrix:')
print(model.transmat_)

print('\nPrinting means and covariances...')
for i in range(model.n_components):
    print(f'State {i}')
    print('Mean:', model.means_[i])
    print('Covariance:', model.covars_[i])
    print()
   
print('HMM analysis complete.')
