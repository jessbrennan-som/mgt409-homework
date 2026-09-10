#!/usr/bin/env python3
"""Build a January income statement from the reconciliation log."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PERIOD = "2026-01"
RECON_FILENAME = "reconciliation_log.json"
OUT_FILENAME = "income_statement.json"

# Explicit classifications for known reconciliation ids.
REVENUE_IDS = {
    "square_mixed_personal_deposit": ("Square walk-in sales (net of personal)", "sales_revenue"),
    "mike_smith_unpaid_iou": ("Mike Smith tune-up receivable", "service_revenue"),
}

EXPENSE_IDS = {
    "park_tool_card_vs_receipt": ("Park Tool tools (full card charge)", "tools_equipment"),
    "ebay_repair_stand_card_vs_order": ("eBay Park Tool repair stand", "tools_equipment"),
    "speedy_courier_receipt_vs_card": ("Speedy Courier emergency delivery", "shipping"),
    "home_depot_receipt_vs_card": ("Home Depot shop supplies", "shop_supplies"),
    "nhbp_counter_order_card_vs_receipt": ("NH Bike Parts counter invoice", "cogs_parts"),
    "nhbp_separate_wholesale_check": ("NH Bike Parts wholesale restock", "cogs_parts"),
}


def round_money(value: float) -> float:
    return round(float(value), 2)


def classify_row(row: dict) -> tuple[str, str, str] | None:
    """Return (kind, label, category) or None if excluded/unknown."""
    amount = float(row.get("included_in_income_statement") or 0)
    if amount == 0:
        return None

    row_id = str(row.get("id") or "")
    resolution = str(row.get("resolution") or "").lower()

    if row_id in REVENUE_IDS:
        label, category = REVENUE_IDS[row_id]
        return "revenue", label, category
    if row_id in EXPENSE_IDS:
        label, category = EXPENSE_IDS[row_id]
        return "expense", label, category

    # Fallback heuristics for any new reconciliation rows.
    revenue_hints = ("revenue", "sales", "deposit", "receivable", "tune-up", "income")
    expense_hints = ("expense", "purchase", "charge", "order", "shipping", "parts", "tools")
    if any(h in resolution for h in revenue_hints) and "exclude" not in resolution:
        if "expense" not in resolution and "purchase" not in resolution:
            return "revenue", row_id.replace("_", " "), "revenue"
    if any(h in resolution for h in expense_hints) or any(
        h in row_id for h in ("receipt", "card_vs", "parts", "tool", "courier", "depot")
    ):
        return "expense", row_id.replace("_", " "), "expense"

    return None


def build_income_statement(rows: list[dict]) -> dict:
    revenue_lines: list[dict] = []
    expense_lines: list[dict] = []

    for row in rows:
        classified = classify_row(row)
        if classified is None:
            continue
        kind, label, category = classified
        amount = round_money(row["included_in_income_statement"])
        line = {
            "id": row["id"],
            "label": label,
            "amount": amount,
            "category": category,
            "sources": list(row.get("sources") or []),
        }
        if kind == "revenue":
            revenue_lines.append(line)
        else:
            expense_lines.append(line)

    total_revenue = round_money(sum(line["amount"] for line in revenue_lines))
    total_expenses = round_money(sum(line["amount"] for line in expense_lines))
    net_income = round_money(total_revenue - total_expenses)

    return {
        "period": PERIOD,
        "revenue": total_revenue,
        "revenue_lines": revenue_lines,
        "expenses": expense_lines,
        "total_expenses": total_expenses,
        "net_income": net_income,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build January income statement JSON from reconciliation_log.json."
    )
    parser.add_argument(
        "--json-dir",
        required=True,
        help="Directory containing reconciliation_log.json (usually output).",
    )
    parser.add_argument(
        "--out-dir",
        required=True,
        help="Directory for income_statement.json (usually output).",
    )
    args = parser.parse_args(argv)

    json_dir = Path(args.json_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    recon_path = json_dir / RECON_FILENAME
    if not recon_path.is_file():
        print(f"Missing reconciliation log: {recon_path}", file=sys.stderr)
        return 1

    rows = json.loads(recon_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        print("reconciliation_log.json must be a JSON array", file=sys.stderr)
        return 1

    statement = build_income_statement(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / OUT_FILENAME
    out_path.write_text(json.dumps(statement, indent=2) + "\n", encoding="utf-8")

    print(f"Read {recon_path}")
    print(f"Wrote {out_path}")
    print(f"period={statement['period']}")
    print(f"revenue={statement['revenue']}")
    print(f"total_expenses={statement['total_expenses']}")
    print(f"net_income={statement['net_income']}")
    for line in statement["expenses"]:
        print(f"  expense: {line['label']} {line['amount']} [{line['category']}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
