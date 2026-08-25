-- ads_stock_prices_api: ADS.DE (Xetra) daily prices, EUR.
SELECT
    date,
        open,
        high,
        low,
        close,
        adj_close,
        volume,
        daily_return_pct
FROM ads_stock_prices
ORDER BY date
