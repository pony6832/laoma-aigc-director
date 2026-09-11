"""Query the platform-neutral cinematic craft catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "references" / "cinematic-grammar.json"


def load_catalog(path: Path = DEFAULT_CATALOG) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != "1.0" or not isinstance(data.get("methods"), list):
        raise ValueError("unsupported cinematic grammar catalog")
    return data


def search(catalog: dict, query: str, limit: int = 5) -> list[dict]:
    normalized = query.casefold().strip()
    if not normalized or limit < 1:
        return []
    ranked = []
    for index, method in enumerate(catalog["methods"]):
        score = sum(
            3 if keyword.casefold() in normalized else 0
            for keyword in method.get("keywords", [])
        )
        score += sum(
            1 if token and token in normalized else 0
            for token in method.get("title", "").casefold().split()
        )
        if score:
            ranked.append((-score, index, method))
    ranked.sort(key=lambda item: (item[0], item[1]))
    return [method for _, _, method in ranked[:limit]]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args(argv)
    try:
        results = search(load_catalog(args.catalog), args.query, args.limit)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
