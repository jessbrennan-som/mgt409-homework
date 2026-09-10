#!/usr/bin/env python3
"""Build a one-page human-readable HTML summary from homework JSON outputs."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

PERSONAL_EXCLUDE_IDS = {
    "amazon_headphones_personal",
    "rei_high_vis_outerwear_business_judgment",
}
BUSINESS_EXCLUDE_IDS = {
    "january_cam_not_invoiced",
    "hartford_mutual_future_contract",
    "wedding_ebike_future_work",
    "yale_cycling_club_future_work",
}


def money(value: float | int | None) -> str:
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0.0
    sign = "-" if amount < 0 else ""
    return f"{sign}${abs(amount):,.2f}"


def esc(value: object) -> str:
    return html.escape(str(value))


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def seen_amount(row: dict) -> float:
    amounts = row.get("amounts_seen") or {}
    if not amounts:
        return float(row.get("included_in_income_statement") or 0)
    return max(float(v) for v in amounts.values())


def render_sources(sources: list) -> str:
    if not sources:
        return "—"
    return ", ".join(esc(s) for s in sources)


def excluded_table_rows(rows: list[dict]) -> str:
    if not rows:
        return "<tr><td colspan='4'>None</td></tr>"
    return "\n".join(
        f"<tr><td>{esc(row.get('id'))}</td>"
        f"<td class='num'>{money(seen_amount(row))}</td>"
        f"<td class='num'>{money(row.get('included_in_income_statement'))}</td>"
        f"<td>{esc(row.get('resolution', ''))}</td></tr>"
        for row in rows
    )


def build_html(statement: dict, recon: list, judgments: list) -> str:
    period = statement.get("period", "2026-01")
    revenue = float(statement.get("revenue") or 0)
    total_expenses = float(statement.get("total_expenses") or 0)
    net_income = float(statement.get("net_income") or 0)
    revenue_lines = statement.get("revenue_lines") or []
    expenses = statement.get("expenses") or []
    net_class = "neg" if net_income < 0 else "pos"

    recon_by_id = {row.get("id"): row for row in recon if isinstance(row, dict)}
    personal_excluded = [recon_by_id[i] for i in PERSONAL_EXCLUDE_IDS if i in recon_by_id]
    business_excluded = [recon_by_id[i] for i in BUSINESS_EXCLUDE_IDS if i in recon_by_id]
    known = PERSONAL_EXCLUDE_IDS | BUSINESS_EXCLUDE_IDS
    other_excluded = [
        row
        for row in recon
        if float(row.get("included_in_income_statement") or 0) == 0
        and row.get("id") not in known
    ]

    revenue_rows = "\n".join(
        f"<tr><td>{esc(line.get('label') or line.get('id'))}</td>"
        f"<td>{esc(line.get('category', ''))}</td>"
        f"<td class='num'>{money(line.get('amount'))}</td>"
        f"<td class='sources'>{render_sources(line.get('sources') or [])}</td></tr>"
        for line in revenue_lines
    )
    expense_rows = "\n".join(
        f"<tr><td>{esc(line.get('label') or line.get('id'))}</td>"
        f"<td>{esc(line.get('category', ''))}</td>"
        f"<td class='num'>{money(line.get('amount'))}</td>"
        f"<td class='sources'>{render_sources(line.get('sources') or [])}</td></tr>"
        for line in expenses
    )
    judgment_rows = "\n".join(
        f"<tr><td>{esc(j.get('transaction_id') or '')}</td>"
        f"<td>{esc(j.get('reconciliation_id') or '')}</td>"
        f"<td class='num'>{money(j.get('included_in_income_statement'))}</td>"
        f"<td class='num'>{money(j.get('amount_used_in_income_statement'))}</td>"
        f"<td>{esc(j.get('confidence_level') or '')}</td>"
        f"<td>{esc(j.get('student_decision') or '')}</td></tr>"
        for j in judgments
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Spoke &amp; Wrench — January 2026 Income Statement Summary</title>
  <style>
    :root {{
      --ink: #1c1917;
      --muted: #57534e;
      --line: #d6d3d1;
      --bg: #fafaf9;
      --card: #ffffff;
      --accent: #0f766e;
      --neg: #b91c1c;
      --pos: #047857;
      --soft: #f5f5f4;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
      color: var(--ink);
      background: linear-gradient(180deg, #ecfdf5 0%, var(--bg) 220px);
      line-height: 1.35;
    }}
    main {{
      max-width: 960px;
      margin: 0 auto;
      padding: 1.25rem 1rem 2rem;
    }}
    header {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 1rem 1.15rem;
      margin-bottom: 1rem;
    }}
    h1 {{
      margin: 0 0 0.25rem;
      font-size: 1.45rem;
      letter-spacing: -0.02em;
    }}
    .subtitle {{ color: var(--muted); margin: 0; font-size: 0.95rem; }}
    .kpis {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0.65rem;
      margin-top: 0.9rem;
    }}
    .kpi {{
      background: var(--soft);
      border-radius: 10px;
      padding: 0.7rem 0.8rem;
    }}
    .kpi .label {{
      color: var(--muted);
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .kpi .value {{ font-size: 1.25rem; font-weight: 700; margin-top: 0.15rem; }}
    section {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 0.9rem 1rem 1rem;
      margin-bottom: 0.85rem;
    }}
    h2 {{
      margin: 0 0 0.55rem;
      font-size: 1.05rem;
      color: var(--accent);
    }}
    p.note {{ margin: 0 0 0.6rem; color: var(--muted); font-size: 0.9rem; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 0.4rem 0.35rem;
      vertical-align: top;
      text-align: left;
    }}
    th {{
      color: var(--muted);
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      font-weight: 600;
    }}
    td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
    td.sources {{ color: var(--muted); font-size: 0.8rem; }}
    tfoot td {{
      font-weight: 700;
      border-bottom: none;
      padding-top: 0.55rem;
    }}
    .neg {{ color: var(--neg); }}
    .pos {{ color: var(--pos); }}
    .grid-2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.85rem;
    }}
    @media (max-width: 800px) {{
      .kpis, .grid-2 {{ grid-template-columns: 1fr; }}
    }}
    @media print {{
      body {{ background: white; }}
      main {{ max-width: none; padding: 0; }}
      section, header {{ break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Spoke &amp; Wrench — January 2026 summary</h1>
      <p class="subtitle">One-page report from reconciled homework outputs. All dollar amounts match the JSON files.</p>
      <div class="kpis">
        <div class="kpi"><div class="label">Period</div><div class="value">{esc(period)}</div></div>
        <div class="kpi"><div class="label">Revenue</div><div class="value">{money(revenue)}</div></div>
        <div class="kpi"><div class="label">Net income</div><div class="value {net_class}">{money(net_income)}</div></div>
      </div>
    </header>

    <section>
      <h2>1. January income statement</h2>
      <p class="note">Built from <code>income_statement.json</code> using only reconciliation rows booked to the P&amp;L.</p>
      <table>
        <thead>
          <tr><th>Revenue line</th><th>Category</th><th class="num">Amount</th><th>Sources</th></tr>
        </thead>
        <tbody>
          {revenue_rows}
        </tbody>
        <tfoot>
          <tr><td colspan="2">Total revenue</td><td class="num">{money(revenue)}</td><td></td></tr>
        </tfoot>
      </table>
      <table style="margin-top:0.75rem;">
        <thead>
          <tr><th>Expense line</th><th>Category</th><th class="num">Amount</th><th>Sources</th></tr>
        </thead>
        <tbody>
          {expense_rows}
        </tbody>
        <tfoot>
          <tr><td colspan="2">Total expenses</td><td class="num">{money(total_expenses)}</td><td></td></tr>
          <tr><td colspan="2">Net income</td><td class="num {net_class}">{money(net_income)}</td><td></td></tr>
        </tfoot>
      </table>
    </section>

    <section>
      <h2>2. Rows excluded from the income statement</h2>
      <p class="note">These reconciliation items have <code>included_in_income_statement = 0</code>. Doc amounts are what appeared in source files; booked stays $0.00.</p>
      <div class="grid-2">
        <div>
          <h2 style="font-size:0.95rem;">Personal exclusions</h2>
          <table>
            <thead>
              <tr><th>Item</th><th class="num">Doc amount</th><th class="num">Booked</th><th>Why excluded</th></tr>
            </thead>
            <tbody>
              {excluded_table_rows(personal_excluded)}
            </tbody>
          </table>
        </div>
        <div>
          <h2 style="font-size:0.95rem;">Business exclusions</h2>
          <table>
            <thead>
              <tr><th>Item</th><th class="num">Doc amount</th><th class="num">Booked</th><th>Why excluded</th></tr>
            </thead>
            <tbody>
              {excluded_table_rows(business_excluded + other_excluded)}
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <section>
      <h2>3. Problem 6 judgment calls (student final say)</h2>
      <p class="note">From <code>judgment_calls.json</code>. All three reviewed at medium confidence; REI jacket moved to personal.</p>
      <table>
        <thead>
          <tr>
            <th>Transaction id</th>
            <th>Reconciliation id</th>
            <th class="num">Included</th>
            <th class="num">Amount used</th>
            <th>Confidence</th>
            <th>Student decision</th>
          </tr>
        </thead>
        <tbody>
          {judgment_rows}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render a one-page HTML summary from homework JSON outputs."
    )
    parser.add_argument(
        "--json-dir",
        default="output",
        help="Directory with income_statement.json, reconciliation_log.json, judgment_calls.json",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output HTML path, e.g. output/income_statement.html",
    )
    args = parser.parse_args(argv)

    json_dir = Path(args.json_dir).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()

    statement_path = json_dir / "income_statement.json"
    recon_path = json_dir / "reconciliation_log.json"
    judgment_path = json_dir / "judgment_calls.json"

    for path in (statement_path, recon_path, judgment_path):
        if not path.is_file():
            print(f"Missing required file: {path}", file=sys.stderr)
            return 1

    statement = load_json(statement_path)
    recon = load_json(recon_path)
    judgments = load_json(judgment_path)
    if not isinstance(recon, list) or not isinstance(judgments, list):
        print("reconciliation_log.json and judgment_calls.json must be arrays", file=sys.stderr)
        return 1

    html_text = build_html(statement, recon, judgments)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_text, encoding="utf-8")
    print(f"Wrote {out_path}")
    print(
        f"period={statement.get('period')} revenue={statement.get('revenue')} "
        f"total_expenses={statement.get('total_expenses')} net_income={statement.get('net_income')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
