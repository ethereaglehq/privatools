#!/usr/bin/env python3
"""Export one guide file per tool (steps + FAQ) for the frontend.

Python stays authoritative: backend/tests/test_tool_guide_export.py fails when
these files drift from backend/app/tool_content.py. Run from the repo root:

    .venv/bin/python scripts/seo/export-tool-guides.py          # write
    .venv/bin/python scripts/seo/export-tool-guides.py --check  # verify only
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app import seo_meta  # noqa: E402
from app.tool_content import TOOL_FAQ, TOOL_HOWTO  # noqa: E402

OUT = ROOT / "frontend" / "src" / "data" / "tool-guide"


def guide_json(slug: str) -> str:
    guide = {"howto": TOOL_HOWTO.get(slug, []), "faq": TOOL_FAQ.get(slug, [])}
    return json.dumps(guide, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 if any file is missing or stale")
    args = parser.parse_args()
    pdf, nonpdf = seo_meta._tool_registries()
    slugs = sorted(set(pdf) | set(nonpdf))
    OUT.mkdir(parents=True, exist_ok=True)
    stale: list[str] = []
    for slug in slugs:
        path = OUT / f"{slug}.json"
        content = guide_json(slug)
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                stale.append(slug)
        else:
            path.write_text(content, encoding="utf-8")
    extra = sorted(path.stem for path in OUT.glob("*.json") if path.stem not in set(slugs))
    for path in ([] if args.check else extra):
        (OUT / f"{path}.json").unlink()
    if args.check and (stale or extra):
        print(f"stale: {stale}\nextra: {extra}", file=sys.stderr)
        return 1
    print(f"{'checked' if args.check else 'wrote'} {len(slugs)} guide files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
