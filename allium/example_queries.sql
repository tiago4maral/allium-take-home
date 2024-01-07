-- Fetch historical prices for USDC (Ethereum)
SELECT 
    token_address,
    chain_ID,
    price,
    timestamp
FROM 
    token_prices
WHERE 
    token_address = '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
    AND chain_ID = 'ethereum'
ORDER BY 
    timestamp DESC;

-- Fetch historical prices for Nola (Arbitrum)
SELECT 
    token_address,
    chain_ID,
    price,
    timestamp
FROM 
    token_prices
WHERE 
    token_address = '0xf8388c2b6edf00e2e27eef5200b1befb24ce141d'
    AND chain_ID = 'arbitrum-one'
ORDER BY 
    timestamp DESC;

-- Fetch historical prices for analoS (Solana)
SELECT 
    token_address,
    chain_ID,
    price,
    timestamp
FROM 
    token_prices
WHERE 
    token_address = '7iT1GRYYhEop2nV1dyCwK2MGyLmPHq47WhPGSwiqcUg5'
    AND chain_ID = 'solana'
ORDER BY 
    timestamp DESC;