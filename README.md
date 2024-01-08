### Project Vision and Goals
The project aims to develop a straightforward and accurate method for fetching token prices from the CoinGecko API, storing them in an easily accessible format, and then utilizing a DBT model to integrate this information into the existing 'erc20_token_transfers' table.

### Database and Project Setup
1. Ensure Docker and Git are Installed.
2. Run: git clone https://github.com/tiago4maral/allium-take-home
3. Run: cd allium-take-home
4. Use the provided `docker-compose.yml` to set up a PostgreSQL container.
5. Run: docker-compose up -d
6. Before running the scripts, you need to install the required Python libraries we are using in the fetcher. Run: pip install -r requirements.txt
7. Execute `python historical_price_fetcher.py` to run the price fetcher, create the table and store it in 
the database. 

### historical_price_fetcher.py
- We can insert any chain and any token_address and the script will take care of everything. In CHAIN_ID we can 
insert the desired chain ID, which I got from https://api.coingecko.com/api/v3/asset_platforms and 
stored in `available_chains_ids` for reference. Almost all of them are available, but 3 doesn't have IDs 
(Immutable, Matrix, and Picasso), so we can't get historical price data from tokens on these chains.

- Function 'is_token_indexed' is important because, as we know, not all tokens are indexed by Coingecko APIs. Here, we check the coins list from CoinGecko and check if our token_contract_address appears in that list. I decided to focus on token_contract_address instead of token_id or token_name because tokens can have the same name
and token_id is something created for the CoinGecko API, on the other hand, token contract address is an
universal variable we can check in several different platforms.

- In the function 'fetch_token_prices', we consider the answer from 'is_token_indexed'. If the token is in CoinGecko's coins list, the token prices fetcher will run normally. If it doesn't, it will return the error
message "Token Prices for '{token_contract_address}' not indexed by CoinGecko APIs". Since we are using
token contract address as one of our variables, instead of coin id, we are using contract market chart endpoint, 
instead of coins/id/market_chart. Everything we need is the token contract address and the chain. This will return
a JSON with the historical price data for that token. 

- In the function 'process_prices_data', we get data from 'fetch_token_prices' and for each price point, we get the Unix timestamp and the price. Then, we convert the Unix timestamps into ISO8601 format because this is closer to the format you guys already use in Allium tables.

- Then, in 'create_table', we create the table for PostgreSQL. We are storing everything in token_prices table. 
We are adding token_address, chain_id, price - numeric format, with 18 numbers after the decimal, and the timestamp of that price. We also create indexes based on token_address and chain_ID (idx_token_chain), since they are always together, and timestamp as well. 

### enriched_transfers.sql
- Here we have the DBT model, getting 'erc20_token_transfers' and 'token_prices' tables from the provided
source and performing the SQL query to insert token prices into the existing 'erc20_token_transfers' table. 
- Future logic for more accurate insertion and more rules applied could be added.

### example_queries.sql
- Here I included some example queries if you guys want to test them. I tested using both SQLTools in VSC
and also in the Query Tool from pgAdmin. 

### Revisiting Project Requirements
Our project requirements were:
#### Develop and provide the DDLs for the required table(s)
- I did this in historical_price_fetcher
#### Historical token price data (in USD) of a given chain and token address can be fetched with a simple query
- I did this in historical_price_fetcher, were we can just insert a token address and a chain ID and the
script will take care of that
#### Take into account how the same token (e.g. USDC) can have different contract addresses across different Blockchains
- I did that by focusing on the token_contract_address and also by checking if price for that token is already
indexed by CoinGecko
#### [Bonus] Describe and implement the logic needed for ingesting historical price data from CoinGecko’s APIs.
- I explained why I decided to use specific API endpoints and the decision-making behind that
#### Write a SQL query (or, even better, a DBT model) that enriches erc20_token_transfers with USD price data
- Built that in enriched_transfers.sql. 








