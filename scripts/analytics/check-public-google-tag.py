#!/usr/bin/env python3
"""Read public tag configuration only; never execute it or send GA events.

Configuration inspection is not a supported Google configuration API, proof of
SDK request behavior or authorization to enable collection. Unknown syntax fails.
"""
import argparse
import hashlib
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RETAINED_AUTOMATIC_FEATURES = frozenset({'scroll', 'outbound_click', 'video'})


def inspect_public_script(script: str) -> dict:
    review = []
    retained = []
    capabilities = []
    try:
        beginning = script.index('{', script.index('var data ='))
        data, _ = json.JSONDecoder().raw_decode(script[beginning:])
        tags = data['resource']['tags']
        if not isinstance(tags, list) or not tags:
            raise ValueError('Missing tag list')
        if any(not isinstance(tag, dict) or not isinstance(tag.get('function'), str) for tag in tags):
            raise ValueError('Unknown tag structure')
    except (ValueError, KeyError, TypeError):
        tags = []
        review.append({'feature': 'unknown_public_tag_format', 'reason': 'Leave GA_BROWSER_TAG_ENABLED off and inspect the changed format.'})

    for tag in tags:
        name = tag['function']
        if name.startswith('__ccd_em_'):
            feature = name.removeprefix('__ccd_em_')
            if feature in RETAINED_AUTOMATIC_FEATURES:
                retained.append({'feature': feature, 'enabled': True, 'reason': 'Explicitly retained by the user.'})
            elif feature == 'page_view':
                history = tag.get('vtp_historyEvents')
                if not isinstance(history, bool):
                    review.append({'feature': 'unknown_history_pageview_configuration'})
                elif history:
                    review.append({'feature': 'history_pageviews', 'enabled': True})
            else:
                # Forms/download/search and any new automatic feature fail.
                # Presence of these configuration tags enables the feature;
                # do not infer a permissive default from undocumented fields.
                review.append({'feature': feature, 'enabled': True})
        if name.startswith('__ogt_1p_data'):
            enabled, automatic = tag.get('vtp_isEnabled'), tag.get('vtp_isAutoEnabled')
            if not isinstance(enabled, bool) or not isinstance(automatic, bool):
                review.append({'feature': 'unknown_user_provided_data_configuration'})
            else:
                capabilities.append({'feature': 'user_provided_data_capability', 'enabled': enabled,
                                     'automaticDetectionEnabled': automatic})
                # The broader capability may remain enabled; the user approved
                # disabling automatic detection, not changing that capability.
                if enabled and automatic:
                    review.append({'feature': 'automatic_user_provided_data', 'enabled': True})

    passed = not review
    return {
        'source': 'Public Google tag configuration (read-only GET or saved public script)',
        'sha256': hashlib.sha256(script.encode()).hexdigest(),
        'dashboardAccessed': False,
        'collectionRequestsSent': 0,
        # Compatibility field: its scope is explicitly configuration-only.
        'safeToEnable': passed,
        'configurationCheckPassed': passed,
        'activationApproved': False,
        'actualSdkVerificationRequired': True,
        'retainedAutomaticFeatures': retained,
        'userDataCapabilities': capabilities,
        'requiresSettingsReview': review,
        'limits': 'Configuration-only inspection of public script syntax. This does not activate tracking or prove SDK safety. Verify fresh real-browser requests with collection intercepted before enabling the runtime switch.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from-file', type=Path, help='Inspect a saved public script without networking')
    args = parser.parse_args()
    if args.from_file:
        script = args.from_file.read_text()
    else:
        source = (ROOT / 'frontend/src/lib/analyticsPrivacy.ts').read_text()
        measurement = re.search(r'GOOGLE_ANALYTICS_ID = "(G-[A-Z0-9]+)"', source)
        if not measurement:
            raise SystemExit('Existing public measurement configuration not found')
        url = 'https://www.googletagmanager.com/gtag/js?id=' + measurement[1]
        with urllib.request.urlopen(url, timeout=20) as response:
            script = response.read(2_000_000).decode()
    report = inspect_public_script(script)
    print(json.dumps(report, indent=2))
    return 0 if report['configurationCheckPassed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
