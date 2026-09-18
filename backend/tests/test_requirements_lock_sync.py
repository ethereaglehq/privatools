"""`requirements.in` and its hashed lock `requirements.txt` must not drift apart.

Since PR #94 the Docker image and CI both install from the hashed lock with
`--require-hashes`; `requirements.in` is only the human-edited source of direct
deps (until September 2026 the two were `requirements.txt` and
`requirements.lock`). Nothing enforced that the two agreed, which made the split
silently dangerous in one specific way:

Dependabot's pip ecosystem edited the source file and never regenerated the
lock. Merging one of its PRs therefore had NO effect on what production runs,
left the two files disagreeing, and still passed CI — because CI reads the lock.
Every pip Dependabot PR (#39-#44, #135-#144, #188-#195) had exactly this shape.

The files now use the `name.in` -> `name.txt` layout with uv's compile header,
which Dependabot's uv ecosystem regenerates itself. This test still catches a
hand edit that skips the compile. When it fires, recompile the locks:

    uv pip compile --generate-hashes --universal --python-version 3.12 \\
        --output-file=requirements.txt requirements.in
    uv pip compile --generate-hashes --universal --python-version 3.12 \\
        --output-file=requirements-dev.txt requirements-dev.in
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Each hashed lock and the source it is compiled from.
_LOCKS = {
    "requirements.txt": "requirements.in",
    "requirements-dev.txt": "requirements-dev.in",
    "requirements-ci.txt": "requirements-ci.in",
}

# `name==version`, ignoring comments/blank lines. Extras are stripped: the lock
# records `uvicorn==0.27.1` where the source says `uvicorn[standard]==0.27.1`.
_PIN_RE = re.compile(r"^\s*([A-Za-z0-9._-]+)\s*(?:\[[^\]]*\])?\s*==\s*([^\s;#\\]+)")


def _parse_pins(path: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = _PIN_RE.match(stripped)
        if match:
            name, version = match.groups()
            pins[name.lower().replace("_", "-")] = version
    return pins


def _assert_in_sync(source_name: str, lock_name: str) -> None:
    source = _parse_pins(REPO_ROOT / source_name)
    lock = _parse_pins(REPO_ROOT / lock_name)
    assert source, f"{source_name} parsed to zero pins — the parser or the file is wrong"
    assert lock, f"{lock_name} parsed to zero pins — the parser or the file is wrong"

    missing = sorted(name for name in source if name not in lock)
    assert not missing, (
        f"{missing} pinned in {source_name} but absent from {lock_name}. "
        f"Regenerate the lock (see this module's docstring)."
    )

    drifted = sorted(
        f"{name}: {source_name}=={source[name]} but {lock_name}=={lock[name]}"
        for name in source
        if lock[name] != source[name]
    )
    assert not drifted, (
        "Direct dependencies disagree with the lock the image actually installs "
        f"from, so these bumps would NOT reach production:\n  " + "\n  ".join(drifted)
    )


def test_runtime_requirements_match_lock():
    _assert_in_sync("requirements.in", "requirements.txt")


# `requirements-dev.in` declares RANGES (pytest>=8.0,<9), not exact pins, so it
# gets a presence check rather than a version-equality one. A range bump that
# never reaches the lock is the same class of bug — Dependabot PR #43 is exactly
# this — and shows up as the named package resolving to an out-of-range version.
_NAME_RE = re.compile(r"^\s*([A-Za-z0-9._-]+)\s*(?:\[[^\]]*\])?\s*(?:[<>=!~]|$)")


def _declared_names(path: Path) -> set[str]:
    names: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "-r ", "--")):
            continue
        match = _NAME_RE.match(stripped)
        if match:
            names.add(match.group(1).lower().replace("_", "-"))
    return names


def test_dev_requirements_present_in_dev_lock():
    declared = _declared_names(REPO_ROOT / "requirements-dev.in")
    locked = _parse_pins(REPO_ROOT / "requirements-dev.txt")
    assert declared, "requirements-dev.in parsed to zero names"
    missing = sorted(declared - locked.keys())
    assert not missing, (
        f"{missing} declared in requirements-dev.in but absent from "
        "requirements-dev.txt. Regenerate the lock (see this module's docstring)."
    )


def test_dev_lock_is_a_superset_of_the_runtime_lock():
    """requirements-dev.in starts with `-r requirements.in`, so every runtime
    pin must also appear in the dev lock at the SAME version — otherwise CI tests
    a different dependency set than the image ships."""
    runtime = _parse_pins(REPO_ROOT / "requirements.txt")
    dev = _parse_pins(REPO_ROOT / "requirements-dev.txt")
    drifted = sorted(
        f"{name}: runtime=={runtime[name]} but dev=={dev[name]}"
        for name in runtime
        if name in dev and dev[name] != runtime[name]
    )
    assert not drifted, (
        "CI would test different versions than the image ships:\n  " + "\n  ".join(drifted)
    )
    missing = sorted(name for name in runtime if name not in dev)
    assert not missing, f"runtime deps missing from the dev lock: {missing}"


def test_lock_is_fully_hashed():
    """`--require-hashes` fails on any entry lacking a hash, so catch it here."""
    for lock_name in _LOCKS:
        text = (REPO_ROOT / lock_name).read_text(encoding="utf-8")
        pins = _parse_pins(REPO_ROOT / lock_name)
        assert pins, f"{lock_name} parsed to zero pins"
        assert "--hash=" in text, f"{lock_name} has no hashes — --require-hashes would fail"


def test_locks_carry_the_compile_header_dependabot_reruns():
    """Dependabot's uv ecosystem regenerates a lock by rerunning `uv pip compile`
    with options it reads back out of the lock itself: --generate-hashes when it
    sees hashes, --universal and --python-version only when the header names
    them, and the output file matched through --output-file. A lock compiled
    by hand without those options would come back from Dependabot unhashed or
    resolved for its own interpreter instead of 3.12 on arm64 and amd64."""
    for lock_name, source_name in _LOCKS.items():
        header = (REPO_ROOT / lock_name).read_text(encoding="utf-8").splitlines()[:2]
        assert header[0] == "# This file was autogenerated by uv via the following command:", (
            f"{lock_name} was not written by `uv pip compile`"
        )
        assert header[1] == (
            "#    uv pip compile --generate-hashes --universal --python-version 3.12 "
            f"--output-file={lock_name} {source_name}"
        ), f"{lock_name} header is not the command in this module's docstring"


def test_dependabot_uses_the_ecosystem_that_regenerates_the_locks():
    """The pip ecosystem edits the .in pins and leaves the hashed locks alone,
    which this module's first test then fails; the uv ecosystem recompiles."""
    config = (REPO_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    assert "package-ecosystem: uv" in config
    assert "package-ecosystem: pip" not in config


def test_ci_requirements_match_lock():
    """CI tooling is hash-pinned too, and drifts the same way if unwatched.

    security.yml installs pip-audit with `--require-hashes -r
    requirements-ci.txt` rather than a bare `pip install pip-audit`, because
    that tool runs in CI with repository context — a compromised PyPI release
    would execute there. That protection is only real while the lock matches
    requirements-ci.in, so hold it to the same contract as the other two.
    """
    _assert_in_sync("requirements-ci.in", "requirements-ci.txt")


def test_ci_lock_pins_pip_audit():
    """The whole point of the CI lock is pip-audit; fail loudly if it vanishes."""
    pins = _parse_pins(REPO_ROOT / "requirements-ci.txt")
    assert "pip-audit" in pins, (
        "requirements-ci.txt no longer pins pip-audit — security.yml installs "
        "from this file and would silently stop auditing."
    )


def test_parser_detects_a_simulated_dependabot_bump(tmp_path):
    """Guards the guard: a source-only bump must be caught, not silently pass."""
    source = tmp_path / "requirements.in"
    lock = tmp_path / "requirements.txt"
    source.write_text("pikepdf==10.9.1\nuvicorn[standard]==0.27.1\n")
    lock.write_text(
        "pikepdf==8.12.0 \\\n    --hash=sha256:abc\n"
        "uvicorn==0.27.1 \\\n    --hash=sha256:def\n"
    )

    source_pins = _parse_pins(source)
    lock_pins = _parse_pins(lock)

    # The extras form must normalise so uvicorn is NOT reported as drift.
    assert source_pins["uvicorn"] == lock_pins["uvicorn"] == "0.27.1"
    # The real bump must be visible.
    assert source_pins["pikepdf"] == "10.9.1"
    assert lock_pins["pikepdf"] == "8.12.0"
