"""HTTP routes for Antragsvorbereitung and the submission package."""

import base64
import logging
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.backend.api_vorgaenge import get_service, get_store_dep
from src.backend.assistent import ConfigurationError, baue_modell
from src.backend.config import get_settings
from src.backend.erzeugung import (
    ARTEFAKTE,
    ErzeugungError,
    VoraussetzungFehlt,
    erzeuge_artefakt,
    manifest,
    pruefprotokoll,
    uebertragungsblatt,
)
from src.backend.store import Store, VorgangAkte, VorgangNotFoundError
from src.backend.vorgang_service import VorgangService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["erzeugung"])


@lru_cache
def _modell() -> Any:
    return baue_modell(get_settings())


async def get_modell() -> Any:
    """The chat model used to phrase drafts. Overridable in tests."""

    try:
        return _modell()
    except ConfigurationError as exc:
        logger.error("Konfigurationsfehler: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


class PortalFeldAntwort(BaseModel):
    bezeichnung: str
    wert: str
    klasse: str
    quelle: str = ""
    hinweis: str = ""


class UebertragungsblattAntwort(BaseModel):
    felder: list[PortalFeldAntwort]
    vollstaendig: bool
    portal_url: str = "https://www.bauportal.nrw.de"
    hinweis: str = "Digital Deutschland übermittelt nichts an eine Behörde."


class ArtefaktInfo(BaseModel):
    schluessel: str
    bezeichnung: str
    zweck: str
    bereit: bool
    fehlende_voraussetzungen: list[str] = Field(default_factory=list)


class ArtefaktListe(BaseModel):
    artefakte: list[ArtefaktInfo]


class ArtefaktAntwort(BaseModel):
    schluessel: str
    bezeichnung: str
    entwurf: str
    luecken: list[str] = Field(default_factory=list)
    klasse: str = "entwurf"


class ManifestEintragAntwort(BaseModel):
    dateiname: str
    urspruenglich: str
    typ: str
    groesse_bytes: int
    pruefsumme: str


class PaketAntwort(BaseModel):
    manifest: list[ManifestEintragAntwort]
    eingefroren_am: str | None = None
    paket_hash: str | None = None
    freigabe_moeglich: bool
    offene_kritische: int


def _akte(store: Store, vorgang_id: str) -> VorgangAkte:
    try:
        return store.akte(vorgang_id)
    except VorgangNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/vorgaenge/{vorgang_id}/uebertragungsblatt", response_model=UebertragungsblattAntwort)
async def blatt(
    vorgang_id: str,
    store: Store = Depends(get_store_dep),
) -> UebertragungsblattAntwort:
    """The copy-ready portal transfer sheet — the output that is actually usable."""

    akte = _akte(store, vorgang_id)
    felder = uebertragungsblatt(akte)
    return UebertragungsblattAntwort(
        felder=[
            PortalFeldAntwort(
                bezeichnung=feld.bezeichnung,
                wert=feld.wert,
                klasse=feld.klasse,
                quelle=feld.quelle,
                hinweis=feld.hinweis,
            )
            for feld in felder
        ],
        vollstaendig=all(feld.klasse == "fakt" for feld in felder),
    )


@router.get("/vorgaenge/{vorgang_id}/artefakte", response_model=ArtefaktListe)
async def artefakte(
    vorgang_id: str,
    store: Store = Depends(get_store_dep),
) -> ArtefaktListe:
    """List what can be drafted, and what is still missing before it can be."""

    from src.backend.erzeugung import pruefe_voraussetzungen

    akte = _akte(store, vorgang_id)
    infos: list[ArtefaktInfo] = []
    for definition in ARTEFAKTE:
        try:
            pruefe_voraussetzungen(akte, definition)
            infos.append(
                ArtefaktInfo(
                    schluessel=definition.schluessel,
                    bezeichnung=definition.bezeichnung,
                    zweck=definition.zweck,
                    bereit=True,
                )
            )
        except VoraussetzungFehlt as exc:
            infos.append(
                ArtefaktInfo(
                    schluessel=definition.schluessel,
                    bezeichnung=definition.bezeichnung,
                    zweck=definition.zweck,
                    bereit=False,
                    fehlende_voraussetzungen=exc.fehlende,
                )
            )
    return ArtefaktListe(artefakte=infos)


@router.post(
    "/vorgaenge/{vorgang_id}/artefakte/{schluessel}/erzeugen",
    response_model=ArtefaktAntwort,
)
async def erzeugen(
    vorgang_id: str,
    schluessel: str,
    store: Store = Depends(get_store_dep),
    model: Any = Depends(get_modell),
) -> ArtefaktAntwort:
    """Draft one artefact. Nothing is generated before its preconditions hold."""

    from src.backend.erzeugung import ARTEFAKT_NACH_SCHLUESSEL

    akte = _akte(store, vorgang_id)
    definition = ARTEFAKT_NACH_SCHLUESSEL.get(schluessel)
    if definition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unbekanntes Artefakt {schluessel!r}.",
        )

    try:
        entwurf, luecken = await erzeuge_artefakt(model, akte, schluessel)
    except VoraussetzungFehlt as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ErzeugungError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return ArtefaktAntwort(
        schluessel=schluessel,
        bezeichnung=definition.bezeichnung,
        entwurf=entwurf,
        luecken=luecken,
    )


@router.get("/vorgaenge/{vorgang_id}/paket", response_model=PaketAntwort)
async def paket(
    vorgang_id: str,
    store: Store = Depends(get_store_dep),
    service: VorgangService = Depends(get_service),
) -> PaketAntwort:
    """Package contents, checksums and whether it may be frozen."""

    akte = _akte(store, vorgang_id)
    befunde = service.befunde(vorgang_id)
    kritische = sum(1 for befund in befunde if befund.schweregrad.value == "kritisch")
    return PaketAntwort(
        manifest=[
            ManifestEintragAntwort(
                dateiname=eintrag.dateiname,
                urspruenglich=eintrag.urspruenglich,
                typ=eintrag.typ,
                groesse_bytes=eintrag.groesse_bytes,
                pruefsumme=eintrag.pruefsumme,
            )
            for eintrag in manifest(akte)
        ],
        eingefroren_am=akte.eingefroren_am.isoformat() if akte.eingefroren_am else None,
        paket_hash=akte.paket_hash,
        freigabe_moeglich=kritische == 0,
        offene_kritische=kritische,
    )


@router.get("/vorgaenge/{vorgang_id}/pruefprotokoll")
async def protokoll_datei(
    vorgang_id: str,
    store: Store = Depends(get_store_dep),
    service: VorgangService = Depends(get_service),
) -> dict[str, str]:
    """The audit record, as a downloadable text file."""

    akte = _akte(store, vorgang_id)
    text = pruefprotokoll(akte, service.befunde(vorgang_id))
    return {
        "name": f"Pruefprotokoll_{akte.vorgang.aktenzeichen}.txt",
        "mime_type": "text/plain",
        "content_base64": base64.b64encode(text.encode("utf-8")).decode("ascii"),
        "text": text,
    }
