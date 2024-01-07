from datetime import datetime
import requests
import psycopg2
from ratelimit import rate_limited

CHAIN_ID = "ethereum"

TOKEN_CONTRACT_ADDRESS = "0x6982508145454ce325ddbe47a25d4ec3d2311933" 

VS_CURRENCY = "usd"

DAYS = "max"

"""We have 30 calls per minute in the free plan / public API. Of course, in bigger plans we could adjust this."""
RATE_LIMIT = 0.5 

DB_CONFIG = {
    "dbname": "allium",
    "user": "postgres",
    "password": "", 
    "host": "localhost"
}

"""Checking if the token is indexed by CoinGecko APIs"""
def is_token_indexed(token_contract_address):
    try:
        token_list_url = "https://api.coingecko.com/api/v3/coins/list?include_platform=true"
        response = requests.get(token_list_url)
        if response.status_code == 200:
            token_list = response.json()
            for token in token_list:
                platforms = token.get("platforms", {})
                if token_contract_address.lower() in [addr.lower() for addr in platforms.values()]:
                    return True
            return False
        else:
            raise ValueError(f"Failed to retrieve token list: {response.status_code}")
    except Exception as e:
        print(f"An error occurred while checking token indexing: {e}")
        return False

"""Checking the result from is_token_indexed and then, based on that, retrieving the prices."""
@rate_limited(RATE_LIMIT)
def fetch_token_prices(chain_id, token_contract_address, vs_currency="usd", days="max"):
    if not is_token_indexed(token_contract_address):
        raise ValueError(f"Token Prices for '{token_contract_address}' not indexed by CoinGecko APIs")

    url = f"https://api.coingecko.com/api/v3/coins/{chain_id}/contract/{token_contract_address}/market_chart/?vs_currency={vs_currency}&days={days}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()['prices']
    else:
        raise ValueError(f"Failed to retrieve data: {response.status_code}")

"""Converting Unix timestamp into iso format."""
def process_prices_data(prices):
    processed_data = []
    for price_point in prices:
        timestamp, price = price_point
        iso_timestamp = datetime.utcfromtimestamp(timestamp / 1000).isoformat()
        processed_data.append((iso_timestamp, price))
    print(processed_data)
    return processed_data

"""Creating the table and indexes"""
def create_table():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS token_prices (
                        token_address TEXT NOT NULL,
                        chain_ID TEXT NOT NULL,
                        price NUMERIC(28, 18) NOT NULL,
                        timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL
                    );
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_token_chain ON token_prices(token_address, chain_ID);
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON token_prices(timestamp);
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("An error occurred while creating the table:", e)

"""Getting our processed data from 'process_prices_data' and insert that into the database."""
def insert_into_database(data):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        for iso_timestamp, price in data:
            query = "INSERT INTO token_prices (token_address, chain_ID, price, timestamp) VALUES (%s, %s, %s, %s)"
            values = (TOKEN_CONTRACT_ADDRESS, CHAIN_ID, price, iso_timestamp)
            cursor.execute(query, values)

        conn.commit()
        cursor.close()
        conn.close()
        print("Data inserted successfully into the database.")
    except Exception as e:
        print("An error occurred while inserting data:", e)

if __name__ == "__main__":
    try:
        create_table()
        is_token_indexed(TOKEN_CONTRACT_ADDRESS)
        prices = fetch_token_prices(CHAIN_ID, TOKEN_CONTRACT_ADDRESS, VS_CURRENCY, DAYS)
        processed_data = process_prices_data(prices)
        insert_into_database(processed_data)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")