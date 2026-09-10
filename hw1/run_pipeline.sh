#!/usr/bin/env bash
# Run homework Problems 2–8 in order.
# Usage:
#   ./run_pipeline.sh                  # uses ./docs_pack and writes ./output
#   ./run_pipeline.sh /path/to/docs    # custom unzipped document pack
#
# Requires: Python 3.10+, deps from requirements.txt, and OPENAI_API_KEY
# (or PORTKEY_API_KEY) for LLM steps (Problems 2–5).
#
# Problem 6 is a human judgment step — this script keeps existing
# output/judgment_calls.json rather than regenerating it.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

DOCS_DIR="${1:-docs_pack}"
OUT_DIR="output"
PYTHON="${PYTHON:-python3}"

if [[ ! -d "$DOCS_DIR" ]]; then
  echo "Document pack not found: $DOCS_DIR" >&2
  echo "Unzip the homework pack into docs_pack/ (or pass its path as arg 1)." >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

echo "=== Problem 2: read_receipts.py (LLM) ==="
"$PYTHON" read_receipts.py --docs-dir "$DOCS_DIR" --out-dir "$OUT_DIR"

echo "=== Problem 3: read_bank.py (LLM) ==="
"$PYTHON" read_bank.py --docs-dir "$DOCS_DIR" --out-dir "$OUT_DIR"

echo "=== Problem 4: read_card.py (LLM) ==="
"$PYTHON" read_card.py --docs-dir "$DOCS_DIR" --out-dir "$OUT_DIR"

echo "=== Problem 5: reconcile.py (LLM) ==="
"$PYTHON" reconcile.py --docs-dir "$DOCS_DIR" --json-dir "$OUT_DIR" --out-dir "$OUT_DIR"

echo "=== Problem 6: judgment_calls.json (human) ==="
if [[ -f "$OUT_DIR/judgment_calls.json" ]]; then
  echo "Keeping existing $OUT_DIR/judgment_calls.json (student final say)."
else
  echo "WARNING: $OUT_DIR/judgment_calls.json missing. Add Problem 6 decisions before grading P&L." >&2
fi

echo "=== Problem 7: income_statement.py (Python math) ==="
"$PYTHON" income_statement.py --json-dir "$OUT_DIR" --out-dir "$OUT_DIR"

echo "=== Problem 8: report.py (HTML) ==="
"$PYTHON" report.py --json-dir "$OUT_DIR" --out "$OUT_DIR/income_statement.html"

echo
echo "Pipeline complete."
echo "Review:"
echo "  - $OUT_DIR/pipeline.html          (process diagram)"
echo "  - $OUT_DIR/income_statement.html  (January summary)"
echo "  - $OUT_DIR/*.json                 (step outputs)"
echo "  - AI_prompts.md                   (prompts typed step by step)"
echo "  - prompts/*.md                    (LLM prompt files)"
