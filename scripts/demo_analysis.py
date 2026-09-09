"""End-to-end demo for the MGT 409 homework environment.

Generates a small synthetic monthly-sales dataset, computes summary statistics
and a moving average with the shared ``mgt409`` helpers, prints a report, and
saves a chart. Running this proves that numpy, pandas, matplotlib, and the local
package are all wired up correctly.

Usage:
    python scripts/demo_analysis.py [--output PATH]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless-safe backend for CI / Cloud Agents
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

# Allow running directly (python scripts/demo_analysis.py) without installing.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mgt409 import describe, moving_average, summary_table  # noqa: E402


def make_dataset(seed: int = 409) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    months = pd.date_range("2025-01-01", periods=12, freq="MS")
    trend = np.linspace(100, 160, 12)
    noise = rng.normal(0, 8, 12)
    sales = np.round(trend + noise, 1)
    marketing = np.round(rng.uniform(10, 25, 12), 1)
    return pd.DataFrame({"month": months, "sales": sales, "marketing_spend": marketing})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="artifacts/sales_report.png",
        help="Path to write the chart PNG (default: artifacts/sales_report.png)",
    )
    args = parser.parse_args()

    df = make_dataset()

    print("=== MGT 409 demo: monthly sales analysis ===\n")
    print(df.to_string(index=False))

    print("\n--- describe(sales) ---")
    for key, value in describe(df["sales"]).items():
        print(f"{key:>7}: {value:.2f}")

    print("\n--- summary_table (numeric columns) ---")
    print(summary_table(df).round(2).to_string())

    window = 3
    ma = moving_average(df["sales"], window)
    print(f"\n--- {window}-month moving average of sales ---")
    print([round(x, 1) for x in ma])

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(df["month"], df["sales"], marker="o", label="Monthly sales")
    ma_months = df["month"].iloc[window - 1 :]
    ax.plot(ma_months, ma, color="crimson", linewidth=2, label=f"{window}-mo moving avg")
    ax.set_title("MGT 409 — Monthly Sales & Moving Average")
    ax.set_xlabel("Month")
    ax.set_ylabel("Sales ($000s)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)

    print(f"\nSaved chart to {out_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
