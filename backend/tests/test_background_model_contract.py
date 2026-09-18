import pytest
from backend.app.services import bg_remover_service
from backend.app.utils.exceptions import DependencyError, ValidationError


def test_invalid_image_fails_before_model_loading(tmp_path, monkeypatch):
    file = tmp_path / "invalid.png"
    file.write_bytes(b"not an image")
    def must_not_load():
        raise AssertionError("Model must not load before input validation")
    monkeypatch.setattr(bg_remover_service, "_get_session", must_not_load)
    with pytest.raises(ValidationError, match="could not be read"):
        bg_remover_service.remove_background(str(file))


@pytest.mark.parametrize("error,status,message", [(DependencyError("The server background model could not start."),503,"The service is temporarily unavailable. Please try again."), (ValidationError("This image could not be read."),400,"This image could not be read.")])
def test_background_route_preserves_actionable_failures(client, monkeypatch, error, status, message):
    def fail(*args):
        raise error
    monkeypatch.setattr(bg_remover_service, "remove_background", fail)
    response = client.post('/api/remove-background', files={'file':('fixture.png', b'fixture', 'image/png')})
    assert response.status_code == status
    # A 5xx names its kind of failure; a 4xx keeps its own message.
    assert response.json()['detail'] == message
