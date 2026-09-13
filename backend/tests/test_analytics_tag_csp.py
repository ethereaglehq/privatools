"""A verified Google tag is still excluded from private documents."""
import importlib
import pytest

def directives(policy):
    return {parts[0]: set(parts[1:]) for item in policy.split(';') if (parts := item.split())}

@pytest.mark.parametrize('path', ['/', '/blog', '/tool/merge-pdf', '/privacy'])
def test_google_origins_require_operator_switch(monkeypatch, path):
    main = importlib.import_module('app.main')
    monkeypatch.delenv('GA_BROWSER_TAG_ENABLED', raising=False)
    assert 'googletagmanager.com' not in main._content_security_policy(path, 'nonce')
    monkeypatch.setenv('GA_BROWSER_TAG_ENABLED', 'true')
    policy = main._content_security_policy(path, 'nonce')
    parsed = directives(policy)
    assert 'https://www.googletagmanager.com' in parsed['script-src']
    assert 'https://www.google-analytics.com' in parsed['connect-src']
    assert 'https://region1.google-analytics.com' in parsed['connect-src']
    assert 'https:' not in parsed['script-src']

@pytest.mark.parametrize('path', ['/account', '/account/sign-in', '/account/settings', '/settings', '/my-stuff', '/my-stuff/vault'])
def test_private_documents_do_not_gain_google_csp_or_meta(monkeypatch, path):
    main = importlib.import_module('app.main')
    monkeypatch.setenv('GA_BROWSER_TAG_ENABLED', 'true')
    assert 'googletagmanager.com' not in main._content_security_policy(path, 'nonce')
    assert 'google-analytics.com' not in main._content_security_policy(path, 'nonce')
