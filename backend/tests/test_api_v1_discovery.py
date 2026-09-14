"""Public discovery describes the installed v1 contract without exposing private APIs."""
from fastapi import FastAPI
from fastapi.routing import APIRoute, iter_route_contexts
from fastapi.testclient import TestClient

from backend.app.main import app


def documents():
    from backend.app.api_v1.catalog import build_catalog
    from backend.app.api_v1.schema import build_schema

    return build_catalog(app), build_schema(app)


def test_catalog_covers_installed_v1_operations_and_excludes_discovery():
    catalog, schema = documents()
    expected = {
        (method, route.path)
        for route in iter_route_contexts(app.routes)
        if isinstance(route.original_route, APIRoute)
        and route.path.startswith('/api/v1/')
        and route.path not in {'/api/v1/operations', '/api/v1/openapi.json'}
        for method in route.methods
    }
    actual = {(operation['method'], operation['path']) for operation in catalog['operations']}
    assert actual == expected
    assert len(actual) >= 143
    assert len({operation['id'] for operation in catalog['operations']}) == len(actual)
    assert set(schema['paths']) == {path for _, path in expected}
    assert all(path.startswith('/api/v1/') for path in schema['paths'])
    assert {'slug': 'chat-with-pdf', 'name': 'Chat with PDF', 'reason': 'Runs in the browser or with a user-selected AI provider; no v1 HTTP endpoint.'} in catalog['unavailable_tools']


def test_schema_describes_real_multipart_and_binary_variants():
    _, schema = documents()
    merge = schema['paths']['/api/v1/merge']['post']
    assert merge['operationId'] == 'v1_post_merge'
    assert set(merge['responses']['200']['content']) == {'application/pdf'}
    ref = merge['requestBody']['content']['multipart/form-data']['schema']['$ref']
    body = schema['components']['schemas'][ref.rsplit('/', 1)[1]]
    assert body['required'] == ['files']
    assert body['properties']['files']['items']['type'] == 'string'
    assert body['properties']['files']['items']['format'] == 'binary'
    assert body['properties']['files']['minItems'] == 2
    assert body['properties']['files']['maxItems'] == 100
    compress = schema['paths']['/api/v1/compress']['post']
    assert set(compress['responses']['200']['content']) == {'application/pdf', 'application/zip'}
    ref = compress['requestBody']['content']['multipart/form-data']['schema']['$ref']
    fields = schema['components']['schemas'][ref.rsplit('/', 1)[1]]['properties']
    assert {'jpeg_quality', 'max_image_dim', 'target_size_mb'} <= fields.keys()
    rotate = schema['paths']['/api/v1/rotate']['post']
    ref = rotate['requestBody']['content']['multipart/form-data']['schema']['$ref']
    assert schema['components']['schemas'][ref.rsplit('/', 1)[1]]['properties']['angle']['multipleOf'] == 90


def test_schema_references_resolve_and_authentication_is_alternative():
    _, schema = documents()

    def visit(value):
        if isinstance(value, dict):
            if '$ref' in value:
                assert value['$ref'].startswith('#/')
                target = schema
                for segment in value['$ref'][2:].split('/'):
                    target = target[segment.replace('~1', '/').replace('~0', '~')]
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(schema)
    alternatives = schema['paths']['/api/v1/merge']['post']['security']
    assert len(alternatives) == 2
    schemes = schema['components']['securitySchemes']
    assert {schemes[next(iter(option))]['name'] for option in alternatives} == {'X-API-Key', 'Authorization'}


def test_costs_follow_execution_facade(monkeypatch):
    from backend.app.api_v1 import quota

    monkeypatch.setattr(quota, 'cost_for', lambda path: 9)
    catalog, _ = documents()
    operations = {item['path']: item for item in catalog['operations']}
    assert operations['/api/v1/merge']['cost']['units'] == 9
    assert operations['/api/v1/pipeline']['cost']['mode'] == 'pipeline_steps'
    assert operations['/api/v1/pipeline']['cost']['units'] is None


def test_discovery_is_public_non_metered_and_has_no_private_schema(monkeypatch):
    from backend.app.api_v1 import docs, quota
    from backend.app.routes.merge import router

    isolated = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    isolated.include_router(router, prefix='/api/v1')

    @isolated.get('/api/auth/private')
    def private():
        return {'private': True}

    def forbidden(*args, **kwargs):
        raise AssertionError('Discovery must not consume a quota')

    monkeypatch.setattr(quota, 'consume', forbidden)
    docs.mount(isolated)
    client = TestClient(isolated)
    for path in ('operations', 'openapi.json'):
        response = client.get('/api/v1/' + path)
        assert response.status_code == 200
        assert response.headers['cache-control'].startswith('public')
        assert '/api/auth/private' not in response.text
    assert client.get('/api/v1/openapi.json').json()['paths'].keys() == {'/api/v1/merge'}


def test_schema_uses_the_real_error_envelope():
    _, schema = documents()
    response = schema['paths']['/api/v1/merge']['post']['responses']['422']
    assert response['content']['application/json']['schema']['$ref'] == '#/components/schemas/ApiError'
    error = schema['components']['schemas']['ApiError']
    assert {'code', 'message'} <= set(error['required'])
    assert error['properties']['detail']['type'] == 'string'


def test_async_capability_tracks_the_worker_and_preserves_explicit_ids(monkeypatch):
    from backend.app.api_v1.jobs import storage
    from backend.app.api_v1.schema import build_schema

    monkeypatch.setattr(storage, 'capability', lambda: {'enabled': True, 'available': True, 'operations': ['merge'], 'result_retention_seconds': 3600})
    catalog, _ = documents()
    merge = next(o for o in catalog['operations'] if o['path'] == '/api/v1/merge')
    assert merge['async'] == {'supported': True, 'operation': 'merge'}
    monkeypatch.setattr(storage, 'capability', lambda: {'enabled': True, 'available': False, 'operations': [], 'result_retention_seconds': 3600})
    catalog, _ = documents()
    assert not next(o for o in catalog['operations'] if o['path'] == '/api/v1/merge')['async']['supported']
    isolated = FastAPI()

    @isolated.post('/api/v1/jobs', operation_id='submit_async_job', status_code=202)
    def submit():
        return {'id': 'example'}

    schema = build_schema(isolated)
    assert schema['paths']['/api/v1/jobs']['post']['operationId'] == 'submit_async_job'


def test_documented_binary_and_json_operations_work_with_real_fixtures(client, sample_pdf, tmp_path):
    import fitz
    from backend.app import store
    from backend.app.auth import accounts

    store.reset_for_tests(tmp_path)
    try:
        user = accounts.create_user('docs@example.com', 'docs-synthetic-password-123')
        key, _ = accounts.issue_api_key(user.id, 'documentation contract')
        headers = {'X-API-Key': key}
        merged = client.post('/api/v1/merge', headers=headers,
                             files=[('files', ('first.pdf', sample_pdf, 'application/pdf')),
                                    ('files', ('second.pdf', sample_pdf, 'application/pdf'))])
        assert merged.status_code == 200
        assert merged.headers['content-type'] == 'application/pdf'
        with fitz.open(stream=merged.content, filetype='pdf') as pdf:
            assert len(pdf) == 2
        text = client.post('/api/v1/pdf-to-text', headers=headers,
                           files={'file': ('input.pdf', sample_pdf, 'application/pdf')})
        assert text.status_code == 200
        assert text.headers['content-type'].startswith('application/json')
        assert 'Sample page one' in text.text
    finally:
        store.reset_for_tests(tmp_path)


def test_cached_schema_includes_later_routes_and_keeps_policy_fresh(monkeypatch):
    from backend.app.api_v1 import quota
    from backend.app.api_v1.catalog import build_catalog
    from backend.app.api_v1.schema import build_schema

    isolated = FastAPI()

    @isolated.get('/api/v1/first', operation_id='first')
    def first():
        return {}

    assert '/api/v1/first' in build_schema(isolated)['paths']

    @isolated.get('/api/v1/second', operation_id='second')
    def second():
        return {}

    assert '/api/v1/second' in build_schema(isolated)['paths']
    monkeypatch.setattr(quota, 'DAILY_UNITS', 123)
    assert build_catalog(isolated)['limits']['daily_units'] == 123


def test_async_limits_come_from_job_config_and_are_separate_from_http_limits(monkeypatch):
    from backend.app.api_v1.jobs import config

    monkeypatch.setattr(config, 'LIMITS', config.Limits(
        input_bytes=1234, result_bytes=5678, per_key=2, per_account=4,
        max_pending=11, storage_bytes=20000, queue_seconds=30,
        runtime_seconds=40, attempts=3,
    ))
    catalog, schema = documents()
    limits = catalog['async']['limits']
    assert limits['max_input_bytes'] == 1234
    assert limits['max_result_bytes'] == 5678
    assert limits['max_outstanding_per_key'] == 2
    assert limits['max_outstanding_per_account'] == 4
    assert limits['max_outstanding_total'] == 11
    assert limits['worker_concurrency'] == 1
    assert limits['queue_deadline_seconds'] == 30
    assert limits['runtime_per_attempt_seconds'] == 40
    assert limits['max_attempts'] == 3
    assert limits['storage_reservation_bytes'] == 20000
    assert limits['storage_reservation_per_job_bytes'] == 12590
    assert schema['x-privatools-async']['limits'] == limits
    assert 'concurrent_requests_per_key' in catalog['limits']
    assert 'max_outstanding_per_key' not in catalog['limits']
