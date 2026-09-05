import base64
from io import BytesIO

import pymupdf
import pytest
from PIL import Image

from src.backend.attachments import (
    MAX_TEXT_CHARACTERS,
    MAX_TOTAL_BYTES,
    AttachmentError,
    AttachmentTooLargeError,
    prepare_attachments,
)
from src.backend.schemas import Attachment


def attachment(name: str, mime_type: str, data: bytes) -> Attachment:
    return Attachment(name=name, mime_type=mime_type, content_base64=base64.b64encode(data).decode("ascii"))


def decode_image_block(block):
    return Image.open(BytesIO(base64.b64decode(block["base64"])))


def make_pdf(pages: int) -> bytes:
    document = pymupdf.open()
    for index in range(pages):
        page = document.new_page(width=800, height=1200)
        page.insert_text((72, 72), f"Page {index + 1}")
    data = document.tobytes()
    document.close()
    return data


def test_text_files_are_labeled_and_combined():
    result = prepare_attachments(
        [attachment("a.txt", "text/plain", b"alpha"), attachment("b.json", "application/json", b'{"b": 2}')]
    )
    text = result.content_blocks[0]["text"]
    assert "Text attachment: a.txt" in text
    assert "alpha" in text
    assert "Text attachment: b.json" in text


def test_combined_text_is_truncated_with_notice():
    result = prepare_attachments([attachment("large.txt", "text/plain", b"a" * (MAX_TEXT_CHARACTERS + 100))])
    text = result.content_blocks[0]["text"]
    assert len(text) == MAX_TEXT_CHARACTERS
    assert text.endswith("[Attachment text truncated at 200,000 characters.]")


def test_image_is_normalized_to_bounded_jpeg():
    source = Image.new("RGBA", (2000, 1000), (255, 0, 0, 128))
    buffer = BytesIO()
    source.save(buffer, format="PNG")
    result = prepare_attachments([attachment("wide.png", "image/png", buffer.getvalue())])
    image_block = next(block for block in result.content_blocks if block["type"] == "image")
    with decode_image_block(image_block) as image:
        assert image.format == "JPEG"
        assert image.mode == "RGB"
        assert image.size == (1400, 700)


def test_pdf_pages_are_rendered_in_order():
    result = prepare_attachments([attachment("sample.pdf", "application/pdf", make_pdf(2))])
    labels = [block["text"] for block in result.content_blocks if block["type"] == "text"]
    assert labels == [
        "PDF attachment: sample.pdf, page 1 of 2",
        "PDF attachment: sample.pdf, page 2 of 2",
    ]
    for block in (item for item in result.content_blocks if item["type"] == "image"):
        with decode_image_block(block) as image:
            assert image.format == "JPEG"
            assert max(image.size) <= 1400


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
        prepare_attachments([item])


def test_rejects_too_many_pdf_pages():
    with pytest.raises(AttachmentError, match="at most 10 pages"):
        prepare_attachments([attachment("long.pdf", "application/pdf", make_pdf(11))])


def test_rejects_more_than_ten_mebibytes():
    with pytest.raises(AttachmentTooLargeError):
        prepare_attachments([attachment("large.txt", "text/plain", b"a" * (MAX_TOTAL_BYTES + 1))])
