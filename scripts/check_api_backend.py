from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.data_client import load_dashboard_data


def main() -> None:
    data, source = load_dashboard_data()
    print(f"Data source: {source}")
    for name, frame in data.items():
        print(f"{name}: {frame.shape[0]} rows x {frame.shape[1]} columns")


if __name__ == "__main__":
    main()
