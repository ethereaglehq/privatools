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


def zero_downtime_checks():
    """What rollout.sh needs on the VM, read-only (deploy/README.md, Zero-downtime deploys)."""
    import re
    import socket
    checks = []
    upstream = Path('/etc/nginx/privatools-upstream.conf')
    port = re.search(r'server\s+127\.0\.0\.1:(\d+);', upstream.read_text()) if upstream.is_file() else None
    checks.append({'check': 'nginx upstream file names 8000 or 8001',
                   'status': 'pass' if port and port.group(1) in ('8000', '8001') else 'fail'})
    site = Path('/etc/nginx/sites-enabled/privatools')
    text = site.read_text() if site.is_file() else ''
    checks.append({'check': 'nginx site proxies only through privatools_app',
                   'status': 'pass' if 'proxy_pass http://privatools_app;' in text and 'proxy_pass http://127.0.0.1:' not in text else 'fail'})
    helper = '/usr/local/sbin/privatools-nginx-upstream'
    checks.append(check_command('sudo -n allows the upstream switch', ['sudo', '-n', '-l', helper, 'set', '8001']))
    with socket.socket() as probe:
        probe.settimeout(2)
        taken = probe.connect_ex(('127.0.0.1', 8001)) == 0
    checks.append({'check': 'interim port 127.0.0.1:8001 free', 'status': 'fail' if taken else 'pass'})
    meminfo = Path('/proc/meminfo').read_text()
    available = int(re.search(r'^MemAvailable:\s+(\d+)', meminfo, re.M).group(1)) // 1024
    checks.append({'check': 'memory for a second container (MemAvailable >= 1536 MB)',
                   'status': 'pass' if available >= 1536 else 'fail', 'availableMb': available})
    return checks


def run(host=False):
    checks = []
    scripts = sorted((ROOT / 'deploy/oracle-vm').glob('*.sh'))
    for script in scripts:
        checks.append(check_command(f'shell syntax: {script.name}', ['bash', '-n', str(script)]))
    shellcheck = shutil.which('shellcheck')
    if shellcheck:
        linted = ['auto-deploy.sh', 'rollout.sh', 'nginx-upstream.sh', 'install-auto-deploy.sh', 'deploy.sh', 'backup-app-data.sh']
        checks.append(check_command('release shell lint', [shellcheck, *[str(ROOT / 'deploy/oracle-vm' / name) for name in linted]]))
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
    if host:
        checks.extend(zero_downtime_checks())
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
