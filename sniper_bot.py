from termcolor import colored, cprint 
from config import *
import warnings
warnings.filterwarnings('ignore')
# OUR ADDRESS WE SNIPING FROM
address = our_solana_address
USDC_SIZE = usdc_size_per_sniper  # Your investment size in USDC for each token
MAX_POSITIONS = max_amount_of_open_positions
dont_trade_list = DO_NOT_TRADE_LIST # Add any other addresses you want to exclude


sell_at_multiple = sell_when_hits_this_multiplier # so when a token 4x's we sell 80%
sell_amount_perc = percentage_of_tokens_to_sell # THIS IS THE BETTER ALGO THEN TRYING TO DO THE MATH BELOW

# DROP IF NO SOCIALS, or some socials, set which ones below to t/f
DROP_IF_NO_WEBSITE = should_we_drop_if_no_website
DROP_IF_NO_TWITTER = should_we_drop_if_no_twitter
DROP_IF_NO_TELEGRAM = should_we_drop_if_no_telegram
ONLY_KEEP_ACTIVE_WEBSITES = only_keep_tokens_with_active_websites_if_they_have_one  # Set to True to only keep active websites, Warning: this slows things alot cause it will try for 60 seconds to connect

# SECURITY CHECKS
MAX_TOP10_HOLDER_PERCENT = top10_holder_percent_max # if the top10HolderPercent is greater than this, we will not buy
DROP_IF_MUTABLE_METADATA = drop_if_mutable_metadata  # if the token has mutable metadata, we will not buy
DROP_IF_2022_TOKEN_PROGRAM = drop_if_2022_token_program # "isToken2022": true,  # ADDING CAUSE THE 2022 TOKEN PROGRAM GIVES ERRORS (see readme)

# TOKEN MINT ADDRESS = SYMBOL (below mint is just for testing and USDC does not change)
token_mint_address = "5SuHxgTNE8cbCoK4gfQ7LxpiKgrkENVEQmq78FoAr6La" # just for testing
usdc_contract_address = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'

import math, os
import requests
import pandas as pd
import time 
import dontshare as d   
import json

import nice_funcs as n
import schedule
from datetime import datetime 



from io import StringIO


def ask_bid(token_mint_address):

    ''' this returns the price '''

    API_KEY = d.birdeye
    
    url = f"https://public-api.birdeye.so/defi/price?address={token_mint_address}"
    headers = {"X-API-KEY": API_KEY}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        json_response = response.json()  # Parse the JSON response
        if 'data' in json_response and 'value' in json_response['data']:
            return json_response['data']['value']  # Return the price value
        else:
            return "Price information not available"  # Return a message if 'data' or 'value' is missing
    else:
        return None  # Return None if there's an error with the API call


def check_website(url):
    ''' this checks the website to make sure it's running, with a 5-second timeout '''
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return True, f"Website {url} is up and running!"
        else:
            return True, f"Website {url} is reachable but returned a status code of {response.status_code}."
    except requests.exceptions.RequestException as e:
        return False, f"Website {url} could not be reached within 5 seconds. Error: {e}"



def security_check(address):

    ''' gets the security check for a token based on birdeye info and returns it in json
    
    decide which to use as filters... 
    - top10HolderPercent > .3 ... be out... this can be a VARIABLE

    {
  "data": {
    "creatorAddress": "8LAnvxpF7kL1iUjDRjmP87xiuyCx4yX3ZRAoDCChKe1L",
    "creatorOwnerAddress": null,
    "ownerAddress": null,
    "ownerOfOwnerAddress": null,
    "creationTx": "48PniJegRijm7wcm8Ygzw9hDC6fysYrXRr5D1UUcuqUTS8B16Le7A8tvWFLoPYvNSaSyfiynhkz8WFfKJbmhwgcp",
    "creationTime": 1702086574,
    "creationSlot": 234822271,
    "mintTx": "48PniJegRijm7wcm8Ygzw9hDC6fysYrXRr5D1UUcuqUTS8B16Le7A8tvWFLoPYvNSaSyfiynhkz8WFfKJbmhwgcp",
    "mintTime": 1702086574,
    "mintSlot": 234822271,
    "creatorBalance": 22.053403028,
    "ownerBalance": null,
    "ownerPercentage": null,
    "creatorPercentage": 2.2054864219584144e-8,
    "metaplexUpdateAuthority": "8LAnvxpF7kL1iUjDRjmP87xiuyCx4yX3ZRAoDCChKe1L",
    "metaplexOwnerUpdateAuthority": null,
    "metaplexUpdateAuthorityBalance": 22.053403028,
    "metaplexUpdateAuthorityPercent": 2.2054864219584144e-8,
    "mutableMetadata": false,
    "top10HolderBalance": 937114842.9086457,
    "top10HolderPercent": 0.9371769332953355,
    "top10UserBalance": 937114842.9086457,
    "top10UserPercent": 0.9371769332953355,
    "isTrueToken": null,
    "totalSupply": 999933747.4232626,
    "preMarketHolder": [],
    "lockInfo": null,
    "freezeable": null,
    "freezeAuthority": null,
    "transferFeeEnable": null,
    "transferFeeData": null,
    "isToken2022": false,
    "nonTransferable": null
  },
  "success": true,
  "statusCode": 200
}

    '''

    API_KEY = d.birdeye

    url = f"https://public-api.birdeye.so/defi/token_security?address={address}"
    headers = {"X-API-KEY": API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        security_data = response.json()  # Return the JSON response if the call is successful
        if security_data and 'data' in security_data:
            # In the context of this code, get('freezeable', False) serves to handle cases where the key 'freezeable' might not be present in the JSON data. 
            # Here’s why False is used as the default:
            # Safe Default: Using False ensures that if the 'freezeable' key is absent, the code will not mistakenly consider the token to be freezeable. 
            # It assumes a non-freezeable state unless explicitly indicated otherwise.
            if security_data['data'].get('freezeable', False):  # Check if the token is freezeable
                print(f"* {address[-4:]} is freezeable. Dropping.")
                return None  # Return None to indicate the token should be dropped
        return security_data
    else:
        return None  # Return None if there's an error with the API call

def extract_urls(description):
    urls = {'twitter': None, 'website': None, 'telegram': None}
    if description and description != "[]":
        try:
            # Assuming the description is a string representation of a list of dicts
            links = json.loads(description.replace("'", '"'))
            for link in links:
                for key, value in link.items():
                    if 'twitter' in key or 'twitter.com' in value or 'x.com' in value:
                        urls['twitter'] = value
                    elif 'telegram' in key:
                        urls['telegram'] = value
                    elif 'website' in key:
                        # Assuming any other link that doesn't include 't.me' is a website
                        if 't.me' not in value:
                            urls['website'] = value
        except json.JSONDecodeError:
            print(f"Error decoding JSON from description: {description}")
    return urls

def token_price(address):
    API_KEY = d.birdeye
    url = f"https://public-api.birdeye.so/defi/price?address={address}"
    headers = {"X-API-KEY": API_KEY}
    response = requests.get(url, headers=headers)
    price_data = response.json()
    
    if price_data['success']:
        return price_data['data']['value']
    else:
        return None

# this function is getting things ready to buy
def buying_df():

    if not os.path.exists(FINAL_SORTED_CSV):
        print(f'No {FINAL_SORTED_CSV} found. Returning an empty DataFrame.')
        # Create an empty DataFrame with specified columns and save to READY_TO_BUY_CSV
        empty_df = pd.DataFrame(columns=[
            'address', 'buy1h', 'sell1h', 'trade1h', 'buy_percentage', 'sell_percentage', 'liquidity',
            'description', 'url', 'usdc_price', 'BUY_AMOUNT', 'TWITTER', 'WEBSITE', 'TELEGRAM'])
        empty_df.to_csv(READY_TO_BUY_CSV, index=False)
        return empty_df

    # Load the CSV into a DataFrame
    df = pd.read_csv(FINAL_SORTED_CSV)

    # New column headers that you want to assign
    new_columns = [
        'address',
        'buy1h',
        'sell1h',
        'trade1h',
        'buy_percentage',
        'sell_percentage',
        'liquidity',
        'description',
        'url'
    ]

    additional_columns = df.columns[len(new_columns):]  # Get any columns beyond the length of new_columns
    new_columns.extend(additional_columns)  # Append the additional column names to the new column list

    # Ensure we now have the correct number of column names
    assert len(new_columns) == len(df.columns), "The number of new column names must match the number of existing DataFrame columns."

    # Assign the new column names to the DataFrame
    df.columns = new_columns

    # Save the DataFrame back to CSV
    df.to_csv(FINAL_SORTED_CSV, index=False)

    # Add new columns to the DataFrame
    df['usdc_price'] = None
    df['BUY_AMOUNT'] = None
    df['TWITTER'] = None
    df['WEBSITE'] = None
    df['TELEGRAM'] = None

    # Loop through address column and update the DataFrame
    for index, row in df.iterrows():
        token_address = row['address']
        price = token_price(token_address)

        if price is not None:
            # Add the price to the df
            df.at[index, 'usdc_price'] = price
            # Calculate buy amount based on USDC_SIZE
            df.at[index, 'BUY_AMOUNT'] = USDC_SIZE / price

        # Extract URLs from the description
        urls = extract_urls(row['description'])
        df.at[index, 'TWITTER'] = urls['twitter']
        df.at[index, 'WEBSITE'] = urls['website']
        df.at[index, 'TELEGRAM'] = urls['telegram']

        # Extract URLs from the description
        urls = extract_urls(row['description'])
        df.at[index, 'TWITTER'] = urls['twitter']
        df.at[index, 'WEBSITE'] = urls['website']
        df.at[index, 'TELEGRAM'] = urls['telegram']

        # Check the website status only if a website URL is provided
        if urls['website']:  # This checks if the 'website' key exists and is not empty
            active, message = check_website(urls['website'])
            print(message)  # Print the status message for the website

            # Conditional drop based on the website's status
            # Drop the row only if there is a website and it is not active
            if ONLY_KEEP_ACTIVE_WEBSITES and not active:
                df.drop(index, inplace=True)
                continue

        security_data = security_check(token_address)
        # If security data is None, skip the row
        if not security_data:
            cprint(f"*  {token_address[-2:]} security none, dropping.", 'white', 'on_magenta')
            df.drop(index, inplace=True)
            continue

        # Check for top10HolderPercent and mutableMetadata conditions
        if security_data['data']['top10HolderPercent'] > MAX_TOP10_HOLDER_PERCENT:
            top10per = round(float(security_data['data']['top10HolderPercent']), 2)
            cprint(f"* {token_address[-2:]} has a top10HolderPercent of {top10per}. dropping.", 'white', 'on_magenta')
            df.drop(index, inplace=True)
            continue  # Skip further processing for this row if dropping
        if DROP_IF_MUTABLE_METADATA and security_data['data']['mutableMetadata']:
            cprint(f"* {token_address[-2:]} has mutable metadata. dropping.", 'white', 'on_magenta')
            df.drop(index, inplace=True)
            continue  # Skip further processing for this row if dropping
        #DROP_IF_2022_TOKEN_PROGRAM = True # "isToken2022": true,  # ADDING CAUSE THE 2022 TOKEN PROGRAM GIVES ERRORS (see readme)
        if DROP_IF_2022_TOKEN_PROGRAM and security_data['data']['isToken2022']:
            cprint(f"* {token_address[-2:]} is a 2022 token program. dropping.", 'white', 'on_magenta')
            df.drop(index, inplace=True)
            continue
        else:
            #cprint(f'mutable metadata is {security_data["data"]["mutableMetadata"]} and top10HolderPercent is {security_data["data"]["top10HolderPercent"]}', 'white', 'on_blue')
            nummm = 'hi'

        # Be mindful of the API's rate limit
        time.sleep(1)  # Adjust the sleep time according to the API's requirements

     # Conditional row drops
    if DROP_IF_NO_WEBSITE:
        df = df.drop(df[df['WEBSITE'].isnull()].index)
    if DROP_IF_NO_TWITTER:
        df = df.drop(df[df['TWITTER'].isnull()].index)
    if DROP_IF_NO_TELEGRAM:
        df = df.drop(df[df['TELEGRAM'].isnull()].index)

    # Drop the description column
    df = df.drop(columns=['description'])

    # Save the updated DataFrame to a new CSV file
    df.to_csv(READY_TO_BUY_CSV, index=False)

    #print(df)

    return df 

import math
def round_down(value, decimals):
    factor = 10 ** decimals
    return math.floor(value * factor) / factor

def kill_switch(token_mint_address):

    ''' this function closes the position in full  '''

    # if time is on the 5 minute do the balance check, if not grab from data/current_position.csv
    balance = get_position(token_mint_address)

    # get current price of token 
    price = token_price(token_mint_address)

    usd_value = balance * price

    tp = sell_at_multiple * USDC_SIZE
    sell_size = balance 
    # round to 2 decimals
    sell_size = round_down(sell_size, 2)
    decimals = 0
    decimals = get_decimals(token_mint_address)
    #print(f'for {token_mint_address[-4:]} decimals is {decimals}')

    sell_size = int(sell_size * 10 **decimals)
    
    #print(f'bal: {balance} price: {price} usdVal: {usd_value} TP: {tp} sell size: {sell_size} decimals: {decimals}')

    while usd_value > 0:

        # log this mint address to a file and save as a new line, keep the old lines there, so it will continue to grow this file is called data/closed_positions.txt
        # only add it to the file if it's not already there
        with open(CLOSED_POSITIONS_TXT, 'r') as f:
            lines = [line.strip() for line in f.readlines()]  # Strip the newline character from each line
            if token_mint_address not in lines:  # Now the comparison should work as expected
                with open(CLOSED_POSITIONS_TXT, 'a') as f:
                    f.write(token_mint_address + '\n')

# 100 selling 70% ...... selling 30 left
        #print(f'for {token_mint_address[-4:]} closing position cause exit all positions is set to {EXIT_ALL_POSITIONS} and value is {usd_value} and tp is {tp} so closing...')
        try:

            n.market_sell(token_mint_address, sell_size)
            cprint(f'just made an order {token_mint_address[-4:]} selling {sell_size} ...', 'white', 'on_blue')
            time.sleep(1)
            n.market_sell(token_mint_address, sell_size)
            cprint(f'just made an order {token_mint_address[-4:]} selling {sell_size} ...', 'white', 'on_blue')
            time.sleep(1)
            n.market_sell(token_mint_address, sell_size)
            cprint(f'just made an order {token_mint_address[-4:]} selling {sell_size} ...', 'white', 'on_blue')
            time.sleep(15)
            
        except:
            cprint('order error.. trying again', 'white', 'on_red')
            # time.sleep(7)

        balance = get_position(token_mint_address)
        price = token_price(token_mint_address)
        usd_value = balance * price
        tp = sell_at_multiple * USDC_SIZE
        sell_size = balance 
        
        # down downwards to 2 decimals
        sell_size = round_down(sell_size, 2)
        
        decimals = 0
        decimals = get_decimals(token_mint_address)
        #print(f'xxxxxxxxx for {token_mint_address[-4:]} decimals is {decimals}')
        sell_size = int(sell_size * 10 **decimals)
        #print(f'balance is {balance} and usd_value is {usd_value} EXIT ALL POSITIONS TRUE and sell_size is {sell_size} decimals is {decimals}')


    else:
        print(f'for {token_mint_address[-4:]} value is {usd_value} ')
        #time.sleep(10)

    print('closing position in full...')

def close_all_positions():

    # get all positions
    open_positions = fetch_wallet_holdings_og(address)

    # loop through all positions and close them getting the mint address from Mint Address column
    for index, row in open_positions.iterrows():
        token_mint_address = row['Mint Address']

        # Check if the current token mint address is the USDC contract address
        #cprint(f'this is the token mint address {token_mint_address} this is don not trade list {dont_trade_list}', 'white', 'on_magenta')
        if token_mint_address in dont_trade_list:
            #print(f'Skipping kill switch for USDC contract at {token_mint_address}')
            continue  # Skip the rest of the loop for this iteration

        print(f'Closing position for {token_mint_address}...')
        kill_switch(token_mint_address)

def pnl_close(token_mint_address):

    ''' this will check to see if price is > sell 1, sell 2, sell 3 and sell accordingly '''

    #print('checking pnl close to see if its time to exit')
    # check solana balance
    

    # if time is on the 5 minute do the balance check, if not grab from data/current_position.csv
    balance = get_position(token_mint_address)
    
    # save to data/current_position.csv w/ pandas

    # get current price of token 
    price = token_price(token_mint_address)

    try:
        usd_value = float(balance) * float(price)
    except:
        usd_value = 0

    tp = sell_at_multiple * USDC_SIZE
    sl = ((1+stop_loss_percentage) * USDC_SIZE)
    sell_size = balance * sell_amount_perc
    decimals = 0
    decimals = get_decimals(token_mint_address)
    #print(f'for {token_mint_address[-4:]} decimals is {decimals}')

    sell_size = int(sell_size * 10 **decimals)
    
    #print(f'bal: {balance} price: {price} usdVal: {usd_value} TP: {tp} sell size: {sell_size} decimals: {decimals}')

    while usd_value > tp:

        # log this mint address to a file and save as a new line, keep the old lines there, so it will continue to grow this file is called data/closed_positions.txt
        # only add it to the file if it's not already there
        with open(CLOSED_POSITIONS_TXT, 'r') as f:
            lines = [line.strip() for line in f.readlines()]  # Strip the newline character from each line
            if token_mint_address not in lines:  # Now the comparison should work as expected
                with open(CLOSED_POSITIONS_TXT, 'a') as f:
                    f.write(token_mint_address + '\n')

        cprint(f'for {token_mint_address[-4:]} value is {usd_value} and tp is {tp} so closing...', 'white', 'on_green')
        try:

            n.market_sell(token_mint_address, sell_size)
            cprint(f'just made an order {token_mint_address[-4:]} selling {sell_size} ...', 'white', 'on_green')
            time.sleep(1)
            n.market_sell(token_mint_address, sell_size)
            cprint(f'just made an order {token_mint_address[-4:]} selling {sell_size} ...', 'white', 'on_green')
            time.sleep(1)
            n.market_sell(token_mint_address, sell_size)
            cprint(f'just made an order {token_mint_address[-4:]} selling {sell_size} ...', 'white', 'on_green')
            time.sleep(15)
            
        except:
            cprint('order error.. trying again', 'white', 'on_red')
            # time.sleep(7)

        balance = get_position(token_mint_address)
        price = token_price(token_mint_address)
        usd_value = balance * price
        tp = sell_at_multiple * USDC_SIZE
        sell_size = balance * sell_amount_perc
        # decimals = 0
        # decimals = get_decimals(token_mint_address)
        #print(f'xxxxxxxxx for {token_mint_address[-4:]} decimals is {decimals}')
        sell_size = int(sell_size * 10 **decimals)
        print(f'USD Value is {usd_value} | TP is {tp} ')


    else:
        #print(f'for {token_mint_address[-4:]} value is {usd_value} and tp is {tp} so not closing...')
        hi = 'hi'
        #time.sleep(10)

    # while usd_value < sl but bigger than .05

    if usd_value != 0:
        #print(f'for {token_mint_address[-4:]} value is {usd_value} and sl is {sl} so not closing...')

        while usd_value < sl and usd_value > 0:

            sell_size = balance 
            sell_size = int(sell_size * 10 **decimals)

            cprint(f'for {token_mint_address[-4:]} value is {usd_value} and sl is {sl} so closing as a loss...', 'white', 'on_blue')
            print(token_mint_address)
            # log this mint address to a file and save as a new line, keep the old lines there, so it will continue to grow this file is called data/closed_positions.txt
            # only add it to the file if it's not already there
            with open(CLOSED_POSITIONS_TXT, 'r') as f:
                lines = [line.strip() for line in f.readlines()]  # Strip the newline character from each line
                if token_mint_address not in lines:  # Now the comparison should work as expected
                    with open(CLOSED_POSITIONS_TXT, 'a') as f:
                        f.write(token_mint_address + '\n')

            #print(f'for {token_mint_address[-4:]} value is {usd_value} and tp is {tp} so closing...')
            try:

                n.market_sell(token_mint_address, sell_size)
                cprint(f'just made an order {token_mint_address[-4:]} selling {sell_size} ...', 'white', 'on_blue')
                time.sleep(1)
                n.market_sell(token_mint_address, sell_size)
                cprint(f'just made an order {token_mint_address[-4:]} selling {sell_size} ...', 'white', 'on_blue')
                time.sleep(1)
                n.market_sell(token_mint_address, sell_size)
                cprint(f'just made an order {token_mint_address[-4:]} selling {sell_size} ...', 'white', 'on_blue')
                time.sleep(1)
                time.sleep(15)
                
            except:
                cprint('order error.. trying again', 'white', 'on_red')
                # time.sleep(7)

            balance = get_position(token_mint_address)
            price = token_price(token_mint_address)
            usd_value = balance * price
            tp = sell_at_multiple * USDC_SIZE
            sl = ((1+stop_loss_percentage) * USDC_SIZE)
            sell_size = balance 
            # decimals = 0
            # decimals = get_decimals(token_mint_address)
            #print(f'xxxxxxxxx for {token_mint_address[-4:]} decimals is {decimals}')
            sell_size = int(sell_size * 10 **decimals)
            print(f'balance is {balance} and price is {price} and usd_value is {usd_value} and tp is {tp} and sell_size is {sell_size} decimals is {decimals}')

            # break the loop if usd_value is 0
            if usd_value == 0:
                print(f'successfully closed {token_mint_address[-4:]} usd_value is {usd_value} so breaking loop...')


                break


        else:
            print(f'for {token_mint_address[-4:]} value is {usd_value} and tp is {tp} so not closing...')
            time.sleep(10)
    else:
        print(f'for {token_mint_address[-4:]} value is {usd_value} and tp is {tp} so not closing...')
        time.sleep(10)

def fetch_wallet_holdings_og(address):

    API_KEY = d.birdeye  # Assume this is your API key; replace it with the actual one

    # Initialize an empty DataFrame
    df = pd.DataFrame(columns=['Mint Address', 'Amount', 'USD Value'])

    url = f"https://public-api.birdeye.so/v1/wallet/token_list?wallet={address}"
    headers = {"x-chain": "solana", "X-API-KEY": API_KEY}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        json_response = response.json()

        if 'data' in json_response and 'items' in json_response['data']:
            df = pd.DataFrame(json_response['data']['items'])
            #print(df.columns)
            #print(df)
            
            # # do about but as floats
            # df['uiAmount'] = df['uiAmount'].astype(float)
            # df['balance'] = df['balance'].astype(float)

            # df['valueUsd'] = df['uiAmount'] * df['balance']

            # print(df)
            # print(df.columns)

            df = df[['address', 'uiAmount', 'valueUsd']]
            df = df.rename(columns={'address': 'Mint Address', 'uiAmount': 'Amount', 'valueUsd': 'USD Value'})
            df = df.dropna()
            df = df[df['USD Value'] > 0.05]
        else:
            cprint("No data available in the response.", 'white', 'on_red')

    else:
        cprint(f"Failed to retrieve token list for {address[-3:]}.", 'white', 'on_magenta')
        time.sleep(10)

 
    # drop any row that is on the do not trade list
    # but keep these two tokens 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v' and Solana contract address
    
    # Addresses to exclude from the "do not trade list"
    exclude_addresses = ['EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v', 'So11111111111111111111111111111111111111112']

    # Update the "do not trade list" by removing the excluded addresses
    updated_dont_trade_list = [mint for mint in dont_trade_list if mint not in exclude_addresses]

    # Filter the dataframe
    for mint in updated_dont_trade_list:
        df = df[df['Mint Address'] != mint]


    # Print the DataFrame if it's not empty
    if not df.empty:
        
        # Save the filtered DataFrame to a CSV file
        TOKEN_PER_ADDY_CSV = 'filtered_wallet_holdings.csv'  # Define your CSV file name
        df.to_csv(TOKEN_PER_ADDY_CSV, index=False)
        # update the df so Mint_address so it's just the last 2
        
        df2 = get_names_nosave(df.copy())
        #df['Mint Address'] = df['Mint Address'].str[-4:]
        # print the df in reverse
        #df2 = df2.iloc[::-1]
        print('')
        #print(df2.tail(20))
        print(df2.head(20))
        # Assuming cprint is a function you have for printing in color
        print('moondev.sol wallet started march 2024')
        cprint(f'** Starting: 200 | Current: ${round(df2["USD Value"].sum(),2)}', 'white', 'on_green')
        print(' ')
        time.sleep(7)
    else:
        # If the DataFrame is empty, print a message or handle it as needed
        cprint("No wallet holdings to display.", 'white', 'on_red')
        time.sleep(30)

    return df





def fetch_wallet_token_single(address, token_mint_address):
    
    df = fetch_wallet_holdings_og(address)

    # filter by token mint address
    df = df[df['Mint Address'] == token_mint_address]

    return df





def fetch_wallet_holdings(address):
    
    df = pd.read_csv(TOKEN_PER_ADDY_CSV)
    
    return df

# fetch_wallet_holdings(address)
# time.sleep(8888)

def get_position(token_mint_address):
    """
    Fetches the balance of a specific token given its mint address from a DataFrame.

    Parameters:
    - dataframe: A pandas DataFrame containing token balances with columns ['Mint Address', 'Amount'].
    - token_mint_address: The mint address of the token to find the balance for.

    Returns:
    - The balance of the specified token if found, otherwise a message indicating the token is not in the wallet.
    """
    dataframe = fetch_wallet_token_single(address, token_mint_address)

    #dataframe = pd.read_csv('data/token_per_addy.csv')

    print('-----------------')
    #print(dataframe)

    #print(dataframe)

    # Check if the DataFrame is empty
    if dataframe.empty:
        print("The DataFrame is empty. No positions to show.")
        time.sleep(5)
        return 0  # Indicating no balance found

    # Ensure 'Mint Address' column is treated as string for reliable comparison
    dataframe['Mint Address'] = dataframe['Mint Address'].astype(str)

    # Check if the token mint address exists in the DataFrame
    if dataframe['Mint Address'].isin([token_mint_address]).any():
        # Get the balance for the specified token
        balance = dataframe.loc[dataframe['Mint Address'] == token_mint_address, 'Amount'].iloc[0]
        #print(f"Balance for {token_mint_address[-4:]} token: {balance}")
        return balance
    else:
        # If the token mint address is not found in the DataFrame, return a message indicating so
        print("Token mint address not found in the wallet.")
        return 0  # Indicating no balance found



def get_decimals(token_mint_address):
    import requests
    import base64
    import json
    # Solana Mainnet RPC endpoint
    url = "https://api.mainnet-beta.solana.com/"
    
    headers = {"Content-Type": "application/json"}

    # Request payload to fetch account information
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getAccountInfo",
        "params": [
            token_mint_address,
            {
                "encoding": "jsonParsed"
            }
        ]
    })

    # Make the request to Solana RPC
    response = requests.post(url, headers=headers, data=payload)
    response_json = response.json()

    # Parse the response to extract the number of decimals
    decimals = response_json['result']['value']['data']['parsed']['info']['decimals']
    #print(f"Decimals for {token_mint_address[-4:]} token: {decimals}")

    return decimals



def get_bal_birdeye(address):

    API_KEY = d.birdeye

    print(f'getting balance for {address}...')
    url = f"https://public-api.birdeye.so/v1/wallet/token_list?wallet={address}"

    headers = {"x-chain": "solana", "X-API-KEY": API_KEY}
    response = requests.get(url, headers=headers)

    #print(response.text)
    json_response = response.json()
    #print(json_response['data'])

    # output to a json in data folder
    with open('data/bal_birdeye.json', 'w') as f:
        json.dump(json_response, f)


def update_market_prices():
    # Load the existing positions
    open_positions = pd.read_csv(TOKEN_PER_ADDY_CSV)

    for index, row in open_positions.iterrows():
        token_mint_address = row['Mint Address']
        # Fetch the latest market price for the token
        current_price = ask_bid(token_mint_address)

        # Update the 'current_market_price' column with the latest price
        open_positions.loc[index, 'current_market_price'] = current_price

    # Save the updated DataFrame back to the CSV
    open_positions.to_csv(TOKEN_PER_ADDY_CSV, index=False)
    print('Market prices updated for all tokens.')


# n.market_buy('7HXQEwsbf43PA1GVJrjRmvYefm6RQ8bdsoDKA9dfDfbx', '1000000')
# time.sleep(7867)
def open_position(token_mint_address):

    ''' this will loop unitl the position is full, it uses the get_token_balance til its full '''

    cprint(f'opening position for {token_mint_address}...', 'white', 'on_blue')

    balance = get_position(token_mint_address) # problematic 
    buying_df = pd.read_csv(READY_TO_BUY_CSV)
    
    # only grab the row with the token_mint_address in it and turn it into a json key/value pair
    token_info = buying_df[buying_df['address'] == token_mint_address].to_dict(orient='records')[0]
    #print(token_info)
    token_size = USDC_SIZE # setting this to usdc size cause the the buying_df is in token amounts not usd
    # float token size and balance
    
    token_size = float(token_size) # usdc amount since orders are in usdc / changed in buying_df()

    price = ask_bid(token_mint_address)
    
    balance = price * balance # this converts the balance to usddc

    balance = float(balance)

    size_needed = token_size - balance

    print(f'****** token size {token_size} price is {price} and balance is {balance} and size is {token_size}')

    with open(CLOSED_POSITIONS_TXT, 'r') as f:
        closed_positions = [line.strip() for line in f.readlines()]
    # closed_positions.txt acts as our black list

    # Check if the token mint address is not in the stripped lines of data/closed_positions.txt
    if token_mint_address not in closed_positions:

        while balance < (.9 * token_size):

            print(f'**Filling Position for {token_mint_address[-4:]} : balance is {balance} and size is {token_size} size needed: {size_needed}')


            # FIGURE OUT THE DECIMALS FOR THE SELL OR WE MAY SELL A 9 DIGIT AT 6 DIGIT and RUN OUT OF SOL
            try:
                size_needed = int(size_needed * 10**6)
                size_needed = str(size_needed)
                print(f'buying this amount {size_needed} for {token_mint_address}')

                for i in range(orders_per_open):
                    order = n.market_buy(token_mint_address, size_needed)
                    cprint(f'just made an order {token_mint_address[-4:]} of size: {size_needed}', 'white', 'on_blue')

                    time.sleep(1)
            except:

                try:
                    cprint(f'trying again to make the order in 30 seconds.....', 'light_blue', 'on_light_magenta')

                    time.sleep(30)
                    print(f'buying this amount {size_needed} for {token_mint_address}')

                    for i in range(orders_per_open):
                        order = n.market_buy(token_mint_address, size_needed)
                        cprint(f'just made an order {token_mint_address[-4:]} of size: {size_needed}', 'white', 'on_blue')
                        time.sleep(1)

                except:
                    cprint('error in buy ---- the next print saying filled isnt true but good cuz logged to closed_positions.txt to not trade again.', 'white', 'on_red')
                    time.sleep(3)
                # current bug - if the order fails, it will never attempt to get back in. need to thnk of a way to handle this and not logged to closed_positions here 
                    break 
            # added this break here and now it assumes filliwe filled n puts on closed_positions.txt so we dont trade again
                

            price = ask_bid(token_mint_address)
            time.sleep(1)
            token_size = float(token_size)
            balance = get_position(token_mint_address)
            balance = float(balance)
            balance = price * balance # this converts the balance to usddc
            size_needed = token_size - balance
            print(f'22****** token size {token_size} price is {price} and balance is {balance} and size is {token_size} ')
    else:
        print('we have already opened OR closed that poistion so not opening again...')
        time.sleep(5)

    print(f'fully filled our position... ')

    with open(CLOSED_POSITIONS_TXT, 'a') as file:  # 'a' mode for appending to the file
        file.write(f'{token_mint_address}\n')  #

    price = ask_bid(token_mint_address)
    
    open_positions = fetch_wallet_holdings_og(address)

    # Check if 'open_price' column exists, if not create it with NaN values
    if 'open_price' not in open_positions.columns:
        open_positions['open_price'] = float('nan')

    # Update 'open_price' only if it's NaN for the specified 'token_mint_address'
    condition = (open_positions['Mint Address'] == token_mint_address) & open_positions['open_price'].isnull()
    open_positions.loc[condition, 'open_price'] = price

    open_positions.to_csv(TOKEN_PER_ADDY_CSV, index=False)


def get_token_overview(address):
    API_KEY = d.birdeye
    url = f"https://public-api.birdeye.so/defi/token_overview?address={address}"
    headers = {"X-API-KEY": API_KEY}
    response = requests.get(url, headers=headers)
    if response.ok:
        json_response = response.json()
        return json_response['data']
    else:
        # Return empty dict if there's an error
        print(f"Error fetching data for address {address}: {response.status_code}")
        return {}

# This function will iterate through addresses in the dataframe, fetch their information, and store their name(s)
def get_names(df):
    names = []  # List to hold the collected names

    for index, row in df.iterrows():
        token_mint_address = row['address']
        token_data = get_token_overview(token_mint_address)
        time.sleep(2)
        
        # Extract the token name using the 'name' key from the token_data
        token_name = token_data.get('name', 'N/A')  # Use 'N/A' if name isn't provided
        print(f'Name for {token_mint_address[-4:]}: {token_name}')
        names.append(token_name)
    
    # Check if 'name' column already exists, update it if it does, otherwise insert it
    if 'name' in df.columns:
        df['name'] = names  # Update existing 'name' column
    else:
        df.insert(0, 'name', names)  # Insert 'name' as the first column

    # Save df to vibe_check.csv
    df.to_csv(READY_TO_BUY_CSV, index=False)
    
    return df

def get_names_nosave(df):
    names = []  # List to hold the collected names

    for index, row in df.iterrows():
        token_mint_address = row['Mint Address']
        token_data = get_token_overview(token_mint_address)
        
        # Extract the token name using the 'name' key from the token_data
        token_name = token_data.get('name', 'N/A')  # Use 'N/A' if name isn't provided
        #print(f'Name for {token_mint_address[-4:]}: {token_name}')
        names.append(token_name)
    
    # Check if 'name' column already exists, update it if it does, otherwise insert it
    if 'name' in df.columns:
        df['name'] = names  # Update existing 'name' column
    else:
        df.insert(0, 'name', names)  # Insert 'name' as the first column

    # drop the Mint_Address
    df.drop('Mint Address', axis=1, inplace=True)
    df.drop('Amount', axis=1, inplace=True)

    #print(df)
    
    return df

import ccxt
import pandas as pd

def is_price_below_41_sma(symbol='ETH/USD'):
    # Initialize the exchange
    exchange = ccxt.kraken()
    exchange.load_markets()

    # Fetch daily OHLCV data for the last 200 days
    daily_ohlcv = exchange.fetch_ohlcv(symbol, '1d', limit=200)
    df = pd.DataFrame(daily_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    # Calculate the 40-day SMA
    df['41_sma'] = df['close'].rolling(window=41).mean()

    # Check if the last daily close is below the 40-day SMA
    last_close = df.iloc[-2]['close']
    last_sma = df.iloc[-1]['41_sma']

    #print(df)
    print(f'Last close: {last_close}, Last 41-day SMA: {last_sma}')
    
    return last_close < last_sma

# Usage in bot:
def bot():

    from ohlcv_filter import ohlcv_bot

    # Get the current time
    now = datetime.now()
    cprint(f'live bot running at {now}', 'white', 'on_green')

    # # Check if the ETH price is below the 40-day SMA
    # while is_price_below_41_sma('ETH/USD'):
    #     #print(f'The last daily close is below the 40-day SMA so setting EXIT_ALL_POSITIONS to True...')
    #     # cprint the above
    #     cprint(f'The last daily close is below the 40-day SMA so setting EXIT_ALL_POSITIONS to True...', 'white', 'on_blue')
    #     time.sleep(2)
    #     close_all_positions()
    #     open_positions_df = fetch_wallet_holdings_og(address)
    #     print(open_positions_df)
    #     # Add here whatever logic you need when exit_all_positions is True
    

    # checking if need to kill all positions
    while EXIT_ALL_POSITIONS:
        cprint(f'exiting all positions bc EXIT_ALL_POSITIONS is set to {EXIT_ALL_POSITIONS}', 'white', 'on_magenta')
        close_all_positions()
        open_positions_df = fetch_wallet_holdings_og(address)
        #print(open_positions_df)

 
    #print('trying to get sol df')
    time.sleep(10)
    # PNL CLOSE FIRST
    open_positions_df = fetch_wallet_holdings_og(address)
    #print(open_positions_df)

    # in df if mint_address = So11111111111111111111111111111111111111111 and Amount < .001 cprint red error, sleep for 5 minutes
    sol_df = open_positions_df[open_positions_df['Mint Address'] == 'So11111111111111111111111111111111111111111']

    # if sol_df is empty, sleep for 30 then try above again
    if sol_df.empty:
        cprint('😅 SOL BALANCE EMPTY... if happens lots, fix', 'white', 'on_magenta')
        time.sleep(30)
        open_positions_df = fetch_wallet_holdings_og(address)
        #print(open_positions_df)

        # in df if mint_address = So11111111111111111111111111111111111111111 and Amount < .001 cprint red error, sleep for 5 minutes
        sol_df = open_positions_df[open_positions_df['Mint Address'] == 'So11111111111111111111111111111111111111111']


    while sol_df['Amount'].values < .005:
        cprint('ERROR: SOL BALANCE IS LESS THAN .005', 'white', 'on_red')
        time.sleep(20)

        sol_df = fetch_wallet_token_single(address, 'So11111111111111111111111111111111111111111')

    # cprint sol balance in light blue bacckground white text 
    cprint(f'SOL BALANCE: {sol_df["Amount"].values}', 'white', 'on_light_blue')

  
    open_positions_count = open_positions_df.shape[0]
    winning_positions_df = open_positions_df[open_positions_df['USD Value'] > sell_at_multiple * USDC_SIZE]
    # print('this is the winning df')
    # print(winning_positions_df)

    # if pnl_start_min <= now.minute <= pnl_end_min: 
    #print(f'checking pnl close because between {pnl_start_min} and {pnl_end_min} min mark...')
    for index, row in winning_positions_df.iterrows():
        token_mint_address = row['Mint Address']

        # only pnl close if not usdc_contract_address
        cprint(f'Winning Loop - this is token mint address {token_mint_address} ', 'white', 'on_green')
        if token_mint_address not in dont_trade_list:
            #print(f'this is the token mint address {token_mint_address} ')
            
            pnl_close(token_mint_address)
        #print('done closing winning positions...')
        # same as above but cprint green
        cprint('done closing winning positions...', 'white', 'on_magenta')

    sl_size = ((1+stop_loss_percentage) * USDC_SIZE)
    #print(f'now only keeping ones under the sl of {sl_size} we want to save time')
    losing_positions_df = open_positions_df[open_positions_df['USD Value'] < sl_size]
    #print('this is the losing df')
    
    # drop all rows that show 0 in USD Value
    losing_positions_df = losing_positions_df[losing_positions_df['USD Value'] != 0]

    #print(losing_positions_df)

    # get usd position usin get_position(token_mint_address)

 
    for index, row in open_positions_df.iterrows():
        token_mint_address = row['Mint Address']

        # Check if the token mint address is in the DO_NOT_TRADE_LIST
        if token_mint_address in DO_NOT_TRADE_LIST:
            print(f'Skipping trading for {token_mint_address} as it is in the DO_NOT_TRADE_LIST')
            continue  # Skip to the next iteration

        # Only pnl close if it's not a USDC contract address
        # Note: This check might be redundant if 'usdc_contract_address' is already in DO_NOT_TRADE_LIST
        if token_mint_address != usdc_contract_address:
            #print(f'This is the token mint address {token_mint_address}')
            pnl_close(token_mint_address)
    cprint('done closing losing positions.. keep swimming ❤️ 🙏.', 'white', 'on_magenta')


    # only run this code below on the 5 minute mark
    if now.minute % 2 == 0:
        print('its the 5 minute mark so running the new scan')

        ohlcv_bot()
        
    df = buying_df()

    # look at closed_positions.txt and if the token is there, then remove that row from the df
    with open(CLOSED_POSITIONS_TXT, 'r') as f:
        closed_positions = [line.strip() for line in f.readlines()]
    # closed_positions.txt acts as our black list
    df = df[~df['address'].isin(closed_positions)]
    # save df to ready_to_buy.csv
    df.to_csv(READY_TO_BUY_CSV, index=False)


    # 0. update the df to have the name in the first column
    df = pd.read_csv(READY_TO_BUY_CSV)
    df = get_names(df)


# MAIN SO NOT USING VIBE CHECK 
    # # 1. call the vibe check and output a new df 
    #df = n.ai_vibe_check(df, MIN_VIBE_SCORE) # passing in the df and the minmum vibe score to keep

    if open_positions_count < MAX_POSITIONS:

        print(f'🚀 moondev.sol has {open_positions_count} open positions & max: {MAX_POSITIONS}')
        for index, row in df.iterrows():

            usdc_holdings = get_position(usdc_contract_address)
            usdc_holdings = float(usdc_holdings)

            token_mint_address = row['address']
            #print(f'this is the token mint address {token_mint_address} and this is the usdc address {usdc_contract_address}')
            
            if usdc_holdings > USDC_SIZE:

                print(f'we have {usdc_holdings} usdc so can open..')
                open_position(token_mint_address)
            else:
                cprint(f'we have {usdc_holdings} usdc holdings and we can not open a position', 'white', 'on_red')
            
            now = datetime.now()
            current_hour = now.hour
            current_minute = now.minute

            # break the loop if the condition is satisfied
            if current_hour % 2 == 0 and 9 <= current_minute <= 13:
                print('Breaking the loop to check the PnL')
                break
            
    else:
        print(f'we have {open_positions_count} open positions and we can not open more bc more than {MAX_POSITIONS}')

    

    # Sleep for a specified time before the next iteration
    time.sleep(5)  # Adjust the sleep time as needed


bot()
print('done w/ 1st run, now looping...')

# schedule bot every 5 minutes
schedule.every(5).minutes.do(bot)

while True:
    try:
        schedule.run_pending()
        time.sleep(180)
    except Exception as e:
        print('***Maybe internet connection lost?***')
        print(e)
        time.sleep(180)