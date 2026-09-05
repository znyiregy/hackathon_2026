"""End-to-end run through the whole chain, without calling OpenAI.

The model is replaced by a stand-in that returns a fixed reading, so this test
exercises exactly what the product does with a document — ingest, extract,
compare, evaluate, review, freeze — and nothing that depends on the network.
"""

import base64
import json
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from src.backend import api_vorgaenge
from src.backend.api import app
from src.backend.assistent import baue_assistent
from src.backend.store import Store
from src.backend.vorgang_service import VorgangService


def _bild_base64() -> str:
    """A tiny valid PNG, so attachment validation has something real to check."""

    puffer = BytesIO()
    Image.new("RGB", (60, 40), "white").save(puffer, format="PNG")
    return base64.b64encode(puffer.getvalue()).decode()


class ModellAttrappe:
    """Stands in for the chat model and returns prepared readings."""

    def __init__(self, antworten: list[dict]) -> None:
        self._antworten = list(antworten)
        self.aufrufe = 0

    async def ainvoke(self, nachrichten, **_kwargs):
        self.aufrufe += 1
        daten = self._antworten.pop(0) if self._antworten else {}

        class Antwort:
            text = json.dumps(daten, ensure_ascii=False)

        return Antwort()


def _lesung(dateiname: str, typ: str, fakten: list[dict]) -> dict:
    return {
        "typ": typ,
        "typ_unklar": False,
        "qualitaet": "gut",
        "qualitaet_begruendung": "Gut lesbar.",
        "dokument_datum": "2024-03-12",
        "zusammenfassung": f"Testlesung für {dateiname}.",
        "namensvorschlag": f"2024-03-12_{typ}_Test_V01.png",
        "fakten": fakten,
    }


@pytest.fixture
def klient():
    """A client wired to a fresh store and a scripted model."""

    store = Store()
    modell = ModellAttrappe(
        [
            # Liegenschaftskarte: Flurstück 143/2
            _lesung(
                "liegenschaftskarte.png",
                "flurkarte",
                [
                    {
                        "schluessel": "flurstueck",
                        "wert": "143/2",
                        "seite": 1,
                        "zitat": "Flurstück: 143/2",
                        "konfidenz": 0.95,
                    },
                    {
                        "schluessel": "gemarkung",
                        "wert": "Dottendorf",
                        "seite": 1,
                        "zitat": "Gemarkung: Dottendorf",
                        "konfidenz": 0.95,
                    },
                ],
            ),
            # Bauantragsentwurf: abweichendes Flurstück, gleiche Gemarkung
            _lesung(
                "bauantrag.png",
                "antragsformular",
                [
                    {
                        "schluessel": "flurstueck",
                        "wert": "143",
                        "seite": 1,
                        "zitat": "Parzelle 143",
                        "konfidenz": 0.8,
                    },
                    {
                        "schluessel": "gemarkung",
                        "wert": "Dottendorf",
                        "seite": 1,
                        "zitat": "Gemarkung Dottendorf",
                        "konfidenz": 0.9,
                    },
                ],
            ),
        ]
    )
    service = VorgangService(store, modell)
    assistent = baue_assistent(store, service, modell)

    app.dependency_overrides[api_vorgaenge.get_store_dep] = lambda: store
    app.dependency_overrides[api_vorgaenge.get_service] = lambda: service
    app.dependency_overrides[api_vorgaenge.get_assistent] = lambda: assistent
    with TestClient(app) as klient:
        yield klient
    app.dependency_overrides.clear()


def _hochladen(klient, vid: str, name: str):
    return klient.post(
        f"/api/vorgaenge/{vid}/dokumente",
        json={
            "dateien": [
                {"name": name, "mime_type": "image/png", "content_base64": _bild_base64()}
            ]
        },
    )


def test_vollstaendiger_durchlauf(klient):
    """Vorgang anlegen → zwei Unterlagen → Widerspruch → lösen → Prüfung."""

    # 1. Vorgang anlegen. 120 Vermietungstage lösen den Zweckentfremdungszweig aus.
    antwort = klient.post(
        "/api/vorgaenge",
        json={
            "strasse": "Kirschblütenweg 7",
            "plz": "53129",
            "ort": "Bonn",
            "bisherige_nutzung": "Wohnnutzung",
            "geplante_nutzung": "Ferienhaus",
            "vermietungstage": 120,
        },
    )
    assert antwort.status_code == 201
    vorgang = antwort.json()
    vid = vorgang["id"]
    assert vorgang["adresse"] == "Kirschblütenweg 7, 53129 Bonn"

    zweckentfremdung = next(
        strang for strang in vorgang["verfahren"] if strang["schluessel"] == "zweckentfremdung"
    )
    assert zweckentfremdung["kritisch"] is True

    # Ohne Unterlagen rät das System zum Upload.
    assert "hoch" in vorgang["naechster_schritt"].lower()

    # 2. Erste Unterlage: keine Vergleichspartner, also kein Widerspruch.
    assert _hochladen(klient, vid, "liegenschaftskarte.png").status_code == 200
    assert klient.get(f"/api/vorgaenge/{vid}/konflikte").json()["konflikte"] == []

    # 3. Zweite Unterlage widerspricht beim Flurstück, nicht bei der Gemarkung.
    assert _hochladen(klient, vid, "bauantrag.png").status_code == 200
    konflikte = klient.get(f"/api/vorgaenge/{vid}/konflikte").json()["konflikte"]
    schluessel = {konflikt["schluessel"] for konflikt in konflikte}
    assert "flurstueck" in schluessel
    assert "gemarkung" not in schluessel, "Gleiche Werte dürfen kein Widerspruch sein."

    flurstueck = next(k for k in konflikte if k["schluessel"] == "flurstueck")
    assert flurstueck["schweregrad"] == "kritisch"
    assert {wert["wert"] for wert in flurstueck["werte"]} == {"143/2", "143"}

    # 4. Der Widerspruch blockiert den nächsten Schritt.
    detail = klient.get(f"/api/vorgaenge/{vid}").json()
    assert detail["kennzahlen"]["konflikte_kritisch"] == 1
    assert "Widersprüche" in detail["naechster_schritt"]

    # 5. Solange etwas Kritisches offen ist, lässt sich nichts einfrieren.
    pruefung = klient.get(f"/api/vorgaenge/{vid}/pruefung").json()
    assert pruefung["freigabe_moeglich"] is False
    eingefroren = klient.post(f"/api/vorgaenge/{vid}/paket/einfrieren").json()
    assert eingefroren["eingefroren"] is False
    assert eingefroren["paket_hash"] is None

    # 6. Die Architektin entscheidet, welcher Wert gilt.
    geloest = klient.post(
        f"/api/vorgaenge/{vid}/konflikte/{flurstueck['id']}/loesen",
        json={"wert": "143/2", "notiz": "Liegenschaftskarte ist maßgeblich."},
    )
    assert geloest.status_code == 200

    detail = klient.get(f"/api/vorgaenge/{vid}").json()
    assert detail["kennzahlen"]["konflikte_kritisch"] == 0

    fakten = klient.get(f"/api/vorgaenge/{vid}/fakten").json()["fakten"]
    flurstueck_fakt = next(f for f in fakten if f["schluessel"] == "flurstueck")
    assert flurstueck_fakt["wert"] == "143/2"
    assert flurstueck_fakt["status"] == "bestaetigt"

    # 7. Anforderungen: die Flurkarte belegt den Lageplan, nicht die Statik.
    anforderungen = klient.get(f"/api/vorgaenge/{vid}/anforderungen").json()["anforderungen"]
    lageplan = next(a for a in anforderungen if "Lageplan" in a["bezeichnung"])
    statik = next(a for a in anforderungen if "Tragwerksnachweis" in a["bezeichnung"])
    assert lageplan["status"] == "belegt"
    assert statik["status"] == "offen"

    # 8. Die Prüfung nennt die Zweckentfremdung weiterhin als kritischen Befund.
    befunde = klient.get(f"/api/vorgaenge/{vid}/pruefung").json()["befunde"]
    assert any("90 Tage" in befund["beobachtung"] for befund in befunde)

    # 9. Alles ist protokolliert.
    protokoll = klient.get(f"/api/vorgaenge/{vid}/protokoll").json()["eintraege"]
    aktionen = {eintrag["aktion"] for eintrag in protokoll}
    assert {"Vorgang angelegt", "Dokument empfangen", "Widerspruch gelöst"} <= aktionen


def test_upload_link_fuer_die_eigentuemerin(klient):
    """Der externe Upload läuft ohne Login und verrät nichts über den Vorgang."""

    vid = klient.post(
        "/api/vorgaenge",
        json={"strasse": "Am Weiher 7", "plz": "53229", "ort": "Bonn", "vermietungstage": 40},
    ).json()["id"]

    link = klient.post(
        f"/api/vorgaenge/{vid}/upload-links",
        json={"empfaenger": "frau.weber@example.de", "angefordert": ["Grundbuchauszug"]},
    ).json()
    token = link["token"]

    seite = klient.get(f"/api/upload/{token}").json()
    assert seite["adresse"] == "Am Weiher 7, 53229 Bonn"
    assert seite["angefordert"] == ["Grundbuchauszug"]
    # Die Seite verrät weder Fakten noch Widersprüche noch das Aktenzeichen.
    assert set(seite) == {"adresse", "angefordert", "gueltig_bis"}

    hochgeladen = klient.post(
        f"/api/upload/{token}",
        json={
            "dateien": [
                {
                    "name": "grundbuch.png",
                    "mime_type": "image/png",
                    "content_base64": _bild_base64(),
                }
            ]
        },
    )
    assert hochgeladen.status_code == 200
    assert hochgeladen.json()["dokumente"][0]["quelle"] == "extern"

    # Nach dem Widerruf ist der Link neutral nicht mehr gültig.
    assert klient.delete(f"/api/upload-links/{token}").status_code == 204
    assert klient.get(f"/api/upload/{token}").status_code == 404


def test_abgelaufener_link_gibt_keine_details_preis(klient):
    antwort = klient.get("/api/upload/gibtesnicht")
    assert antwort.status_code == 404
    assert "nicht mehr gültig" in antwort.json()["detail"]


def test_unbekannter_vorgang_ist_ein_sauberer_404(klient):
    assert klient.get("/api/vorgaenge/gibtesnicht").status_code == 404


def test_ungueltige_datei_kippt_nicht_den_ganzen_stapel(klient):
    """Eine schlechte Datei darf die guten daneben nicht mitreißen."""

    vid = klient.post(
        "/api/vorgaenge", json={"strasse": "Teststraße 1", "plz": "53129"}
    ).json()["id"]
    antwort = klient.post(
        f"/api/vorgaenge/{vid}/dokumente",
        json={
            "dateien": [
                {
                    "name": "tabelle.xlsx",
                    "mime_type": "application/vnd.ms-excel",
                    "content_base64": base64.b64encode(b"nichts").decode(),
                },
                {
                    "name": "plan.png",
                    "mime_type": "image/png",
                    "content_base64": _bild_base64(),
                },
            ]
        },
    )
    assert antwort.status_code == 200
    koerper = antwort.json()

    # Die gute Datei ist angekommen …
    assert [d["dateiname"] for d in koerper["dokumente"]] == ["plan.png"]
    # … und die schlechte wird beim Namen genannt, statt still zu verschwinden.
    assert len(koerper["abgelehnt"]) == 1
    assert koerper["abgelehnt"][0]["name"] == "tabelle.xlsx"
    assert "tabelle.xlsx" in koerper["abgelehnt"][0]["grund"]
