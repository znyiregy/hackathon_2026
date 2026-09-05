"""Deterministic comparison, requirement evaluation and submission review.

The split that makes this product trustworthy: the model extracts and phrases,
this module compares and judges. Nothing here calls an LLM. Severity is never
decided by a model.
"""

import re
import unicodedata
from datetime import date, datetime

from src.backend.domain import (
    Anforderung,
    AnforderungStatus,
    Befund,
    Dokument,
    Fakt,
    FaktStatus,
    Konflikt,
    KonfliktWert,
    Qualitaet,
    Schweregrad,
)
from src.backend.katalog import (
    ANFORDERUNGEN,
    FAKT_NACH_SCHLUESSEL,
)

#: Facts where two different values are a hard blocker rather than a hint.
KRITISCHE_SCHLUESSEL = frozenset(
    {
        "flurstueck",
        "gemarkung",
        "flur",
        "strasse_hausnummer",
        "plz",
        "eigentuemer",
        "grundbuchblatt",
    }
)

# ``ß`` ist zu diesem Zeitpunkt bereits zu ``ss`` normalisiert.
_STRASSE_ERSATZ = (
    ("strasse", "str"),
    ("str.", "str"),
)


def _basis_normalisierung(wert: str) -> str:
    text = unicodedata.normalize("NFKC", wert).strip().lower()
    text = text.replace("ß", "ss")
    return re.sub(r"\s+", " ", text)


def normalisiere_adresse(wert: str) -> str:
    """Normalise a street address so spelling variants stop being conflicts.

    ``Musterstraße 12`` and ``Musterstr. 12`` are the same address; ``12`` and
    ``21`` are not. Separators become spaces rather than vanishing, so
    ``Kurt-Schumacher-Str. 12`` and ``Kurt Schumacher Straße 12`` still match.
    """

    text = _basis_normalisierung(wert)
    for muster, ersatz in _STRASSE_ERSATZ:
        text = text.replace(muster, ersatz)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


#: A number token: digits, optionally grouped by dots/spaces, optional decimals.
_ZAHL_MUSTER = re.compile(r"-?\d[\d.,  ]*\d|-?\d")


def normalisiere_zahl(wert: str) -> float | None:
    """Read a number as German documents write it, ignoring the unit.

    German convention decides what a dot means: with a comma present the dot
    groups thousands (``1.234,50`` → 1234.5). Without a comma, a dot followed
    by exactly three digits also groups thousands (``1.250`` → 1250), while any
    other dot is a decimal point (``92.40`` → 92.4). Getting this wrong turns
    equal areas into conflicts and hides real ones.
    """

    treffer = _ZAHL_MUSTER.search(wert)
    if treffer is None:
        return None

    text = treffer.group(0).replace(" ", "").replace(" ", "").rstrip(".,")
    if not text:
        return None

    if "," in text:
        # Comma is the decimal separator; every dot groups thousands.
        text = text.replace(".", "").replace(",", ".", 1).replace(",", "")
    elif "." in text:
        vorne, _, hinten = text.rpartition(".")
        gruppiert = len(hinten) == 3 and vorne.replace(".", "").replace("-", "").isdigit()
        if gruppiert:
            text = text.replace(".", "")

    try:
        return float(text)
    except ValueError:
        return None


def normalisiere_datum(wert: str) -> date | None:
    """Read a date in the formats German documents actually use."""

    text = wert.strip()
    for muster in ("%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, muster).date()
        except ValueError:
            continue
    treffer = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", text)
    if treffer:
        tag, monat, jahr = (int(teil) for teil in treffer.groups())
        try:
            return date(jahr, monat, tag)
        except ValueError:
            return None
    return None


def _vergleichsschluessel(schluessel: str, wert: str) -> str:
    """Reduce a raw value to the form two documents must share to agree."""

    if schluessel in {"strasse_hausnummer"}:
        return normalisiere_adresse(wert)
    if schluessel.endswith("_datum"):
        datum = normalisiere_datum(wert)
        return datum.isoformat() if datum else _basis_normalisierung(wert)
    definition = FAKT_NACH_SCHLUESSEL.get(schluessel)
    if definition is not None and definition.einheit in {"m²", "m", "Tage"}:
        zahl = normalisiere_zahl(wert)
        # One decimal place: 92,40 and 92,4 agree; 92,4 and 96,2 do not.
        return f"{zahl:.1f}" if zahl is not None else _basis_normalisierung(wert)
    return _basis_normalisierung(wert)


def _schweregrad_fuer(schluessel: str) -> Schweregrad:
    if schluessel in KRITISCHE_SCHLUESSEL:
        return Schweregrad.KRITISCH
    return Schweregrad.WARNUNG


def finde_konflikte(aussagen: dict[str, list[KonfliktWert]]) -> list[Konflikt]:
    """Compare competing values per typed fact and emit conflicts.

    ``aussagen`` maps a fact key to every value asserted for it. Values are
    only ever compared within one key, so ``wohnflaeche_woflv`` is never
    weighed against ``nutzflaeche_din277``.
    """

    konflikte: list[Konflikt] = []
    for schluessel, werte in sorted(aussagen.items()):
        definition = FAKT_NACH_SCHLUESSEL.get(schluessel)
        if definition is None or not definition.vergleichbar or len(werte) < 2:
            continue

        gruppen: dict[str, list[KonfliktWert]] = {}
        for wert in werte:
            gruppen.setdefault(_vergleichsschluessel(schluessel, wert.wert), []).append(wert)
        if len(gruppen) < 2:
            continue

        vertreter = [gruppe[0] for gruppe in gruppen.values()]
        konflikte.append(
            Konflikt(
                schluessel=schluessel,
                bezeichnung=definition.bezeichnung,
                schweregrad=_schweregrad_fuer(schluessel),
                werte=vertreter,
                hinweis=_konflikt_hinweis(schluessel),
            )
        )

    konflikte.extend(_plausibilitaets_hinweise(aussagen))
    return konflikte


def _konflikt_hinweis(schluessel: str) -> str:
    if schluessel == "flurstueck":
        return "Ein abweichendes Flurstück führt regelmäßig zu einer Nachforderung."
    if schluessel == "eigentuemer":
        return (
            "Abweichende Eigentümerangaben müssen über den aktuellen Grundbuchauszug "
            "geklärt werden. Nicht durch Annahme auflösen."
        )
    if schluessel in {"strasse_hausnummer", "plz"}:
        return "Eine abweichende Adresse betrifft die Zuordnung des gesamten Vorgangs."
    return "Zwei unterschiedliche Angaben in den Unterlagen. Bitte kanonischen Wert wählen."


def _plausibilitaets_hinweise(aussagen: dict[str, list[KonfliktWert]]) -> list[Konflikt]:
    """Sanity-check related but differently defined facts.

    Wohnfläche should not exceed Nutzfläche. That is a hint, never a critical
    finding — three correct numbers under three definitions are normal in a
    German building file.
    """

    hinweise: list[Konflikt] = []
    wohn = aussagen.get("wohnflaeche_woflv") or []
    nutz = aussagen.get("nutzflaeche_din277") or []
    if not wohn or not nutz:
        return hinweise

    # Größte Wohnfläche gegen kleinste Nutzfläche, damit das Ergebnis nicht
    # von der Reihenfolge der Uploads abhängt.
    wohn_paare = [(normalisiere_zahl(w.wert), w) for w in wohn]
    nutz_paare = [(normalisiere_zahl(n.wert), n) for n in nutz]
    wohn_gueltig = [(zahl, quelle) for zahl, quelle in wohn_paare if zahl is not None]
    nutz_gueltig = [(zahl, quelle) for zahl, quelle in nutz_paare if zahl is not None]
    if not wohn_gueltig or not nutz_gueltig:
        return hinweise

    wohn_zahl, wohn_quelle = max(wohn_gueltig, key=lambda paar: paar[0])
    nutz_zahl, nutz_quelle = min(nutz_gueltig, key=lambda paar: paar[0])
    if wohn_zahl <= nutz_zahl:
        return hinweise

    hinweise.append(
        Konflikt(
            schluessel="flaechen_plausibilitaet",
            bezeichnung="Wohnfläche / Nutzfläche",
            schweregrad=Schweregrad.HINWEIS,
            werte=[wohn_quelle, nutz_quelle],
            hinweis=(
                "Wohnfläche nach WoFlV liegt über der Nutzfläche nach DIN 277. "
                "Unterschiedliche Bezugsgrößen — häufig kein Widerspruch, aber prüfenswert."
            ),
        )
    )
    return hinweise


def bewerte_anforderungen(dokumente: list[Dokument]) -> list[Anforderung]:
    """Fill the requirement checklist from the classified documents.

    A document only counts as evidence once it has been classified and is not
    judged unusable. A related document existing is never enough on its own to
    mark a requirement fulfilled.
    """

    # Ein Dokument belegt erst, wenn sein Typ feststeht. Eine unsichere
    # Zuordnung des Modells darf die Ampel nie auf grün stellen — genau das
    # verbietet der Systemprompt dem Modell, also darf der Code es auch nicht.
    brauchbar = [
        dokument
        for dokument in dokumente
        if dokument.typ
        and not dokument.typ_unklar
        and dokument.qualitaet is not Qualitaet.UNBRAUCHBAR
    ]

    anforderungen: list[Anforderung] = []
    for definition in ANFORDERUNGEN:
        belege = [dokument for dokument in brauchbar if dokument.typ in definition.belegt_durch]
        eingeschraenkt = [
            dokument for dokument in belege if dokument.qualitaet is Qualitaet.EINGESCHRAENKT
        ]

        if not belege:
            status = AnforderungStatus.OFFEN
        elif eingeschraenkt and len(eingeschraenkt) == len(belege):
            status = AnforderungStatus.TEILWEISE
        else:
            status = AnforderungStatus.BELEGT

        anforderungen.append(
            Anforderung(
                bezeichnung=definition.bezeichnung,
                pflicht=definition.pflicht,
                status=status,
                rechtsgrundlage=definition.rechtsgrundlage,
                beleg_dokument_ids=[dokument.id for dokument in belege],
                hinweis=definition.hinweis,
            )
        )
    return anforderungen


def einreichungspruefung(
    fakten: list[Fakt],
    konflikte: list[Konflikt],
    anforderungen: list[Anforderung],
    dokumente: list[Dokument],
    vermietungstage: int,
) -> list[Befund]:
    """Produce the findings a case officer's checklist would produce.

    What is simulated is the checklist and the incentive, not a person. The
    question is never "what would a strict official say" but "which checklist
    item cannot be ticked from these documents".
    """

    befunde: list[Befund] = []

    for konflikt in konflikte:
        if konflikt.geklaert or konflikt.schweregrad is Schweregrad.HINWEIS:
            continue
        quellen = " · ".join(f"{wert.wert} ({wert.dateiname})" for wert in konflikt.werte)
        befunde.append(
            Befund(
                schweregrad=konflikt.schweregrad,
                beobachtung=f"{konflikt.bezeichnung}: widersprüchliche Angaben in den Unterlagen.",
                grundlage="Dokumentübergreifender Vergleich geprüfter Fakten.",
                beleg=quellen,
                massnahme="Kanonischen Wert wählen und die abweichende Unterlage korrigieren.",
            )
        )

    for anforderung in anforderungen:
        if anforderung.status is AnforderungStatus.BELEGT:
            continue
        if anforderung.pflicht and anforderung.status is AnforderungStatus.OFFEN:
            schweregrad = Schweregrad.KRITISCH
            massnahme = "Unterlage beschaffen oder bei der Eigentümerin anfordern."
        elif anforderung.pflicht:
            schweregrad = Schweregrad.WARNUNG
            massnahme = "Vorhandenen Beleg prüfen und vollständige Fassung nachreichen."
        else:
            schweregrad = Schweregrad.HINWEIS
            massnahme = "Empfohlener Beleg. Fehlt er, mit Begründung dokumentieren."
        befunde.append(
            Befund(
                schweregrad=schweregrad,
                beobachtung=f"{anforderung.bezeichnung}: Status {anforderung.status.value}.",
                grundlage=anforderung.rechtsgrundlage,
                beleg=anforderung.hinweis,
                massnahme=massnahme,
            )
        )

    # Zwei verschiedene Sachverhalte, die im Blueprint zusammenfallen:
    #
    # Ein KI-Vorschlag, den niemand geprüft hat, ist ein echter Blocker — genau
    # dafür existiert die Bestätigung. Eine Pflichtangabe dagegen, zu der es in
    # keiner Unterlage etwas gibt, kann die Architektin gerade nicht bestätigen;
    # daraus einen kritischen Befund zu machen würde das Einfrieren dauerhaft
    # sperren und das Freigabetor bedeutungslos machen.
    ungeprueft = [
        fakt
        for fakt in fakten
        if fakt.pflicht and fakt.wert and fakt.status is not FaktStatus.BESTAETIGT
    ]
    if ungeprueft:
        namen = ", ".join(fakt.bezeichnung for fakt in ungeprueft[:5])
        weitere = f" und {len(ungeprueft) - 5} weitere" if len(ungeprueft) > 5 else ""
        befunde.append(
            Befund(
                schweregrad=Schweregrad.KRITISCH,
                beobachtung=f"{len(ungeprueft)} KI-Vorschläge sind noch nicht bestätigt.",
                grundlage="Jede KI-Aussage muss von einer berechtigten Person bestätigt werden.",
                beleg=f"{namen}{weitere}",
                massnahme="Faktenblatt durchgehen und jede Angabe gegen die Quelle prüfen.",
            )
        )

    ohne_quelle = [
        fakt for fakt in fakten if fakt.pflicht and not fakt.wert
    ]
    if ohne_quelle:
        namen = ", ".join(fakt.bezeichnung for fakt in ohne_quelle[:5])
        weitere = f" und {len(ohne_quelle) - 5} weitere" if len(ohne_quelle) > 5 else ""
        befunde.append(
            Befund(
                schweregrad=Schweregrad.WARNUNG,
                beobachtung=f"{len(ohne_quelle)} Pflichtangaben haben noch keinen Wert.",
                grundlage="Die Unterlagen enthalten dazu nichts.",
                beleg=f"{namen}{weitere}",
                massnahme="Von Ihnen eintragen oder die passende Unterlage anfordern.",
            )
        )

    unbrauchbar = [
        dokument for dokument in dokumente if dokument.qualitaet is Qualitaet.UNBRAUCHBAR
    ]
    if unbrauchbar:
        befunde.append(
            Befund(
                schweregrad=Schweregrad.WARNUNG,
                beobachtung=f"{len(unbrauchbar)} Unterlage(n) sind nicht auswertbar.",
                grundlage="Dokumentqualitätsbewertung.",
                beleg=", ".join(dokument.dateiname for dokument in unbrauchbar),
                massnahme="Bessere Vorlage anfordern, bevor das Paket eingefroren wird.",
            )
        )

    if vermietungstage > 90:
        befunde.append(
            Befund(
                schweregrad=Schweregrad.KRITISCH,
                beobachtung=(
                    f"Geplante Vermietung von {vermietungstage} Tagen überschreitet die Schwelle "
                    "von 90 Tagen im Kalenderjahr."
                ),
                grundlage="Zweckentfremdungssatzung der Bundesstadt Bonn.",
                beleg="Deterministische Regel auf die geplanten Vermietungstage.",
                massnahme=(
                    "Zweckentfremdungsgenehmigung beim Amt für Soziales und Wohnen beantragen. "
                    "Die Baugenehmigung allein erlaubt die Vermietung nicht."
                ),
            )
        )

    reihenfolge = {Schweregrad.KRITISCH: 0, Schweregrad.WARNUNG: 1, Schweregrad.HINWEIS: 2}
    return sorted(befunde, key=lambda befund: reihenfolge[befund.schweregrad])


def freigabe_moeglich(befunde: list[Befund]) -> bool:
    """A package may only be frozen when nothing critical is open."""

    return not any(befund.schweregrad is Schweregrad.KRITISCH for befund in befunde)


def naechster_schritt(
    dokumente: list[Dokument],
    fakten: list[Fakt],
    konflikte: list[Konflikt],
    anforderungen: list[Anforderung],
) -> str:
    """Plain-language next action, computed from state — never generated."""

    zu_pruefen = [dokument for dokument in dokumente if dokument.typ_unklar]
    offene_konflikte = [
        konflikt
        for konflikt in konflikte
        if not konflikt.geklaert and konflikt.schweregrad is Schweregrad.KRITISCH
    ]
    fehlende = [
        anforderung
        for anforderung in anforderungen
        if anforderung.pflicht and anforderung.status is AnforderungStatus.OFFEN
    ]
    unbestaetigt = [
        fakt for fakt in fakten if fakt.pflicht and fakt.status is not FaktStatus.BESTAETIGT
    ]

    if not dokumente:
        return "Laden Sie die Projektunterlagen hoch oder erzeugen Sie einen Upload-Link für die Eigentümerin."
    if offene_konflikte:
        namen = ", ".join(konflikt.bezeichnung for konflikt in offene_konflikte[:2])
        return f"Lösen Sie die {len(offene_konflikte)} kritischen Widersprüche ({namen}), bevor Antragsinhalte entstehen."
    if zu_pruefen:
        return f"Ordnen Sie {len(zu_pruefen)} Unterlage(n) ein, deren Typ noch unklar ist."
    if unbestaetigt:
        return f"Bestätigen Sie die restlichen Projektdaten — {len(unbestaetigt)} Pflichtangaben sind offen."
    if fehlende:
        return f"Fordern Sie {len(fehlende)} fehlende Pflichtunterlage(n) an."
    return "Führen Sie die Einreichungsprüfung durch und frieren Sie das Paket ein."
