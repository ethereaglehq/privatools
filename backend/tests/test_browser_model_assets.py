"""Model assets bypass HTML SEO safely, with runtime-appropriate MIME types."""
import pytest
from backend.app import main


@pytest.mark.parametrize('filename,mime,content', [
    ('u2netp.onnx','application/octet-stream',b'fixed-model-binary'),
    ('ort-wasm-simd-threaded.wasm','application/wasm',b'\x00asm'),
    ('ort-wasm-simd-threaded.mjs','text/javascript',b'export const ready = true;'),
    ('NOTICE.txt','text/plain',b'U2-Net and rembg license notice'),
])
def test_fixed_model_files_are_served_as_bytes(client, monkeypatch, tmp_path, filename, mime, content):
    folder=tmp_path/'models';folder.mkdir();(folder/filename).write_bytes(content)
    monkeypatch.setattr(main,'_frontend_path',tmp_path)
    response=client.get('/models/'+filename)
    assert response.status_code==200
    assert response.content==content
    assert response.headers['content-type'].startswith(mime)
    assert response.headers['cache-control']=='public, max-age=0, must-revalidate'
    assert '<html' not in response.text


def test_unknown_model_file_is_not_exposed_even_if_present(client,monkeypatch,tmp_path):
    folder=tmp_path/'models';folder.mkdir();(folder/'private.json').write_text('{"private":"not public"}')
    monkeypatch.setattr(main,'_frontend_path',tmp_path)
    response=client.get('/models/private.json')
    assert response.status_code==404
    assert response.json()=={'detail':'Not found'}


def test_missing_fixed_model_is_json_404_not_spa_html(client,monkeypatch,tmp_path):
    monkeypatch.setattr(main,'_frontend_path',tmp_path)
    response=client.get('/models/u2netp.onnx')
    assert response.status_code==404
    assert response.headers['content-type'].startswith('application/json')
    assert response.json()=={'detail':'Not found'}
