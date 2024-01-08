
{{ config(materialized='table') }}

WITH 

transfers AS (
    SELECT
        *,
        block_timestamp::DATE as date
    FROM 
        {{ source('source', 'erc20_token_transfers') }}
),

prices AS (
    SELECT 
        token_address,
        timestamp,
        price
    FROM 
        {{ source('source', 'token_prices') }}
),

/* We are getting the closest price for each token transfer at or before the time of the transfer. */

enriched_transfers AS (
    SELECT
        t.*,
        tp.price AS usd_price
    FROM
        transfers t
    LEFT JOIN LATERAL (
        SELECT
            price
        FROM
            prices tp
        WHERE
            tp.token_address = t.token_address
            AND tp.timestamp <= t.block_timestamp
        ORDER BY
            tp.timestamp DESC
        LIMIT 1
    ) tp ON true
)

SELECT * FROM enriched_transfers

