"""Domain model for Nutzungsänderung Vorgänge.

Facts, not files, are the primary object. A document is evidence; the durable
value is the typed, sourced statement. Every fact therefore carries its
provenance and a review status that only a person can advance to ``bestaetigt``.
"""

from datetime import datetime, timezone
from enum import StrEnum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid4().hex[:12]


class FaktStatus(StrEnum):
    """Review state of a single project fact."""

    KI_ENTWURF = "ki_entwurf"
    BESTAETIGT = "bestaetigt"
    OFFEN = "offen"
    KONFLIKT = "konflikt"


class Schweregrad(StrEnum):
    KRITISCH = "kritisch"
    WARNUNG = "warnung"
    HINWEIS = "hinweis"


class AnforderungStatus(StrEnum):
    BELEGT = "belegt"
    TEILWEISE = "teilweise"
    OFFEN = "offen"
    NICHT_PRUEFBAR = "nicht_pruefbar"


class DokumentStatus(StrEnum):
    EMPFANGEN = "empfangen"
    GEPRUEFT = "geprueft"
    EINGEORDNET = "eingeordnet"
    GELESEN = "gelesen"
    FEHLER = "fehler"


class Qualitaet(StrEnum):
    GUT = "gut"
    EINGESCHRAENKT = "eingeschraenkt"
    UNBRAUCHBAR = "unbrauchbar"


class Herkunft(BaseModel):
    """Where a fact value came from, so the UI can show the source page.

    ``wert`` is what this document asserts. The conflict engine compares these
    values, never the quotes — a quote is prose and would make identical values
    look like contradictions.
    """

    dokument_id: str
    dateiname: str
    wert: str = ""
    seite: int | None = None
    zitat: str = ""


class Fakt(BaseModel):
    """One typed project fact.

    ``schluessel`` carries the definition: ``wohnflaeche_woflv`` and
    ``nutzflaeche_din277`` are different facts and are never compared with
    each other.
    """

    id: str = Field(default_factory=_new_id)
    schluessel: str
    bezeichnung: str
    kategorie: str
    wert: str | None = None
    einheit: str = ""
    status: FaktStatus = FaktStatus.OFFEN
    pflicht: bool = True
    konfidenz: float | None = None
    herkunft: list[Herkunft] = Field(default_factory=list)
    bestaetigt_von: str | None = None
    bestaetigt_am: datetime | None = None
    notiz: str = ""


class KonfliktWert(BaseModel):
    """One competing value for a fact, with the document that asserts it."""

    wert: str
    dokument_id: str
    dateiname: str
    seite: int | None = None


class Konflikt(BaseModel):
    id: str = Field(default_factory=_new_id)
    schluessel: str
    bezeichnung: str
    schweregrad: Schweregrad
    werte: list[KonfliktWert] = Field(default_factory=list)
    hinweis: str = ""
    geklaert: bool = False
    gewaehlter_wert: str | None = None
    entschieden_von: str | None = None
    entschieden_am: datetime | None = None


class Anforderung(BaseModel):
    """One required Bauvorlage or Nachweis for this procedure."""

    id: str = Field(default_factory=_new_id)
    bezeichnung: str
    pflicht: bool = True
    status: AnforderungStatus = AnforderungStatus.OFFEN
    rechtsgrundlage: str = ""
    beleg_dokument_ids: list[str] = Field(default_factory=list)
    hinweis: str = ""


class Befund(BaseModel):
    """One finding of the pre-submission review."""

    id: str = Field(default_factory=_new_id)
    schweregrad: Schweregrad
    beobachtung: str
    grundlage: str = ""
    beleg: str = ""
    massnahme: str = ""


class Dokument(BaseModel):
    id: str = Field(default_factory=_new_id)
    dateiname: str
    mime_type: str
    groesse_bytes: int = 0
    seiten: int | None = None
    typ: str | None = None
    typ_unklar: bool = False
    qualitaet: Qualitaet | None = None
    qualitaet_begruendung: str = ""
    status: DokumentStatus = DokumentStatus.EMPFANGEN
    namensvorschlag: str | None = None
    zusammenfassung: str = ""
    fehler: str = ""
    hochgeladen_am: datetime = Field(default_factory=_now)
    quelle: Literal["buero", "extern"] = "buero"


class Verfahrensstrang(BaseModel):
    """One of the parallel procedures this constellation triggers."""

    schluessel: str
    bezeichnung: str
    behoerde: str
    status: str
    kritisch: bool = False
    erlaeuterung: str = ""


class Vorgang(BaseModel):
    id: str = Field(default_factory=_new_id)
    aktenzeichen: str
    strasse: str
    plz: str
    ort: str = "Bonn"
    bisherige_nutzung: str = "Wohnnutzung"
    geplante_nutzung: str = "Ferienhaus"
    vermietungstage: int = 0
    angelegt_am: datetime = Field(default_factory=_now)
    geaendert_am: datetime = Field(default_factory=_now)

    @property
    def adresse(self) -> str:
        return f"{self.strasse}, {self.plz} {self.ort}"


class UploadLink(BaseModel):
    """A tokenised, expiring, upload-only link for an external contributor."""

    token: str
    vorgang_id: str
    empfaenger: str = ""
    angefordert: list[str] = Field(default_factory=list)
    erstellt_am: datetime = Field(default_factory=_now)
    gueltig_bis: datetime
    widerrufen: bool = False

    def ist_gueltig(self, jetzt: datetime | None = None) -> bool:
        jetzt = jetzt or _now()
        return not self.widerrufen and jetzt < self.gueltig_bis


class AuditEintrag(BaseModel):
    id: str = Field(default_factory=_new_id)
    zeitpunkt: datetime = Field(default_factory=_now)
    akteur: str
    aktion: str
    detail: str = ""
