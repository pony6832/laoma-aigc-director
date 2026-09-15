#!/usr/bin/env python3
"""Query the normalized visual-prompt reference catalog."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "references" / "visual-prompt-catalog.json"


def load_catalog(path: str | Path = DEFAULT_CATALOG) -> dict:
    catalog = json.loads(Path(path).read_text(encoding="utf-8"))
    defaults = catalog["category_defaults"]
    expanded = []
    for raw in catalog["items"]:
        item = dict(raw)
        item.setdefault("source_sections", [item["category"]])
        item.setdefault("risk_qc", defaults[item["category"]])
        item.setdefault("invocation_zh", catalog["invocation_template_zh"].format(**item))
        expanded.append(item)
    catalog["items"] = expanded
    return catalog


def _tokens(query: str) -> list[str]:
    return [token for token in re.split(r"[\s,，、/]+", query.casefold()) if token]


def search(query: str, catalog: dict | None = None, limit: int = 8) -> list[dict]:
    if not query.strip() or limit <= 0:
        return []
    catalog = catalog or load_catalog()
    tokens = _tokens(query)
    scored = []
    for item in catalog["items"]:
        primary = " ".join(
            [item["canonical_key"], item["shortcut"], item["name_zh"], item["category"]]
        ).casefold()
        secondary = " ".join(
            [item["function"], item["prompt_fragment"], item["risk_qc"], *item["source_sections"]]
        ).casefold()
        score = sum(4 for token in tokens if token in primary)
        score += sum(1 for token in tokens if token in secondary)
        if score:
            scored.append((score, item["id"], item))
    scored.sort(key=lambda row: (-row[0], row[1]))
    return [row[2] for row in scored[:limit]]


def main() -> int:
    parser = argparse.ArgumentParser(description="Query visual prompt categories and fragments.")
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    args = parser.parse_args()
    print(json.dumps(search(args.query, load_catalog(args.catalog), args.limit), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
