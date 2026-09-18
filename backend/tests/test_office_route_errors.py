"""Office failures must preserve actionable status without disclosing paths."""
import pytest

from backend.app.services import office_to_pdf_service
from backend.app.utils.exceptions import DependencyError, ExternalToolError, ToolTimeoutError


@pytest.mark.parametrize("error,status,message", [
    (DependencyError("Office conversion is unavailable: LibreOffice is not installed."), 503,
     "The service is temporarily unavailable. Please try again."),
    (ExternalToolError("LibreOffice could not convert this document."), 502,
     "Processing failed. Please try again."),
    (ToolTimeoutError("Office conversion timed out."), 504,
     "The operation timed out. Try a smaller file."),
])
def test_office_route_preserves_typed_failures(client, monkeypatch, error, status, message):
    async def fail(_):
        raise error

    monkeypatch.setattr(office_to_pdf_service, "office_to_pdf", fail)
    response = client.post("/api/office-to-pdf", files={"file": ("example.docx", b"synthetic", "application/octet-stream")})
    assert response.status_code == status
    # A 5xx names its kind of failure, never the service's own text.
    assert response.json()["detail"] == message


def test_office_unexpected_error_does_not_disclose_server_path(client, monkeypatch):
    async def fail(_):
        raise RuntimeError("/private/server/document.docx")

    monkeypatch.setattr(office_to_pdf_service, "office_to_pdf", fail)
    response = client.post("/api/office-to-pdf", files={"file": ("example.docx", b"synthetic", "application/octet-stream")})
    assert response.status_code == 500
    assert "/private/server" not in response.text
