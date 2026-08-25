from __future__ import annotations

"""Assemble a static, self-contained HTML preview of the dashboard (hero + KPIs +
all charts) using the real stylesheet and live Plotly figures. Handy for a quick
visual check without running the Dash server."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app as a  # noqa: E402

kpis, line, bar, bubble, sun, sent, social, insta = a.update_dashboard(
    a.QUARTERS, a.REGIONS, a.PRODUCTS, "total_revenue_m", a.CHANNELS, "Q2 2026",
    ["volume", "tone", "stock"],
)

css = (ROOT / "assets" / "style.css").read_text()


def fig_html(fig, first=False):
    return fig.to_html(full_html=False, include_plotlyjs="cdn" if first else False,
                       config={"displayModeBar": False},
                       default_height="460px")


def kpi_html():
    latest = a.DATA["quarterly"].sort_values("quarter_order").iloc[-1]
    cards = [
        ("Q2 2026 revenue", f"\u20ac{latest['total_revenue_m']/1000:.2f}B",
         f"{latest['currency_neutral_revenue_change_pct']:+.0f}% currency-neutral YoY", "positive"),
        ("Gross margin", f"{latest['gross_margin_pct']:.1f}%",
         f"{latest['gross_margin_change_bps']:+.0f} bps YoY", "positive"),
        ("Operating profit", f"\u20ac{latest['operating_profit_m']:.0f}M",
         f"{latest['operating_margin_pct']:.1f}% margin", "positive"),
        ("Inventory", f"\u20ac{latest['inventories_m']/1000:.1f}B",
         f"{latest['inventory_change_pct']:+.0f}% YoY", "positive"),
    ]
    out = []
    for label, value, delta, tone in cards:
        out.append(
            f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-delta {tone}">{delta}</div></div>'
        )
    return "".join(out)


html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>adidas Brand Recovery Dashboard \u2014 preview</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800;900&display=swap" rel="stylesheet">
<style>{css}</style></head>
<body><div class="app-shell">
  <section class="hero">
    <div class="hero-copy">
      <div class="stripes"><span></span><span></span><span></span></div>
      <div class="eyebrow">FY2026 PUBLIC DATA DASHBOARD</div>
      <h1>adidas Global Brand Recovery Tracker</h1>
      <p>A Dash and Plotly dashboard connecting adidas' post-Yeezy recovery: quarterly momentum,
      regional pressure points, the wholesale-versus-DTC channel shift, public news tone, a
      still-cautious market reaction, and social reach.</p>
    </div>
    <div class="hero-badge"><div class="badge-main">WORLD CUP</div><div class="badge-sub">Q4'25 \u2013 Q2'26</div></div>
  </section>
  <div class="kpi-row">{kpi_html()}</div>
  <section class="chart-grid">
    <div class="chart-card wide">{fig_html(line, first=True)}</div>
    <div class="chart-card">{fig_html(bar)}</div>
    <div class="chart-card">{fig_html(bubble)}</div>
    <div class="chart-card">{fig_html(sun)}</div>
    <div class="chart-card wide">{fig_html(sent)}</div>
    <div class="chart-card">{fig_html(social)}</div>
    <div class="chart-card">{fig_html(insta)}</div>
  </section>
  <footer><strong>Data layer: {a.DATA_SOURCE_LABEL} (static preview). </strong>
  Sources: adidas AG investor releases, GDELT, Yahoo Finance (ADS.DE), public social snapshots.
  Region\u00d7product cross-tabs and the Q4'25 segment split are modeled from disclosed totals and
  currency-neutral growth rates.</footer>
</div></body></html>"""

out = ROOT / "preview.html"
out.write_text(html)
print(f"Wrote {out}")
