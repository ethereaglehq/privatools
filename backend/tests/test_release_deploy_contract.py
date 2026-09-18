"""Execute the actual deploy gate with inert command doubles; never use Docker/git/network.

These prove selection/signature/digest/rollback behavior, not a live VM rollout.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / 'deploy/oracle-vm/auto-deploy.sh'
NEW = 'a' * 40
OLD = 'b' * 40
DIGEST = 'ghcr.io/ethereaglehq/privatools@sha256:' + 'c' * 64
OLD_IMAGE = 'sha256:' + 'd' * 64

FAKE = r'''
import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
mode = os.getenv('FAKE_MODE', '')
root = pathlib.Path(os.environ['FAKE_ROOT'])
with (root / 'commands.jsonl').open('a') as f:
    f.write(json.dumps({'name': name, 'args': args, 'image': os.getenv('PRIVATOOLS_IMAGE'), 'sha': os.getenv('GIT_SHA')}) + '\n')
new, old = 'a' * 40, 'b' * 40
digest = 'ghcr.io/ethereaglehq/privatools@sha256:' + 'c' * 64
old_image = 'sha256:' + 'd' * 64
if name == 'git':
    if args[0] == 'rev-parse': print(old if args[-1] == 'HEAD' else new)
    elif args[0] == 'tag': print('' if mode == 'no_tag' else 'v9.9.9')
elif name == 'docker':
    if args[:3] == ['compose', 'ps', '-q']: print('existing-container')
    elif args[:2] == ['inspect', '--format']:
        if args[2] == '{{.Image}}': print(old_image)
        else: print('PRIVATOOLS_BUILD_SHA=' + old)
    elif args[:2] == ['image', 'inspect']:
        if '.RepoDigests' in args[-1]: print('' if mode == 'no_digest' else digest)
        else: print(old if mode == 'wrong_revision' else new)
    elif args[:2] == ['compose', 'up']:
        (root / 'active').write_text('old' if os.getenv('PRIVATOOLS_IMAGE') == old_image else 'new')
        if mode == 'startup_failed' and os.getenv('PRIVATOOLS_IMAGE') != old_image: sys.exit(1)
elif name == 'cosign':
    sys.exit(1 if mode == 'bad_signature' else 0)
elif name == 'curl':
    active = (root / 'active').read_text() if (root / 'active').exists() else 'old'
    if active == 'new' and mode in ('unhealthy', 'startup_failed'): sys.exit(22)
    print(json.dumps({'build_sha': new if active == 'new' else old}))
'''


def run_deploy(tmp_path, mode='', with_cosign=True, deploy_mode=None):
    fake_bin = tmp_path / 'bin'
    fake_bin.mkdir()
    for name in ['git', 'docker', 'curl', 'flock', 'sleep'] + (['cosign'] if with_cosign else []):
        script = fake_bin / name
        script.write_text(f'#!{sys.executable}\n' + FAKE)
        script.chmod(0o755)
    for name in ['date', 'head', 'sed', 'tr', 'seq', 'rm']:
        (fake_bin / name).symlink_to(shutil.which(name))
    env = {**os.environ, 'PATH': str(fake_bin), 'FAKE_ROOT': str(tmp_path), 'FAKE_MODE': mode,
           'REPO_DIR': str(tmp_path), 'LOCK_FILE': str(tmp_path / 'lock'), 'HEALTH_RETRIES': '1',
           'HEALTH_INTERVAL': '0', 'DEPLOY_PING_URL': '', 'DEPLOY_IMAGE_REPO_FALLBACK': ''}
    env.pop('DEPLOY_MODE', None)
    if deploy_mode is not None:
        env['DEPLOY_MODE'] = deploy_mode
    result = subprocess.run(['/bin/bash', str(DEPLOY)], env=env, capture_output=True, text=True)
    calls = [json.loads(line) for line in (tmp_path / 'commands.jsonl').read_text().splitlines()]
    return result, calls


def ups(calls):
    return [c for c in calls if c['name'] == 'docker' and c['args'][:2] == ['compose', 'up']]


def test_default_tag_gate_does_not_fall_back_to_branch(tmp_path):
    result, calls = run_deploy(tmp_path, 'no_tag')
    assert result.returncode == 0, result.stdout + result.stderr
    assert not ups(calls)
    assert not any(c['args'][:2] == ['reset', '--hard'] for c in calls)


def test_invalid_mode_does_not_deploy(tmp_path):
    result, calls = run_deploy(tmp_path, deploy_mode='typo')
    assert result.returncode == 1
    assert not ups(calls)


@pytest.mark.parametrize('mode,with_cosign', [('bad_signature', True), ('no_digest', True), ('', False)])
def test_missing_or_bad_signature_prerequisites_fail_closed(tmp_path, mode, with_cosign):
    result, calls = run_deploy(tmp_path, mode, with_cosign)
    assert result.returncode != 0
    assert not ups(calls)


def test_wrong_revision_waits_without_replacing_container(tmp_path):
    result, calls = run_deploy(tmp_path, 'wrong_revision')
    assert result.returncode == 0
    assert not ups(calls)
    assert 'not ready yet' in result.stdout


def test_verified_digest_is_exactly_the_image_run(tmp_path):
    result, calls = run_deploy(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    verify = next(c for c in calls if c['name'] == 'cosign')
    assert verify['args'][1] == DIGEST
    assert '@refs/tags/v' in verify['args'][3]
    assert ups(calls)[0]['image'] == DIGEST
    assert ups(calls)[0]['sha'] == NEW
    assert ups(calls)[0]['args'][-2:] == ['--pull', 'never']
    assert (tmp_path / '.privatools-auto-deploy.sha').read_text().strip() == NEW
    assert not any(c['args'][:2] == ['image', 'prune'] for c in calls)


@pytest.mark.parametrize('mode', ['unhealthy', 'startup_failed'])
def test_failed_readiness_restores_previous_immutable_image_and_sha(tmp_path, mode):
    result, calls = run_deploy(tmp_path, mode)
    assert result.returncode == 1
    assert 'ROLLBACK successful' in result.stdout
    assert len(ups(calls)) == 2
    assert ups(calls)[1]['image'] == OLD_IMAGE
    assert ups(calls)[1]['sha'] == OLD
    assert ups(calls)[1]['args'][-2:] == ['--pull', 'never']
    assert (tmp_path / '.privatools-auto-deploy.failed').read_text().strip() == NEW
    assert not (tmp_path / '.privatools-auto-deploy.sha').exists()


def test_release_calls_real_typecheck_and_has_no_nonblocking_test_jobs():
    workflow = (ROOT / '.github/workflows/test.yml').read_text()
    assert 'npx tsc --noEmit -p tsconfig.app.json' in workflow
    assert 'npm run lint -- --max-warnings 0' in workflow
    assert 'npm run test:content' in workflow
    assert 'continue-on-error' not in workflow
    ci = (ROOT / '.github/workflows/ci.yml').read_text()
    assert 'continue-on-error: true' not in ci
    assert 'npx playwright' not in ci
    release = (ROOT / '.github/workflows/release.yml').read_text()
    assert 'uses: ./.github/workflows/test.yml' in release
    assert 'needs: tests' in release


def test_release_gate_boots_the_built_image():
    # A build that compiles can still ship an image that never serves; the
    # gate runs it before the deploy's readiness check has to.
    workflow = (ROOT / '.github/workflows/test.yml').read_text()
    assert 'load: true' in workflow
    assert 'python3 scripts/ci/probe-image.py "$PROBE_IMAGE"' in workflow
    assert (ROOT / 'scripts/ci/probe-image.py').is_file()


def test_local_private_data_is_excluded_from_build_context():
    ignored = set((ROOT / '.dockerignore').read_text().splitlines())
    assert {'.venv/', 'data/', 'backups/', 'docs/', '**/.env*', '**/*.db', '**/*.db-wal', '**/*.db-shm',
            '.secrets/', '.claude/', '.codex/', '.agents/', 'frontend/.impeccable/'} <= ignored


def test_runtime_image_requires_actual_media_capabilities():
    docker = (ROOT / 'Dockerfile').read_text()
    for capability in [' subtitles[[:space:]]', ' libx264[[:space:]]', ' aac[[:space:]]']:
        assert capability in docker
    assert docker.index('ffmpeg -hide_banner -filters') < docker.index('USER appuser')


def test_release_provider_defaults_match_verified_google_and_github():
    docker = (ROOT / 'Dockerfile').read_text()
    compose = (ROOT / 'docker-compose.yml').read_text()
    workflow = (ROOT / '.github/workflows/release.yml').read_text()
    assert 'ARG VITE_CLERK_SOCIAL_PROVIDERS="google,github"' in docker
    assert 'VITE_CLERK_SOCIAL_PROVIDERS=$VITE_CLERK_SOCIAL_PROVIDERS' in docker
    assert 'VITE_CLERK_SOCIAL_PROVIDERS: ${VITE_CLERK_SOCIAL_PROVIDERS:-google,github}' in compose
    assert "VITE_CLERK_SOCIAL_PROVIDERS=${{ vars.CLERK_SOCIAL_PROVIDERS || 'google,github' }}" in workflow
    for template in ['frontend/.env.example', 'deploy/oracle-vm/.env.example']:
        assert 'VITE_CLERK_SOCIAL_PROVIDERS=google,github' in (ROOT / template).read_text()


@pytest.mark.parametrize('override,expected', [(None, 'google,github'), ('github', 'github'), ('google', 'google')])
def test_compose_provider_expression_preserves_configured_overrides(override, expected):
    # Execute the exact source parameter expression with the same POSIX default
    # semantics as Compose's :- interpolation; no Docker daemon or env files.
    compose = (ROOT / 'docker-compose.yml').read_text()
    line = next(line for line in compose.splitlines() if 'VITE_CLERK_SOCIAL_PROVIDERS:' in line)
    expression = line.split(': ', 1)[1].strip()
    env = {'VITE_CLERK_SOCIAL_PROVIDERS': override} if override is not None else {}
    result = subprocess.run(['/bin/bash', '-c', 'printf "%s" "' + expression + '"'], env=env, capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout == expected
