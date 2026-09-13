#!/usr/bin/env python3
"""Read-only release preflight. Never builds, pulls, deploys, reloads or prints env values."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def check_command(name, command, cwd=ROOT):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=90)
    # Diagnostics can contain environment paths/values. Keep the machine report
    # limited to command identity and exit status; run a failed check privately.
    return {'check': name, 'status': 'pass' if result.returncode == 0 else 'fail', 'exitCode': result.returncode}


def run(host=False):
    checks = []
    scripts = sorted((ROOT / 'deploy/oracle-vm').glob('*.sh'))
    for script in scripts:
        checks.append(check_command(f'shell syntax: {script.name}', ['bash', '-n', str(script)]))
    shellcheck = shutil.which('shellcheck')
    if shellcheck:
        checks.append(check_command('release shell lint', [shellcheck, *[str(ROOT / 'deploy/oracle-vm' / name) for name in ['auto-deploy.sh', 'deploy.sh', 'backup-app-data.sh']]]))
    else:
        checks.append({'check': 'release shell lint', 'status': 'unavailable'})
    binaries = {name: shutil.which(name) is not None for name in ['docker', 'nginx', 'cosign']}
    for name, available in binaries.items():
        checks.append({'check': f'{name} available', 'status': 'pass' if available else 'unavailable'})
    if binaries['docker']:
        checks.append(check_command('Compose model (no environment output)', ['docker', 'compose', 'config', '--quiet']))
        if host:
            checks.append(check_command('Docker daemon', ['docker', 'info', '--format', '{{.Architecture}}']))
    if host and binaries['nginx']:
        checks.append(check_command('installed nginx configuration', ['nginx', '-t']))
        result = subprocess.run(['nginx', '-V'], capture_output=True, text=True, timeout=15)
        checks.append({'check': 'nginx real-IP module', 'status': 'pass' if '--with-http_realip_module' in result.stdout + result.stderr else 'fail'})
    dirty = subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT, capture_output=True, text=True, timeout=15)
    checks.append({'check': 'reviewed checkout is clean', 'status': 'pass' if dirty.returncode == 0 and not dirty.stdout else 'pending'})
    return {
        'mode': 'host-read-only' if host else 'source-read-only',
        'deployed': False,
        'checks': checks,
        'releaseReady': False,
        'reason': 'This preflight does not approve publication or verify secrets, provider flows, the signed candidate image, edge settings or database restoration.',
        'next': 'Complete deploy/README.md with an approved exact commit/tag/digest and recorded host checks before publication.'
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', action='store_true', help='Also check the installed Docker daemon and nginx configuration; still read-only.')
    options = parser.parse_args()
    report = run(options.host)
    print(json.dumps(report, indent=2))
    raise SystemExit(1 if any(c['status'] == 'fail' for c in report['checks']) else 0)
