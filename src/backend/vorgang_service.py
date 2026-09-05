"""Application service for Vorgänge: ingestion, facts, conflicts, review."""

import asyncio
import base64
import hashlib
import logging
from datetime import date, datetime, timezone
from typing import Any

from src.backend.auswertung import (
    AuswertungError,
    werte_dokument_aus,
    uebernimm_befund,
)
from src.backend.domain import (
    Befund,
    Dokument,
    DokumentStatus,
    Fakt,
    FaktStatus,
    Herkunft,
    Konflikt,
    KonfliktWert,
    Qualitaet,
    Verfahrensstrang,
    Vorgang,
)
from src.backend.katalog import FAKTEN, verfahrensstraenge
from src.backend.regeln import (
    bewerte_anforderungen,
    einreichungspruefung,
    finde_konflikte,
    freigabe_moeglich,
    naechster_schritt,
)
from src.backend.schemas import Attachment
from src.backend.store import Store, VorgangAkte

logger = logging.getLogger(__name__)

AKTEUR = "Architektin"


class VorgangService:
    """Coordinates document ingestion and the deterministic evaluation passes."""

    def __init__(self, store: Store, model: Any) -> None:
        self._store = store
        self._model = model

    # -- Vorgänge ---------------------------------------------------------

    def anlegen(
        self,
        strasse: str,
        plz: str,
        ort: str,
        bisherige_nutzung: str,
        geplante_nutzung: str,
        vermietungstage: int,
    ) -> VorgangAkte:
        vorgang = Vorgang(
            aktenzeichen=self._store.naechstes_aktenzeichen(),
            strasse=strasse,
            plz=plz,
            ort=ort,
            bisherige_nutzung=bisherige_nutzung,
            geplante_nutzung=geplante_nutzung,
            vermietungstage=vermietungstage,
        )
        akte = self._store.anlegen(vorgang)
        self._grundfakten_setzen(akte)
        self._neu_bewerten(akte)
        return akte

    def _grundfakten_setzen(self, akte: VorgangAkte) -> None:
        """Seed the fact sheet from what the Architektin entered herself.

        Facts she typed count as confirmed; everything else starts open.
        """

        vorgang = akte.vorgang
        eingaben = {
            "strasse_hausnummer": vorgang.strasse,
            "plz": vorgang.plz,
            "ort": vorgang.ort,
            "bisherige_nutzung": vorgang.bisherige_nutzung,
            "geplante_nutzung": vorgang.geplante_nutzung,
            "vermietungstage": str(vorgang.vermietungstage),
        }
        for definition in FAKTEN:
            wert = eingaben.get(definition.schluessel)
            fakt = Fakt(
                schluessel=definition.schluessel,
                bezeichnung=definition.bezeichnung,
                kategorie=definition.kategorie,
                einheit=definition.einheit,
                pflicht=definition.pflicht,
                notiz=definition.hinweis,
            )
            if wert:
                fakt.wert = wert
                fakt.status = FaktStatus.BESTAETIGT
                fakt.bestaetigt_von = AKTEUR
                fakt.bestaetigt_am = datetime.now(timezone.utc)
            akte.fakten[definition.schluessel] = fakt

    # -- Dokumenteingang --------------------------------------------------

    async def dokument_aufnehmen(
        self,
        vorgang_id: str,
        datei: Attachment,
        quelle: str = "buero",
    ) -> Dokument:
        """Store one file and let the model read it.

        The file itself never enters the assistant's conversation context; only
        the extracted facts and the filename travel further.
        """

        akte = self._store.akte(vorgang_id)
        rohdaten = base64.b64decode(datei.content_base64, validate=False)
        dokument = Dokument(
            dateiname=datei.name,
            mime_type=datei.mime_type,
            groesse_bytes=len(rohdaten),
            quelle="extern" if quelle == "extern" else "buero",
            status=DokumentStatus.GEPRUEFT,
        )
        self._store.dokument_hinzufuegen(vorgang_id, dokument, datei)
        akte.protokoll(AKTEUR if quelle == "buero" else "Externe Person", "Dokument empfangen", datei.name)

        try:
            befund = await werte_dokument_aus(self._model, dokument, datei, date.today())
        except AuswertungError as exc:
            dokument.status = DokumentStatus.FEHLER
            dokument.fehler = str(exc)
            dokument.qualitaet = Qualitaet.UNBRAUCHBAR
            dokument.qualitaet_begruendung = str(exc)
            akte.protokoll("System", "Auswertung fehlgeschlagen", f"{datei.name}: {exc}")
            self._neu_bewerten(akte)
            return dokument
        except Exception as exc:  # noqa: BLE001 — one bad file must not kill the batch
            logger.exception("Auswertung von %s fehlgeschlagen", datei.name)
            dokument.status = DokumentStatus.FEHLER
            dokument.fehler = "Die Auswertung konnte nicht abgeschlossen werden."
            # Ohne diese Markierung taucht die Datei in keiner Kennzahl und in
            # keinem Befund auf — die Architektin erführe nie, dass sie fehlt.
            dokument.qualitaet = Qualitaet.UNBRAUCHBAR
            dokument.qualitaet_begruendung = "Die Auswertung ist fehlgeschlagen."
            akte.protokoll("System", "Auswertung fehlgeschlagen", f"{datei.name}: {exc}")
            self._neu_bewerten(akte)
            return dokument

        uebernimm_befund(dokument, befund)
        self._fakten_uebernehmen(akte, befund.fakten)
        akte.protokoll("System", "Dokument ausgewertet", f"{datei.name} → {dokument.typ}")
        self._neu_bewerten(akte)
        return dokument

    async def dokumente_aufnehmen(
        self,
        vorgang_id: str,
        dateien: list[Attachment],
        quelle: str = "buero",
    ) -> list[Dokument]:
        """Read several documents at once. One failure never blocks the rest."""

        ergebnisse = await asyncio.gather(
            *(self.dokument_aufnehmen(vorgang_id, datei, quelle) for datei in dateien),
            return_exceptions=True,
        )
        dokumente: list[Dokument] = []
        for datei, ergebnis in zip(dateien, ergebnisse, strict=True):
            if isinstance(ergebnis, Dokument):
                dokumente.append(ergebnis)
            else:
                logger.error("Dokument %s konnte nicht aufgenommen werden: %s", datei.name, ergebnis)
        return dokumente

    def _fakten_uebernehmen(
        self,
        akte: VorgangAkte,
        gelesene: list[tuple[str, str, Herkunft, float | None]],
    ) -> None:
        """Merge extracted values into the fact sheet as AI drafts.

        A fact a person already confirmed is never overwritten; the new reading
        is recorded as provenance so the conflict engine can still see it.
        """

        for schluessel, wert, herkunft, konfidenz in gelesene:
            fakt = akte.fakten.get(schluessel)
            if fakt is None:
                continue
            fakt.herkunft.append(herkunft)
            if fakt.status is FaktStatus.BESTAETIGT:
                continue
            if fakt.wert is None:
                fakt.wert = wert
                fakt.status = FaktStatus.KI_ENTWURF
                fakt.konfidenz = konfidenz

    # -- Ableitungen ------------------------------------------------------

    def _neu_bewerten(self, akte: VorgangAkte) -> None:
        """Recompute conflicts and requirements from current state."""

        aussagen = self._konfliktbasis(akte)
        bestehende = {konflikt.schluessel: konflikt for konflikt in akte.konflikte.values()}
        akte.konflikte.clear()
        for konflikt in finde_konflikte(aussagen):
            alt = bestehende.get(konflikt.schluessel)
            if alt is not None:
                # Die ID bleibt stabil, sonst laufen Klicks und Assistenten-
                # Aufrufe nach dem nächsten Upload ins Leere.
                konflikt.id = alt.id
                if alt.geklaert:
                    konflikt.geklaert = True
                    konflikt.gewaehlter_wert = alt.gewaehlter_wert
                    konflikt.entschieden_von = alt.entschieden_von
                    konflikt.entschieden_am = alt.entschieden_am
            akte.konflikte[konflikt.schluessel] = konflikt

        # Erst zurücksetzen, dann neu setzen — sonst bleibt ein Fakt für immer
        # im Konfliktstatus, obwohl die Konfliktliste längst leer ist.
        for fakt in akte.fakten.values():
            if fakt.status is FaktStatus.KONFLIKT:
                fakt.status = FaktStatus.KI_ENTWURF if fakt.wert else FaktStatus.OFFEN

        for konflikt in akte.konflikte.values():
            fakt = akte.fakten.get(konflikt.schluessel)
            if fakt is not None and not konflikt.geklaert and fakt.status is not FaktStatus.BESTAETIGT:
                fakt.status = FaktStatus.KONFLIKT

        anforderungen = bewerte_anforderungen(list(akte.dokumente.values()))
        akte.anforderungen = {anforderung.bezeichnung: anforderung for anforderung in anforderungen}
        akte.vorgang.geaendert_am = datetime.now(timezone.utc)

    def _konfliktbasis(self, akte: VorgangAkte) -> dict[str, list[KonfliktWert]]:
        """Build the per-key value lists the conflict engine compares.

        Each document that asserted a value contributes the *value* it asserted,
        never its quote. Comparing quotes would report ``Gemarkung: Holzlar``
        against ``Gemarkung Holzlar`` as a contradiction — the false-alarm
        machine that gets a tool switched off in week two.

        A value the Architektin entered herself also takes part, so a document
        that disagrees with her intake is surfaced rather than silently adopted.
        """

        aussagen: dict[str, list[KonfliktWert]] = {}
        for fakt in akte.fakten.values():
            for herkunft in fakt.herkunft:
                wert = herkunft.wert.strip()
                if not wert:
                    continue
                aussagen.setdefault(fakt.schluessel, []).append(
                    KonfliktWert(
                        wert=wert,
                        dokument_id=herkunft.dokument_id,
                        dateiname=herkunft.dateiname,
                        seite=herkunft.seite,
                        zitat=herkunft.zitat,
                    )
                )

            # Was die Architektin selbst eingetragen hat, zählt als eigene Aussage.
            if fakt.bestaetigt_von and fakt.wert and not fakt.herkunft:
                continue
            if fakt.bestaetigt_von and fakt.wert:
                aussagen.setdefault(fakt.schluessel, []).append(
                    KonfliktWert(
                        wert=fakt.wert.strip(),
                        dokument_id="eingabe",
                        dateiname="Ihre Eingabe bei der Vorgangsanlage",
                        seite=None,
                    )
                )
        return {schluessel: werte for schluessel, werte in aussagen.items() if werte}

    # -- Entscheidungen ---------------------------------------------------

    def fakt_bestaetigen(
        self,
        vorgang_id: str,
        schluessel: str,
        wert: str | None = None,
        akteur: str = AKTEUR,
    ) -> Fakt:
        """Confirm a fact.

        ``akteur`` records who actually decided. The assistant passes its own
        label, so the audit record never claims the Architektin confirmed
        something the model decided on her behalf.
        """

        akte = self._store.akte(vorgang_id)
        fakt = akte.fakten.get(schluessel)
        if fakt is None:
            raise KeyError(f"Fakt {schluessel!r} existiert nicht.")
        if wert is not None:
            fakt.wert = wert
        if not fakt.wert:
            raise ValueError("Ein Fakt ohne Wert kann nicht bestätigt werden.")
        fakt.status = FaktStatus.BESTAETIGT
        fakt.bestaetigt_von = akteur
        fakt.bestaetigt_am = datetime.now(timezone.utc)
        akte.protokoll(akteur, "Fakt bestätigt", f"{fakt.bezeichnung} = {fakt.wert}")
        self._neu_bewerten(akte)
        return fakt

    def konflikt_loesen(
        self,
        vorgang_id: str,
        konflikt_id: str,
        wert: str,
        notiz: str = "",
        akteur: str = AKTEUR,
        nur_angebotene_werte: bool = False,
    ) -> Konflikt:
        """Close a conflict with the value the Architektin chose.

        ``nur_angebotene_werte`` restricts the choice to the values the
        documents actually assert. The assistant sets it, so the model can
        never invent a third value and have it recorded as a human decision.
        """

        akte = self._store.akte(vorgang_id)
        konflikt = next(
            (eintrag for eintrag in akte.konflikte.values() if eintrag.id == konflikt_id),
            None,
        )
        if konflikt is None:
            raise KeyError(f"Konflikt {konflikt_id!r} existiert nicht.")
        if nur_angebotene_werte:
            angeboten = {eintrag.wert for eintrag in konflikt.werte}
            if wert not in angeboten:
                raise ValueError(
                    "Nur ein Wert aus den Unterlagen kann übernommen werden. "
                    f"Angeboten: {', '.join(sorted(angeboten))}."
                )
        konflikt.geklaert = True
        konflikt.gewaehlter_wert = wert
        konflikt.entschieden_von = akteur
        konflikt.entschieden_am = datetime.now(timezone.utc)

        fakt = akte.fakten.get(konflikt.schluessel)
        if fakt is not None:
            fakt.wert = wert
            fakt.status = FaktStatus.BESTAETIGT
            fakt.bestaetigt_von = akteur
            fakt.bestaetigt_am = konflikt.entschieden_am
        akte.protokoll(
            akteur,
            "Widerspruch gelöst",
            f"{konflikt.bezeichnung} → {wert}" + (f" ({notiz})" if notiz else ""),
        )
        self._neu_bewerten(akte)
        return konflikt

    def dokument_aktualisieren(
        self,
        vorgang_id: str,
        dokument_id: str,
        typ: str | None = None,
        namensvorschlag: str | None = None,
    ) -> Dokument:
        akte = self._store.akte(vorgang_id)
        dokument = akte.dokumente.get(dokument_id)
        if dokument is None:
            raise KeyError(f"Dokument {dokument_id!r} existiert nicht.")
        if typ is not None:
            dokument.typ = typ
            dokument.typ_unklar = False
            akte.protokoll(AKTEUR, "Dokumenttyp gesetzt", f"{dokument.dateiname} → {typ}")
        if namensvorschlag is not None:
            dokument.namensvorschlag = namensvorschlag
        self._neu_bewerten(akte)
        return dokument

    # -- Auswertungen -----------------------------------------------------

    def befunde(self, vorgang_id: str) -> list[Befund]:
        akte = self._store.akte(vorgang_id)
        befunde = einreichungspruefung(
            list(akte.fakten.values()),
            list(akte.konflikte.values()),
            list(akte.anforderungen.values()),
            list(akte.dokumente.values()),
            akte.vorgang.vermietungstage,
        )
        akte.befunde = befunde
        return befunde

    def verfahren(self, vorgang_id: str) -> list[Verfahrensstrang]:
        akte = self._store.akte(vorgang_id)
        return verfahrensstraenge(akte.vorgang.vermietungstage)

    def naechster_schritt(self, vorgang_id: str) -> str:
        akte = self._store.akte(vorgang_id)
        return naechster_schritt(
            list(akte.dokumente.values()),
            list(akte.fakten.values()),
            list(akte.konflikte.values()),
            list(akte.anforderungen.values()),
        )

    def paket_einfrieren(self, vorgang_id: str) -> tuple[bool, str | None]:
        """Freeze the package if nothing critical is open.

        Returns the outcome and the package hash, so the Architektin has an
        immutable, audited state to put in her file for liability reasons.
        """

        akte = self._store.akte(vorgang_id)
        befunde = self.befunde(vorgang_id)
        if not freigabe_moeglich(befunde):
            return False, None

        manifest = "\n".join(
            sorted(
                f"{dokument.namensvorschlag or dokument.dateiname}:{dokument.groesse_bytes}"
                for dokument in akte.dokumente.values()
            )
        )
        fakten = "\n".join(
            f"{fakt.schluessel}={fakt.wert}" for fakt in sorted(akte.fakten.values(), key=lambda f: f.schluessel)
        )
        paket_hash = hashlib.sha256(f"{manifest}\n{fakten}".encode()).hexdigest()
        akte.paket_hash = paket_hash
        akte.eingefroren_am = datetime.now(timezone.utc)
        akte.protokoll(AKTEUR, "Paket eingefroren", paket_hash[:16])
        return True, paket_hash

    def kennzahlen(self, akte: VorgangAkte) -> dict[str, int]:
        fakten = list(akte.fakten.values())
        konflikte = [konflikt for konflikt in akte.konflikte.values() if not konflikt.geklaert]
        anforderungen = list(akte.anforderungen.values())
        return {
            "dokumente": len(akte.dokumente),
            "dokumente_zu_pruefen": sum(1 for d in akte.dokumente.values() if d.typ_unklar),
            "dokumente_unbrauchbar": sum(
                1 for d in akte.dokumente.values() if d.qualitaet is Qualitaet.UNBRAUCHBAR
            ),
            "fakten_gesamt": len(fakten),
            "fakten_bestaetigt": sum(1 for f in fakten if f.status is FaktStatus.BESTAETIGT),
            "konflikte_kritisch": sum(1 for k in konflikte if k.schweregrad.value == "kritisch"),
            "konflikte_warnung": sum(1 for k in konflikte if k.schweregrad.value == "warnung"),
            "konflikte_hinweis": sum(1 for k in konflikte if k.schweregrad.value == "hinweis"),
            "anforderungen_gesamt": len(anforderungen),
            "anforderungen_belegt": sum(1 for a in anforderungen if a.status.value == "belegt"),
            "anforderungen_fehlend": sum(
                1 for a in anforderungen if a.pflicht and a.status.value == "offen"
            ),
        }
