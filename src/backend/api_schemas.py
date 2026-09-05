"""Request and response shapes for the Vorgang API."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.backend.domain import (
    Anforderung,
    AuditEintrag,
    Befund,
    Dokument,
    Fakt,
    Konflikt,
    Verfahrensstrang,
)
from src.backend.schemas import Attachment


class VorgangAnlegen(BaseModel):
    strasse: str = Field(min_length=1, max_length=200)
    plz: str = Field(min_length=4, max_length=10)
    ort: str = Field(default="Bonn", max_length=100)
    bisherige_nutzung: str = Field(default="Wohnnutzung", max_length=200)
    geplante_nutzung: str = Field(default="Ferienhaus", max_length=200)
    vermietungstage: int = Field(default=0, ge=0, le=366)


class VorgangZeile(BaseModel):
    """One row of the Vorgangsübersicht — sorted by what blocks."""

    id: str
    aktenzeichen: str
    adresse: str
    bisherige_nutzung: str
    geplante_nutzung: str
    naechster_schritt: str
    dokumente_zu_pruefen: int
    konflikte_kritisch: int
    anforderungen_fehlend: int
    geaendert_am: datetime


class VorgangDetail(BaseModel):
    id: str
    aktenzeichen: str
    adresse: str
    strasse: str
    plz: str
    ort: str
    bisherige_nutzung: str
    geplante_nutzung: str
    vermietungstage: int
    angelegt_am: datetime
    geaendert_am: datetime
    naechster_schritt: str
    kennzahlen: dict[str, int]
    verfahren: list[Verfahrensstrang]
    eingefroren_am: datetime | None = None
    paket_hash: str | None = None


class DokumenteHochladen(BaseModel):
    dateien: list[Attachment] = Field(min_length=1)


class DokumentAktualisieren(BaseModel):
    typ: str | None = None
    namensvorschlag: str | None = None


class FaktBestaetigen(BaseModel):
    wert: str | None = None


class KonfliktLoesen(BaseModel):
    wert: str = Field(min_length=1)
    notiz: str = ""


class UploadLinkAnlegen(BaseModel):
    empfaenger: str = ""
    angefordert: list[str] = Field(default_factory=list)
    gueltig_stunden: int = Field(default=72, ge=1, le=720)


class UploadLinkAntwort(BaseModel):
    token: str
    empfaenger: str
    angefordert: list[str]
    gueltig_bis: datetime
    widerrufen: bool


class UploadSeite(BaseModel):
    """What the external contributor's page needs — nothing about the case."""

    adresse: str
    angefordert: list[str]
    gueltig_bis: datetime


class AssistentAnfrage(BaseModel):
    nachricht: str = Field(min_length=1, max_length=8000)


class AssistentNachricht(BaseModel):
    rolle: str
    inhalt: str
    werkzeug: str | None = None


class AssistentAntwort(BaseModel):
    antwort: str
    nachrichten: list[AssistentNachricht]


class PaketAntwort(BaseModel):
    eingefroren: bool
    paket_hash: str | None = None
    begruendung: str = ""


class AbgelehnteDatei(BaseModel):
    """A file that never made it into the Vorgang, and why."""

    name: str
    grund: str


class DokumenteAntwort(BaseModel):
    """Always the full list for this Vorgang, plus whatever was rejected.

    Returning the complete list after a write means the frontend can replace
    its state with the answer instead of silently losing rows.
    """

    dokumente: list[Dokument]
    abgelehnt: list[AbgelehnteDatei] = Field(default_factory=list)


class SeitenvorschauAntwort(BaseModel):
    """One rendered source page — the feature that makes a claim checkable."""

    bild_base64: str
    mime_type: str
    seite: int
    seiten_gesamt: int
    markiert: bool
    dateiname: str


class FaktenAntwort(BaseModel):
    fakten: list[Fakt]
    kategorien: list[str]


class KonflikteAntwort(BaseModel):
    konflikte: list[Konflikt]


class AnforderungenAntwort(BaseModel):
    anforderungen: list[Anforderung]


class BefundeAntwort(BaseModel):
    befunde: list[Befund]
    freigabe_moeglich: bool


class AuditAntwort(BaseModel):
    eintraege: list[AuditEintrag]
