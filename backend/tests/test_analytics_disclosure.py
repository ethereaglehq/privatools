"""Analytics statements outside the Privacy page stay literally true.

The Privacy page (React and server-rendered) and llms.txt are checked in
test_seo_meta.py and the frontend tests. These cover the README bullet that
summarises analytics and the runbook notes operators rely on after a deploy.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _readme_analytics_bullet() -> str:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    return next(line for line in readme.splitlines() if "Google Analytics by default" in line)


def test_readme_scopes_arrival_data_to_each_page_load():
    bullet = _readme_analytics_bullet()
    # A reload or a new tab is a new page load; "visit" suggested a session.
    assert "first page view of each page load" in bullet
    assert "first of each visit" not in bullet


def test_readme_does_not_promise_a_category_for_every_failure():
    bullet = _readme_analytics_bullet()
    assert "for most failed runs, a fixed failure category" in bullet
    assert "for a failed run, a fixed failure category" not in bullet


def test_runbook_explains_why_automated_checks_see_no_tag():
    runbook = (ROOT / "deploy" / "analytics.md").read_text(encoding="utf-8")
    assert "--disable-blink-features=AutomationControlled" in runbook
    assert "Playwright" in runbook


def test_runbook_checks_whether_the_crawler_disappears_after_deploy():
    runbook = (ROOT / "deploy" / "analytics.md").read_text(encoding="utf-8")
    assert "Singapore" in runbook
    assert "1280x1200" in runbook
    assert "one page view per user" in runbook
