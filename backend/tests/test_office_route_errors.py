"""Office failures must preserve actionable status without disclosing paths."""
import pytest

from backend.app.services import office_to_pdf_service
from backend.app.utils.exceptions import DependencyError, ExternalToolError, ToolTimeoutError


@pytest.mark.parametrize("error,status", [
    (DependencyError("Office conversion is unavailable: LibreOffice is not installed."), 503),
    (ExternalToolError("LibreOffice could not convert this document."), 502),
    (ToolTimeoutError("Office conversion timed out."), 504),
])
def test_office_route_preserves_typed_failures(client, monkeypatch, error, status):
    async def fail(_):
        raise error

    monkeypatch.setattr(office_to_pdf_service, "office_to_pdf", fail)
    response = client.post("/api/office-to-pdf", files={"file": ("example.docx", b"synthetic", "application/octet-stream")})
    assert response.status_code == status
    assert response.json()["detail"] == error.detail


def test_office_unexpected_error_does_not_disclose_server_path(client, monkeypatch):
    async def fail(_):
        raise RuntimeError("/private/server/document.docx")

    monkeypatch.setattr(office_to_pdf_service, "office_to_pdf", fail)
    response = client.post("/api/office-to-pdf", files={"file": ("example.docx", b"synthetic", "application/octet-stream")})
    assert response.status_code == 500
    assert "/private/server" not in response.text
