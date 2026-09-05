"""Render the page a fact came from, with the quote highlighted.

This is the trust feature. A filename and a quote as text ask the Architektin
to believe the system. Showing her the page, with the sentence marked where it
actually stands, lets her check in one glance — and checking is the whole
point of a tool she is personally liable for.
"""

import base64
import logging
import re
from dataclasses import dataclass
from io import BytesIO

import pymupdf
from PIL import Image, ImageOps

from src.backend.schemas import Attachment

logger = logging.getLogger(__name__)

#: Rendered wide enough to read a Bauzeichnung label, small enough to send.
MAX_BREITE = 1400
JPEG_QUALITAET = 82
#: Warm amber, matching the "unbestätigt" colour of the interface.
MARKIERUNG = (0.98, 0.75, 0.10)


class VorschauError(RuntimeError):
    """Raised when a page cannot be rendered."""


@dataclass(frozen=True)
class Seitenbild:
    """One rendered page, ready for the browser."""

    bild_base64: str
    mime_type: str
    seite: int
    seiten_gesamt: int
    #: False when the quote could not be located — a scan, or reworded text.
    markiert: bool


def _als_jpeg(bild: Image.Image) -> str:
    bild = ImageOps.exif_transpose(bild).convert("RGB")
    if bild.width > MAX_BREITE:
        hoehe = round(bild.height * MAX_BREITE / bild.width)
        bild = bild.resize((MAX_BREITE, hoehe), Image.Resampling.LANCZOS)
    puffer = BytesIO()
    bild.save(puffer, format="JPEG", quality=JPEG_QUALITAET, optimize=True)
    return base64.b64encode(puffer.getvalue()).decode("ascii")


def _suchbegriffe(zitat: str) -> list[str]:
    """Progressively shorter search terms.

    A quote is rarely a verbatim substring of the page: line breaks, hyphenation
    and OCR noise get in the way. Trying the whole quote first and then falling
    back to its opening words finds the right spot far more often than one
    exact search.
    """

    sauber = re.sub(r"\s+", " ", zitat).strip()
    if not sauber:
        return []

    begriffe = [sauber]
    # Bezeichner wie "Flurstück: 1477" — der Wert allein trifft oft besser.
    if ":" in sauber:
        nach_doppelpunkt = sauber.split(":", 1)[1].strip()
        if len(nach_doppelpunkt) >= 3:
            begriffe.append(nach_doppelpunkt)
    woerter = sauber.split(" ")
    for anzahl in (8, 5, 3, 2):
        if len(woerter) > anzahl:
            begriffe.append(" ".join(woerter[:anzahl]))
    if len(sauber) > 3:
        begriffe.append(woerter[0])
    # Reihenfolge erhalten, Dubletten entfernen.
    gesehen: set[str] = set()
    return [b for b in begriffe if len(b) >= 2 and not (b in gesehen or gesehen.add(b))]


def _markiere(seite: pymupdf.Page, zitat: str) -> bool:
    """Highlight the quote on the page. Returns whether anything was found."""

    for begriff in _suchbegriffe(zitat):
        try:
            treffer = seite.search_for(begriff, quads=False)
        except Exception:  # noqa: BLE001 — a failed search is not an error here
            continue
        if not treffer:
            continue
        # Bei sehr kurzen Begriffen würde ein Treffer pro Seite alles einfärben.
        if len(begriff) <= 3 and len(treffer) > 6:
            continue
        for rechteck in treffer[:40]:
            annotation = seite.add_highlight_annot(rechteck)
            annotation.set_colors(stroke=MARKIERUNG)
            annotation.update(opacity=0.45)
        return True
    return False


def seite_rendern(datei: Attachment, seite_nr: int, zitat: str = "") -> Seitenbild:
    """Render one page of a stored document, highlighting the quote if found."""

    try:
        rohdaten = base64.b64decode(datei.content_base64, validate=False)
    except (ValueError, TypeError) as exc:
        raise VorschauError("Die Datei konnte nicht gelesen werden.") from exc

    name = datei.name.lower()
    if name.endswith(".pdf"):
        return _pdf_seite(rohdaten, seite_nr, zitat)
    if name.endswith((".png", ".jpg", ".jpeg")):
        try:
            with Image.open(BytesIO(rohdaten)) as bild:
                bild.load()
                # Ein Foto oder Scan hat keine durchsuchbare Textebene; die
                # Seite wird gezeigt, die Markierung entfällt ehrlich.
                return Seitenbild(_als_jpeg(bild), "image/jpeg", 1, 1, markiert=False)
        except Exception as exc:  # noqa: BLE001
            raise VorschauError("Das Bild konnte nicht geöffnet werden.") from exc

    raise VorschauError("Für diesen Dateityp gibt es keine Seitenvorschau.")


def _pdf_seite(rohdaten: bytes, seite_nr: int, zitat: str) -> Seitenbild:
    try:
        dokument = pymupdf.open(stream=rohdaten, filetype="pdf")
    except Exception as exc:  # noqa: BLE001
        raise VorschauError("Das PDF konnte nicht geöffnet werden.") from exc

    try:
        gesamt = dokument.page_count
        if gesamt == 0:
            raise VorschauError("Das PDF enthält keine Seiten.")
        index = min(max(seite_nr, 1), gesamt) - 1
        seite = dokument[index]

        markiert = _markiere(seite, zitat) if zitat else False

        pixmap = seite.get_pixmap(matrix=pymupdf.Matrix(2, 2), colorspace=pymupdf.csRGB, alpha=False)
        bild = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
        return Seitenbild(_als_jpeg(bild), "image/jpeg", index + 1, gesamt, markiert)
    except VorschauError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise VorschauError("Die Seite konnte nicht dargestellt werden.") from exc
    finally:
        dokument.close()
