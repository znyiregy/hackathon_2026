"""In-memory storage for Vorgänge and everything attached to them.

This is a prototype store: state lives in the process and is lost on restart.
It is deliberately the only module that knows how data is persisted, so a real
database can replace it without touching the rules or the API layer.
"""

import secrets
import threading
from datetime import datetime, timedelta, timezone

from src.backend.domain import (
    Anforderung,
    AuditEintrag,
    Befund,
    Dokument,
    Fakt,
    Konflikt,
    UploadLink,
    Vorgang,
)
from src.backend.schemas import Attachment


class VorgangNotFoundError(KeyError):
    """Raised when a Vorgang id does not exist."""


class DokumentNotFoundError(KeyError):
    """Raised when a document id does not exist in a Vorgang."""


class UploadLinkInvalidError(KeyError):
    """Raised when an upload token is unknown, revoked or expired."""


class VorgangAkte:
    """Everything belonging to one Vorgang, including raw file bytes.

    File content stays here and is never placed in the parent agent's context;
    only filenames and extracted facts travel further.
    """

    def __init__(self, vorgang: Vorgang) -> None:
        self.vorgang = vorgang
        self.dokumente: dict[str, Dokument] = {}
        self.dateien: dict[str, Attachment] = {}
        self.fakten: dict[str, Fakt] = {}
        self.konflikte: dict[str, Konflikt] = {}
        self.anforderungen: dict[str, Anforderung] = {}
        self.befunde: list[Befund] = []
        self.audit: list[AuditEintrag] = []
        self.eingefroren_am: datetime | None = None
        self.paket_hash: str | None = None

    def protokoll(self, akteur: str, aktion: str, detail: str = "") -> None:
        self.audit.append(AuditEintrag(akteur=akteur, aktion=aktion, detail=detail))


class Store:
    """Process-wide storage.

    The lock guards the store's own dictionaries. It does **not** guard a
    :class:`VorgangAkte` once it has been handed out — callers mutate those
    directly. That is safe today because every route is ``async def`` and the
    mutating passes contain no ``await``, so they run to completion within one
    event-loop step. Introducing a threadpool route or an ``await`` inside
    those passes would make it a real race.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._akten: dict[str, VorgangAkte] = {}
        self._links: dict[str, UploadLink] = {}
        self._laufende_nummer = 0

    # -- Vorgänge ---------------------------------------------------------

    def naechstes_aktenzeichen(self) -> str:
        with self._lock:
            self._laufende_nummer += 1
            return f"DD-2026-{self._laufende_nummer:03d}"

    def anlegen(self, vorgang: Vorgang) -> VorgangAkte:
        with self._lock:
            akte = VorgangAkte(vorgang)
            akte.protokoll("System", "Vorgang angelegt", vorgang.adresse)
            self._akten[vorgang.id] = akte
            return akte

    def akte(self, vorgang_id: str) -> VorgangAkte:
        with self._lock:
            try:
                return self._akten[vorgang_id]
            except KeyError as exc:
                raise VorgangNotFoundError(f"Vorgang {vorgang_id!r} existiert nicht.") from exc

    def alle(self) -> list[VorgangAkte]:
        with self._lock:
            return sorted(self._akten.values(), key=lambda akte: akte.vorgang.angelegt_am, reverse=True)

    def loeschen(self, vorgang_id: str) -> None:
        with self._lock:
            self._akten.pop(vorgang_id, None)
            for token, link in list(self._links.items()):
                if link.vorgang_id == vorgang_id:
                    self._links.pop(token, None)

    # -- Dokumente --------------------------------------------------------

    def dokument_hinzufuegen(
        self,
        vorgang_id: str,
        dokument: Dokument,
        datei: Attachment,
    ) -> Dokument:
        akte = self.akte(vorgang_id)
        with self._lock:
            akte.dokumente[dokument.id] = dokument
            akte.dateien[dokument.id] = datei
            akte.vorgang.geaendert_am = datetime.now(timezone.utc)
            return dokument

    def datei(self, vorgang_id: str, dokument_id: str) -> Attachment:
        akte = self.akte(vorgang_id)
        with self._lock:
            try:
                return akte.dateien[dokument_id]
            except KeyError as exc:
                raise DokumentNotFoundError(f"Dokument {dokument_id!r} existiert nicht.") from exc

    # -- Upload-Links -----------------------------------------------------

    def link_erzeugen(
        self,
        vorgang_id: str,
        empfaenger: str,
        angefordert: list[str],
        gueltig_stunden: int = 72,
    ) -> UploadLink:
        self.akte(vorgang_id)
        with self._lock:
            link = UploadLink(
                token=secrets.token_urlsafe(24),
                vorgang_id=vorgang_id,
                empfaenger=empfaenger,
                angefordert=angefordert,
                gueltig_bis=datetime.now(timezone.utc) + timedelta(hours=gueltig_stunden),
            )
            self._links[link.token] = link
            return link

    def link(self, token: str) -> UploadLink:
        with self._lock:
            link = self._links.get(token)
        if link is None or not link.ist_gueltig():
            raise UploadLinkInvalidError("Dieser Link ist nicht mehr gültig.")
        return link

    def links_fuer(self, vorgang_id: str) -> list[UploadLink]:
        with self._lock:
            return [link for link in self._links.values() if link.vorgang_id == vorgang_id]

    def link_widerrufen(self, token: str) -> bool:
        """Revoke a link. Returns False if the token was never issued."""

        with self._lock:
            link = self._links.get(token)
            if link is None:
                return False
            link.widerrufen = True
            return True


_store = Store()


def get_store() -> Store:
    """Return the process-wide store."""

    return _store
