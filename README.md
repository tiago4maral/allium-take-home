### Project Vision and Goals
The project aims to develop a straightforward and accurate method for fetching token prices from the CoinGecko API, storing them in an easily accessible format, and then utilizing a DBT model to integrate this information into the existing 'erc20_token_transfers' table.

### Database Setup
- Ensure Docker is installed and running on your system.
- Use the provided `docker-compose.yml` to set up a PostgreSQL container

### historical_price_fetcher.py
- We can insert any chain and any token_address and the script will take care of everything. In CHAIN_ID we can 
insert the desired chain ID, which I got from https://api.coingecko.com/api/v3/asset_platforms and 
stored in 'available_chains_ids' for reference. Almost all of them are available, but 3 doesn't have IDs 
(Immutable, Matrix, and Picasso), so we can't get historical price data from tokens on these chains.

- In TOKEN_CONTRACT_ADDRESS we can insert any available token contract address indexed by Coingecko, available in 
that chain. More on why I decided to focus on token address instead of token id or token name below.

- In DAYS, we state that we should get data up to that number of days ago (I'm getting MAX). Also, since
we are using the free plan, our MAX will return daily prices. Better plans would bring more granular data.

- Function 'is_token_indexed' is important because, as we know, not all tokens are indexed by Coingecko APIs. Here, we check the coins list from CoinGecko and check if our token_contract_address appears in that list. I decided to focus on token_contract_address instead of token_id or token_name because tokens can have the same name
and token_id is something created for the CoinGecko API, on the other hand, token contract address is an
universal variable we can check in several different platforms.

- In the function 'fetch_token_prices', we consider the answer from 'is_token_indexed'. If the token is in CoinGecko's coins list, the token prices fetcher will run normally. If it doesn't, it will return the error
message "Token Prices for '{token_contract_address}' not indexed by CoinGecko APIs". Since we are using
token contract address as one of our variables, instead of coin id, we are using contract market chart endpoint, 
instead of coins/id/market_chart. Everything we need is the token contract address and the chain. This will return
a JSON with the historical price data for that token. 

- In the function 'process_prices_data', we get data from 'fetch_token_prices' and for each price point, we get the 
Unix timestamp and the price. Then, we convert the Unix timestamps into ISO8601 format because this is closer to 
the format you guys already use in Allium tables.

- Then, in 'create_table', we create the table for PostgreSQL. We are storing everything in token_prices table. 
We are adding token_address, chain_id, price - numeric format, with 18 numbers after the decimal, and the timestamp of
that price. We also create indexes based on token_address and chain_ID (idx_token_chain), since they are always 
together, and timestamp as well. 

### enriched_transfers.sql
- Here we have the DBT model, getting 'erc20_token_transfers' and 'token_prices' tables from the provided
source and performing the SQL query to insert token prices into the existing 'erc20_token_transfers' table. 
- Future logic for more accurate insertion and more rules applied could be added.

### example_queries.sql
- Here I included some example queries if you guys want to test them. I tested using both SQLTools in VSC
and also in the Query Tool from pgAdmin. 






