"""Inspect inert public-script fixtures; no requests, SDK execution or GA settings edits."""
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts/check-public-google-tag.py'
spec = importlib.util.spec_from_file_location('public_google_tag_check', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def inspect(tags):
    return module.inspect_public_script('var data = ' + json.dumps({'resource': {'tags': tags}}) + ';')


def test_user_retained_three_features_pass_without_being_suppressed():
    result = inspect([{'function': '__ccd_em_' + feature} for feature in ['scroll', 'outbound_click', 'video']])
    assert result['safeToEnable'] is True
    assert result['configurationCheckPassed'] is True
    assert {item['feature'] for item in result['retainedAutomaticFeatures']} == {'scroll', 'outbound_click', 'video'}
    assert all(item['enabled'] for item in result['retainedAutomaticFeatures'])
    assert result['requiresSettingsReview'] == []
    assert result['activationApproved'] is False
    assert result['actualSdkVerificationRequired'] is True
    assert result['collectionRequestsSent'] == 0


@pytest.mark.parametrize('feature', ['form', 'forms', 'download', 'file_download', 'site_search', 'future_automatic_tracker'])
def test_forbidden_or_unknown_automatic_features_fail(feature):
    result = inspect([{'function': '__ccd_em_' + feature}, {'function': '__ccd_em_scroll'}])
    assert result['safeToEnable'] is False
    assert result['requiresSettingsReview'] == [{'feature': feature, 'enabled': True}]
    assert result['retainedAutomaticFeatures'][0]['feature'] == 'scroll'


@pytest.mark.parametrize('history,passed', [(True, False), (False, True), ('false', False), (None, False)])
def test_history_configuration_must_be_recognized_and_off(history, passed):
    result = inspect([{'function': '__ccd_em_page_view', 'vtp_historyEvents': history}])
    assert result['configurationCheckPassed'] is passed


@pytest.mark.parametrize('enabled,automatic,passed', [(True, False, True), (True, True, False), (False, False, True), ('true', False, False), (True, None, False)])
def test_automatic_user_data_is_off_while_broader_capability_can_remain(enabled, automatic, passed):
    result = inspect([{'function': '__ogt_1p_data_v2', 'vtp_isEnabled': enabled, 'vtp_isAutoEnabled': automatic,
                       'vtp_isAutoCollectPiiEnabledFlag': True}])
    assert result['configurationCheckPassed'] is passed
    if enabled is True and automatic is False:
        assert result['userDataCapabilities'] == [{'feature': 'user_provided_data_capability', 'enabled': True, 'automaticDetectionEnabled': False}]


@pytest.mark.parametrize('source', ['alert("never execute")', 'var data = nope;', 'var data = {}', 'var data = {"resource":{"tags":[]}}', 'var data = {"resource":{"tags":[null]}}', 'var data = {"resource":{"tags":{"function":"__ccd_em_scroll"}}}'])
def test_unknown_format_fails_closed(source):
    result = module.inspect_public_script(source)
    assert result['configurationCheckPassed'] is False
    assert result['requiresSettingsReview'][0]['feature'] == 'unknown_public_tag_format'
    assert result['retainedAutomaticFeatures'] == []
