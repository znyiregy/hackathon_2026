"""HTTP routes for Vorgänge, documents, facts, conflicts and the assistant."""

import logging
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from langchain.messages import HumanMessage, ToolMessage

from src.backend.api_schemas import (
    AbgelehnteDatei,
    AnforderungenAntwort,
    AssistentAnfrage,
    AssistentAntwort,
    AssistentNachricht,
    AuditAntwort,
    BefundeAntwort,
    DokumentAktualisieren,
    DokumenteAntwort,
    DokumenteHochladen,
    FaktBestaetigen,
    FaktenAntwort,
    KonflikteAntwort,
    KonfliktLoesen,
    PaketAntwort,
    SeitenvorschauAntwort,
    UploadLinkAnlegen,
    UploadLinkAntwort,
    UploadSeite,
    VorgangAnlegen,
    VorgangDetail,
    VorgangZeile,
)
from src.backend.assistent import ConfigurationError, baue_assistent, baue_modell
from src.backend.attachments import AttachmentError, AttachmentTooLargeError, validate_attachments
from src.backend.config import get_settings
from src.backend.domain import Fakt
from src.backend.katalog import KATEGORIEN
from src.backend.regeln import freigabe_moeglich
from src.backend.vorschau import VorschauError, seite_rendern
from src.backend.store import (
    Store,
    UploadLinkInvalidError,
    VorgangAkte,
    VorgangNotFoundError,
    get_store,
)
from src.backend.vorgang_service import VorgangService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["vorgaenge"])


@lru_cache
def _bausteine() -> tuple[Store, VorgangService, Any]:
    settings = get_settings()
    store = get_store()
    model = baue_modell(settings)
    service = VorgangService(store, model)
    assistent = baue_assistent(store, service, model)
    return store, service, assistent


def _hole_bausteine() -> tuple[Store, VorgangService, Any]:
    try:
        return _bausteine()
    except ConfigurationError as exc:
        logger.error("Konfigurationsfehler: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


async def get_service() -> VorgangService:
    return _hole_bausteine()[1]


async def get_store_dep() -> Store:
    return _hole_bausteine()[0]


async def get_assistent() -> Any:
    return _hole_bausteine()[2]


def _akte_oder_404(store: Store, vorgang_id: str) -> VorgangAkte:
    try:
        return store.akte(vorgang_id)
    except VorgangNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def _trenne_gueltige(
    dateien: list[Any],
) -> tuple[list[Any], list[AbgelehnteDatei]]:
    """Split an upload into files that can be stored and files that cannot.

    Validating the batch as a whole meant one oversized PDF threw away seven
    good ones and the Architektin had to pick them all again.
    """

    gueltig: list[Any] = []
    abgelehnt: list[AbgelehnteDatei] = []
    for datei in dateien:
        try:
            validate_attachments([*gueltig, datei])
        except (AttachmentTooLargeError, AttachmentError) as exc:
            abgelehnt.append(AbgelehnteDatei(name=datei.name, grund=str(exc)))
            continue
        gueltig.append(datei)
    return gueltig, abgelehnt


def _detail(akte: VorgangAkte, service: VorgangService) -> VorgangDetail:
    vorgang = akte.vorgang
    return VorgangDetail(
        id=vorgang.id,
        aktenzeichen=vorgang.aktenzeichen,
        adresse=vorgang.adresse,
        strasse=vorgang.strasse,
        plz=vorgang.plz,
        ort=vorgang.ort,
        bisherige_nutzung=vorgang.bisherige_nutzung,
        geplante_nutzung=vorgang.geplante_nutzung,
        vermietungstage=vorgang.vermietungstage,
        angelegt_am=vorgang.angelegt_am,
        geaendert_am=vorgang.geaendert_am,
        naechster_schritt=service.naechster_schritt(vorgang.id),
        kennzahlen=service.kennzahlen(akte),
        verfahren=service.verfahren(vorgang.id),
        eingefroren_am=akte.eingefroren_am,
        paket_hash=akte.paket_hash,
    )


# -- Vorgänge -------------------------------------------------------------


@router.get("/vorgaenge", response_model=list[VorgangZeile])
async def liste(
    store: Store = Depends(get_store_dep),
    service: VorgangService = Depends(get_service),
) -> list[VorgangZeile]:
    zeilen = []
    for akte in store.alle():
        zahlen = service.kennzahlen(akte)
        zeilen.append(
            VorgangZeile(
                id=akte.vorgang.id,
                aktenzeichen=akte.vorgang.aktenzeichen,
                adresse=akte.vorgang.adresse,
                bisherige_nutzung=akte.vorgang.bisherige_nutzung,
                geplante_nutzung=akte.vorgang.geplante_nutzung,
                naechster_schritt=service.naechster_schritt(akte.vorgang.id),
                dokumente_zu_pruefen=zahlen["dokumente_zu_pruefen"],
                konflikte_kritisch=zahlen["konflikte_kritisch"],
                anforderungen_fehlend=zahlen["anforderungen_fehlend"],
                geaendert_am=akte.vorgang.geaendert_am,
            )
        )
    # Sorted by what blocks, not by date.
    zeilen.sort(
        key=lambda zeile: (
            -zeile.konflikte_kritisch,
            -zeile.anforderungen_fehlend,
            -zeile.dokumente_zu_pruefen,
        )
    )
    return zeilen


@router.post("/vorgaenge", response_model=VorgangDetail, status_code=status.HTTP_201_CREATED)
async def anlegen(
    anfrage: VorgangAnlegen,
    service: VorgangService = Depends(get_service),
) -> VorgangDetail:
    akte = service.anlegen(
        anfrage.strasse,
        anfrage.plz,
        anfrage.ort,
        anfrage.bisherige_nutzung,
        anfrage.geplante_nutzung,
        anfrage.vermietungstage,
    )
    return _detail(akte, service)


@router.get("/vorgaenge/{vorgang_id}", response_model=VorgangDetail)
async def detail(
    vorgang_id: str,
    store: Store = Depends(get_store_dep),
    service: VorgangService = Depends(get_service),
) -> VorgangDetail:
    return _detail(_akte_oder_404(store, vorgang_id), service)


@router.delete("/vorgaenge/{vorgang_id}", status_code=status.HTTP_204_NO_CONTENT)
async def loeschen(vorgang_id: str, store: Store = Depends(get_store_dep)) -> None:
    _akte_oder_404(store, vorgang_id)
    store.loeschen(vorgang_id)


# -- Dokumente ------------------------------------------------------------


@router.get("/vorgaenge/{vorgang_id}/dokumente", response_model=DokumenteAntwort)
async def dokumente(vorgang_id: str, store: Store = Depends(get_store_dep)) -> DokumenteAntwort:
    akte = _akte_oder_404(store, vorgang_id)
    return DokumenteAntwort(dokumente=list(akte.dokumente.values()))


@router.post("/vorgaenge/{vorgang_id}/dokumente", response_model=DokumenteAntwort)
async def hochladen(
    vorgang_id: str,
    anfrage: DokumenteHochladen,
    store: Store = Depends(get_store_dep),
    service: VorgangService = Depends(get_service),
) -> DokumenteAntwort:
    akte = _akte_oder_404(store, vorgang_id)
    gueltig, abgelehnt = _trenne_gueltige(anfrage.dateien)
    if gueltig:
        await service.dokumente_aufnehmen(vorgang_id, gueltig)
    return DokumenteAntwort(
        dokumente=list(akte.dokumente.values()),
        abgelehnt=abgelehnt,
    )


@router.patch("/vorgaenge/{vorgang_id}/dokumente/{dokument_id}", response_model=DokumenteAntwort)
async def dokument_aktualisieren(
    vorgang_id: str,
    dokument_id: str,
    anfrage: DokumentAktualisieren,
    store: Store = Depends(get_store_dep),
    service: VorgangService = Depends(get_service),
) -> DokumenteAntwort:
    try:
        service.dokument_aktualisieren(
            vorgang_id, dokument_id, anfrage.typ, anfrage.namensvorschlag
        )
    except VorgangNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return DokumenteAntwort(dokumente=list(store.akte(vorgang_id).dokumente.values()))


@router.get(
    "/vorgaenge/{vorgang_id}/dokumente/{dokument_id}/seite/{seite_nr}",
    response_model=SeitenvorschauAntwort,
)
async def seitenvorschau(
    vorgang_id: str,
    dokument_id: str,
    seite_nr: int,
    zitat: str = "",
    store: Store = Depends(get_store_dep),
) -> SeitenvorschauAntwort:
    """Render the page a fact came from, with its quote highlighted.

    Every claim in the interface is one click from the page it stands on.
    """

    akte = _akte_oder_404(store, vorgang_id)
    dokument = akte.dokumente.get(dokument_id)
    datei = akte.dateien.get(dokument_id)
    if dokument is None or datei is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diese Unterlage gehört nicht zu diesem Vorgang.",
        )

    try:
        bild = seite_rendern(datei, seite_nr, zitat)
    except VorschauError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return SeitenvorschauAntwort(
        bild_base64=bild.bild_base64,
        mime_type=bild.mime_type,
        seite=bild.seite,
        seiten_gesamt=bild.seiten_gesamt,
        markiert=bild.markiert,
        dateiname=dokument.dateiname,
    )


# -- Fakten, Konflikte, Anforderungen -------------------------------------


@router.get("/vorgaenge/{vorgang_id}/fakten", response_model=FaktenAntwort)
async def fakten(vorgang_id: str, store: Store = Depends(get_store_dep)) -> FaktenAntwort:
    akte = _akte_oder_404(store, vorgang_id)
    reihenfolge = {kategorie: index for index, kategorie in enumerate(KATEGORIEN)}
    sortiert = sorted(
        akte.fakten.values(),
        key=lambda fakt: (reihenfolge.get(fakt.kategorie, 99), fakt.bezeichnung),
    )
    return FaktenAntwort(fakten=sortiert, kategorien=list(KATEGORIEN))


@router.post("/vorgaenge/{vorgang_id}/fakten/{schluessel}/bestaetigen", response_model=Fakt)
async def fakt_bestaetigen(
    vorgang_id: str,
    schluessel: str,
    anfrage: FaktBestaetigen,
    service: VorgangService = Depends(get_service),
) -> Fakt:
    try:
        return service.fakt_bestaetigen(vorgang_id, schluessel, anfrage.wert)
    except VorgangNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/vorgaenge/{vorgang_id}/konflikte", response_model=KonflikteAntwort)
async def konflikte(vorgang_id: str, store: Store = Depends(get_store_dep)) -> KonflikteAntwort:
    akte = _akte_oder_404(store, vorgang_id)
    reihenfolge = {"kritisch": 0, "warnung": 1, "hinweis": 2}
    sortiert = sorted(
        akte.konflikte.values(),
        key=lambda konflikt: (konflikt.geklaert, reihenfolge.get(konflikt.schweregrad.value, 9)),
    )
    return KonflikteAntwort(konflikte=sortiert)


@router.post("/vorgaenge/{vorgang_id}/konflikte/{konflikt_id}/loesen", response_model=KonflikteAntwort)
async def konflikt_loesen(
    vorgang_id: str,
    konflikt_id: str,
    anfrage: KonfliktLoesen,
    store: Store = Depends(get_store_dep),
    service: VorgangService = Depends(get_service),
) -> KonflikteAntwort:
    try:
        service.konflikt_loesen(vorgang_id, konflikt_id, anfrage.wert, anfrage.notiz)
    except VorgangNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return KonflikteAntwort(konflikte=list(store.akte(vorgang_id).konflikte.values()))


@router.get("/vorgaenge/{vorgang_id}/anforderungen", response_model=AnforderungenAntwort)
async def anforderungen(vorgang_id: str, store: Store = Depends(get_store_dep)) -> AnforderungenAntwort:
    akte = _akte_oder_404(store, vorgang_id)
    return AnforderungenAntwort(anforderungen=list(akte.anforderungen.values()))


@router.get("/vorgaenge/{vorgang_id}/pruefung", response_model=BefundeAntwort)
async def pruefung(
    vorgang_id: str,
    store: Store = Depends(get_store_dep),
    service: VorgangService = Depends(get_service),
) -> BefundeAntwort:
    _akte_oder_404(store, vorgang_id)
    befunde = service.befunde(vorgang_id)
    return BefundeAntwort(befunde=befunde, freigabe_moeglich=freigabe_moeglich(befunde))


@router.post("/vorgaenge/{vorgang_id}/paket/einfrieren", response_model=PaketAntwort)
async def paket_einfrieren(
    vorgang_id: str,
    store: Store = Depends(get_store_dep),
    service: VorgangService = Depends(get_service),
) -> PaketAntwort:
    _akte_oder_404(store, vorgang_id)
    eingefroren, paket_hash = service.paket_einfrieren(vorgang_id)
    return PaketAntwort(
        eingefroren=eingefroren,
        paket_hash=paket_hash,
        begruendung=""
        if eingefroren
        else "Es sind noch kritische Befunde offen. Das Paket kann nicht eingefroren werden.",
    )


@router.get("/vorgaenge/{vorgang_id}/protokoll", response_model=AuditAntwort)
async def protokoll(vorgang_id: str, store: Store = Depends(get_store_dep)) -> AuditAntwort:
    akte = _akte_oder_404(store, vorgang_id)
    return AuditAntwort(eintraege=list(reversed(akte.audit)))


# -- Upload-Links ---------------------------------------------------------


@router.get("/vorgaenge/{vorgang_id}/upload-links", response_model=list[UploadLinkAntwort])
async def upload_links(vorgang_id: str, store: Store = Depends(get_store_dep)) -> list[UploadLinkAntwort]:
    _akte_oder_404(store, vorgang_id)
    return [
        UploadLinkAntwort(
            token=link.token,
            empfaenger=link.empfaenger,
            angefordert=link.angefordert,
            gueltig_bis=link.gueltig_bis,
            widerrufen=link.widerrufen,
        )
        for link in store.links_fuer(vorgang_id)
    ]


@router.post("/vorgaenge/{vorgang_id}/upload-links", response_model=UploadLinkAntwort)
async def upload_link_anlegen(
    vorgang_id: str,
    anfrage: UploadLinkAnlegen,
    store: Store = Depends(get_store_dep),
) -> UploadLinkAntwort:
    akte = _akte_oder_404(store, vorgang_id)
    link = store.link_erzeugen(
        vorgang_id, anfrage.empfaenger, anfrage.angefordert, anfrage.gueltig_stunden
    )
    akte.protokoll("Architektin", "Upload-Link erzeugt", anfrage.empfaenger)
    return UploadLinkAntwort(
        token=link.token,
        empfaenger=link.empfaenger,
        angefordert=link.angefordert,
        gueltig_bis=link.gueltig_bis,
        widerrufen=link.widerrufen,
    )


@router.delete("/upload-links/{token}", status_code=status.HTTP_204_NO_CONTENT)
async def upload_link_widerrufen(token: str, store: Store = Depends(get_store_dep)) -> None:
    if not store.link_widerrufen(token):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dieser Link existiert nicht."
        )


@router.get("/upload/{token}", response_model=UploadSeite)
async def upload_seite(token: str, store: Store = Depends(get_store_dep)) -> UploadSeite:
    """What the external contributor sees. Deliberately reveals nothing else."""

    try:
        link = store.link(token)
    except UploadLinkInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    try:
        akte = store.akte(link.vorgang_id)
    except VorgangNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dieser Link ist nicht mehr gültig."
        ) from exc
    return UploadSeite(
        adresse=akte.vorgang.adresse,
        angefordert=link.angefordert,
        gueltig_bis=link.gueltig_bis,
    )


@router.post("/upload/{token}", response_model=DokumenteAntwort)
async def upload_extern(
    token: str,
    anfrage: DokumenteHochladen,
    store: Store = Depends(get_store_dep),
    service: VorgangService = Depends(get_service),
) -> DokumenteAntwort:
    try:
        link = store.link(token)
    except UploadLinkInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    try:
        validate_attachments(anfrage.dateien)
    except AttachmentTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=str(exc)) from exc
    except AttachmentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    neu = await service.dokumente_aufnehmen(link.vorgang_id, anfrage.dateien, quelle="extern")
    return DokumenteAntwort(dokumente=neu)


# -- Assistent ------------------------------------------------------------


@router.post("/vorgaenge/{vorgang_id}/assistent", response_model=AssistentAntwort)
async def assistent(
    vorgang_id: str,
    anfrage: AssistentAnfrage,
    store: Store = Depends(get_store_dep),
    assistent_graph: Any = Depends(get_assistent),
) -> AssistentAntwort:
    """Talk to the assistant about one Vorgang.

    The thread id is the Vorgang id, so the conversation and the case file stay
    together for the life of the process.
    """

    _akte_oder_404(store, vorgang_id)
    try:
        ergebnis = await assistent_graph.ainvoke(
            {"messages": [HumanMessage(content=anfrage.nachricht)], "vorgang_id": vorgang_id},
            config={"configurable": {"thread_id": vorgang_id}},
        )
    except Exception as exc:  # noqa: BLE001 — surfaced to the UI as a retryable error
        logger.exception("Assistent konnte nicht antworten")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Der Assistent konnte nicht antworten. Bitte erneut versuchen.",
        ) from exc

    nachrichten = ergebnis.get("messages", [])
    if not nachrichten:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Der Assistent hat nicht geantwortet.",
        )

    gerendert: list[AssistentNachricht] = []
    for nachricht in _aktuelle_runde(nachrichten):
        if isinstance(nachricht, ToolMessage):
            gerendert.append(
                AssistentNachricht(
                    rolle="werkzeug",
                    inhalt=str(getattr(nachricht, "content", "")),
                    werkzeug=getattr(nachricht, "name", None),
                )
            )
    antwort = _text(nachrichten[-1])
    if not antwort:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Der Assistent hat keine Antwort formuliert. Bitte erneut versuchen.",
        )
    gerendert.append(AssistentNachricht(rolle="assistent", inhalt=antwort))
    return AssistentAntwort(antwort=antwort, nachrichten=gerendert)


def _aktuelle_runde(nachrichten: list[Any]) -> list[Any]:
    for index in range(len(nachrichten) - 1, -1, -1):
        if isinstance(nachrichten[index], HumanMessage):
            return nachrichten[index + 1 :]
    return nachrichten


def _text(nachricht: Any) -> str:
    text = getattr(nachricht, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()
    inhalt = getattr(nachricht, "content", nachricht)
    if isinstance(inhalt, str):
        return inhalt.strip()
    if isinstance(inhalt, list):
        teile = [
            block.get("text", "")
            for block in inhalt
            if isinstance(block, dict) and block.get("type") in {"text", "output_text"}
        ]
        if teile:
            return "\n".join(teile).strip()
    return ""
