new_data = True
MARKET_CAP_MAX = 30000
NUM_TOKENS_2SEARCH = 10000
MIN_24HR_VOLUME = 1000

MAX_SELL_PERCENTAGE = 70
MIN_TRADES_LAST_HOUR = 9
MIN_UNIQ_WALLET2HR = 30
MIN_VIEW24H = 15
MIN_LIQUIDITY = 400

import pandas as pd
import datetime
import dontshare_config as ds

import requests
import time, json
import pprint
import re as reggie

def birdeye_bot():

    base_url = 'https://www.birdeye.so/token'

    url = 'https:/public-api.birdeye.so/defi/tokenlist?sort_by=v24hUSD&sort_type=desc'

    headers = { 'X-API-KEY': ds.birdeye_key }

    tokens = []
    offset = 0
    limit = 50
    total_tokens = 0
    max_tokens = NUM_TOKENS_2SEARCH
    mc_high = MARKET_CAP_MAX
    mc_low = 50

    min_liquidity = MIN_LIQUIDITY
    min_view24h = MIN_VIEW24H
    min_last_trades = 59

    while total_tokens < max_tokens:
        try:
            print(f'scanning solana for new tokens total scanned: {total_tokens}...')
            params = {"sort_by":"v24hUSD","sort_type":"desc","offset":offset,"limit":limit}
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                response_data = response.json()
                new_tokens = response_data.get('data', []).get('tokens', [])
                tokens.extend(new_tokens)
                total_tokens += len(new_tokens)
                offset += limit
            else:
                print
                time.sleep(10)
                continue

            time.sleep(0.1)

        except Exception as e:
            print(f'Request failed: {e}. Retying in 10 seconds...')
            time.sleep(10)
            continue

    df = pd.DataFrame(tokens)
    df['token_url'] = df['address'].apply(lambda x: base_url + '/' + x)
    df = df.dropna(subset=['liquidity', 'v24hUSD'])
    df = df[df['liquidity'] > min_liquidity]
    df = df[df['v24hUSD'] >= min_view24h]
    df = df[(df['mc'] >= mc_low) & (df['mc'] <= mc_high)]

    drop_columns = ['logoURI', '_id']
    for col in drop_columns:
        if col in df.columns:
            df = df.drop(col, axis=1)

    df['lastTradeUnixTime'] = pd.to_datetime(df['lastTradeUnixTime'], unit='s').dt.tz_localize('UTC').dt.tz_convert('US/Eastern')

    current_time = datetime.datetime.now(datetime.timezone.utc)

    ten_minutes_ago = current_time - datetime.timedelta(minutes=10)

    df = df[df['lastTradeUnixTime'] >= ten_minutes_ago]

    df.to_csv('birdeye_solana.csv', index=False)

    pd.set_option('display.max_columns', None)

    return df

if new_data == True:
    print('Getting new data...')
    df = birdeye_bot()

else: 
    df = pd.read_csv('birdeye_solana.csv')
    

def new_launches(data):

    new_launches = data[data['v24hChangePercent'].isma()]

    timestamp = 'data/new_launches.csv'

    new_launches.to_csv(timestamp, index=False)

    return new_launches

new_launches(df)

def print_pretty_json(data):
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(data)

def find_urls(string):
    return reggie.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', string)

BASE_URL = 'https://public-api.birdeye.so/defi/'

API_KEY = ds.birdeye_key

def token_overview(address, MAX_SELL_PERCENTAGE, MIN_TRADRES_LAST_HOUR, MIN_UNIQ_WALLET2HR, MIN_VIEW24H, MIN_LIQUIDITY):

    overview_url = f'{BASE_URL}/token_overview?address={address}'
    headers = { 'X-API-KEY': API_KEY }

    response = requests.get(overview_url, headers=headers)
    results = {}

    if response.status_code == 200:
        response_data = response.json()
        results = response_data.get('data', {})

        buy1h = response_data.get('buy1h', 0)
        sell1h = response_data.get('sell1h', 0)
        trade1h = buy1h - sell1h
        total_trades = trade1h

        buy_percentage = (buy1h/total_trades*100) if total_trades else 0
        sell_percentage = (sell1h/total_trades*100) if total_trades else 0

        if sell_percentage > MAX_SELL_PERCENTAGE:
            return None
        if trade1h < MIN_TRADES_LAST_HOUR:
            return None
        if response_data.get('uniqWallets2h', 0) < MIN_UNIQ_WALLET2HR:
            return None
        if response_data.get('v24hUSD', 0) < MIN_VIEW24H:
            return None
        if response_data.get('liquidity', 0) < MIN_LIQUIDITY:
            return None
            
        results.update({
            'address': address,
            'buy1h': buy1h,
            'sell1h': sell1h,
            'trade1h': trade1h,
            'buy_percentage': buy_percentage,
            'sell_percentage': sell_percentage,
            'liquidity': response_data.get('liquidity', 0)             
        })

        extensions = response_data.get('extensions', {})
        description = extensions.get('description', '') if extensions else ''
        urls = find_urls(description)
        links = [('telegram', u) for u in urls if 't.me' in u]
        links.extend([('x.com', u) for u in urls if 'x.com' in u])
        links.extend([('website', u) for u in urls if 't.me' not in u and 'x.com' not in u])
        results['links'] = links

        return results
    
    else:
        print(f'Failed to retrieve token overview for {address}. Response: {response.status_code}')
        return None


df = pd.read_csv('data/new_launches.csv')

dfs_to_concat = []

for index, row in df.itterrows():
    while True:
        try:
            token_data = token_overview(row['address'], MAX_SELL_PERCENTAGE, MIN_TRADES_LAST_HOUR, MIN_UNIQ_WALLET2HR, MIN_VIEW24H, MIN_LIQUIDITY)
            
            if token_data:
                token_data['address'] = row['address']

                token_data['url'] = f'https://dexscreener.com/solana/{token_data["address"]}'

                token_data.pop('priceChangeXhrs', None)

                temp_df = pd.DataFrame([token_data])

                dfs_to_concat.append(temp_df)

            break
            
        except Exception as e:
            print(f'Failed to get token overview for {row["address"]}. Retrying in 10 seconds...')
            time.sleep(10)
            continue
            
if dfs_to_concat:

    result_df = pd.concat(dfs_to_concat)

    result_df.to_csv('data/new_launches_overview.csv', index=False)

    csv_file_path = 'data/hyper_sorted_so.csv'
    print('New launches overview saved to ata/hyper_sorted_so.csv')

else:
    print('')
    print('No new launches to process')
    print('After Filttering, there are no tokens meeting the criteria.')
    print('Try chaing your parameters or increasing NUM_TOKENS_2SEARCH')