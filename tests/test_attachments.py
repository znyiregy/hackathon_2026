import base64
from io import BytesIO

import pymupdf
import pytest
from PIL import Image

from src.backend.attachments import (
    MAX_IMAGE_DIMENSION,
    MAX_TEXT_CHARACTERS,
    MAX_TOTAL_BYTES,
    AttachmentError,
    AttachmentTooLargeError,
    content_blocks_for_analysis,
    validate_attachments,
)
from src.backend.schemas import Attachment


def attachment(name: str, mime_type: str, data: bytes) -> Attachment:
    return Attachment(name=name, mime_type=mime_type, content_base64=base64.b64encode(data).decode("ascii"))


def make_pdf(pages: int) -> bytes:
    document = pymupdf.open()
    for index in range(pages):
        page = document.new_page(width=800, height=1200)
        page.insert_text((72, 72), f"Page {index + 1}")
    data = document.tobytes()
    document.close()
    return data


def test_validates_text_image_and_pdf_without_creating_model_content():
    image = Image.new("RGB", (20, 10), "red")
    image_data = BytesIO()
    image.save(image_data, format="PNG")

    assert validate_attachments(
        [
            attachment("notes.txt", "text/plain", b"private content"),
            attachment("image.png", "image/png", image_data.getvalue()),
            attachment("report.pdf", "application/pdf", make_pdf(1)),
        ]
    ) is None


def test_analysis_text_is_truncated_with_notice():
    blocks = content_blocks_for_analysis(
        attachment("large.txt", "text/plain", b"a" * (MAX_TEXT_CHARACTERS + 100))
    )

    assert blocks[0]["text"].endswith("[File text truncated at 200,000 characters.]")
    assert len(blocks[0]["text"]) == MAX_TEXT_CHARACTERS


def test_analysis_image_is_converted_to_bounded_jpeg():
    image = Image.new("RGBA", (2000, 1000), (255, 0, 0, 128))
    image_data = BytesIO()
    image.save(image_data, format="PNG")

    block = content_blocks_for_analysis(attachment("wide.png", "image/png", image_data.getvalue()))[0]
    with Image.open(BytesIO(base64.b64decode(block["base64"]))) as rendered:
        assert rendered.format == "JPEG"
        assert rendered.mode == "RGB"
        assert max(rendered.size) == MAX_IMAGE_DIMENSION


@pytest.mark.parametrize(
    "item",
    [
        Attachment(name="bad.txt", mime_type="text/plain", content_base64="not-base64"),
        attachment("bad.txt", "text/plain", b"\xff"),
        attachment("bad.png", "image/png", b"not an image"),
        attachment("bad.pdf", "application/pdf", b"not a pdf"),
        attachment("notes.exe", "application/octet-stream", b"content"),
        attachment("notes.txt", "application/pdf", b"content"),
    ],
)
def test_rejects_invalid_attachments(item):
    with pytest.raises(AttachmentError):
        validate_attachments([item])


def test_rejects_too_many_pdf_pages():
    with pytest.raises(AttachmentError, match="at most 10 pages"):
        validate_attachments([attachment("long.pdf", "application/pdf", make_pdf(11))])


def test_rejects_more_than_ten_mebibytes():
    with pytest.raises(AttachmentTooLargeError):
        validate_attachments([attachment("large.txt", "text/plain", b"a" * (MAX_TOTAL_BYTES + 1))])
