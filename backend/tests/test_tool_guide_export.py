"""Per-tool guide files must not drift from backend/app/tool_content.py.

Regenerate with: .venv/bin/python scripts/seo/export-tool-guides.py
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from app import seo_meta
from app.tool_content import TOOL_FAQ, TOOL_HOWTO

ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "frontend" / "src" / "data" / "tool-guide"
SCRIPT = ROOT / "scripts" / "seo" / "export-tool-guides.py"


def _exporter():
    spec = importlib.util.spec_from_file_location("export_tool_guides", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _registry_slugs() -> set[str]:
    pdf, nonpdf = seo_meta._tool_registries()
    return set(pdf) | set(nonpdf)


def test_export_covers_exactly_the_registered_tools():
    exported = {path.stem for path in EXPORT_DIR.glob("*.json")}
    assert exported == _registry_slugs()


def test_export_content_matches_python_exactly():
    exporter = _exporter()
    drifted = [slug for slug in _registry_slugs()
               if (EXPORT_DIR / f"{slug}.json").read_text(encoding="utf-8") != exporter.guide_json(slug)]
    assert not drifted, f"Regenerate the export; stale: {drifted[:8]}"


def test_every_tool_has_steps_and_answers():
    for slug in _registry_slugs():
        guide = json.loads((EXPORT_DIR / f"{slug}.json").read_text(encoding="utf-8"))
        assert set(guide) == {"howto", "faq"}

        howto = TOOL_HOWTO.get(slug)
        assert howto is not None, f"{slug} is a registered tool but has no TOOL_HOWTO entry"
        faq = TOOL_FAQ.get(slug)
        assert faq is not None, f"{slug} is a registered tool but has no TOOL_FAQ entry"

        assert guide["howto"] == howto and len(guide["howto"]) >= 2
        assert guide["faq"] == faq and guide["faq"]
        for step in guide["howto"]:
            assert set(step) == {"name", "text"} and step["name"].strip() and len(step["text"].strip()) > 20
        for entry in guide["faq"]:
            assert set(entry) == {"q", "a"} and entry["q"].strip() and len(entry["a"].strip()) > 20
        questions = [entry["q"] for entry in guide["faq"]]
        assert len(questions) == len(set(questions)), f"{slug} asks the same question twice"
        step_names = [step["name"] for step in guide["howto"]]
        assert len(step_names) == len(set(step_names)), f"{slug} repeats a step name"
