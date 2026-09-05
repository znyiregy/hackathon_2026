"""Application content: Portal-Übertragungsblatt, drafts, package manifest.

After 1 September 2026 the submission itself happens in Bauportal.NRW, so a
beautiful PDF package is worth little. What is worth something is a validated,
structured record whose fields map onto the portal assistant's fields, plus the
completeness judgement that decides whether the upload triggers a query.

Three content classes are kept apart and stay distinguishable in the UI:

``fakt``     the value comes from a confirmed project fact — never invented
``entwurf``  an AI draft the Architektin has not accepted yet
``vorlage``  boilerplate that is not yet project-specific
"""

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from langchain.messages import HumanMessage, SystemMessage

from src.backend.domain import Fakt, FaktStatus
from src.backend.store import VorgangAkte

logger = logging.getLogger(__name__)

Inhaltsklasse = Literal["fakt", "entwurf", "vorlage", "fehlt"]


class ErzeugungError(RuntimeError):
    """Raised when an artefact cannot be produced."""


class VoraussetzungFehlt(ErzeugungError):
    """Raised when required facts are not confirmed yet.

    Nothing is generated before its preconditions hold, and the error says
    exactly what has to happen first.
    """

    def __init__(self, fehlende: list[str]) -> None:
        self.fehlende = fehlende
        super().__init__(
            "Diese Inhalte entstehen erst, wenn die Grundlagen bestätigt sind. "
            f"Offen: {', '.join(fehlende)}."
        )


@dataclass(frozen=True)
class PortalFeld:
    """One field of the portal transfer sheet, ready to copy."""

    bezeichnung: str
    wert: str
    klasse: Inhaltsklasse
    quelle: str = ""
    hinweis: str = ""


#: Portal fields in the order the NRW portal assistant asks for them.
PORTAL_FELDER: tuple[tuple[str, str], ...] = (
    ("Straße und Hausnummer", "strasse_hausnummer"),
    ("Postleitzahl", "plz"),
    ("Ort", "ort"),
    ("Gemarkung", "gemarkung"),
    ("Flur", "flur"),
    ("Flurstück", "flurstueck"),
    ("Grundstücksfläche", "grundstuecksflaeche"),
    ("Eigentümer", "eigentuemer"),
    ("Grundbuchblatt", "grundbuchblatt"),
    ("Baujahr", "baujahr"),
    ("Gebäudeklasse", "gebaeudeklasse"),
    ("Anzahl Geschosse", "geschosse"),
    ("Wohneinheiten im Bestand", "wohneinheiten_bestand"),
    ("Bisherige Nutzung", "bisherige_nutzung"),
    ("Geplante Nutzung", "geplante_nutzung"),
    ("Fläche der Ferienwohnung", "flaeche_ferienwohnung"),
    ("Wohnfläche nach WoFlV", "wohnflaeche_woflv"),
    ("Nutzfläche nach DIN 277", "nutzflaeche_din277"),
    ("Maximale Bettenzahl", "betten_max"),
    ("Genehmigte Stellplätze", "stellplaetze_bestand"),
    ("Nachzuweisende Stellplätze", "stellplaetze_geplant"),
)


def uebertragungsblatt(akte: VorgangAkte) -> list[PortalFeld]:
    """Build the copy-ready portal transfer sheet from confirmed facts.

    A fact that is not confirmed is shown as ``fehlt`` rather than filled in
    with an unreviewed guess — the sheet is copied into a portal that produces
    a legally binding application.
    """

    felder: list[PortalFeld] = []
    for bezeichnung, schluessel in PORTAL_FELDER:
        fakt = akte.fakten.get(schluessel)
        if fakt is None or not fakt.wert:
            felder.append(
                PortalFeld(
                    bezeichnung=bezeichnung,
                    wert="",
                    klasse="fehlt",
                    hinweis="Noch kein Wert. Im Faktenblatt ergänzen.",
                )
            )
            continue

        wert = f"{fakt.wert} {fakt.einheit}".strip()
        if fakt.status is FaktStatus.BESTAETIGT:
            quelle = fakt.herkunft[0].dateiname if fakt.herkunft else "Ihre Eingabe"
            felder.append(
                PortalFeld(bezeichnung=bezeichnung, wert=wert, klasse="fakt", quelle=quelle)
            )
        else:
            felder.append(
                PortalFeld(
                    bezeichnung=bezeichnung,
                    wert=wert,
                    klasse="entwurf",
                    quelle=fakt.herkunft[0].dateiname if fakt.herkunft else "",
                    hinweis="Noch nicht bestätigt — vor dem Übertragen prüfen.",
                )
            )
    return felder


@dataclass(frozen=True)
class ArtefaktDefinition:
    """One document the MVP drafts, and what it needs before it can be drafted."""

    schluessel: str
    bezeichnung: str
    zweck: str
    #: Fact keys that must be confirmed before drafting starts.
    voraussetzungen: tuple[str, ...]
    anweisung: str


ARTEFAKTE: tuple[ArtefaktDefinition, ...] = (
    ArtefaktDefinition(
        schluessel="betriebsbeschreibung",
        bezeichnung="Betriebs- und Nutzungsbeschreibung",
        zweck=(
            "Die lästigste Schreibarbeit des Antrags. Beschreibt Gästezahl, "
            "Ruhezeiten, Gastgeber vor Ort und was ausdrücklich nicht stattfindet."
        ),
        voraussetzungen=("strasse_hausnummer", "geplante_nutzung", "vermietungstage"),
        anweisung=(
            "Schreibe eine Betriebs- und Nutzungsbeschreibung für den Bauantrag. "
            "Nenne ausdrücklich: maximale Gästezahl, keine Veranstaltungen oder "
            "Feiern, keine gastronomische Bewirtung, Ruhezeiten von 22:00 bis "
            "07:00 Uhr, und ob eine gastgebende Person vor Ort wohnt. "
            "Sechs bis zehn Sätze, Fließtext, sachlich, keine Aufzählung."
        ),
    ),
    ArtefaktDefinition(
        schluessel="anschreiben",
        bezeichnung="Anschreiben an die Bauaufsicht",
        zweck="Begleitschreiben zur Einreichung über das Bauportal.NRW.",
        voraussetzungen=("strasse_hausnummer", "bisherige_nutzung", "geplante_nutzung"),
        anweisung=(
            "Schreibe ein knappes, förmliches Anschreiben an das Bauaufsichtsamt "
            "der Bundesstadt Bonn zur Nutzungsänderung. Nenne Vorhaben, Adresse "
            "und Flurstück. Höchstens acht Sätze. Keine rechtliche Bewertung, "
            "keine Behauptung über Genehmigungsfähigkeit."
        ),
    ),
    ArtefaktDefinition(
        schluessel="begruendung_planungsrecht",
        bezeichnung="Begründungsgerüst Ausnahme / Befreiung",
        zweck=(
            "Gerüst für die planungsrechtliche Argumentation. Keine Zulässigkeits"
            "aussage — nur die Struktur, die die Architektin selbst füllt."
        ),
        voraussetzungen=("strasse_hausnummer", "geplante_nutzung"),
        anweisung=(
            "Entwirf ein Begründungsgerüst für eine mögliche Ausnahme oder "
            "Befreiung nach § 31 BauGB. Gliedere in: Ausgangslage, Art der "
            "Nutzung, Nachbarschaftsverträglichkeit, Erschließung und "
            "Stellplätze, offene Punkte. Formuliere jeden Abschnitt als Gerüst "
            "mit ausdrücklich markierten Lücken in eckigen Klammern, die die "
            "Architektin füllt. Behaupte NIEMALS, das Vorhaben sei zulässig "
            "oder genehmigungsfähig."
        ),
    ),
)

ARTEFAKT_NACH_SCHLUESSEL = {a.schluessel: a for a in ARTEFAKTE}

SYSTEM_PROMPT = """Du formulierst Antragsinhalte für ein deutsches
Architekturbüro. Du arbeitest ausschließlich mit den geprüften Fakten, die dir
übergeben werden.

Nicht verhandelbare Regeln:
- Erfinde keine Zahlen, Namen, Flächen oder Daten. Fehlt eine Angabe, schreibe
  an dieser Stelle einen Platzhalter in eckigen Klammern, zum Beispiel
  [Wohnfläche ergänzen].
- Du behauptest nie, ein Vorhaben sei zulässig, genehmigungsfähig oder
  rechtmäßig. Du beschreibst nur das Vorhaben und benennst offene Punkte.
- Du triffst keine rechtliche Bewertung und zitierst keine Norm, die dir nicht
  ausdrücklich genannt wurde.
- Deutsch, sachlich, in der Form, die eine Bauaufsicht erwartet.

Antworte ausschließlich mit dem fertigen Text. Keine Vorrede, keine
Überschrift, keine Erklärung deiner Vorgehensweise."""


def _bestaetigte_fakten(akte: VorgangAkte) -> dict[str, Fakt]:
    return {
        schluessel: fakt
        for schluessel, fakt in akte.fakten.items()
        if fakt.status is FaktStatus.BESTAETIGT and fakt.wert
    }


def pruefe_voraussetzungen(akte: VorgangAkte, definition: ArtefaktDefinition) -> None:
    """Raise unless every precondition fact is confirmed."""

    bestaetigt = _bestaetigte_fakten(akte)
    fehlend = [
        akte.fakten[schluessel].bezeichnung
        for schluessel in definition.voraussetzungen
        if schluessel not in bestaetigt and schluessel in akte.fakten
    ]
    if fehlend:
        raise VoraussetzungFehlt(fehlend)


def _faktenblock(akte: VorgangAkte) -> str:
    bestaetigt = _bestaetigte_fakten(akte)
    if not bestaetigt:
        return "Es liegen keine bestätigten Fakten vor."
    zeilen = [
        f"- {fakt.bezeichnung}: {fakt.wert} {fakt.einheit}".rstrip()
        for fakt in bestaetigt.values()
    ]
    return "\n".join(zeilen)


def _text(antwort: Any) -> str:
    text = getattr(antwort, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()
    inhalt = getattr(antwort, "content", antwort)
    if isinstance(inhalt, str) and inhalt.strip():
        return inhalt.strip()
    if isinstance(inhalt, list):
        teile = [
            block.get("text", "")
            for block in inhalt
            if isinstance(block, dict) and block.get("type") in {"text", "output_text"}
        ]
        if teile:
            return "\n".join(teile).strip()
    raise ErzeugungError("Das Modell hat keinen Text geliefert.")


async def erzeuge_artefakt(
    model: Any,
    akte: VorgangAkte,
    schluessel: str,
) -> tuple[str, list[str]]:
    """Draft one artefact from confirmed facts.

    Returns the draft and the placeholders it still contains, so the UI can
    show them as red inline gaps that link back to the fact sheet.
    """

    definition = ARTEFAKT_NACH_SCHLUESSEL.get(schluessel)
    if definition is None:
        raise ErzeugungError(f"Unbekanntes Artefakt {schluessel!r}.")

    pruefe_voraussetzungen(akte, definition)

    vorgang = akte.vorgang
    auftrag = (
        f"{definition.anweisung}\n\n"
        f"Vorhaben: Nutzungsänderung {vorgang.bisherige_nutzung} → "
        f"{vorgang.geplante_nutzung}\n"
        f"Adresse: {vorgang.adresse}\n"
        f"Geplante Vermietung: {vorgang.vermietungstage} Tage im Kalenderjahr\n\n"
        f"Geprüfte Fakten:\n{_faktenblock(akte)}"
    )

    try:
        antwort = await model.ainvoke(
            [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=auftrag)]
        )
    except Exception as exc:  # noqa: BLE001 — surfaced to the UI as retryable
        logger.exception("Artefakt %s konnte nicht erzeugt werden", schluessel)
        raise ErzeugungError("Der Entwurf konnte nicht erzeugt werden.") from exc

    entwurf = _text(antwort)
    luecken = _luecken(entwurf)
    akte.protokoll("Architektin", "Entwurf erzeugt", definition.bezeichnung)
    return entwurf, luecken


def _luecken(text: str) -> list[str]:
    """Collect the ``[…]`` placeholders a draft still carries."""

    import re

    return sorted({treffer.strip() for treffer in re.findall(r"\[([^\]]{1,80})\]", text)})


@dataclass(frozen=True)
class ManifestEintrag:
    dateiname: str
    urspruenglich: str
    typ: str
    groesse_bytes: int
    pruefsumme: str


def manifest(akte: VorgangAkte) -> list[ManifestEintrag]:
    """List the package contents under their proposed names, with checksums."""

    eintraege: list[ManifestEintrag] = []
    for dokument in akte.dokumente.values():
        datei = akte.dateien.get(dokument.id)
        pruefsumme = ""
        if datei is not None:
            import base64

            try:
                rohdaten = base64.b64decode(datei.content_base64, validate=False)
                pruefsumme = hashlib.sha256(rohdaten).hexdigest()[:16]
            except (ValueError, TypeError):
                pruefsumme = ""
        eintraege.append(
            ManifestEintrag(
                dateiname=dokument.namensvorschlag or dokument.dateiname,
                urspruenglich=dokument.dateiname,
                typ=dokument.typ or "unklar",
                groesse_bytes=dokument.groesse_bytes,
                pruefsumme=pruefsumme,
            )
        )
    return sorted(eintraege, key=lambda eintrag: eintrag.dateiname)


def pruefprotokoll(akte: VorgangAkte, befunde: list[Any]) -> str:
    """Render the audit record the Architektin files for liability reasons."""

    vorgang = akte.vorgang
    jetzt = datetime.now(timezone.utc).astimezone()
    zeilen = [
        "PRÜFPROTOKOLL — DIGITAL DEUTSCHLAND",
        "=" * 60,
        "",
        f"Vorgang:        {vorgang.aktenzeichen}",
        f"Objekt:         {vorgang.adresse}",
        f"Vorhaben:       Nutzungsänderung {vorgang.bisherige_nutzung} → {vorgang.geplante_nutzung}",
        f"Erstellt am:    {jetzt.strftime('%d.%m.%Y %H:%M')}",
        f"Paket-Prüfsumme: {akte.paket_hash or 'nicht eingefroren'}",
        "",
        "HINWEIS",
        "-" * 60,
        "Diese Vorbereitung ist keine Rechtsberatung und keine Aussage über die",
        "Genehmigungsfähigkeit. Die Einreichung erfolgt durch die",
        "bauvorlageberechtigte Person über das Bauportal.NRW.",
        "",
        "BESTÄTIGTE PROJEKTDATEN",
        "-" * 60,
    ]

    bestaetigt = _bestaetigte_fakten(akte)
    if bestaetigt:
        for fakt in bestaetigt.values():
            quelle = fakt.herkunft[0].dateiname if fakt.herkunft else "Eingabe der Architektin"
            wert = f"{fakt.wert} {fakt.einheit}".strip()
            zeilen.append(f"  {fakt.bezeichnung}: {wert}")
            zeilen.append(f"      Quelle: {quelle} · bestätigt von {fakt.bestaetigt_von}")
    else:
        zeilen.append("  Keine bestätigten Projektdaten.")

    zeilen += ["", "UNTERLAGEN", "-" * 60]
    for eintrag in manifest(akte):
        zeilen.append(f"  {eintrag.dateiname}  [{eintrag.typ}]  sha256:{eintrag.pruefsumme}")
    if not akte.dokumente:
        zeilen.append("  Keine Unterlagen aufgenommen.")

    zeilen += ["", "BEFUNDE DER EINREICHUNGSPRÜFUNG", "-" * 60]
    if befunde:
        for befund in befunde:
            grad = getattr(befund, "schweregrad", "")
            grad_text = getattr(grad, "value", str(grad)).upper()
            zeilen.append(f"  [{grad_text}] {getattr(befund, 'beobachtung', '')}")
            massnahme = getattr(befund, "massnahme", "")
            if massnahme:
                zeilen.append(f"      Maßnahme: {massnahme}")
    else:
        zeilen.append("  Keine Befunde.")

    zeilen += ["", "ENTSCHEIDUNGSPROTOKOLL", "-" * 60]
    for eintrag in akte.audit:
        zeitpunkt = eintrag.zeitpunkt.astimezone().strftime("%d.%m.%Y %H:%M")
        detail = f" — {eintrag.detail}" if eintrag.detail else ""
        zeilen.append(f"  {zeitpunkt}  {eintrag.akteur}: {eintrag.aktion}{detail}")

    return "\n".join(zeilen)
