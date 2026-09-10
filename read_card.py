#!/usr/bin/env python3
"""Extract credit card charge rows using an LLM prompt."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from openai import OpenAI
from pypdf import PdfReader

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "card_extract.md"
DEFAULT_MODEL = os.environ.get(
    "CARD_LLM_MODEL",
    os.environ.get("BANK_LLM_MODEL", os.environ.get("RECEIPTS_LLM_MODEL", "gpt-4o-mini")),
)
CARD_PDF_CANDIDATES = (
    "credit_card_jan2026.pdf",
    "creditcard_jan2026.pdf",
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
            "Set PORTKEY_API_KEY or OPENAI_API_KEY before running read_card.py"
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

    required = ("date", "merchant", "amount_usd", "classification", "expense_category")
    missing = [key for key in required if key not in row]
    if missing:
        raise ValueError(f"Row missing keys {missing}: {row}")

    out = {
        "date": row["date"],
        "merchant": row["merchant"],
        "amount_usd": abs(float(row["amount_usd"])),
        "classification": str(row["classification"]).strip().lower(),
        "expense_category": row["expense_category"],
    }

    if out["classification"] not in {"business", "personal"}:
        raise ValueError(f"Invalid classification: {out['classification']!r}")

    if out["classification"] == "personal":
        out["expense_category"] = None
    elif out["expense_category"] in ("", None):
        raise ValueError(f"Business row missing expense_category: {row}")
    else:
        out["expense_category"] = str(out["expense_category"]).strip()

    return out


def find_card_pdf(docs_dir: Path) -> Path:
    pdfs_dir = docs_dir / "pdfs"
    search_roots = [pdfs_dir, docs_dir] if pdfs_dir.is_dir() else [docs_dir]
    for root in search_roots:
        for name in CARD_PDF_CANDIDATES:
            candidate = root / name
            if candidate.is_file():
                return candidate
        matches = sorted(root.rglob("*credit*card*.pdf")) + sorted(
            root.rglob("*creditcard*.pdf")
        )
        if matches:
            return matches[0]
    raise FileNotFoundError(
        "Could not find credit card statement PDF "
        f"(tried {', '.join(CARD_PDF_CANDIDATES)}) under {docs_dir}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract credit card charges from a document pack via LLM."
    )
    parser.add_argument(
        "--docs-dir",
        required=True,
        help="Unzipped document pack directory (contains pdfs/, emails/, manifest.json).",
    )
    parser.add_argument(
        "--out-dir",
        default="output",
        help="Directory for credit_card_transactions.json (default: output).",
    )
    args = parser.parse_args(argv)

    docs_dir = Path(args.docs_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    if not docs_dir.is_dir():
        print(f"docs-dir not found: {docs_dir}", file=sys.stderr)
        return 1

    card_pdf = find_card_pdf(docs_dir)
    text = extract_pdf_text(card_pdf)
    if not text:
        print(f"No extractable text in {card_pdf}", file=sys.stderr)
        return 1

    system_prompt = load_prompt()
    client = make_client()
    user_content = (
        f"source_file: {card_pdf.name}\n\n"
        f"Credit card statement PDF text:\n{text}"
    )
    raw = call_llm(client, system_prompt, user_content)
    try:
        parsed = parse_llm_json_array(raw)
        rows = [normalize_row(row) for row in parsed]
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"Could not parse LLM output: {exc}", file=sys.stderr)
        print(f"Raw: {raw[:1000]}", file=sys.stderr)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "credit_card_transactions.json"
    out_path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"Read {card_pdf}")
    print(f"Wrote {len(rows)} credit card charge row(s) to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
