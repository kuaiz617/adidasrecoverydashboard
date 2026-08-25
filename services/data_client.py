from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

CSV_FILES = {
    "quarterly": "adidas_quarterly_metrics.csv",
    "divisional": "adidas_divisional_revenue.csv",
    "sentiment": "gdelt_adidas_news_sentiment.csv",
    "stock": "ads_stock_prices.csv",
    "social": "adidas_social_snapshot.csv",
    "instagram": "adidas_instagram_followers.csv",
}

DEFAULT_PIPES = {
    "quarterly": "adidas_quarterly_metrics_api",
    "divisional": "adidas_divisional_revenue_api",
    "sentiment": "adidas_news_sentiment_api",
    "stock": "ads_stock_prices_api",
    "social": "adidas_social_snapshot_api",
    "instagram": "adidas_instagram_followers_api",
}

DATE_COLUMNS = {
    "quarterly": ["period_end", "release_date"],
    "divisional": [],
    "sentiment": ["date"],
    "stock": ["date"],
    "social": ["date"],
    "instagram": ["month"],
}

QUARTER_ORDER = {"Q4 2025": 1, "Q1 2026": 2, "Q2 2026": 3}


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _normalize_frame(name: str, frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    for column in DATE_COLUMNS[name]:
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column])

    string_columns = {"quarter", "region", "product", "platform", "handle", "scale_metric_label", "source", "source_url"}
    for column in frame.columns:
        if column in string_columns or column in DATE_COLUMNS[name]:
            continue
        converted = pd.to_numeric(frame[column], errors="coerce")
        if converted.notna().sum() == frame[column].notna().sum():
            frame[column] = converted

    if "quarter" in frame.columns:
        frame["quarter_order"] = frame["quarter"].map(QUARTER_ORDER)

    if name == "quarterly":
        frame = frame.sort_values("quarter_order")
    elif name == "divisional":
        frame = frame.sort_values(["quarter_order", "region", "product"])
    elif name in {"sentiment", "stock"}:
        frame = frame.sort_values("date")
    elif name == "instagram":
        frame = frame.sort_values("month")

    return frame


def _load_local_data() -> dict[str, pd.DataFrame]:
    frames = {}
    for name, filename in CSV_FILES.items():
        frames[name] = _normalize_frame(name, pd.read_csv(DATA_DIR / filename))
    return frames


def _fetch_tinybird_pipe(name: str) -> pd.DataFrame:
    token = os.getenv("TINYBIRD_TOKEN")
    if not token:
        raise RuntimeError("TINYBIRD_TOKEN is not set")

    base_url = os.getenv("TINYBIRD_API_BASE", "https://api.tinybird.co").rstrip("/")
    pipe_name = os.getenv(f"TINYBIRD_PIPE_{name.upper()}", DEFAULT_PIPES[name])
    url = f"{base_url}/v0/pipes/{pipe_name}.json"
    response = requests.get(
        url,
        params={"token": token},
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data")
    if data is None:
        raise RuntimeError(f"Tinybird pipe {pipe_name} did not return a data array")
    return _normalize_frame(name, pd.DataFrame(data))


def _load_tinybird_data() -> dict[str, pd.DataFrame]:
    return {name: _fetch_tinybird_pipe(name) for name in CSV_FILES}


def load_dashboard_data() -> tuple[dict[str, pd.DataFrame], str]:
    """Load data from Tinybird when configured, otherwise from bundled CSVs."""
    backend = os.getenv("DATA_BACKEND", "local").strip().lower()
    if backend in {"tinybird", "api"}:
        try:
            return _load_tinybird_data(), "Tinybird API"
        except Exception as exc:
            if _truthy(os.getenv("REQUIRE_TINYBIRD")):
                raise
            print(f"Tinybird API load failed; falling back to local CSV data: {exc}")
            return _load_local_data(), "Local CSV fallback"

    return _load_local_data(), "Local CSV"
