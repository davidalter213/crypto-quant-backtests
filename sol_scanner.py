'''
find 100x potential tokens on solana
i know that only 1 out of 100 will actually be a 100x
AFTER i put in all these filters... still most will go to zero

# using birdeye api for this, but maybe later i can use helius for some
helius could be interesting but for speed purposes im using birdeye
https://docs.helius.dev/compression-and-das-api/digital-asset-standard-das-api/get-asset

Done
[x] get top 200 trending tokens from birdeye
    - their algo aint bad for this, theres some good tokeys
[-] get new tokens from birdeye
    - birdeye has a limit of 10 per call so kinda trash
       - i think i will use it for now, but append new tokens. 
       the better way is probably to use my helius set up i have to listen 
       BUT that will only get newely launched tokens.... not past ones. 
[x] get top traders from birdeye
    - this allows us to see who the whale are on SUPER_CYCLE_TOKENS list below
    - honestly one of the best ways to find ppl or bots to follow is this call 

bots to study - some of these bot have made close to a BILLION dollars. maybe we should look into mev a lil closer.......................................................................................... a billion.
- https://gmgn.ai/sol/address/3HC9tHdnrz9iNsn2o6P6JV1aptmbUZeA8kApzsxuHPfX
- https://gmgn.ai/sol/address/benRLpbWCL8P8t51ufYt522419hGF5zif3CqgWGbEUm
- https://gmgn.ai/sol/address/kpqUj83k4ieDRZjh7HMqrjkb5tkn84xy642t4Zm1WKe
- https://gmgn.ai/sol/address/7rhxnLV8C77o6d8oz26AgK8x8m5ePsdeRawjqvojbjnQ
- https://gmgn.ai/sol/address/MfDuWeqSHEqTFVYZ7LoexgAK9dxk7cy4DFJWjWMGVWa

potential wallets to follow
- https://gmgn.ai/sol/address/CDny4Uns9fsYUeUufVEBh4zosrk7xT2kpGjsBCjUTP9r
'''


NEW_TOKEN_HOURS = 3
SUPER_CYCLE_TOKENS = ['EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm', 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263', '7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr'] # this is the list of tokens im trading this supercycle


import schedule
import time
from CONFIG import *
import pandas as pd
from datetime import datetime, timezone
import watch_txs as w
import analyze_picks as a
import nice_funcs as n 
import time 
from termcolor import colored, cprint 
import moonapicall as moon
import requests
import json



def get_trending_tokens(limit=200):
    url = "https://public-api.birdeye.so/defi/token_trending"
    headers = {
        "accept": "application/json",
        "x-chain": "solana",
        "X-API-KEY": KEY
    }
    
    all_tokens = []
    for offset in range(0, limit, 20):
        params = {
            "sort_by": "rank",
            "sort_type": "asc",
            "offset": offset,
            "limit": min(20, limit - offset)
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            tokens = data.get('data', {}).get('tokens', [])
            for token in tokens:
                all_tokens.append({
                    'address': token.get('address'),
                    'liquidity': token.get('liquidity'),
                    'name': token.get('name'),
                    'volume24hUSD': token.get('volume24hUSD'),
                    'price': token.get('price')
                })
            
            print(colored(f"Obtenidos {len(tokens)} tokens (offset {offset})", "cyan"))
            
            if len(tokens) < 20:
                break
            
            time.sleep(1)  # Pequeña pausa para no sobrecargar la API
            
        except requests.exceptions.RequestException as e:
            print(colored(f"Error al obtener los tokens en tendencia: {e}", "red"))
            break
    
    if all_tokens:
        df = pd.DataFrame(all_tokens)
        
        # Añadir el link de DexScreener
        df['dexscreener_link'] = df['address'].apply(lambda x: f"https://dexscreener.com/solana/{x}")
        
        df.to_csv(BIRDEYE_TRENDING_TOKENS_CSV, index=False)
        print(colored(f"Se guardaron {len(all_tokens)} tokens en tendencia en {BIRDEYE_TRENDING_TOKENS_CSV}", "green"))
    else:
        print(colored("No se encontraron tokens válidos", "red"))

def get_new_tokens():
    url = "https://public-api.birdeye.so/defi/v2/tokens/new_listing"
    headers = {
        "accept": "application/json",
        "x-chain": "solana",
        "X-API-KEY": KEY
    }
    
    end_time = int(time.time())
    start_time = end_time - (NEW_TOKEN_HOURS * 3600)
    
    # Intentar cargar tokens existentes
    try:
        existing_df = pd.read_csv(NEW_TOKEN_HOURS_CSV)
        if not existing_df.empty:
            last_token_time = existing_df['listingTime'].max()
            start_time = max(start_time, int(last_token_time) + 1)
    except FileNotFoundError:
        existing_df = pd.DataFrame()
    
    params = {
        "time_from": start_time,
        "time_to": end_time,
        "limit": 10
    }
    
    print(colored(f"Solicitando tokens nuevos desde {datetime.fromtimestamp(start_time, tz=timezone.utc)} hasta {datetime.fromtimestamp(end_time, tz=timezone.utc)}", "cyan"))
    
    all_new_tokens = []
    
    try:
        while start_time < end_time:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            new_tokens = data.get('data', {}).get('items', [])
            if not new_tokens:
                break
            
            all_new_tokens.extend(new_tokens)
            
            print(colored(f"Obtenidos {len(new_tokens)} tokens nuevos", "cyan"))
            
            last_token_time = new_tokens[-1].get('listingTime', start_time)
            start_time = last_token_time + 1
            params['time_from'] = start_time
            
            time.sleep(1)  # Pequeña pausa para no sobrecargar la API
        
        if all_new_tokens:
            new_df = pd.DataFrame(all_new_tokens)
            new_df['dexscreener_link'] = new_df['address'].apply(lambda x: f"https://dexscreener.com/solana/{x}")
            
            # Combinar con tokens existentes y eliminar duplicados
            combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['address'], keep='last')
            combined_df.to_csv(NEW_TOKEN_HOURS_CSV, index=False)
            
            print(colored(f"Se guardaron {len(new_df)} tokens nuevos en {NEW_TOKEN_HOURS_CSV}", "green"))
            print(colored(f"Total de tokens en el archivo: {len(combined_df)}", "green"))
            
            print(colored(f"Tokens nuevos en esta ejecución:", "cyan"))
            for token in all_new_tokens:
                print(f"Nombre: {token.get('name')}, Símbolo: {token.get('symbol')}, Dirección: {token.get('address')}")
        else:
            print(colored("No se encontraron tokens nuevos en este intervalo", "yellow"))
        
    except requests.exceptions.RequestException as e:
        print(colored(f"Error al obtener los tokens nuevos: {e}", "red"))
        print(colored(f"URL de la solicitud: {response.url}", "yellow"))
        print(colored(f"Respuesta del servidor: {response.text}", "yellow"))

def get_top_traders():
    url = "https://public-api.birdeye.so/defi/v2/tokens/top_traders"
    headers = {
        "accept": "application/json",
        "x-chain": "solana",
        "X-API-KEY": KEY
    }
    
    params = {
        "time_frame": "24h",
        "sort_type": "desc",
        "sort_by": "volume",
        "limit": 10  # Ajustado a 10 como máximo permitido por la API
    }
    
    all_top_traders = []
    
    for token_address in SUPER_CYCLE_TOKENS:
        token_traders = []
        params["address"] = token_address
        
        for offset in range(0, 100, 10):  # Hacemos 10 llamadas para obtener 100 traders
            params["offset"] = offset
            
            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                traders = data.get('data', {}).get('items', [])
                for trader in traders:
                    token_traders.append({
                        'tokenAddress': token_address,
                        'owner': trader.get('owner'),
                        'volume': trader.get('volume'),
                        'trades': trader.get('trade'),
                        'gmgn_link': f"https://gmgn.ai/sol/address/{trader.get('owner')}"
                    })
                
                print(colored(f"Obtenidos {len(traders)} top traders para el token {token_address} (offset {offset})", "cyan"))
                
                if len(traders) < 10:  # Si obtenemos menos de 10, hemos llegado al final
                    break
                
                time.sleep(1)  # Pequeña pausa para no sobrecargar la API
                
            except requests.exceptions.RequestException as e:
                print(colored(f"Error al obtener los top traders para el token {token_address}: {e}", "red"))
                print(colored(f"URL de la solicitud: {response.url}", "yellow"))
                print(colored(f"Respuesta del servidor: {response.text}", "yellow"))
                break
        
        all_top_traders.extend(token_traders)
        print(colored(f"Total de top traders obtenidos para el token {token_address}: {len(token_traders)}", "green"))
    
    if all_top_traders:
        df = pd.DataFrame(all_top_traders)
        df.to_csv(TOP_TRADERS_BIRDEYE_CSV, index=False)
        print(colored(f"Se guardaron {len(all_top_traders)} top traders en {TOP_TRADERS_BIRDEYE_CSV}", "green"))
    else:
        print(colored("No se encontraron top traders", "yellow"))

# Llamar a todas las funciones
# get_trending_tokens(200)
# get_new_tokens()
get_top_traders()
