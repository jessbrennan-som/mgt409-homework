# Bank statement transaction extraction

You extract structured rows from a business bank statement PDF (Spoke & Wrench Bicycle Repair).

## Task

Given the full text of the January bank statement, extract **one JSON object per posted transaction line**. Ignore beginning/ending balances, totals headers, account metadata, and footer notes unless they help classify a line—do not emit rows for those.

## Output

Reply with a JSON **array** only (no markdown fences, no commentary). Each element:

```json
{
  "date": "posting or transaction date as shown",
  "description": "description text shown on the statement",
  "amount_usd": 0.00,
  "classification": "business",
  "direction": "debit",
  "accounting_label": "rent"
}
```

### Field rules

- `date`: posting/transaction date from the line.
- `description`: the statement description text for that line (keep it faithful; do not invent merchants or details).
- `amount_usd`: absolute dollar amount as a **positive number** (never negative). Strip `+`/`-` and currency symbols.
- `direction`: `credit` if money in (deposit / positive on statement), `debit` if money out (withdrawal / negative on statement).
- `classification`: `business` or `personal`. Use statement cues (e.g. lines marked personal, owner draw, ATM personal cash → `personal`). Otherwise treat shop activity as `business`.
- `accounting_label`: short label for reconciliation work, based only on the line (examples: `rent`, `utilities`, `cogs_parts`, `tools_equipment`, `insurance`, `bank_fees`, `owner_draw`, `sales_revenue`, `service_revenue`). Prefer clear, reusable labels.

### Hard constraints

- Do **not** invent transactions that are not on the statement.
- Do **not** invent dates, amounts, or description text.
- If a field truly cannot be determined from the statement, **omit that key** (do not include `null`).
- Output **only** the JSON array.
