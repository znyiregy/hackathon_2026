"""Validation for uploaded files that are retained in agent state."""

import base64
import binascii
from io import BytesIO
from pathlib import Path
from typing import Any

import pymupdf
from PIL import Image, ImageOps, UnidentifiedImageError

from src.backend.schemas import Attachment


MAX_TOTAL_BYTES = 10 * 1024 * 1024
MAX_TEXT_CHARACTERS = 200_000
MAX_PDF_PAGES = 10
MAX_IMAGE_DIMENSION = 1400
JPEG_QUALITY = 92

_TEXT_MIME_TYPES: dict[str, set[str]] = {
    ".txt": {"text/plain"},
    ".md": {"text/markdown", "text/plain"},
    ".csv": {"text/csv", "text/plain", "application/vnd.ms-excel"},
    ".json": {"application/json", "text/plain"},
}
_IMAGE_MIME_TYPES: dict[str, set[str]] = {
    ".png": {"image/png"},
    ".jpg": {"image/jpeg", "image/jpg"},
    ".jpeg": {"image/jpeg", "image/jpg"},
}


class AttachmentError(ValueError):
    """Raised for invalid or unsupported attachment content."""


class AttachmentTooLargeError(AttachmentError):
    """Raised when decoded request attachments exceed the byte limit."""


def _decode(attachment: Attachment) -> bytes:
    try:
        return base64.b64decode(attachment.content_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AttachmentError(f"{attachment.name}: content_base64 is not valid base64.") from exc


def _validate_image(data: bytes, name: str) -> None:
    try:
        with Image.open(BytesIO(data)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
        raise AttachmentError(f"{name}: the image is corrupt or unsupported.") from exc


def _jpeg_bytes(image: Image.Image) -> bytes:
    image = ImageOps.exif_transpose(image)
    if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.getchannel("A"))
        image = background
    else:
        image = image.convert("RGB")
    image.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)
    output = BytesIO()
    image.save(output, format="JPEG", quality=JPEG_QUALITY)
    return output.getvalue()


def _image_content_block(data: bytes, name: str) -> dict[str, str]:
    try:
        with Image.open(BytesIO(data)) as image:
            image.load()
            jpeg = _jpeg_bytes(image)
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
        raise AttachmentError(f"{name}: the image is corrupt or unsupported.") from exc
    return {"type": "image", "base64": base64.b64encode(jpeg).decode("ascii"), "mime_type": "image/jpeg"}


def _validate_pdf(data: bytes, name: str) -> None:
    try:
        document = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise AttachmentError(f"{name}: the PDF is corrupt or unsupported.") from exc

    try:
        if document.page_count > MAX_PDF_PAGES:
            raise AttachmentError(f"{name}: PDFs may contain at most {MAX_PDF_PAGES} pages.")
        if document.page_count == 0:
            raise AttachmentError(f"{name}: the PDF contains no pages.")
    finally:
        document.close()


def _pdf_content_blocks(data: bytes, name: str) -> list[dict[str, str]]:
    try:
        document = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise AttachmentError(f"{name}: the PDF is corrupt or unsupported.") from exc

    try:
        if document.page_count > MAX_PDF_PAGES:
            raise AttachmentError(f"{name}: PDFs may contain at most {MAX_PDF_PAGES} pages.")
        if document.page_count == 0:
            raise AttachmentError(f"{name}: the PDF contains no pages.")
        blocks = []
        matrix = pymupdf.Matrix(2, 2)
        for page in document:
            pixmap = page.get_pixmap(matrix=matrix, colorspace=pymupdf.csRGB, alpha=False)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            jpeg = _jpeg_bytes(image)
            blocks.append(
                {"type": "image", "base64": base64.b64encode(jpeg).decode("ascii"), "mime_type": "image/jpeg"}
            )
        return blocks
    except AttachmentError:
        raise
    except Exception as exc:
        raise AttachmentError(f"{name}: the PDF could not be rendered.") from exc
    finally:
        document.close()


def _truncate_text(text: str) -> str:
    if len(text) <= MAX_TEXT_CHARACTERS:
        return text
    marker = "\n\n[File text truncated at 200,000 characters.]"
    return text[: MAX_TEXT_CHARACTERS - len(marker)] + marker


def content_blocks_for_analysis(attachment: Attachment) -> list[dict[str, Any]]:
    """Convert one stored file to multimodal blocks for the file subagent only."""

    data = _decode(attachment)
    suffix = Path(attachment.name).suffix.lower()
    mime_type = attachment.mime_type.lower().split(";", maxsplit=1)[0].strip()

    if suffix in _TEXT_MIME_TYPES:
        if mime_type not in _TEXT_MIME_TYPES[suffix]:
            raise AttachmentError(f"{attachment.name}: MIME type {attachment.mime_type!r} does not match the file extension.")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AttachmentError(f"{attachment.name}: text files must use UTF-8 encoding.") from exc
        return [{"type": "text", "text": _truncate_text(text)}]
    if suffix in _IMAGE_MIME_TYPES:
        if mime_type not in _IMAGE_MIME_TYPES[suffix]:
            raise AttachmentError(f"{attachment.name}: MIME type {attachment.mime_type!r} does not match the file extension.")
        return [_image_content_block(data, attachment.name)]
    if suffix == ".pdf":
        if mime_type != "application/pdf":
            raise AttachmentError(f"{attachment.name}: MIME type {attachment.mime_type!r} does not match the file extension.")
        return _pdf_content_blocks(data, attachment.name)
    raise AttachmentError(f"{attachment.name}: unsupported file type. Use TXT, MD, CSV, JSON, PDF, PNG, or JPEG.")


def validate_attachments(attachments: list[Attachment]) -> None:
    """Validate uploaded files without placing their contents in LLM messages."""

    decoded: list[tuple[Attachment, bytes]] = []
    total_bytes = 0
    for attachment in attachments:
        data = _decode(attachment)
        total_bytes += len(data)
        if total_bytes > MAX_TOTAL_BYTES:
            raise AttachmentTooLargeError("Attachments may contain at most 10 MiB of decoded data in total.")
        decoded.append((attachment, data))

    for attachment, data in decoded:
        suffix = Path(attachment.name).suffix.lower()
        mime_type = attachment.mime_type.lower().split(";", maxsplit=1)[0].strip()

        if suffix in _TEXT_MIME_TYPES:
            if mime_type not in _TEXT_MIME_TYPES[suffix]:
                raise AttachmentError(f"{attachment.name}: MIME type {attachment.mime_type!r} does not match the file extension.")
            try:
                data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise AttachmentError(f"{attachment.name}: text files must use UTF-8 encoding.") from exc
        elif suffix in _IMAGE_MIME_TYPES:
            if mime_type not in _IMAGE_MIME_TYPES[suffix]:
                raise AttachmentError(f"{attachment.name}: MIME type {attachment.mime_type!r} does not match the file extension.")
            _validate_image(data, attachment.name)
        elif suffix == ".pdf":
            if mime_type != "application/pdf":
                raise AttachmentError(f"{attachment.name}: MIME type {attachment.mime_type!r} does not match the file extension.")
            _validate_pdf(data, attachment.name)
        else:
            raise AttachmentError(f"{attachment.name}: unsupported file type. Use TXT, MD, CSV, JSON, PDF, PNG, or JPEG.")
