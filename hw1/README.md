# MGT 409 — Homework 1 (Spoke & Wrench January books)

This folder is the complete, gradeable package for Homework 1.
Work was done **step by step** (Problems 2→9). Outputs from each stage are saved under `output/`, prompts are in `prompts/` and `AI_prompts.md`, and scripts can be re-run in order.

## What’s included

| Path | What it is |
|---|---|
| `read_receipts.py` | Problem 2 — LLM receipt extraction |
| `read_bank.py` | Problem 3 — LLM bank extraction |
| `read_card.py` | Problem 4 — LLM credit-card extraction |
| `reconcile.py` | Problem 5 — LLM reconciliation |
| `income_statement.py` | Problem 7 — Python income statement |
| `report.py` | Problem 8 — HTML summary page |
| `run_pipeline.sh` | Runs Problems 2→8 in order |
| `prompts/*.md` | LLM prompt files used by the scripts |
| `AI_prompts.md` | Log of prompts typed in my own words |
| `output/*.json` | Saved outputs from each step |
| `output/income_statement.html` | Human-readable January summary |
| `output/pipeline.html` | Diagram of the whole process |
| `output/judgment_calls.json` | Problem 6 student judgment decisions |
| `docs_pack/` | Unzipped source document pack |
| `requirements.txt` | Python dependencies |

## Install

```bash
cd hw1
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### API key (needed only to re-run LLM steps 2–5)

```bash
export OPENAI_API_KEY="your-key-here"
# or
export PORTKEY_API_KEY="your-key-here"
```

You can open and grade the existing `output/` files without an API key.

## Re-run the full pipeline (Problems 2–8)

```bash
chmod +x run_pipeline.sh
./run_pipeline.sh
# or with a custom unzipped pack:
./run_pipeline.sh /path/to/unzipped/docs_pack
```

This runs, in order:

1. `read_receipts.py` → `output/receipts.json`
2. `read_bank.py` → `output/bank_transactions.json`
3. `read_card.py` → `output/credit_card_transactions.json`
4. `reconcile.py` → `output/reconciliation_log.json`
5. keeps `output/judgment_calls.json` (Problem 6 was human review)
6. `income_statement.py` → `output/income_statement.json`
7. `report.py` → `output/income_statement.html`

## Run one step at a time

```bash
python read_receipts.py --docs-dir docs_pack --out-dir output
python read_bank.py --docs-dir docs_pack --out-dir output
python read_card.py --docs-dir docs_pack --out-dir output
python reconcile.py --docs-dir docs_pack --json-dir output --out-dir output
python income_statement.py --json-dir output --out-dir output
python report.py --json-dir output --out output/income_statement.html
```

## What to review for grading

1. **Step-by-step prompts:** `AI_prompts.md`
2. **LLM prompt files:** `prompts/`
3. **Process diagram:** open `output/pipeline.html`
4. **Final statement:** open `output/income_statement.html`
5. **Judgment calls (Problem 6):** `output/judgment_calls.json`
6. **Intermediate JSON:** `output/receipts.json`, `bank_transactions.json`, `credit_card_transactions.json`, `reconciliation_log.json`, `income_statement.json`

## Notes

- Problems 2–5 use an LLM. Problems 7–8 are deterministic Python.
- Problem 6 is human judgment (confidence review); decisions are stored in `judgment_calls.json` and already applied in the reconciliation/P&L outputs.
- January P&L from the saved run: revenue **$645.00**, expenses **$1,608.10**, net income **-$963.10**.
