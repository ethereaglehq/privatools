#!/usr/bin/env python3
"""Insert seoTitle/metaDescription into the tool registries from JSON copy files."""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRIES = [ROOT / "frontend/src/data/tools.ts", ROOT / "frontend/src/data/non-pdf-tools.ts"]

def main(paths: list[str]) -> int:
    copy: dict[str, dict[str, str]] = {}
    for path in paths:
        copy.update(json.loads(Path(path).read_text(encoding="utf-8")))
    missing = []
    for registry in REGISTRIES:
        text = registry.read_text(encoding="utf-8")
        def insert(match: re.Match) -> str:
            slug = match.group(1)
            entry = copy.get(slug)
            if entry is None:
                missing.append(slug)
                return match.group(0)
            indent = match.group(2)
            title = json.dumps(entry["seoTitle"], ensure_ascii=False)
            desc = json.dumps(entry["metaDescription"], ensure_ascii=False)
            return f"{match.group(0)}\n{indent}seoTitle: {title},\n{indent}metaDescription: {desc},"
        # slug line ... longDescription line, capturing the indent of longDescription.
        pattern = re.compile(r'slug: "([a-z0-9-]+)",[\s\S]*?\n(\s*)longDescription: "(?:[^"\\]|\\.)*",')
        text = pattern.sub(insert, text)
        registry.write_text(text, encoding="utf-8")
    if missing:
        print("no copy for:", ", ".join(missing), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
