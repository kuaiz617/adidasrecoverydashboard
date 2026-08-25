-- adidas_news_sentiment_api: GDELT English-language adidas news volume and tone.
SELECT
    date,
        article_count,
        average_tone,
        article_count_7d_avg,
        average_tone_7d_avg
FROM gdelt_adidas_news_sentiment
ORDER BY date
