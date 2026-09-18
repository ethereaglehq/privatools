"""Website tool routes answer a server failure with a generic message.

/api/v1 always did (test_api_v1_error_contract.py). The unversioned routes the
site calls returned a ToolError's own detail on a 5xx, so a service that puts
stderr or an exception string into one (web_optimize_service does, with
qpdf's stderr, which names the upload's temp path) showed it to visitors from
any route that re-raises ToolError to keep its status code.
"""

import logging

import pytest

from backend.app.services import pdf_to_word_service
from backend.app.utils.exceptions import (
    DependencyError,
    ExternalToolError,
    PdfEncryptedError,
    ProcessingError,
    ToolTimeoutError,
    ValidationError,
)
from backend.app.utils.logging import _RequestIDFilter

# The shape web_optimize_service gives qpdf's stderr.
PRIVATE = "qpdf linearize failed: WARNING: /app/temp/upload_3f2a.pdf: can't find PDF header"


def _convert(client, sample_pdf, monkeypatch, error):
    def fail(_path):
        raise error

    # pdf-to-word re-raises ToolError so the handler keeps its status code.
    monkeypatch.setattr(pdf_to_word_service, "pdf_to_word", fail)
    return client.post("/api/pdf-to-word", files={"file": ("a.pdf", sample_pdf, "application/pdf")})


@pytest.mark.parametrize("error,status,message", [
    (ProcessingError(PRIVATE), 500, "Processing failed. Please try again."),
    (ExternalToolError(PRIVATE), 502, "Processing failed. Please try again."),
    (DependencyError(PRIVATE), 503, "The service is temporarily unavailable. Please try again."),
    (ToolTimeoutError(PRIVATE), 504, "The operation timed out. Try a smaller file."),
])
def test_server_failure_returns_a_generic_message_and_request_id(
    client, sample_pdf, monkeypatch, error, status, message,
):
    response = _convert(client, sample_pdf, monkeypatch, error)
    assert response.status_code == status
    assert response.json()["detail"] == message
    assert "/app/temp" not in response.text
    assert response.json()["request_id"] == response.headers["X-Request-ID"]


def test_server_failure_detail_is_logged_under_the_request_id(client, sample_pdf, monkeypatch):
    records = []
    handler = logging.Handler()
    handler.emit = records.append
    handler.addFilter(_RequestIDFilter())
    errors = logging.getLogger("privatools.errors")
    errors.addHandler(handler)
    try:
        response = _convert(client, sample_pdf, monkeypatch, ExternalToolError(PRIVATE))
    finally:
        errors.removeHandler(handler)
    logged = [record for record in records if PRIVATE in record.getMessage()]
    assert logged, "the private detail must stay in the server log"
    assert logged[0].request_id == response.headers["X-Request-ID"]


@pytest.mark.parametrize("error", [
    PdfEncryptedError(),
    ValidationError("Page 12 does not exist in this 3-page PDF."),
])
def test_client_errors_keep_their_message(client, sample_pdf, monkeypatch, error):
    response = _convert(client, sample_pdf, monkeypatch, error)
    assert response.status_code == 400
    assert response.json()["detail"] == error.detail
