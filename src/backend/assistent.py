"""The interviewing assistant — the surface the Architektin actually works in.

The assistant does not answer questions about a case file; it walks the
Architektin through the case, one decision at a time. Its tools read the
deterministic state produced in :mod:`src.backend.regeln` and never recompute
severity themselves.
"""

import logging
from typing import Annotated, Any

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import InjectedState

from src.backend.config import Settings
from src.backend.domain import AnforderungStatus, FaktStatus, Schweregrad
from src.backend.katalog import DOKUMENTTYP_BEZEICHNUNG
from src.backend.store import Store, VorgangNotFoundError
from src.backend.vorgang_service import VorgangService

logger = logging.getLogger(__name__)

#: Who the audit record names when the assistant acts on the Architektin's
#: instruction. Never "Architektin" — the protocol exists for liability.
ASSISTENT_AKTEUR = "Assistent im Auftrag der Architektin"


class ConfigurationError(RuntimeError):
    """Raised when the backend is not configured to reach a model."""


SYSTEM_PROMPT = """Du bist der Vorbereitungsassistent von Digital Deutschland und
arbeitest mit einer bauvorlageberechtigten Architektin an einem Antrag auf
Nutzungsänderung in Bonn.

Du führst das Gespräch. Du wartest nicht auf Aufträge, sondern fragst nach dem,
was als Nächstes gebraucht wird — immer nur eine Frage auf einmal, in klarem
Deutsch, in der Sie-Form.

So arbeitest du:
- Beginne jede Antwort mit dem, was sich gerade geändert hat, wenn etwas
  passiert ist. Dann die nächste Frage oder der nächste Vorschlag.
- Rufe `vorgangsstand` auf, bevor du einschätzt, wie es um den Vorgang steht.
  Rate nie über Zahlen, die du abfragen kannst.
- Gibt es kritische Widersprüche, hat deren Klärung Vorrang vor allem anderen.
  Zeige beide Werte mit ihrer Quelle und frage, welcher gilt. Entscheide nie
  selbst, welcher Wert richtig ist.
- Fehlen Pflichtunterlagen, biete an, einen Upload-Link für die Eigentümerin zu
  erzeugen, und nenne konkret, welche Unterlagen angefordert werden sollen.
- Bestätigt die Architektin einen Wert, rufe `fakt_bestaetigen` auf.
- Fasse dich kurz. Höchstens ein kurzer Absatz, dann die Frage. Keine
  Aufzählungen über fünf Punkte, keine Wiederholung ganzer Listen, die die
  Architektin nebenan schon sieht.

Was du niemals tust:
- Du sagst nie, dass ein Vorhaben zulässig oder genehmigungsfähig ist. Du
  benennst Anforderungen, Belege und offene Fragen.
- Du behauptest nie, den Inhalt eines Dokuments gelesen zu haben, das dir nicht
  als Fakt vorliegt.
- Du übermittelst nichts an eine Behörde und behauptest das auch nicht.
- Du markierst eine Anforderung nie als erfüllt, nur weil ein verwandtes
  Dokument existiert.
- Du löst einen Widerspruch nie durch Raten. Kannst du ihn nicht auflösen,
  sagst du das und nennst den Beleg, der fehlt.

Sagst du etwas, das du nicht belegen kannst, sagst du stattdessen offen, dass du
es nicht weißt."""


def _schweregrad_wort(grad: Schweregrad) -> str:
    return {
        Schweregrad.KRITISCH: "kritisch",
        Schweregrad.WARNUNG: "Warnung",
        Schweregrad.HINWEIS: "Hinweis",
    }[grad]


def baue_werkzeuge(store: Store, service: VorgangService) -> list[Any]:
    """Build the assistant's tools, bound to the store and the service."""

    def _akte(state: dict[str, Any]):
        vorgang_id = state.get("vorgang_id")
        if not isinstance(vorgang_id, str) or not vorgang_id:
            raise VorgangNotFoundError("Diesem Gespräch ist kein Vorgang zugeordnet.")
        return store.akte(vorgang_id)

    @tool
    def vorgangsstand(state: Annotated[dict[str, Any], InjectedState]) -> str:
        """Aktueller Stand des Vorgangs: Zahlen, nächster Schritt, Verfahrensstränge."""

        try:
            akte = _akte(state)
        except VorgangNotFoundError as exc:
            return str(exc)

        zahlen = service.kennzahlen(akte)
        vorgang = akte.vorgang
        zeilen = [
            f"Vorgang {vorgang.aktenzeichen} — {vorgang.adresse}",
            f"Nutzungsänderung {vorgang.bisherige_nutzung} → {vorgang.geplante_nutzung}",
            f"Geplante Vermietung: {vorgang.vermietungstage} Tage im Kalenderjahr",
            "",
            f"Unterlagen: {zahlen['dokumente']} gesamt, {zahlen['dokumente_zu_pruefen']} noch einzuordnen, "
            f"{zahlen['dokumente_unbrauchbar']} nicht auswertbar",
            f"Projektdaten: {zahlen['fakten_bestaetigt']} von {zahlen['fakten_gesamt']} bestätigt",
            f"Widersprüche offen: {zahlen['konflikte_kritisch']} kritisch, "
            f"{zahlen['konflikte_warnung']} Warnungen, {zahlen['konflikte_hinweis']} Hinweise",
            f"Anforderungen: {zahlen['anforderungen_belegt']} von {zahlen['anforderungen_gesamt']} belegt, "
            f"{zahlen['anforderungen_fehlend']} Pflichtunterlagen fehlen",
            "",
            f"Nächster sinnvoller Schritt: {service.naechster_schritt(vorgang.id)}",
        ]

        kritische = [strang for strang in service.verfahren(vorgang.id) if strang.kritisch]
        if kritische:
            zeilen.append("")
            zeilen.append("Kritischer Parallelstrang:")
            for strang in kritische:
                zeilen.append(f"- {strang.bezeichnung} ({strang.behoerde}): {strang.erlaeuterung}")
        return "\n".join(zeilen)

    @tool
    def widersprueche(state: Annotated[dict[str, Any], InjectedState]) -> str:
        """Alle offenen Widersprüche mit beiden Werten und ihrer Quelle."""

        try:
            akte = _akte(state)
        except VorgangNotFoundError as exc:
            return str(exc)

        offen = [konflikt for konflikt in akte.konflikte.values() if not konflikt.geklaert]
        if not offen:
            return "Es sind keine Widersprüche offen."

        zeilen = []
        for konflikt in offen:
            zeilen.append(f"[{_schweregrad_wort(konflikt.schweregrad)}] {konflikt.bezeichnung} (id={konflikt.id})")
            for wert in konflikt.werte:
                seite = f", S. {wert.seite}" if wert.seite else ""
                zeilen.append(f"    {wert.wert} — {wert.dateiname}{seite}")
            if konflikt.hinweis:
                zeilen.append(f"    Hinweis: {konflikt.hinweis}")
        return "\n".join(zeilen)

    @tool
    def offene_projektdaten(state: Annotated[dict[str, Any], InjectedState]) -> str:
        """Pflichtangaben, die noch nicht bestätigt sind, mit Vorschlag und Quelle."""

        try:
            akte = _akte(state)
        except VorgangNotFoundError as exc:
            return str(exc)

        offen = [
            fakt
            for fakt in akte.fakten.values()
            if fakt.pflicht and fakt.status is not FaktStatus.BESTAETIGT
        ]
        if not offen:
            return "Alle Pflichtangaben sind bestätigt."

        zeilen = []
        for fakt in offen[:12]:
            quelle = fakt.herkunft[0].dateiname if fakt.herkunft else "keine Quelle im Material"
            wert = fakt.wert or "— noch kein Wert —"
            zeilen.append(f"{fakt.schluessel}: {fakt.bezeichnung} = {wert} ({fakt.status.value}, Quelle: {quelle})")
        if len(offen) > 12:
            zeilen.append(f"... und {len(offen) - 12} weitere.")
        return "\n".join(zeilen)

    @tool
    def fehlende_unterlagen(state: Annotated[dict[str, Any], InjectedState]) -> str:
        """Anforderungen, die noch nicht belegt sind, mit Rechtsgrundlage."""

        try:
            akte = _akte(state)
        except VorgangNotFoundError as exc:
            return str(exc)

        offen = [
            anforderung
            for anforderung in akte.anforderungen.values()
            if anforderung.status is not AnforderungStatus.BELEGT
        ]
        if not offen:
            return "Alle Anforderungen sind belegt."

        zeilen = []
        for anforderung in offen:
            pflicht = "Pflicht" if anforderung.pflicht else "empfohlen"
            zeilen.append(
                f"{anforderung.bezeichnung} [{pflicht}, {anforderung.status.value}] "
                f"— {anforderung.rechtsgrundlage}"
            )
        return "\n".join(zeilen)

    @tool
    def dokumentenliste(state: Annotated[dict[str, Any], InjectedState]) -> str:
        """Alle aufgenommenen Unterlagen mit Typ, Qualität und Benennungsvorschlag."""

        try:
            akte = _akte(state)
        except VorgangNotFoundError as exc:
            return str(exc)

        if not akte.dokumente:
            return "Es sind noch keine Unterlagen aufgenommen."

        zeilen = []
        for dokument in akte.dokumente.values():
            typ = DOKUMENTTYP_BEZEICHNUNG.get(dokument.typ or "", dokument.typ or "unklar")
            unklar = " (Typ unklar)" if dokument.typ_unklar else ""
            qualitaet = dokument.qualitaet.value if dokument.qualitaet else "unbewertet"
            zeilen.append(f"{dokument.dateiname} → {typ}{unklar}, Qualität {qualitaet}")
            if dokument.namensvorschlag:
                zeilen.append(f"    Benennungsvorschlag: {dokument.namensvorschlag}")
        return "\n".join(zeilen)

    @tool
    def fakt_bestaetigen(
        schluessel: str,
        wert: str,
        state: Annotated[dict[str, Any], InjectedState],
    ) -> str:
        """Eine Projektangabe im Namen der Architektin bestätigen.

        Nur aufrufen, wenn die Architektin den Wert im Gespräch bestätigt hat.
        """

        vorgang_id = state.get("vorgang_id")
        if not isinstance(vorgang_id, str) or not vorgang_id:
            return "Diesem Gespräch ist kein Vorgang zugeordnet."
        try:
            fakt = service.fakt_bestaetigen(vorgang_id, schluessel, wert, akteur=ASSISTENT_AKTEUR)
        except (KeyError, ValueError) as exc:
            return f"Konnte {schluessel!r} nicht bestätigen: {exc}"
        return f"Bestätigt: {fakt.bezeichnung} = {fakt.wert}"

    @tool
    def widerspruch_loesen(
        konflikt_id: str,
        wert: str,
        state: Annotated[dict[str, Any], InjectedState],
        notiz: str = "",
    ) -> str:
        """Einen Widerspruch mit dem von der Architektin gewählten Wert schließen."""

        vorgang_id = state.get("vorgang_id")
        if not isinstance(vorgang_id, str) or not vorgang_id:
            return "Diesem Gespräch ist kein Vorgang zugeordnet."
        try:
            konflikt = service.konflikt_loesen(
                vorgang_id,
                konflikt_id,
                wert,
                notiz,
                akteur=ASSISTENT_AKTEUR,
                # Das Modell darf nur zwischen den Werten wählen, die in den
                # Unterlagen stehen — nie einen dritten erfinden.
                nur_angebotene_werte=True,
            )
        except (KeyError, ValueError) as exc:
            return f"Konnte den Widerspruch nicht schließen: {exc}"
        return f"Widerspruch {konflikt.bezeichnung} geschlossen. Kanonischer Wert: {wert}"

    @tool
    def upload_link_erzeugen(
        empfaenger: str,
        unterlagen: list[str],
        state: Annotated[dict[str, Any], InjectedState],
    ) -> str:
        """Einen einmaligen Upload-Link für eine externe Person erzeugen."""

        vorgang_id = state.get("vorgang_id")
        if not isinstance(vorgang_id, str) or not vorgang_id:
            return "Diesem Gespräch ist kein Vorgang zugeordnet."
        try:
            link = store.link_erzeugen(vorgang_id, empfaenger, unterlagen)
            store.akte(vorgang_id).protokoll(
                ASSISTENT_AKTEUR, "Upload-Link erzeugt", f"{empfaenger}: {', '.join(unterlagen)}"
            )
        except VorgangNotFoundError as exc:
            return str(exc)
        return (
            f"Upload-Link erzeugt für {empfaenger or 'externe Person'}. "
            f"Token: {link.token}. Gültig bis {link.gueltig_bis.isoformat()}. "
            f"Angefordert: {', '.join(unterlagen) if unterlagen else 'nichts angegeben'}."
        )

    @tool
    def einreichungspruefung_ausfuehren(state: Annotated[dict[str, Any], InjectedState]) -> str:
        """Die Vor-Einreichungsprüfung ausführen und die Befunde zurückgeben."""

        vorgang_id = state.get("vorgang_id")
        if not isinstance(vorgang_id, str) or not vorgang_id:
            return "Diesem Gespräch ist kein Vorgang zugeordnet."
        befunde = service.befunde(vorgang_id)
        if not befunde:
            return "Die Prüfung hat keine Befunde ergeben."
        zeilen = []
        for befund in befunde[:15]:
            zeilen.append(f"[{_schweregrad_wort(befund.schweregrad)}] {befund.beobachtung}")
            if befund.massnahme:
                zeilen.append(f"    Maßnahme: {befund.massnahme}")
        if len(befunde) > 15:
            zeilen.append(f"... und {len(befunde) - 15} weitere Befunde.")
        return "\n".join(zeilen)

    return [
        vorgangsstand,
        widersprueche,
        offene_projektdaten,
        fehlende_unterlagen,
        dokumentenliste,
        fakt_bestaetigen,
        widerspruch_loesen,
        upload_link_erzeugen,
        einreichungspruefung_ausfuehren,
    ]


def baue_modell(settings: Settings) -> ChatOpenAI:
    if not settings.openai_api_key:
        raise ConfigurationError("OPENAI_API_KEY ist nicht konfiguriert.")
    if not settings.openai_model:
        raise ConfigurationError("OPENAI_MODEL ist nicht konfiguriert.")
    if not settings.reasoning_effort:
        raise ConfigurationError("REASONING_EFFORT ist nicht konfiguriert.")
    return ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        use_responses_api=True,
        reasoning={"effort": settings.reasoning_effort},
    )


def baue_assistent(store: Store, service: VorgangService, model: Any) -> Any:
    """Create the LangGraph agent that interviews the Architektin."""

    from typing import Annotated as _Annotated, TypedDict

    from langchain.messages import AnyMessage
    from langgraph.graph.message import add_messages

    class State(TypedDict):
        messages: _Annotated[list[AnyMessage], add_messages]
        vorgang_id: str

    return create_agent(
        model=model,
        tools=baue_werkzeuge(store, service),
        system_prompt=SYSTEM_PROMPT,
        state_schema=State,
        checkpointer=InMemorySaver(),
    )
