#!/usr/bin/env python3
"""Reconcile overlapping amounts across docs and prior JSON extracts via LLM."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from openai import OpenAI
from pypdf import PdfReader

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "reconcile.md"
DEFAULT_MODEL = os.environ.get(
    "RECONCILE_LLM_MODEL",
    os.environ.get(
        "CARD_LLM_MODEL",
        os.environ.get("BANK_LLM_MODEL", os.environ.get("RECEIPTS_LLM_MODEL", "gpt-4o-mini")),
    ),
)
REQUIRED_JSON_FILES = (
    "receipts.json",
    "bank_transactions.json",
    "credit_card_transactions.json",
)
REQUIRED_ROW_KEYS = (
    "id",
    "sources",
    "amounts_seen",
    "included_in_income_statement",
    "resolution",
)


def load_prompt() -> str:
    if not PROMPT_PATH.is_file():
        raise FileNotFoundError(f"Missing prompt file: {PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding="utf-8")


def make_client() -> OpenAI:
    api_key = os.environ.get("PORTKEY_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set PORTKEY_API_KEY or OPENAI_API_KEY before running reconcile.py"
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
        max_completion_tokens=6000,
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


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join((page.extract_text() or "") for page in reader.pages).strip()


def gather_doc_texts(docs_dir: Path) -> dict[str, str]:
    texts: dict[str, str] = {}
    search_roots = [docs_dir]
    for sub in ("pdfs", "emails"):
        candidate = docs_dir / sub
        if candidate.is_dir():
            search_roots.append(candidate)

    seen: set[Path] = set()
    for root in search_roots:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path in seen:
                continue
            seen.add(path)
            if path.suffix.lower() == ".pdf":
                texts[path.name] = extract_pdf_text(path)
            elif path.suffix.lower() in {".txt", ".md"} or path.name == "manifest.json":
                texts[path.name] = path.read_text(encoding="utf-8", errors="replace")
    return texts


def load_json_inputs(json_dir: Path) -> dict[str, object]:
    loaded: dict[str, object] = {}
    for name in REQUIRED_JSON_FILES:
        path = json_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"Missing required JSON input: {path}")
        loaded[name] = json.loads(path.read_text(encoding="utf-8"))
    return loaded


def normalize_row(row: dict) -> dict:
    if not isinstance(row, dict):
        raise ValueError("Each reconciliation row must be an object")
    missing = [key for key in REQUIRED_ROW_KEYS if key not in row]
    if missing:
        raise ValueError(f"Row missing keys {missing}: {row}")

    sources = row["sources"]
    if not isinstance(sources, list) or not all(isinstance(s, str) and s for s in sources):
        raise ValueError(f"sources must be a list of filenames: {row}")

    amounts_seen = row["amounts_seen"]
    if not isinstance(amounts_seen, dict) or not amounts_seen:
        raise ValueError(f"amounts_seen must be a non-empty object: {row}")
    normalized_amounts: dict[str, float] = {}
    for key, value in amounts_seen.items():
        normalized_amounts[str(key)] = abs(float(value))

    included = abs(float(row["included_in_income_statement"]))
    resolution = str(row["resolution"]).strip()
    if not resolution:
        raise ValueError(f"resolution must be non-empty: {row}")

    return {
        "id": str(row["id"]).strip(),
        "sources": list(sources),
        "amounts_seen": normalized_amounts,
        "included_in_income_statement": included,
        "resolution": resolution,
    }


def build_user_payload(json_inputs: dict[str, object], doc_texts: dict[str, str]) -> str:
    sections = [
        "Prior extraction JSON inputs:",
        json.dumps(json_inputs, indent=2),
        "",
        "Relevant document texts:",
    ]
    for name, text in doc_texts.items():
        sections.append(f"----- BEGIN {name} -----")
        sections.append(text if text else "[NO EXTRACTABLE TEXT]")
        sections.append(f"----- END {name} -----")
        sections.append("")
    sections.append(
        "Return only the JSON array of reconciliation rows for items that overlap "
        "or need an income-statement decision."
    )
    return "\n".join(sections)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reconcile overlapping document amounts into reconciliation_log.json."
    )
    parser.add_argument(
        "--docs-dir",
        required=True,
        help="Unzipped document pack directory (pdfs/, emails/, manifest.json).",
    )
    parser.add_argument(
        "--json-dir",
        default="output",
        help="Directory containing receipts.json, bank_transactions.json, "
        "credit_card_transactions.json (default: output).",
    )
    parser.add_argument(
        "--out-dir",
        default="output",
        help="Directory for reconciliation_log.json (default: output).",
    )
    args = parser.parse_args(argv)

    docs_dir = Path(args.docs_dir).expanduser().resolve()
    json_dir = Path(args.json_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()

    if not docs_dir.is_dir():
        print(f"docs-dir not found: {docs_dir}", file=sys.stderr)
        return 1
    if not json_dir.is_dir():
        print(f"json-dir not found: {json_dir}", file=sys.stderr)
        return 1

    try:
        json_inputs = load_json_inputs(json_dir)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    doc_texts = gather_doc_texts(docs_dir)
    if not doc_texts:
        print(f"No documents found under {docs_dir}", file=sys.stderr)
        return 1

    system_prompt = load_prompt()
    client = make_client()
    raw = call_llm(client, system_prompt, build_user_payload(json_inputs, doc_texts))
    try:
        parsed = parse_llm_json_array(raw)
        rows = [normalize_row(row) for row in parsed]
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"Could not parse LLM output: {exc}", file=sys.stderr)
        print(f"Raw: {raw[:2000]}", file=sys.stderr)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "reconciliation_log.json"
    out_path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} reconciliation row(s) to {out_path}")
    for row in rows:
        print(
            f"- {row['id']}: include {row['included_in_income_statement']} "
            f"from {', '.join(row['sources'])}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
