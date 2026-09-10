# Reconciliation log

You reconcile Spoke & Wrench January 2026 amounts that appear in more than one document, conflict across documents, or need a single income-statement booking decision.

## Inputs

You will receive:
1. JSON arrays from earlier extraction steps (`receipts.json`, `bank_transactions.json`, `credit_card_transactions.json`)
2. Text from relevant source documents (receipts, statements, emails, lease, quote, IOU, etc.)

## Task

Produce a JSON **array** of reconciliation rows. Each row is **one reconciled economic item** — not a dump of every raw line from the earlier JSON files.

Include a row when:
- The same purchase/payment appears in multiple places (e.g. receipt + credit card, or receipt + bank), or
- Amounts disagree across docs and you must choose what to book, or
- Something is easy to miscount (split orders, duplicates, mixed deposits, quotes/emails that are not January revenue, unpaid IOUs, unbilled CAM, personal vs business judgment calls)

Do **not** create a row for every ordinary bank/card line that has no overlap or special decision.

## Output schema

Each row must be an object with exactly these keys:

```json
{
  "id": "park_tool_card_vs_receipt",
  "sources": ["receipt_park_tool.pdf", "credit_card_jan2026.pdf"],
  "amounts_seen": {
    "receipt_park_tool.pdf": 88.7,
    "credit_card_jan2026.pdf": 127.4
  },
  "included_in_income_statement": 127.4,
  "resolution": "Plain English explanation of how docs were matched and why this amount is booked (or excluded)."
}
```

### Field rules

- `id`: short slug for the reconciled item (snake_case), like `park_tool_card_vs_receipt` or `speedy_courier_duplicate`.
- `sources`: list of **document filenames** actually used for that row (PDFs, emails, or the JSON extract filenames when that is the practical source key). Prefer original doc filenames when available.
- `amounts_seen`: object mapping each source filename → the dollar amount seen in that source for this item. Use numbers, not strings.
- `included_in_income_statement`: the single dollar amount to book after reconciliation. Use `0` if excluded from the January income statement (personal, duplicate, not yet revenue, not yet invoiced, owner draw, etc.).
- `resolution`: short plain English: how you matched the docs and why you chose the final amount.

## Guidance for common traps (use only if supported by the provided docs)

- Duplicate receipt + card: book once.
- Split shipments / partial receipts vs larger card charge: explain both amounts; book the correct January total without double-counting.
- Separate vendor orders paid different ways: do not merge into one expense.
- Mixed deposits that include personal amounts: reduce revenue accordingly when notes say so.
- Quotes / future work emails: not January revenue → `0`.
- Unpaid IOUs / unbilled CAM: follow the documents for whether January should include them.
- Personal purchases on the business card: `0` expense on the income statement.

## Hard constraints

- Do **not** invent documents, amounts, or matches that are not supported by the inputs.
- Do **not** output markdown fences or commentary—JSON array only.
- Prefer fewer, clearer reconciliation rows over exhaustive line-by-line restatement.
