# Credit card charge extraction

You extract structured rows from a business credit card statement PDF (Spoke & Wrench / Jordan Lee).

## Task

Given the full text of the January credit card statement, extract **one JSON object per charge line**. Ignore statement headers, balances, payment-due info, and footer notes—do not emit rows for those.

## Output

Reply with a JSON **array** only (no markdown fences, no commentary). Each element:

```json
{
  "date": "charge date as shown",
  "merchant": "merchant name on the statement",
  "amount_usd": 0.00,
  "classification": "business",
  "expense_category": "cogs_parts"
}
```

### Field rules

- `date`: charge date from the line.
- `merchant`: merchant name exactly as shown (or a faithful short form of that name)—do not invent merchants.
- `amount_usd`: charge amount in US dollars as a positive number.
- `classification`: `business` or `personal`. The card is used for shop and household purchases. Mark clearly household/personal spend (groceries, consumer streaming, etc.) as `personal`. Mark shop/vendor/operating spend as `business`. Use only cues from the statement text—do not invent facts.
- `expense_category`: for **business** rows, a shop-useful expense label (examples: `cogs_parts`, `tools_equipment`, `shipping`, `office_supplies`, `marketing`, `software`, `fuel`, `utilities`). Do **not** copy the issuer’s broad category (e.g. “Merchandise / electronics”) as the expense_category. For **personal** rows, set `expense_category` to `null`.

### Hard constraints

- Do **not** invent charges that are not on the statement.
- Do **not** invent dates, merchants, or amounts.
- Issuer categories on the statement are too broad for reconciliation—replace them with a better shop label only when classification is `business`.
- Output **only** the JSON array.
