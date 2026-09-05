"""Curated requirement and fact model for the Bonn Nutzungsänderung case.

Requirements are modelled, not prompted. This module is the hand-curated
backbone: which facts exist, which Bauvorlagen the simplified procedure under
§ 64 BauO NRW demands, and which parallel procedures the constellation
triggers. It is versioned like code and must be reviewed by a
bauvorlageberechtigte person before it is trusted.
"""

from dataclasses import dataclass

from src.backend.domain import Verfahrensstrang


@dataclass(frozen=True)
class FaktDefinition:
    """One typed fact, including the definition its unit implies."""

    schluessel: str
    bezeichnung: str
    kategorie: str
    einheit: str = ""
    pflicht: bool = True
    hinweis: str = ""
    #: Fact keys this one may be sanity-checked against — never equated with.
    plausibel_gegen: tuple[str, ...] = ()
    #: Free-text narrative fields describe different points in time and are
    #: never compared across documents — doing so only produces false alarms.
    vergleichbar: bool = True


# ~30 facts, grouped the way the Faktenblatt groups them on screen.
FAKTEN: tuple[FaktDefinition, ...] = (
    # Grundstück
    FaktDefinition("strasse_hausnummer", "Straße und Hausnummer", "Grundstück"),
    FaktDefinition("plz", "Postleitzahl", "Grundstück"),
    FaktDefinition("ort", "Ort", "Grundstück"),
    FaktDefinition("gemarkung", "Gemarkung", "Grundstück"),
    FaktDefinition("flur", "Flur", "Grundstück"),
    FaktDefinition("flurstueck", "Flurstück", "Grundstück"),
    FaktDefinition("grundstuecksflaeche", "Grundstücksfläche", "Grundstück", "m²"),
    FaktDefinition(
        "baulastenverzeichnis",
        "Eintrag im Baulastenverzeichnis",
        "Grundstück",
        pflicht=False,
    ),
    # Eigentum
    FaktDefinition("eigentuemer", "Eigentümer", "Eigentum"),
    FaktDefinition("grundbuchblatt", "Grundbuchblatt", "Eigentum"),
    FaktDefinition(
        "grundbuchauszug_datum",
        "Datum des Grundbuchauszugs",
        "Eigentum",
        hinweis="Muss bei Einreichung höchstens drei Monate alt sein.",
    ),
    FaktDefinition("weg_teilungserklaerung", "Teilungserklärung vorhanden", "Eigentum", pflicht=False),
    # Gebäude
    FaktDefinition("baujahr", "Baujahr", "Gebäude"),
    FaktDefinition("gebaeudeklasse", "Gebäudeklasse", "Gebäude"),
    FaktDefinition("geschosse", "Anzahl Geschosse", "Gebäude"),
    FaktDefinition("gebaeudehoehe", "Höhe des obersten Aufenthaltsraums", "Gebäude", "m"),
    FaktDefinition("wohneinheiten_bestand", "Wohneinheiten im Bestand", "Gebäude"),
    FaktDefinition("bauschein_datum", "Datum der historischen Baugenehmigung", "Gebäude"),
    # Flächen — different definitions, never compared with each other
    FaktDefinition(
        "wohnflaeche_woflv",
        "Wohnfläche nach WoFlV",
        "Flächen",
        "m²",
        hinweis="Balkone zu 25 %, Dachschrägen gemindert.",
        plausibel_gegen=("nutzflaeche_din277",),
    ),
    FaktDefinition(
        "nutzflaeche_din277",
        "Nutzfläche nach DIN 277",
        "Flächen",
        "m²",
        plausibel_gegen=("wohnflaeche_woflv",),
    ),
    FaktDefinition("brutto_grundflaeche", "Brutto-Grundfläche", "Flächen", "m²", pflicht=False),
    FaktDefinition("flaeche_ferienwohnung", "Fläche der Ferienwohnung", "Flächen", "m²"),
    FaktDefinition("anzahl_raeume", "Anzahl Räume der Ferienwohnung", "Flächen"),
    # Nutzung
    FaktDefinition("bisherige_nutzung", "Bisherige Nutzung", "Nutzung", vergleichbar=False),
    FaktDefinition("geplante_nutzung", "Geplante Nutzung", "Nutzung", vergleichbar=False),
    FaktDefinition("betten_max", "Maximale Bettenzahl", "Nutzung"),
    FaktDefinition(
        "vermietungstage",
        "Geplante Vermietungstage je Kalenderjahr",
        "Nutzung",
        "Tage",
        hinweis="Steuert den Zweckentfremdungszweig: mehr als 90 Tage ist genehmigungspflichtig.",
    ),
    FaktDefinition("gastgeber_vor_ort", "Gastgeber wohnt im Objekt", "Nutzung", pflicht=False),
    # Erschließung und Nachweise
    FaktDefinition("stellplaetze_bestand", "Genehmigte Stellplätze", "Erschließung"),
    FaktDefinition("stellplaetze_geplant", "Nachzuweisende Stellplätze", "Erschließung"),
    FaktDefinition(
        "planungsrechtliche_lage",
        "Planungsrechtliche Beurteilungsgrundlage",
        "Planungsrecht",
        vergleichbar=False,
    ),
    FaktDefinition("gebietstyp", "Gebietstyp", "Planungsrecht"),
    FaktDefinition("rauchwarnmelder", "Rauchwarnmelder nachgewiesen", "Brandschutz"),
    FaktDefinition("zweiter_rettungsweg", "Zweiter Rettungsweg", "Brandschutz"),
    FaktDefinition("tragende_wand_entfernt", "Tragende Wand entfernt", "Statik"),
)

FAKT_NACH_SCHLUESSEL = {definition.schluessel: definition for definition in FAKTEN}

KATEGORIEN: tuple[str, ...] = (
    "Grundstück",
    "Eigentum",
    "Gebäude",
    "Flächen",
    "Nutzung",
    "Erschließung",
    "Planungsrecht",
    "Brandschutz",
    "Statik",
)


@dataclass(frozen=True)
class AnforderungDefinition:
    """One required Bauvorlage, with the document types that can satisfy it."""

    schluessel: str
    bezeichnung: str
    pflicht: bool
    rechtsgrundlage: str
    #: Document type keys that count as evidence for this requirement.
    belegt_durch: tuple[str, ...] = ()
    hinweis: str = ""


# Derived from the Bonn-Beuel checklist. Classification A = mandatory,
# B = conditional, C = recommended, D = not required for this case.
ANFORDERUNGEN: tuple[AnforderungDefinition, ...] = (
    AnforderungDefinition(
        "antragsvordruck",
        "Antragsvordruck (Bauantragsformular)",
        True,
        "§ 64 BauO NRW · VV BauPrüfVO",
        ("antragsformular",),
        "Amtlicher NRW-Vordruck. Wird im Portal erfasst, nicht auf Papier eingereicht.",
    ),
    AnforderungDefinition(
        "betriebsbeschreibung",
        "Betriebsbeschreibung / Nutzungskonzept",
        True,
        "§ 64 BauO NRW",
        ("betriebsbeschreibung", "nutzungsaufstellung"),
        "Gästezahl, keine Veranstaltungen, Ruhezeiten, Gastgeber vor Ort.",
    ),
    AnforderungDefinition(
        "amtlicher_lageplan",
        "Amtlicher Lageplan / Auszug Flurkarte",
        True,
        "§ 3 BauPrüfVO NRW",
        ("flurkarte", "lageplan"),
        "Maßstab 1:500, höchstens sechs Monate alt, beide Stellplätze eingetragen.",
    ),
    AnforderungDefinition(
        "bauzeichnungen",
        "Bauzeichnungen (Grundrisse, Schnitt)",
        True,
        "§ 4 BauPrüfVO NRW",
        ("bauzeichnung", "grundriss"),
        "Maßstab 1:100. Ein Bestandsplan ersetzt die überarbeitete Einreichzeichnung nicht.",
    ),
    AnforderungDefinition(
        "baubeschreibung",
        "Baubeschreibung",
        True,
        "§ 5 BauPrüfVO NRW",
        ("baubeschreibung",),
    ),
    AnforderungDefinition(
        "flaechenberechnung",
        "Flächenberechnungen (Wohn-/Nutzfläche, BGF)",
        True,
        "§ 6 BauPrüfVO NRW · DIN 277 / WoFlV",
        ("flaechenberechnung",),
    ),
    AnforderungDefinition(
        "stellplatznachweis",
        "Stellplatznachweis und Stellplatzplan",
        True,
        "§ 48 BauO NRW · Stellplatzsatzung Bonn",
        ("stellplatzskizze", "stellplatznachweis"),
        "Mindestens 2,50 m × 5,00 m je Stellplatz, unabhängig anfahrbar.",
    ),
    AnforderungDefinition(
        "tragwerksnachweis",
        "Tragwerksnachweis / Statische Bescheinigung",
        True,
        "§ 68 BauO NRW",
        ("statik", "tragwerksnachweis"),
        "Erforderlich wegen der nachträglich entfernten tragenden Wand.",
    ),
    AnforderungDefinition(
        "brandschutznachweis",
        "Brandschutznachweis (Gebäudeklasse 2)",
        False,
        "§ 66 BauO NRW",
        ("brandschutznachweis",),
        "Bedingt erforderlich. Rettungswege in den Zeichnungen darstellen.",
    ),
    AnforderungDefinition(
        "rauchwarnmelder",
        "Nachweis Rauchwarnmelder",
        True,
        "§ 49 BauO NRW · DIN 14676",
        ("rauchwarnmelder", "bauzeichnung"),
        "In allen Schlafräumen und Fluren in den Grundrissen markieren.",
    ),
    AnforderungDefinition(
        "zweckentfremdung_bestand",
        "Bestehende Zweckentfremdungsgenehmigung",
        False,
        "Zweckentfremdungssatzung Bonn",
        ("zweckentfremdungsgenehmigung",),
        "Empfohlener Beleg. Eine Nutzungsaufstellung, die nur darauf verweist, ersetzt sie nicht.",
    ),
    AnforderungDefinition(
        "historische_baugenehmigung",
        "Historische Baugenehmigung und Bestandspläne",
        False,
        "Bestandsschutz",
        ("bauschein", "bestandszeichnung"),
        "Empfohlener Beleg für bestehende Baurechte.",
    ),
    AnforderungDefinition(
        "grundbuchauszug",
        "Aktueller Grundbuchauszug",
        True,
        "§ 1 BauPrüfVO NRW",
        ("grundbuchauszug",),
        "Höchstens drei Monate alt. Weist das Eigentum vollständig nach.",
    ),
)

ANFORDERUNG_NACH_SCHLUESSEL = {
    definition.schluessel: definition for definition in ANFORDERUNGEN
}

#: Document types the classifier may assign. Deliberately Bonn-NÄ specific.
DOKUMENTTYPEN: tuple[tuple[str, str], ...] = (
    ("antragsformular", "Antragsformular"),
    ("betriebsbeschreibung", "Betriebsbeschreibung"),
    ("nutzungsaufstellung", "Nutzungsaufstellung"),
    ("flurkarte", "Flurkarte / Liegenschaftskarte"),
    ("lageplan", "Lageplan"),
    ("bauzeichnung", "Bauzeichnung (Einreichung)"),
    ("grundriss", "Grundriss (Bestand)"),
    ("bestandszeichnung", "Bestandszeichnung"),
    ("schnitt", "Schnittzeichnung"),
    ("baubeschreibung", "Baubeschreibung"),
    ("flaechenberechnung", "Flächenberechnung"),
    ("stellplatzskizze", "Stellplatzskizze"),
    ("stellplatznachweis", "Stellplatznachweis"),
    ("statik", "Statik / Tragwerksnachweis"),
    ("brandschutznachweis", "Brandschutznachweis"),
    ("rauchwarnmelder", "Nachweis Rauchwarnmelder"),
    ("bauschein", "Historischer Bauschein"),
    ("grundbuchauszug", "Grundbuchauszug"),
    ("zweckentfremdungsgenehmigung", "Zweckentfremdungsgenehmigung"),
    ("foto", "Foto / Bestandsaufnahme"),
    ("rechnung", "Rechnung / Angebot"),
    ("produktdatenblatt", "Produktdatenblatt"),
    ("korrespondenz", "Korrespondenz"),
    ("sonstiges", "Sonstiges"),
)

DOKUMENTTYP_BEZEICHNUNG = dict(DOKUMENTTYPEN)


def verfahrensstraenge(vermietungstage: int) -> list[Verfahrensstrang]:
    """Return the permission constellation this case triggers.

    The Zweckentfremdung branch is decided deterministically from the planned
    rental days, never by the model.
    """

    zweckentfremdung_kritisch = vermietungstage > 90
    return [
        Verfahrensstrang(
            schluessel="bauordnungsrecht",
            bezeichnung="Bauordnungsrechtliche Nutzungsänderung",
            behoerde="Bauaufsichtsamt / Bauordnungsamt Bonn",
            status="in_bearbeitung",
            erlaeuterung=(
                "Der Fall liegt voraussichtlich im vereinfachten Verfahren nach § 64 BauO NRW. "
                "Das muss eine bauvorlageberechtigte Person bestätigen."
            ),
        ),
        Verfahrensstrang(
            schluessel="planungsrecht",
            bezeichnung="Bauplanungsrechtliche Zulässigkeit",
            behoerde="über das Bauaufsichtsamt, ggf. Stadtplanungsamt",
            status="offen",
            erlaeuterung=(
                "Eine Ferienwohnung ist rechtlich kein Wohnen (§ 13a BauNVO; BVerwG 4 C 5.16). "
                "Beurteilungsgrundlage dokumentieren, Zulässigkeit nie behaupten."
            ),
        ),
        Verfahrensstrang(
            schluessel="zweckentfremdung",
            bezeichnung="Zweckentfremdung",
            behoerde="Amt für Soziales und Wohnen (50-52), Abt. Wohnen",
            status="kritisch" if zweckentfremdung_kritisch else "hinweis",
            kritisch=zweckentfremdung_kritisch,
            erlaeuterung=(
                f"Geplante Vermietung {vermietungstage} Tage im Kalenderjahr überschreitet die "
                "Schwelle von 90 Tagen. Ohne Zweckentfremdungsgenehmigung darf ab Tag 91 nicht "
                "vermietet werden."
                if zweckentfremdung_kritisch
                else (
                    f"Geplante Vermietung {vermietungstage} Tage im Kalenderjahr liegt unter der "
                    "Schwelle von 90 Tagen. Bei Änderung der Planung neu prüfen."
                )
            ),
        ),
        Verfahrensstrang(
            schluessel="wohnraum_id",
            bezeichnung="Wohnraum-Identitätsnummer",
            behoerde="Amt für Soziales und Wohnen (50-52)",
            status="hinweis",
            erlaeuterung=(
                "Anzeige- und Registrierungspflicht vor Überlassung. Die Nummer muss in jedem "
                "Inserat sichtbar angegeben werden."
            ),
        ),
        Verfahrensstrang(
            schluessel="privatrecht",
            bezeichnung="Privatrecht (WEG, Teilungserklärung, Miteigentum)",
            behoerde="keine Behörde",
            status="hinweis",
            erlaeuterung=(
                "Eine Genehmigung überwindet weder die Teilungserklärung noch Rechte der "
                "Miteigentümer. Vor Vermietung prüfen lassen."
            ),
        ),
        Verfahrensstrang(
            schluessel="folgepflichten",
            bezeichnung="Gewerbe, Beherbergungsabgabe, Meldepflichten",
            behoerde="verschiedene",
            status="hinweis",
            erlaeuterung="Folgepflichten bei gewerblicher Vermietung. Nicht Teil dieser Vorbereitung.",
        ),
    ]
