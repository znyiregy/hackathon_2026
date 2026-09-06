"""Tests for the deterministic half: comparison, requirements, review."""

from src.backend.domain import (
    AnforderungStatus,
    Dokument,
    Fakt,
    FaktStatus,
    KonfliktWert,
    Qualitaet,
    Schweregrad,
)
from src.backend.regeln import (
    bewerte_anforderungen,
    einreichungspruefung,
    finde_konflikte,
    freigabe_moeglich,
    naechster_schritt,
    normalisiere_adresse,
    normalisiere_datum,
    normalisiere_zahl,
)


def _wert(wert: str, datei: str = "a.pdf", seite: int = 1) -> KonfliktWert:
    return KonfliktWert(wert=wert, dokument_id="d1", dateiname=datei, seite=seite)


class TestNormalisierung:
    def test_strassenschreibweisen_sind_gleich(self):
        assert normalisiere_adresse("Musterstraße 12") == normalisiere_adresse("Musterstr. 12")

    def test_verdrehte_hausnummer_ist_nicht_gleich(self):
        assert normalisiere_adresse("Musterstr. 12") != normalisiere_adresse("Musterstr. 21")

    def test_deutsche_dezimalzahl(self):
        assert normalisiere_zahl("92,4 m²") == 92.4

    def test_tausenderpunkt(self):
        assert normalisiere_zahl("1.234,50 m²") == 1234.5

    def test_datum_in_deutscher_schreibweise(self):
        assert normalisiere_datum("24.09.1962") == normalisiere_datum("1962-09-24")


class TestKonflikte:
    def test_gleiche_adresse_anders_geschrieben_ist_kein_konflikt(self):
        aussagen = {
            "strasse_hausnummer": [
                _wert("Kirschblütenweg 7", "lageplan.pdf"),
                _wert("Kirschblütenweg 7", "grundbuch.pdf"),
            ]
        }
        assert finde_konflikte(aussagen) == []

    def test_abweichendes_flurstueck_ist_kritisch(self):
        aussagen = {
            "flurstueck": [
                _wert("143/2", "liegenschaftskarte.pdf"),
                _wert("143", "bauantrag.pdf"),
            ]
        }
        konflikte = finde_konflikte(aussagen)
        assert len(konflikte) == 1
        assert konflikte[0].schweregrad is Schweregrad.KRITISCH

    def test_wohnflaeche_und_nutzflaeche_werden_nie_verglichen(self):
        """Different definitions are different facts, never a contradiction."""

        aussagen = {
            "wohnflaeche_woflv": [_wert("92,4 m²", "wohnflaeche.pdf")],
            "nutzflaeche_din277": [_wert("96,2 m²", "berechnung.pdf")],
        }
        konflikte = finde_konflikte(aussagen)
        assert konflikte == []

    def test_wohnflaeche_groesser_als_nutzflaeche_ist_nur_ein_hinweis(self):
        aussagen = {
            "wohnflaeche_woflv": [_wert("120,0 m²", "wohnflaeche.pdf")],
            "nutzflaeche_din277": [_wert("96,2 m²", "berechnung.pdf")],
        }
        konflikte = finde_konflikte(aussagen)
        assert len(konflikte) == 1
        assert konflikte[0].schweregrad is Schweregrad.HINWEIS

    def test_gerundete_flaeche_ist_kein_konflikt(self):
        aussagen = {
            "wohnflaeche_woflv": [_wert("92,40 m²"), _wert("92,4 m²", "b.pdf")],
        }
        assert finde_konflikte(aussagen) == []


class TestAnforderungen:
    def test_ohne_dokumente_ist_alles_offen(self):
        anforderungen = bewerte_anforderungen([])
        assert all(a.status is AnforderungStatus.OFFEN for a in anforderungen)

    def test_grundbuchauszug_wird_belegt(self):
        dokument = Dokument(
            dateiname="grundbuch.pdf",
            mime_type="application/pdf",
            typ="grundbuchauszug",
            qualitaet=Qualitaet.GUT,
        )
        anforderungen = bewerte_anforderungen([dokument])
        grundbuch = next(a for a in anforderungen if "Grundbuchauszug" in a.bezeichnung)
        assert grundbuch.status is AnforderungStatus.BELEGT

    def test_unbrauchbares_dokument_belegt_nichts(self):
        dokument = Dokument(
            dateiname="grundbuch.jpg",
            mime_type="image/jpeg",
            typ="grundbuchauszug",
            qualitaet=Qualitaet.UNBRAUCHBAR,
        )
        anforderungen = bewerte_anforderungen([dokument])
        grundbuch = next(a for a in anforderungen if "Grundbuchauszug" in a.bezeichnung)
        assert grundbuch.status is AnforderungStatus.OFFEN

    def test_bestandsplan_belegt_nicht_die_einreichzeichnung(self):
        """An existing plan does not replace the required revised drawing."""

        dokument = Dokument(
            dateiname="bestand.pdf",
            mime_type="application/pdf",
            typ="bestandszeichnung",
            qualitaet=Qualitaet.GUT,
        )
        anforderungen = bewerte_anforderungen([dokument])
        zeichnungen = next(a for a in anforderungen if "Bauzeichnungen" in a.bezeichnung)
        assert zeichnungen.status is AnforderungStatus.OFFEN


class TestEinreichungspruefung:
    def test_vermietung_ueber_90_tagen_ist_kritisch(self):
        befunde = einreichungspruefung([], [], [], [], vermietungstage=120)
        # Über den Amtsnamen erkannt, nicht über den Wortlaut — der Text darf
        # sich ändern, der Befund muss bleiben.
        zweckentfremdung = [b for b in befunde if "Soziales und Wohnen" in b.massnahme]
        assert len(zweckentfremdung) == 1
        assert zweckentfremdung[0].schweregrad is Schweregrad.KRITISCH
        assert "120" in zweckentfremdung[0].beobachtung

    def test_vermietung_unter_90_tagen_erzeugt_keinen_befund(self):
        befunde = einreichungspruefung([], [], [], [], vermietungstage=60)
        assert not [b for b in befunde if "Soziales und Wohnen" in b.massnahme]

    def test_ungeprueftes_ki_ergebnis_sperrt_die_freigabe(self):
        """Ein Vorschlag, den niemand geprüft hat, ist ein echter Blocker."""

        fakt = Fakt(
            schluessel="flurstueck",
            bezeichnung="Flurstück",
            kategorie="Grundstück",
            wert="143/2",
            status=FaktStatus.KI_ENTWURF,
        )
        befunde = einreichungspruefung([fakt], [], [], [], vermietungstage=0)
        assert not freigabe_moeglich(befunde)

    def test_pflichtangabe_ohne_quelle_sperrt_die_freigabe_nicht(self):
        """Sonst wäre das Freigabetor dauerhaft zu und damit bedeutungslos."""

        fakt = Fakt(
            schluessel="gebaeudehoehe",
            bezeichnung="Höhe des obersten Aufenthaltsraums",
            kategorie="Gebäude",
            wert=None,
            status=FaktStatus.OFFEN,
        )
        befunde = einreichungspruefung([fakt], [], [], [], vermietungstage=0)
        assert freigabe_moeglich(befunde)
        assert any(b.schweregrad is Schweregrad.WARNUNG for b in befunde)

    def test_befunde_sind_nach_schweregrad_sortiert(self):
        befunde = einreichungspruefung([], [], bewerte_anforderungen([]), [], vermietungstage=120)
        grade = [b.schweregrad for b in befunde]
        assert grade == sorted(
            grade,
            key=lambda g: {Schweregrad.KRITISCH: 0, Schweregrad.WARNUNG: 1, Schweregrad.HINWEIS: 2}[g],
        )


class TestNaechsterSchritt:
    def test_ohne_dokumente_wird_zum_upload_geraten(self):
        text = naechster_schritt([], [], [], [])
        assert "hoch" in text.lower() or "upload" in text.lower()

    def test_kritischer_konflikt_hat_vorrang(self):
        dokument = Dokument(dateiname="a.pdf", mime_type="application/pdf", typ="grundbuchauszug")
        konflikte = finde_konflikte(
            {"flurstueck": [_wert("143/2"), _wert("143", "b.pdf")]}
        )
        text = naechster_schritt([dokument], [], konflikte, [])
        # Der kritische Widerspruch wird beim Namen genannt, alles andere wartet.
        assert "Flurstück" in text


class TestHerkunftWerte:
    """Regression: the engine compares asserted values, never their quotes."""

    def test_gleicher_wert_unterschiedlich_zitiert_ist_kein_konflikt(self):
        from src.backend.domain import Herkunft, Vorgang
        from src.backend.store import Store
        from src.backend.vorgang_service import VorgangService

        service = VorgangService(Store(), model=None)
        akte = service.anlegen("Am Weiher 7", "53229", "Bonn", "Wohnen", "Ferienhaus", 120)

        fakt = akte.fakten["gemarkung"]
        fakt.wert = "Holzlar"
        fakt.herkunft = [
            Herkunft(
                dokument_id="d1",
                dateiname="flurkarte.pdf",
                wert="Holzlar",
                zitat="Gemarkung: Holzlar",
            ),
            Herkunft(
                dokument_id="d2",
                dateiname="bauschein.pdf",
                wert="Holzlar",
                zitat="Gemarkung Holzlar",
            ),
        ]
        service._neu_bewerten(akte)
        assert "gemarkung" not in akte.konflikte

    def test_echt_abweichender_wert_bleibt_ein_konflikt(self):
        from src.backend.domain import Herkunft
        from src.backend.store import Store
        from src.backend.vorgang_service import VorgangService

        service = VorgangService(Store(), model=None)
        akte = service.anlegen("Am Weiher 7", "53229", "Bonn", "Wohnen", "Ferienhaus", 120)

        fakt = akte.fakten["flurstueck"]
        fakt.wert = "1477"
        fakt.herkunft = [
            Herkunft(dokument_id="d1", dateiname="flurkarte.pdf", wert="1477", zitat="Flurstück: 1477"),
            Herkunft(dokument_id="d2", dateiname="antrag.pdf", wert="147", zitat="Parz. 147"),
        ]
        service._neu_bewerten(akte)
        assert "flurstueck" in akte.konflikte
        assert akte.konflikte["flurstueck"].schweregrad is Schweregrad.KRITISCH
