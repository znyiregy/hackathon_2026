"""Document intelligence: classify, judge quality, extract typed facts.

This is the model's half of the split. It reads a document and phrases what it
found. It never decides severity, never resolves a conflict and never marks a
requirement fulfilled — those are decided in :mod:`src.backend.regeln`.
"""

import json
import logging
import re
from datetime import date
from typing import Any

from langchain.messages import HumanMessage, SystemMessage

from src.backend.attachments import AttachmentError, content_blocks_for_analysis
from src.backend.domain import Dokument, DokumentStatus, Herkunft, Qualitaet
from src.backend.katalog import DOKUMENTTYPEN, FAKTEN
from src.backend.schemas import Attachment

logger = logging.getLogger(__name__)


class AuswertungError(RuntimeError):
    """Raised when a document could not be analysed at all."""


_TYP_LISTE = "\n".join(f"- {schluessel}: {bezeichnung}" for schluessel, bezeichnung in DOKUMENTTYPEN)
_FAKT_LISTE = "\n".join(
    f"- {definition.schluessel}: {definition.bezeichnung}"
    + (f" [{definition.einheit}]" if definition.einheit else "")
    + (f" — {definition.hinweis}" if definition.hinweis else "")
    for definition in FAKTEN
)

SYSTEM_PROMPT = f"""Du wertest eine einzelne Bauakte-Unterlage für ein deutsches
Architekturbüro aus. Du arbeitest ausschließlich mit dem gelieferten Material.

Deine Aufgaben:
1. Dokumenttyp bestimmen. Erlaubte Werte:
{_TYP_LISTE}
2. Qualität beurteilen: "gut", "eingeschraenkt" oder "unbrauchbar".
   "unbrauchbar" heißt: der Inhalt ist nicht verlässlich lesbar.
3. Dokumentdatum bestimmen, falls das Dokument selbst eines ausweist.
4. Projektfakten auslesen. Erlaubte Schlüssel:
{_FAKT_LISTE}
5. Einen Benennungsvorschlag im Format JJJJ-MM-TT_Dokumenttyp_Detail_V01.ext bilden.

Regeln, die nicht verhandelbar sind:
- Rate nichts. Fehlt eine Angabe im Material, lässt du sie weg.
- Ein Datum im ursprünglichen Dateinamen ist kein Dokumentdatum.
- Wohnfläche nach WoFlV und Nutzfläche nach DIN 277 sind verschiedene Fakten.
  Ordne eine Flächenangabe nur zu, wenn das Dokument die Bezugsgröße nennt.
- Bist du beim Typ unsicher, setze "typ_unklar": true statt zu raten.
- Zu jedem Fakt gehört ein wörtliches Zitat aus dem Material als Beleg.
- Du triffst keine rechtliche Aussage und beurteilst keine Zulässigkeit.

Antworte ausschließlich mit einem JSON-Objekt dieser Form:
{{"typ": "...", "typ_unklar": false, "qualitaet": "gut",
  "qualitaet_begruendung": "...", "dokument_datum": "JJJJ-MM-TT" oder null,
  "zusammenfassung": "ein bis zwei Sätze auf Deutsch",
  "namensvorschlag": "...",
  "fakten": [{{"schluessel": "...", "wert": "...", "seite": 1,
               "zitat": "...", "konfidenz": 0.0 bis 1.0}}]}}"""


def _json_aus_antwort(text: str) -> dict[str, Any]:
    """Read the JSON object out of a model response, tolerating code fences."""

    kandidat = text.strip()
    if kandidat.startswith("```"):
        kandidat = re.sub(r"^```(?:json)?\s*|\s*```$", "", kandidat, flags=re.DOTALL)
    try:
        geladen = json.loads(kandidat)
    except json.JSONDecodeError:
        treffer = re.search(r"\{.*\}", kandidat, flags=re.DOTALL)
        if treffer is None:
            raise AuswertungError("Das Modell hat kein auswertbares JSON geliefert.") from None
        try:
            geladen = json.loads(treffer.group(0))
        except json.JSONDecodeError as exc:
            raise AuswertungError("Das Modell hat kein auswertbares JSON geliefert.") from exc
    if not isinstance(geladen, dict):
        raise AuswertungError("Das Modell hat kein JSON-Objekt geliefert.")
    return geladen


def _antworttext(antwort: Any) -> str:
    text = getattr(antwort, "text", None)
    if isinstance(text, str) and text.strip():
        return text
    inhalt = getattr(antwort, "content", antwort)
    if isinstance(inhalt, str):
        return inhalt
    if isinstance(inhalt, list):
        teile = [
            block.get("text", "")
            for block in inhalt
            if isinstance(block, dict) and block.get("type") in {"text", "output_text"}
        ]
        if teile:
            return "\n".join(teile)
    raise AuswertungError("Das Modell hat keine Textantwort geliefert.")


_ERLAUBTE_TYPEN = {schluessel for schluessel, _ in DOKUMENTTYPEN}
_ERLAUBTE_SCHLUESSEL = {definition.schluessel for definition in FAKTEN}


class DokumentBefund:
    """What the model read out of one document."""

    def __init__(
        self,
        typ: str,
        typ_unklar: bool,
        qualitaet: Qualitaet,
        qualitaet_begruendung: str,
        dokument_datum: date | None,
        zusammenfassung: str,
        namensvorschlag: str,
        fakten: list[tuple[str, str, Herkunft, float | None]],
    ) -> None:
        self.typ = typ
        self.typ_unklar = typ_unklar
        self.qualitaet = qualitaet
        self.qualitaet_begruendung = qualitaet_begruendung
        self.dokument_datum = dokument_datum
        self.zusammenfassung = zusammenfassung
        self.namensvorschlag = namensvorschlag
        self.fakten = fakten


def _qualitaet(wert: Any) -> Qualitaet:
    try:
        return Qualitaet(str(wert).strip().lower())
    except ValueError:
        return Qualitaet.EINGESCHRAENKT


def _datum(wert: Any) -> date | None:
    if not isinstance(wert, str):
        return None
    try:
        return date.fromisoformat(wert.strip())
    except ValueError:
        return None


async def werte_dokument_aus(
    model: Any,
    dokument: Dokument,
    datei: Attachment,
    empfangsdatum: date,
) -> DokumentBefund:
    """Send one document to the model and return its structured reading."""

    try:
        material = content_blocks_for_analysis(datei)
    except AttachmentError as exc:
        raise AuswertungError(str(exc)) from exc

    inhalt: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                f"Ursprünglicher Dateiname: {dokument.dateiname}\n"
                f"Eingangsdatum: {empfangsdatum.isoformat()}\n"
                "Wenn das Dokument selbst kein Datum ausweist, verwende im "
                "Benennungsvorschlag das Eingangsdatum mit dem Zusatz -E.\n\n"
                "Material folgt."
            ),
        },
        *material,
    ]

    antwort = await model.ainvoke(
        [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=inhalt)]
    )
    daten = _json_aus_antwort(_antworttext(antwort))

    typ = str(daten.get("typ", "")).strip()
    if typ not in _ERLAUBTE_TYPEN:
        typ = "sonstiges"

    fakten: list[tuple[str, str, Herkunft, float | None]] = []
    for eintrag in daten.get("fakten", []) or []:
        if not isinstance(eintrag, dict):
            continue
        schluessel = str(eintrag.get("schluessel", "")).strip()
        wert = eintrag.get("wert")
        if schluessel not in _ERLAUBTE_SCHLUESSEL or wert in (None, ""):
            continue
        seite = eintrag.get("seite")
        konfidenz = eintrag.get("konfidenz")
        fakten.append(
            (
                schluessel,
                str(wert).strip(),
                Herkunft(
                    dokument_id=dokument.id,
                    dateiname=dokument.dateiname,
                    wert=str(wert).strip(),
                    seite=int(seite) if isinstance(seite, (int, float)) else None,
                    zitat=str(eintrag.get("zitat", "")).strip()[:400],
                ),
                float(konfidenz) if isinstance(konfidenz, (int, float)) else None,
            )
        )

    return DokumentBefund(
        typ=typ,
        typ_unklar=bool(daten.get("typ_unklar", False)),
        qualitaet=_qualitaet(daten.get("qualitaet")),
        qualitaet_begruendung=str(daten.get("qualitaet_begruendung", "")).strip()[:400],
        dokument_datum=_datum(daten.get("dokument_datum")),
        zusammenfassung=str(daten.get("zusammenfassung", "")).strip()[:600],
        namensvorschlag=str(daten.get("namensvorschlag", "")).strip()[:255],
        fakten=fakten,
    )


def uebernimm_befund(dokument: Dokument, befund: DokumentBefund) -> None:
    """Write the model's reading onto the document record."""

    dokument.typ = befund.typ
    dokument.typ_unklar = befund.typ_unklar
    dokument.qualitaet = befund.qualitaet
    dokument.qualitaet_begruendung = befund.qualitaet_begruendung
    dokument.zusammenfassung = befund.zusammenfassung
    dokument.namensvorschlag = befund.namensvorschlag or None
    dokument.status = DokumentStatus.GELESEN
