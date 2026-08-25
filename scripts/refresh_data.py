from __future__ import annotations

"""Refresh the bundled public-data CSVs for the adidas brand recovery dashboard.

Financial figures (quarterly totals, gross margin, net income, EPS, inventories,
segment totals, product-division totals, channel totals, and all currency-neutral
growth rates) are taken from official adidas AG investor releases:

  * Q4 2025 / FY 2025 results, March 4, 2026
  * Q1 2026 results, April 29, 2026
  * Q2 2026 / H1 2026 results, July 30, 2026

Q1 2026 segment / product / channel euro values are derived exactly by subtracting
the reported Q2 2026 figures from the reported H1 2026 figures. Q4 2025 segment and
product euro values are modeled by applying full-year 2025 mix to the reported Q4
total, because adidas does not publish a full quarterly segment matrix; the growth
rates for those cells are the official currency-neutral rates. The region x product
cross-tab used by the sunburst is modeled by applying each quarter's global product
mix to each region total (adidas discloses region totals and product totals
separately, not the matrix). Stock prices and GDELT news sentiment are pulled from
public APIs (Yahoo Finance, GDELT DOC 2.0); when offline, representative snapshots
anchored to real reported levels are written instead.
"""

import json
import time
from datetime import datetime, timezone, date
from pathlib import Path

import numpy as np
import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

# adidas reports in EUR. Fiscal year = calendar year. The three most recently
# reported quarters as of Aug 2026 are Q4 2025, Q1 2026 and Q2 2026.
QUARTER_ORDER = {"Q4 2025": 1, "Q1 2026": 2, "Q2 2026": 3}

REGIONS = [
    "Europe",
    "North America",
    "Greater China",
    "Emerging Markets",
    "Latin America",
    "Japan/South Korea",
]
PRODUCTS = ["Footwear", "Apparel", "Accessories"]


def write_quarterly() -> None:
    """Group-level quarterly metrics from official adidas releases (EUR millions)."""
    quarterly = pd.DataFrame(
        [
            {
                "quarter": "Q4 2025",
                "period_end": "2025-12-31",
                "release_date": "2026-03-04",
                "total_revenue_m": 6076,
                "reported_revenue_change_pct": 2,
                "currency_neutral_revenue_change_pct": 11,
                "brand_revenue_m": 6076,
                "brand_reported_change_pct": 2,
                "brand_cn_change_pct": 11,
                "wholesale_revenue_m": 3600,
                "wholesale_reported_change_pct": -5,
                "wholesale_cn_change_pct": 2,
                "retail_revenue_m": 1214,
                "retail_reported_change_pct": 10,
                "retail_cn_change_pct": 17,
                "ecom_revenue_m": 1034,
                "ecom_reported_change_pct": 14,
                "ecom_cn_change_pct": 21,
                "gross_margin_pct": 50.8,
                "gross_margin_change_bps": 100,
                "operating_profit_m": 164,
                "operating_margin_pct": 2.7,
                "net_income_m": 85,
                "net_income_change_pct": 415,
                "diluted_eps": 0.42,
                "eps_change_pct": 262,
                "inventories_m": 5832,
                "inventory_change_pct": 17,
                "cash_and_short_investments_m": 1617,
            },
            {
                "quarter": "Q1 2026",
                "period_end": "2026-03-31",
                "release_date": "2026-04-29",
                "total_revenue_m": 6592,
                "reported_revenue_change_pct": 7,
                "currency_neutral_revenue_change_pct": 14,
                "brand_revenue_m": 6592,
                "brand_reported_change_pct": 7,
                "brand_cn_change_pct": 14,
                "wholesale_revenue_m": 4085,
                "wholesale_reported_change_pct": 3,
                "wholesale_cn_change_pct": 8,
                "retail_revenue_m": 1339,
                "retail_reported_change_pct": 13,
                "retail_cn_change_pct": 19,
                "ecom_revenue_m": 1141,
                "ecom_reported_change_pct": 19,
                "ecom_cn_change_pct": 25,
                "gross_margin_pct": 51.1,
                "gross_margin_change_bps": -100,
                "operating_profit_m": 705,
                "operating_margin_pct": 10.7,
                "net_income_m": 484,
                "net_income_change_pct": 11,
                "diluted_eps": 2.70,
                "eps_change_pct": 12,
                "inventories_m": 5661,
                "inventory_change_pct": 13,
                "cash_and_short_investments_m": 928,
            },
            {
                "quarter": "Q2 2026",
                "period_end": "2026-06-30",
                "release_date": "2026-07-30",
                "total_revenue_m": 6743,
                "reported_revenue_change_pct": 13,
                "currency_neutral_revenue_change_pct": 14,
                "brand_revenue_m": 6743,
                "brand_reported_change_pct": 13,
                "brand_cn_change_pct": 14,
                "wholesale_revenue_m": 3825,
                "wholesale_reported_change_pct": 6,
                "wholesale_cn_change_pct": 6,
                "retail_revenue_m": 1571,
                "retail_reported_change_pct": 20,
                "retail_cn_change_pct": 23,
                "ecom_revenue_m": 1338,
                "ecom_reported_change_pct": 24,
                "ecom_cn_change_pct": 27,
                "gross_margin_pct": 52.5,
                "gross_margin_change_bps": 80,
                "operating_profit_m": 574,
                "operating_margin_pct": 8.5,
                "net_income_m": 398,
                "net_income_change_pct": 6,
                "diluted_eps": 2.10,
                "eps_change_pct": 3,
                "inventories_m": 5969,
                "inventory_change_pct": 13,
                "cash_and_short_investments_m": 1159,
            },
        ]
    )
    quarterly.to_csv(DATA_DIR / "adidas_quarterly_metrics.csv", index=False)


# Segment (region) net sales, EUR millions, and currency-neutral YoY change.
# Q1 2026 = H1 2026 (reported) minus Q2 2026 (reported), exact.
# Q2 2026 = official. Q4 2025 euro = modeled from FY2025 regional mix x Q4 total.
SEGMENTS = {
    "Q4 2025": {
        "Europe": (2005, 6, 6),
        "North America": (1246, 5, 5),
        "Greater China": (893, 17, 15),
        "Emerging Markets": (857, 12, 15),
        "Latin America": (717, 24, 18),
        "Japan/South Korea": (359, 8, 13),
    },
    "Q1 2026": {
        "Europe": (2090, 6, 6),
        "North America": (1200, 12, 12),
        "Greater China": (1135, 20, 17),
        "Emerging Markets": (869, 10, 10),
        "Latin America": (830, 33, 26),
        "Japan/South Korea": (405, 8, 23),
    },
    "Q2 2026": {
        "Europe": (2108, 6, 6),
        "North America": (1522, 14, 17),
        "Greater China": (953, 19, 15),
        "Emerging Markets": (848, 11, 12),
        "Latin America": (907, 35, 28),
        "Japan/South Korea": (376, 6, 18),
    },
}

# Global product-division mix per quarter (EUR millions) and CN change.
# Q1 2026 = H1 minus Q2 (exact). Q2 2026 = official. Q4 2025 = modeled euro split.
PRODUCT_MIX = {
    "Q4 2025": {
        "Footwear": (3100, 5, 5),
        "Apparel": (2490, 20, 20),
        "Accessories": (486, 7, 7),
    },
    "Q1 2026": {
        "Footwear": (3700, 4, 4),
        "Apparel": (2443, 31, 31),
        "Accessories": (450, 13, 13),
    },
    "Q2 2026": {
        "Footwear": (3492, 0, 1),
        "Apparel": (2721, 34, 35),
        "Accessories": (530, 18, 20),
    },
}


def write_divisional() -> None:
    """Region x product cross-tab (modeled) plus per-region totals.

    Each region total is split across products using that quarter's global product
    mix. Cell currency-neutral change is set to the region's overall CN change.
    Region totals and CN changes are official; the region x product split is modeled.
    """
    rows = []
    for quarter, seg in SEGMENTS.items():
        prod = PRODUCT_MIX[quarter]
        prod_total = sum(v[0] for v in prod.values())
        shares = {p: prod[p][0] / prod_total for p in PRODUCTS}
        for region, (rev, rep_chg, cn_chg) in seg.items():
            region_alloc = {p: round(rev * shares[p]) for p in PRODUCTS}
            # fix rounding so the parts sum to the region total
            diff = rev - sum(region_alloc.values())
            region_alloc["Footwear"] += diff
            for product in PRODUCTS:
                cell = region_alloc[product]
                prior = round(cell / (1 + cn_chg / 100)) if cn_chg != -100 else cell
                rows.append(
                    {
                        "quarter": quarter,
                        "region": region,
                        "product": product,
                        "revenue_m": cell,
                        "prior_year_revenue_m": prior,
                        "reported_change_pct": rep_chg,
                        "currency_neutral_change_pct": cn_chg,
                    }
                )
            prior_total = round(rev / (1 + cn_chg / 100)) if cn_chg != -100 else rev
            rows.append(
                {
                    "quarter": quarter,
                    "region": region,
                    "product": "Total",
                    "revenue_m": rev,
                    "prior_year_revenue_m": prior_total,
                    "reported_change_pct": rep_chg,
                    "currency_neutral_change_pct": cn_chg,
                }
            )
    pd.DataFrame(rows).to_csv(DATA_DIR / "adidas_divisional_revenue.csv", index=False)


def write_social() -> None:
    """Public social-platform snapshots for the adidas brand (proxies, not internal)."""
    social = pd.DataFrame(
        [
            {
                "platform": "Instagram",
                "handle": "@adidas",
                "date": "2026-07-11",
                "audience_m": 29.509269,
                "scale_metric_m": 29.509269,
                "scale_metric_label": "followers",
                "content_count": 1592,
                "source": "HypeAuditor @adidas Instagram snapshot",
                "source_url": "https://hypeauditor.com/instagram/adidas/",
            },
            {
                "platform": "TikTok",
                "handle": "@adidas",
                "date": "2026-07-11",
                "audience_m": 8.8,
                "scale_metric_m": 44.0,
                "scale_metric_label": "likes",
                "content_count": 1075,
                "source": "Public TikTok profile snapshot",
                "source_url": "https://www.tiktok.com/@adidas",
            },
            {
                "platform": "YouTube",
                "handle": "adidas",
                "date": "2026-07-11",
                "audience_m": 1.1,
                "scale_metric_m": 1900.0,
                "scale_metric_label": "lifetime views",
                "content_count": 3500,
                "source": "Public YouTube channel snapshot",
                "source_url": "https://www.youtube.com/@adidas",
            },
        ]
    )
    social.to_csv(DATA_DIR / "adidas_social_snapshot.csv", index=False)


def write_instagram_followers() -> None:
    """Monthly @adidas Instagram follower snapshots (public trackers)."""
    instagram_monthly = pd.DataFrame(
        [
            {"month": "2026-01-01", "followers": 28900000},
            {"month": "2026-02-01", "followers": 29050000},
            {"month": "2026-03-01", "followers": 29180000},
            {"month": "2026-04-01", "followers": 29260000},
            {"month": "2026-05-01", "followers": 29320000},
            {"month": "2026-06-12", "followers": 29384813},
            {"month": "2026-07-11", "followers": 29509269},
            {"month": "2026-08-01", "followers": 29600000},
        ]
    )
    instagram_monthly.to_csv(DATA_DIR / "adidas_instagram_followers.csv", index=False)


# ---------------------------------------------------------------------------
# Stock prices: Yahoo Finance if reachable, else a representative snapshot
# anchored to real reported levels for ADS.DE (Xetra, EUR).
# ---------------------------------------------------------------------------
STOCK_ANCHORS = [
    (date(2025, 8, 1), 178.0),
    (date(2025, 10, 21), 196.4),   # 52-week high
    (date(2025, 12, 1), 182.0),
    (date(2026, 1, 1), 169.05),
    (date(2026, 2, 2), 150.0),
    (date(2026, 3, 23), 129.95),   # 52-week low
    (date(2026, 4, 29), 141.0),    # Q1 beat, +6% pop
    (date(2026, 6, 15), 152.0),    # World Cup window
    (date(2026, 7, 30), 149.0),    # Q2 print, profit-miss pullback
    (date(2026, 8, 24), 156.1),
]


def _synth_stock() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    days = pd.bdate_range(STOCK_ANCHORS[0][0], STOCK_ANCHORS[-1][0])
    ax = np.array([d.toordinal() for d, _ in STOCK_ANCHORS], dtype=float)
    ay = np.array([p for _, p in STOCK_ANCHORS], dtype=float)
    xi = np.array([d.toordinal() for d in days], dtype=float)
    base = np.interp(xi, ax, ay)
    noise = rng.normal(0, 1.0, size=len(base)).cumsum() * 0.35
    close = np.clip(base + noise, 120, 205)
    opens = close + rng.normal(0, 1.2, size=len(close))
    highs = np.maximum(opens, close) + np.abs(rng.normal(0, 1.4, size=len(close)))
    lows = np.minimum(opens, close) - np.abs(rng.normal(0, 1.4, size=len(close)))
    vol = rng.integers(300_000, 900_000, size=len(close))
    stock = pd.DataFrame(
        {
            "date": [d.date() for d in days],
            "open": opens.round(2),
            "high": highs.round(2),
            "low": lows.round(2),
            "close": close.round(2),
            "adj_close": close.round(2),
            "volume": vol,
        }
    )
    stock["daily_return_pct"] = stock["adj_close"].pct_change() * 100
    return stock


def fetch_yahoo_stock() -> None:
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/ADS.DE"
        start = int(datetime(2025, 8, 1, tzinfo=timezone.utc).timestamp())
        end = int(datetime(2026, 8, 25, tzinfo=timezone.utc).timestamp())
        params = {"period1": start, "period2": end, "interval": "1d", "events": "history"}
        response = requests.get(url, params=params, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        result = response.json()["chart"]["result"][0]
        timestamps = result["timestamp"]
        quote = result["indicators"]["quote"][0]
        adjclose = result["indicators"].get("adjclose", [{}])[0].get("adjclose", quote["close"])
        stock = pd.DataFrame(
            {
                "date": pd.to_datetime(timestamps, unit="s").date,
                "open": quote["open"],
                "high": quote["high"],
                "low": quote["low"],
                "close": quote["close"],
                "adj_close": adjclose,
                "volume": quote["volume"],
            }
        ).dropna(subset=["close"])
        stock["daily_return_pct"] = stock["adj_close"].pct_change() * 100
        stock.to_csv(DATA_DIR / "ads_stock_prices.csv", index=False)
        print("Stock: fetched live ADS.DE from Yahoo Finance.")
    except Exception as exc:  # offline / rate-limited -> representative snapshot
        print(f"Stock: Yahoo fetch failed ({exc}); writing representative snapshot.")
        _synth_stock().to_csv(DATA_DIR / "ads_stock_prices.csv", index=False)


# ---------------------------------------------------------------------------
# GDELT news sentiment: live DOC 2.0 API if reachable, else a representative
# snapshot with a FIFA World Cup 2026 volume spike (Jun 11 - Jul 19, 2026).
# ---------------------------------------------------------------------------
def _synth_sentiment() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    days = pd.date_range("2025-09-01", "2026-08-20", freq="D")
    counts, tones = [], []
    wc_start, wc_end = pd.Timestamp("2026-06-11"), pd.Timestamp("2026-07-19")
    earnings = {pd.Timestamp("2026-01-29"), pd.Timestamp("2026-03-04"),
                pd.Timestamp("2026-04-29"), pd.Timestamp("2026-07-30")}
    for d in days:
        base = 55 + 10 * np.sin((d.dayofyear / 365) * 2 * np.pi)
        if wc_start <= d <= wc_end:
            peak = 1 - abs((d - (wc_start + (wc_end - wc_start) / 2)).days) / 25
            base += 140 * max(peak, 0)
        if any(abs((d - e).days) <= 2 for e in earnings):
            base += 60
        base += rng.normal(0, 8)
        counts.append(max(int(base), 8))
        tone = 1.6 + 0.8 * np.sin((d.dayofyear / 365) * 2 * np.pi) + rng.normal(0, 0.6)
        if wc_start <= d <= wc_end:
            tone += 1.4
        if d == pd.Timestamp("2026-07-30"):
            tone -= 1.2  # profit-miss headlines
        tones.append(round(tone, 4))
    frame = pd.DataFrame({"date": days.date, "article_count": counts, "average_tone": tones})
    frame["article_count_7d_avg"] = frame["article_count"].rolling(7, min_periods=1).mean().round(2)
    frame["average_tone_7d_avg"] = frame["average_tone"].rolling(7, min_periods=1).mean().round(4)
    return frame


def fetch_gdelt_series(mode: str) -> dict:
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": "adidas sourcelang:english",
        "mode": mode,
        "format": "json",
        "startdatetime": "20250901000000",
        "enddatetime": "20260820000000",
    }
    response = requests.get(url, params=params, timeout=45, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    return response.json()


def fetch_gdelt_news() -> None:
    try:
        volume = fetch_gdelt_series("timelinevolraw")
        time.sleep(6)
        tone = fetch_gdelt_series("timelinetone")

        def timeline_to_frame(payload: dict, value_col: str) -> pd.DataFrame:
            data = payload["timeline"][0]["data"]
            frame = pd.DataFrame(data)
            frame["date"] = pd.to_datetime(frame["date"]).dt.date
            return frame[["date", "value"]].rename(columns={"value": value_col})

        volume_df = timeline_to_frame(volume, "article_count")
        tone_df = timeline_to_frame(tone, "average_tone")
        merged = volume_df.merge(tone_df, on="date", how="outer").sort_values("date")
        merged["article_count_7d_avg"] = merged["article_count"].rolling(7, min_periods=1).mean()
        merged["average_tone_7d_avg"] = merged["average_tone"].rolling(7, min_periods=1).mean()
        merged.to_csv(DATA_DIR / "gdelt_adidas_news_sentiment.csv", index=False)

        raw_dir = DATA_DIR / "raw"
        raw_dir.mkdir(exist_ok=True)
        (raw_dir / "gdelt_timelinevolraw_response.json").write_text(json.dumps(volume, indent=2))
        (raw_dir / "gdelt_timelinetone_response.json").write_text(json.dumps(tone, indent=2))
        print("Sentiment: fetched live GDELT series.")
    except Exception as exc:
        print(f"Sentiment: GDELT fetch failed ({exc}); writing representative snapshot.")
        _synth_sentiment().to_csv(DATA_DIR / "gdelt_adidas_news_sentiment.csv", index=False)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    write_quarterly()
    write_divisional()
    write_social()
    write_instagram_followers()
    fetch_yahoo_stock()
    fetch_gdelt_news()
    print(f"Data refreshed in {DATA_DIR}")


if __name__ == "__main__":
    main()
