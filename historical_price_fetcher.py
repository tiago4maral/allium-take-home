from datetime import datetime
import requests
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from ratelimit import rate_limited

"""The chain the token is running (available from https://api.coingecko.com/api/v3/asset_platforms and stored in 
'available_chains_ids' for reference"""
CHAIN_ID = "ethereum"

"""we can insert any available token contract address indexed by Coingecko, available in that chain. 
More on why I decided to focus on token address instead of token id or token name in README.md."""
TOKEN_CONTRACT_ADDRESS = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48" 

"""The currency we want to get the prices, in our case, it's USD."""
VS_CURRENCY = "usd"

"""We state that we should get data up to that number of days ago (I'm getting MAX). 
Also, since we are using the free plan, our MAX will return daily prices. Better plans would bring more 
granular data."""
DAYS = "max"

"""We have 30 calls per minute in the free plan / public API. Of course, in bigger plans we could adjust this."""
RATE_LIMIT = 0.5 

"""Our PSQL database configuration"""
DB_CONFIG = {
    "user": "postgres",
    "password": "", 
    "host": "localhost",
    "dbname": "postgres"
}

DB_NAME = "allium"

"""Here we are creating the database so we can host the tables and test the queries as well."""
def create_database():
    con = psycopg2.connect(user=DB_CONFIG["user"], password=DB_CONFIG["password"], host=DB_CONFIG["host"], dbname='postgres')
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT) 

    cursor = con.cursor()

    cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (DB_NAME,))
    exists = cursor.fetchone()
    if not exists:
        cursor.execute(f"CREATE DATABASE {DB_NAME};")
        print(f"Database '{DB_NAME}' created successfully.")

    cursor.close()
    con.close()

    DB_CONFIG["dbname"] = DB_NAME

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

"""Checking the result from is_token_indexed and then, based on that, retrieving (or not) the prices."""
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
    # print(processed_data)
    return processed_data

"""Creating the table, constraints, and indexes"""
def create_table():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS token_prices (
                        token_address TEXT NOT NULL,
                        chain_ID TEXT NOT NULL,
                        price NUMERIC(28, 18) NOT NULL,
                        timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                        PRIMARY KEY (token_address, chain_ID, timestamp)
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
        create_database()
        create_table()
        is_token_indexed(TOKEN_CONTRACT_ADDRESS)
        prices = fetch_token_prices(CHAIN_ID, TOKEN_CONTRACT_ADDRESS, VS_CURRENCY, DAYS)
        processed_data = process_prices_data(prices)
        insert_into_database(processed_data)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")