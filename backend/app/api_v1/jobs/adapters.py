"""Explicit async operation contracts. Heavy services are imported only in a child."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError


class EmptyOptions(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class CompressOptions(EmptyOptions):
    level: Literal["light", "recommended", "extreme", "email", "print", "archive", "web"] = "recommended"


@dataclass(frozen=True)
class Adapter:
    operation: str
    options: type[BaseModel]
    min_files: int = 1
    max_files: int = 1
    media_type: str = "application/pdf"
    filename: str = "result.pdf"


ADAPTERS = {
    "grayscale": Adapter("grayscale", EmptyOptions),
    "compress": Adapter("compress", CompressOptions),
    "merge": Adapter("merge", EmptyOptions, min_files=2, max_files=10),
    "pdf-to-text": Adapter("pdf-to-text", EmptyOptions, media_type="application/json", filename="result.json"),
}


def validate_options(operation: str, options: dict) -> dict:
    if operation not in ADAPTERS:
        raise ValueError("unsupported_async_operation")
    try:
        return ADAPTERS[operation].options.model_validate(options).model_dump()
    except ValidationError as exc:
        raise ValueError("invalid_job_options") from exc


def execute(operation: str, options: dict, inputs: list[str], scratch: Path) -> Path:
    """Called after the child has set TEMP_DIR/TMPDIR and resource limits."""
    if operation == "grayscale":
        from ...services.grayscale_service import convert_to_grayscale
        return Path(convert_to_grayscale(inputs[0]))
    if operation == "compress":
        from ...services.compress_service import compress_pdf
        return Path(compress_pdf(inputs[0], level=options["level"]))
    if operation == "merge":
        from ...services.merge_service import merge_pdfs
        return Path(merge_pdfs(inputs))
    if operation == "pdf-to-text":
        import json
        from ...services.pdf_to_text_service import extract_text
        result = scratch / "result.json"
        result.write_text(json.dumps(extract_text(inputs[0]), ensure_ascii=False), encoding="utf-8")
        return result
    raise ValueError("unsupported_async_operation")
