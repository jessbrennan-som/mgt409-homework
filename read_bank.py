#!/usr/bin/env python3
"""Extract bank statement transaction rows using an LLM prompt."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from openai import OpenAI
from pypdf import PdfReader

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "bank_extract.md"
DEFAULT_MODEL = os.environ.get("BANK_LLM_MODEL", os.environ.get("RECEIPTS_LLM_MODEL", "gpt-4o-mini"))
BANK_PDF_CANDIDATES = (
    "bank_statement_jan2026.pdf",
    "bankstatement_jan2026.pdf",
)


def load_prompt() -> str:
    if not PROMPT_PATH.is_file():
        raise FileNotFoundError(f"Missing prompt file: {PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding="utf-8")


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()


def make_client() -> OpenAI:
    api_key = os.environ.get("PORTKEY_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set PORTKEY_API_KEY or OPENAI_API_KEY before running read_bank.py"
        )
    if os.environ.get("PORTKEY_API_KEY"):
        return OpenAI(
            api_key=api_key,
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.portkey.ai/v1"),
            default_headers={"x-portkey-api-key": api_key},
        )
    return OpenAI(api_key=api_key)


def call_llm(client: OpenAI, system_prompt: str, user_content: str) -> str:
    resp = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        max_completion_tokens=4000,
    )
    return (resp.choices[0].message.content or "").strip()


def parse_llm_json_array(raw: str) -> list:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array, got {type(data).__name__}")
    return data


def normalize_row(row: dict) -> dict:
    if not isinstance(row, dict):
        raise ValueError("Each row must be a JSON object")

    allowed = (
        "date",
        "description",
        "amount_usd",
        "classification",
        "direction",
        "accounting_label",
    )
    out: dict = {}
    for key in allowed:
        if key not in row:
            continue
        value = row[key]
        if value is None or value == "":
            continue
        out[key] = value

    if "amount_usd" in out:
        try:
            out["amount_usd"] = abs(float(out["amount_usd"]))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid amount_usd: {out['amount_usd']!r}") from exc

    if "direction" in out:
        direction = str(out["direction"]).strip().lower()
        if direction not in {"credit", "debit"}:
            raise ValueError(f"Invalid direction: {out['direction']!r}")
        out["direction"] = direction

    if "classification" in out:
        classification = str(out["classification"]).strip().lower()
        if classification not in {"business", "personal"}:
            raise ValueError(f"Invalid classification: {out['classification']!r}")
        out["classification"] = classification

    return out


def find_bank_pdf(docs_dir: Path) -> Path:
    pdfs_dir = docs_dir / "pdfs"
    search_roots = [pdfs_dir, docs_dir] if pdfs_dir.is_dir() else [docs_dir]
    for root in search_roots:
        for name in BANK_PDF_CANDIDATES:
            candidate = root / name
            if candidate.is_file():
                return candidate
        matches = sorted(root.rglob("*bank*statement*.pdf")) + sorted(
            root.rglob("*bankstatement*.pdf")
        )
        if matches:
            return matches[0]
    raise FileNotFoundError(
        "Could not find bank statement PDF "
        f"(tried {', '.join(BANK_PDF_CANDIDATES)}) under {docs_dir}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract bank statement transactions from a document pack via LLM."
    )
    parser.add_argument(
        "--docs-dir",
        required=True,
        help="Unzipped document pack directory (contains pdfs/, emails/, manifest.json).",
    )
    parser.add_argument(
        "--out-dir",
        default="output",
        help="Directory for bank_transactions.json (default: output).",
    )
    args = parser.parse_args(argv)

    docs_dir = Path(args.docs_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    if not docs_dir.is_dir():
        print(f"docs-dir not found: {docs_dir}", file=sys.stderr)
        return 1

    bank_pdf = find_bank_pdf(docs_dir)
    text = extract_pdf_text(bank_pdf)
    if not text:
        print(f"No extractable text in {bank_pdf}", file=sys.stderr)
        return 1

    system_prompt = load_prompt()
    client = make_client()
    user_content = (
        f"source_file: {bank_pdf.name}\n\n"
        f"Bank statement PDF text:\n{text}"
    )
    raw = call_llm(client, system_prompt, user_content)
    try:
        parsed = parse_llm_json_array(raw)
        rows = [normalize_row(row) for row in parsed]
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Could not parse LLM output: {exc}", file=sys.stderr)
        print(f"Raw: {raw[:1000]}", file=sys.stderr)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "bank_transactions.json"
    out_path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"Read {bank_pdf}")
    print(f"Wrote {len(rows)} bank transaction row(s) to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
