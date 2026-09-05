"""Validation and conversion of API attachments into model content blocks."""

import base64
import binascii
from dataclasses import dataclass
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


@dataclass(frozen=True)
class PreparedAttachments:
    content_blocks: list[dict[str, Any]]
    decoded_bytes: int


def _decode(attachment: Attachment) -> bytes:
    try:
        return base64.b64decode(attachment.content_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AttachmentError(f"{attachment.name}: content_base64 is not valid base64.") from exc


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


def _image_to_block(data: bytes, name: str) -> list[dict[str, Any]]:
    try:
        with Image.open(BytesIO(data)) as image:
            image.load()
            jpeg = _jpeg_bytes(image)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise AttachmentError(f"{name}: the image is corrupt or unsupported.") from exc
    return [
        {"type": "text", "text": f"Image attachment: {name}"},
        {"type": "image", "base64": base64.b64encode(jpeg).decode("ascii"), "mime_type": "image/jpeg"},
    ]


def _pdf_to_blocks(data: bytes, name: str) -> list[dict[str, Any]]:
    try:
        document = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise AttachmentError(f"{name}: the PDF is corrupt or unsupported.") from exc

    try:
        if document.page_count > MAX_PDF_PAGES:
            raise AttachmentError(f"{name}: PDFs may contain at most {MAX_PDF_PAGES} pages.")
        if document.page_count == 0:
            raise AttachmentError(f"{name}: the PDF contains no pages.")

        blocks: list[dict[str, Any]] = []
        matrix = pymupdf.Matrix(2, 2)  # 144 DPI, because PDF's baseline is 72 DPI.
        for index, page in enumerate(document):
            pixmap = page.get_pixmap(matrix=matrix, colorspace=pymupdf.csRGB, alpha=False)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            jpeg = _jpeg_bytes(image)
            blocks.extend(
                [
                    {"type": "text", "text": f"PDF attachment: {name}, page {index + 1} of {document.page_count}"},
                    {
                        "type": "image",
                        "base64": base64.b64encode(jpeg).decode("ascii"),
                        "mime_type": "image/jpeg",
                    },
                ]
            )
        return blocks
    except AttachmentError:
        raise
    except Exception as exc:
        raise AttachmentError(f"{name}: the PDF could not be rendered.") from exc
    finally:
        document.close()


def _truncate_text(chunks: list[str]) -> str:
    combined = "\n\n".join(chunks)
    if len(combined) <= MAX_TEXT_CHARACTERS:
        return combined
    marker = "\n\n[Attachment text truncated at 200,000 characters.]"
    return combined[: MAX_TEXT_CHARACTERS - len(marker)] + marker


def prepare_attachments(attachments: list[Attachment]) -> PreparedAttachments:
    decoded: list[tuple[Attachment, bytes]] = []
    total_bytes = 0
    for attachment in attachments:
        data = _decode(attachment)
        total_bytes += len(data)
        if total_bytes > MAX_TOTAL_BYTES:
            raise AttachmentTooLargeError("Attachments may contain at most 10 MiB of decoded data in total.")
        decoded.append((attachment, data))

    text_chunks: list[str] = []
    image_blocks: list[dict[str, Any]] = []
    for attachment, data in decoded:
        suffix = Path(attachment.name).suffix.lower()
        mime_type = attachment.mime_type.lower().split(";", maxsplit=1)[0].strip()

        if suffix in _TEXT_MIME_TYPES:
            if mime_type not in _TEXT_MIME_TYPES[suffix]:
                raise AttachmentError(f"{attachment.name}: MIME type {attachment.mime_type!r} does not match the file extension.")
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise AttachmentError(f"{attachment.name}: text files must use UTF-8 encoding.") from exc
            text_chunks.append(f"Text attachment: {attachment.name}\n---\n{text}")
        elif suffix in _IMAGE_MIME_TYPES:
            if mime_type not in _IMAGE_MIME_TYPES[suffix]:
                raise AttachmentError(f"{attachment.name}: MIME type {attachment.mime_type!r} does not match the file extension.")
            image_blocks.extend(_image_to_block(data, attachment.name))
        elif suffix == ".pdf":
            if mime_type != "application/pdf":
                raise AttachmentError(f"{attachment.name}: MIME type {attachment.mime_type!r} does not match the file extension.")
            image_blocks.extend(_pdf_to_blocks(data, attachment.name))
        else:
            raise AttachmentError(f"{attachment.name}: unsupported file type. Use TXT, MD, CSV, JSON, PDF, PNG, or JPEG.")

    blocks: list[dict[str, Any]] = []
    if text_chunks:
        blocks.append({"type": "text", "text": _truncate_text(text_chunks)})
    blocks.extend(image_blocks)
    return PreparedAttachments(content_blocks=blocks, decoded_bytes=total_bytes)
