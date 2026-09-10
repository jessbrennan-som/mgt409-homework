#!/usr/bin/env python3
"""Extract one JSON row per purchase-receipt PDF using an LLM prompt."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from openai import OpenAI
from pypdf import PdfReader

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "receipts_extract.md"
DEFAULT_MODEL = os.environ.get("RECEIPTS_LLM_MODEL", "gpt-4o-mini")


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
            "Set PORTKEY_API_KEY or OPENAI_API_KEY before running read_receipts.py"
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
        max_completion_tokens=800,
    )
    return (resp.choices[0].message.content or "").strip()


def parse_llm_json(raw: str) -> dict | None:
    text = raw.strip()
    if not text or text.lower() == "null":
        return None
    # Tolerate accidental markdown fences
    fence = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    if text.lower() == "null":
        return None
    data = json.loads(text)
    if data is None:
        return None
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object or null, got {type(data).__name__}")
    return data


def normalize_row(row: dict, source_file: str) -> dict:
    fields = ["vendor", "date", "description", "amount_usd", "category", "source_file"]
    out: dict = {}
    missing = list(row.get("Fields_not_found") or [])
    if not isinstance(missing, list):
        missing = [str(missing)]

    for key in fields:
        if key == "source_file":
            out[key] = source_file
            continue
        if key not in row or row[key] in ("", None):
            out[key] = None
            if key not in missing:
                missing.append(key)
        else:
            out[key] = row[key]

    if out.get("amount_usd") is not None:
        try:
            out["amount_usd"] = float(out["amount_usd"])
        except (TypeError, ValueError):
            out["amount_usd"] = None
            if "amount_usd" not in missing:
                missing.append("amount_usd")

    out["Fields_not_found"] = missing
    return out


def find_pdfs(docs_dir: Path) -> list[Path]:
    pdfs_dir = docs_dir / "pdfs"
    search_root = pdfs_dir if pdfs_dir.is_dir() else docs_dir
    return sorted(p for p in search_root.rglob("*.pdf") if p.is_file())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract purchase receipts from a document pack via LLM."
    )
    parser.add_argument(
        "--docs-dir",
        required=True,
        help="Unzipped document pack directory (contains pdfs/, emails/, manifest.json).",
    )
    parser.add_argument(
        "--out-dir",
        default="output",
        help="Directory for receipts.json (default: output).",
    )
    args = parser.parse_args(argv)

    docs_dir = Path(args.docs_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    if not docs_dir.is_dir():
        print(f"docs-dir not found: {docs_dir}", file=sys.stderr)
        return 1

    system_prompt = load_prompt()
    client = make_client()
    pdfs = find_pdfs(docs_dir)
    if not pdfs:
        print(f"No PDFs found under {docs_dir}", file=sys.stderr)
        return 1

    rows: list[dict] = []
    for pdf_path in pdfs:
        text = extract_pdf_text(pdf_path)
        user_content = (
            f"source_file: {pdf_path.name}\n\n"
            f"PDF text:\n{text if text else '[NO EXTRACTABLE TEXT]'}"
        )
        raw = call_llm(client, system_prompt, user_content)
        try:
            parsed = parse_llm_json(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"WARN: could not parse LLM output for {pdf_path.name}: {exc}", file=sys.stderr)
            print(f"Raw: {raw[:500]}", file=sys.stderr)
            continue
        if parsed is None:
            print(f"skip (not a purchase receipt): {pdf_path.name}")
            continue
        row = normalize_row(parsed, pdf_path.name)
        rows.append(row)
        print(f"extracted: {pdf_path.name} -> {row.get('vendor')} ${row.get('amount_usd')}")

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "receipts.json"
    out_path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} receipt row(s) to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
