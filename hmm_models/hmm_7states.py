import pandas as pd
import numpy as np
from hmmlearn import hmm
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
import time
import os

print('Starting Bitcoin HMM analysis..')

#load and preprocess data
def load_and_preprocess_data(file_path):
    print(f'Loading data from {file_path}')
    df = pd.read_csv(file_path)
    df.drop(df.columns[-1], axis=1, inplace=True)

    print('Creating datetime index...')
    df.index = pd.date_range(start='2019-01-01', periods=len(df), freq='h')
    df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
    print(df.columns)

    print('Calculating returns and volatility...')
    df['returns'] = df['close'].pct_change()
    df['volatility'] = df['returns'].rolling(window = 24).std()

    print('Calculating volume change...')
    df['volume_change'] = df['volume'].pct_change()

    print('Dropping NaN values...')
    df.dropna(inplace=True)

    print(f'Data loaded and preprocessed. Shape: {df.shape}')
    return df

def train_hmm(data, n_components=7):
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
    return model, scaler, X_scaled

# predict states
def predict_states(model, data, scaler):
    print('Predicting states...')
    features = ['returns', 'volatility', 'volume_change']
    X = data[features].values
    X_scaled = scaler.transform(X)
    states = model.predict(X_scaled)
    print(f'States predicted. Unique states: {np.unique(states)}')
    return states

def analyze_states(data, states, model):
    print('Analyzing states...')
    df_analysis = data.copy()
    df_analysis['states'] = states

    state_names = [
        "Bullish Trending",
        "Bearish Trending",
        "Sideways Consolidation",
        "Upwards Consolidation",
        "Downwards Consolidation",
        "Downwards Capitulation",
        "Upwards Capitulation"
    ]

    for state in range(model.n_components):
        print(f'Analyzing State {state} ({state_names[state]}):')
        state_data = df_analysis[df_analysis['states'] == state]
        print(state_data[['returns', 'volatility', 'volume_change']].describe())
        print(f'Number of periods in state: {state} {len(state_data)}')

def predict_nextstate(model, current_state):
    return np.argmax(model.transmat_[current_state])

def save_state_changes(states, data, state_names, output_file):
    state_changes = []
    current_state = states[0]
    start_time = data.index[0]

    for i, state in enumerate(states):
        if state != current_state:
            state_changes.append((start_time, data.index[i-1], current_state))
            current_state = state
            start_time = data.index[i]
    
    state_changes.append((start_time, data.index[-1], current_state))

    os.makedirs('data', exist_ok=True)

    with open(output_file, 'w') as f:
        f.write('start_time,end_time,state\n')
        for start_time, end_time, state in state_changes:
            f.write(f'{start_time},{end_time},{state_names[state]}\n')

    print(f'State changes saved to {output_file}')

def plot_states(data, states, model):
    print('Plotting results...')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

    ax1.plot(data.index, data['close'])
    ax1.set_title('Bitcoin Price and HMM States')
    ax1.set_ylabel('Price')

    state_names = [
        'Bullish Trending',
        'Bearish Trending',
        'Sideways Consolidation',
        'Upwards Consolidation',
        'Downwards Consolidation',
        'Downwards Capitulation',
        'Upwards Capitulation'
    ]

    colors = plt.cm.rainbow(np.linspace(0, 1, model.n_components))

    for state in range(model.n_components):
        mask = (states == state)
        ax1.fill_between(data.index, data['close'].min(), data['close'].max(), 
                         where=mask, alpha=0.3, label=state_names[state], color=colors[state])
    
    ax1.legend(loc = 'upper left', bbox_to_anchor = (1, 1))

    ax2.plot(data.index, data['returns'])
    ax2.set_title('Bitcoin Returns')
    ax2.set_ylabel('returns')
    ax2.set_xlabel('date')

    plt.tight_layout()
    print('Saving plot...')
    plt.savefig('data/plot.png')
    plt.show()

def calculate_prediction_accuracy(true_states, predicted_states):
    return np.mean(np.array(true_states[1:]) == np.array(predicted_states[:-1]))

def calculate_bic(model, X):
    n_features = X.shape[1]
    n_samples = X.shape[0]
    n_params = (model.n_components - 1) + model.n_components * (model.n_components - 1) + 2* model.n_components * n_features
    bic = -2 * model.score(X) * n_params * np.log(n_samples)
    return bic

def time_series_cv(X, n_splits=5):
    tscv = TimeSeriesSplit(n_splits=n_splits)
    scores = []

    for train_index, test_index in tscv.split(X):
        X_train, X_test = X[train_index], X[test_index]
        model = hmm.GaussianHMM(n_components=7, covariance_type='full', n_iter=100, random_state=42)
        model.fit(X_train)
        scores.append(model.score(X_test))
    
    return np.mean(scores), np.std(scores)

def analyze_feature_importance(model, feature_names):
    importance = np.abs(model.means_).sum(axis=0)
    importance = importance / importance.sum()
    for name, imp in zip(feature_names, importance):
        print(f'{name}: {imp: .4f}')


#main execution
print('Starting main execution...')
file_path = 'src/btc_1h.csv'
data = load_and_preprocess_data(file_path)

print('Training HMM...')
model, scaler, X_scaled = train_hmm(data, n_components=7)

print('Predicting states...')
states = predict_states(model, data, scaler)

state_names = [
    'Bullish Trending',
    'Bearish Trending',
    'Sideways Consolidation',
    'Upwards Consolidation',
    'Downwards Consolidation',
    'Downwards Capitulation',
    'Upwards Capitulation'
] 

output_file = 'data/state_changes.csv'
save_state_changes(states, data, state_names, output_file)

print('Analyzing states...')
analyze_states(data, states, model)

print('Plotting results...')
plot_states(data, states, model)

print('Printing transition matrix...')
print('Transition matrix:')
print(model.transmat_)

print('\nPrinting means and covariances of each state...')
for i in range(model.n_components):
    print(f'State {i}:')
    print('Mean:', model.means_[i])
    print('Covariance:', model.covars_[i])
    print()

print('Bitcoin HMM analysis complete.')

next_state_predictions = [predict_nextstate(model, state) for state in states]

accuracy = calculate_prediction_accuracy(states, next_state_predictions)
print(f'State Prediction accuracy: {accuracy:.2f}')

bic = calculate_bic(model, X_scaled)
print(f'BIC: {bic:.2f}')

cv_mean, cv_std = time_series_cv(X_scaled)
print(f'Cross-validated log likelihood: {cv_mean:.2f} +/- {cv_std:.2f}')

print('Feature importance Analysis:')
feature_names = ['returns', 'volatility', 'volume_change']
analyze_feature_importance(model, feature_names)
    