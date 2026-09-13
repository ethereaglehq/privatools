"""AI configuration acquires its model runtime policy without provider egress."""
from pathlib import Path
import re

import pytest

from app.main import (
    _BYOK_ORIGINS, _BYOK_PATHS, _TESSERACT_PATHS, _TRANSFORMERS_PATHS,
    _content_security_policy,
)


def sources(path: str, directive: str) -> set[str]:
    policy = _content_security_policy(path, "test-nonce", "")
    match = re.search(rf"(?:^|;\s*){directive} ([^;]+)", policy)
    assert match
    return set(match.group(1).split())


@pytest.mark.parametrize("path", ["/ai", "/ai/"])
def test_ai_workspace_can_instantiate_downloaded_models(path: str):
    script = sources(path, "script-src")
    assert {"'wasm-unsafe-eval'", "https://cdn.jsdelivr.net", "blob:"} <= script
    assert "'unsafe-eval'" not in script
    assert {"https://huggingface.co", "https://*.hf.co", "https://cdn.jsdelivr.net"} <= sources(path, "connect-src")
    assert "blob:" in sources(path, "worker-src")


@pytest.mark.parametrize("path", ["/ai", "/ai/"])
def test_saving_provider_settings_does_not_grant_provider_network_access(path: str):
    assert not (set(_BYOK_ORIGINS) & sources(path, "connect-src"))


@pytest.mark.parametrize("path", ["/", "/tools", "/tool/merge-pdf", "/api", "/trust", "/settings", "/ai-other"])
def test_model_script_policy_stays_scoped(path: str):
    assert not ({"'wasm-unsafe-eval'", "https://cdn.jsdelivr.net", "blob:"} & sources(path, "script-src"))


def test_client_navigation_boundaries_match_server_policy_sets():
    # A stale client capability list can keep a tool inside a document whose
    # response policy blocks it, even though direct navigation works.
    source = (Path(__file__).resolve().parents[2] / "frontend/src/skins/cspRoutes.ts").read_text()
    for name, expected in [
        ("CSP_TRANSFORMER_PATHS", _TRANSFORMERS_PATHS),
        ("CSP_OCR_PATHS", _TESSERACT_PATHS),
        ("CSP_BYOK_PATHS", _BYOK_PATHS),
    ]:
        match = re.search(rf"export const {name} = \[([\s\S]*?)\] as const", source)
        assert match, f"No {name} list found"
        assert set(re.findall(r'"(/[^"]+)"', match.group(1))) == expected
