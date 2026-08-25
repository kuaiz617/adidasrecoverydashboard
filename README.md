# adidas Global Brand Recovery Dashboard

An interactive Dash + Plotly dashboard analyzing **adidas AG's** FY2026 public
performance. It is modeled on the same structure as a Nike recovery tracker, but
rebuilt end-to-end around adidas: euro reporting, adidas' six market segments, the
wholesale-versus-DTC channel shift, and the FIFA World Cup 2026 demand spike.

The data layer can be served through Tinybird SQL Pipe endpoints, or through the
bundled local CSV fallback so it runs immediately with no setup.

**Research question:** Is adidas' FY2026 recovery genuinely broad-based, or is the
rebound concentrated in DTC and a few fast-growing regions while wholesale, Europe,
and the share price stay under pressure?
Live Render app:https://adidasrecoverydashboard.onrender.com/

The three quarters shown are the most recently reported as of August 2026:
**Q4 2025, Q1 2026, and Q2 2026** (adidas reports on a calendar fiscal year).

## Dashboard features

- Line chart of adidas' core financial trajectory with selectable metrics (revenue,
  operating profit, gross margin, net income, diluted EPS).
- Grouped bar chart for Wholesale, Own retail, and E-commerce revenue with channel
  toggles — showing the deliberate DTC-over-wholesale shift.
- Animated regional bubble chart across Europe, North America, Greater China,
  Emerging Markets, Latin America, and Japan/South Korea, with currency-neutral YoY
  growth on the y-axis.
- Sunburst of the region → product revenue hierarchy per quarter.
- Public-attention chart combining GDELT news volume, GDELT average tone, and the
  ADS.DE (Xetra) closing price, with earnings-release markers.
- Social platform scale view for Instagram, TikTok, and YouTube.
- Instagram follower trend for @adidas.

## The story in the data

adidas' operating recovery is strong and broadening: currency-neutral revenue grew
**+11% → +14% → +14%** across the three quarters, gross margin climbed back above
52%, and the World Cup drove a 35% currency-neutral jump in apparel in Q2 2026. But
the recovery is uneven — **DTC surged ~25% while wholesale was held to single
digits on purpose, Europe lagged the rest of the world at ~6%, and the ADS.DE share
price actually fell** from about €196 (Oct 2025) to a €130 low (Mar 2026) before
recovering only to the mid-€150s, meaning the market had not yet rewarded the
turnaround as of August 2026.

## Project structure

```text
.
|-- app.py                 # Dash app: layout + single callback that builds all figures
|-- requirements.txt
|-- render.yaml            # Render web-service config
|-- .env.example
|-- assets/
|   `-- style.css          # dark adidas theme (three-stripes hero motif)
|-- data/                  # bundled CSV fallback (committed)
|   |-- adidas_quarterly_metrics.csv
|   |-- adidas_divisional_revenue.csv
|   |-- adidas_social_snapshot.csv
|   |-- adidas_instagram_followers.csv
|   |-- ads_stock_prices.csv
|   `-- gdelt_adidas_news_sentiment.csv
|-- datasources/           # Tinybird .datasource schemas
|-- pipes/                 # Tinybird .pipe endpoint definitions
|-- tinybird/pipes/        # plain SQL mirror of each pipe
|-- services/
|   `-- data_client.py     # Tinybird-or-CSV loader
`-- scripts/
    |-- refresh_data.py    # rebuild CSVs from official + public sources
    |-- check_api_backend.py
    `-- build_preview.py   # write a static preview.html
```

## How to run

```bash
python3 -m pip install -r requirements.txt
python3 app.py
```

Then open the local URL printed in the terminal, usually:

```text
http://127.0.0.1:8050
```

To confirm which data layer is active:

```bash
python3 scripts/check_api_backend.py
```

To generate a static HTML preview of the whole page:

```bash
python3 scripts/build_preview.py   # writes preview.html
```

## Deploying on Render

1. Push this repo to GitHub.
2. Create a new **Web Service** on Render pointing at the repo (it auto-detects
   `render.yaml`).
3. It runs on the bundled CSVs out of the box (`DATA_BACKEND=local`). To use
   Tinybird instead, set `DATA_BACKEND=tinybird` and add your `TINYBIRD_TOKEN`.

Start command: `gunicorn app:server`.

## Refreshing public data

The repository already includes CSVs, so the app runs without refreshing. To pull
fresh stock prices (Yahoo Finance, ADS.DE) and GDELT public-attention data, and to
regenerate the financial CSVs from the figures encoded in the script:

```bash
python3 scripts/refresh_data.py
```

If Yahoo or GDELT are unreachable, the script writes representative snapshots
anchored to the real reported levels so the dashboard still runs.

## Data sources & honesty notes

- **Official (adidas AG investor releases):** all quarterly totals, gross margin,
  operating profit, net income, EPS, inventories, per-segment revenue totals,
  per-product-division totals, channel totals, and every currency-neutral growth
  rate. From the Q4'25/FY25 (Mar 4, 2026), Q1'26 (Apr 29, 2026), and Q2'26/H1'26
  (Jul 30, 2026) releases.
- **Derived exactly:** Q1 2026 segment / product / channel euro values are computed
  as H1 2026 (reported) minus Q2 2026 (reported).
- **Modeled (clearly flagged in the app footer):** the region × product cross-tab
  used by the sunburst (adidas discloses region totals and product totals
  separately, not the matrix) and the Q4 2025 per-segment euro split (allocated from
  the full-year 2025 regional mix). Growth rates on those cells are the official
  currency-neutral rates.
- **Public proxies:** GDELT Project DOC 2.0 API (news volume & tone), Yahoo Finance
  chart API (ADS.DE daily prices), and public social snapshots (Instagram, TikTok,
  YouTube). Social and news metrics are external proxies, not internal adidas data.

Revenue figures reflect the **adidas brand** and contain no Yeezy sales in either the
current or prior-year periods.
