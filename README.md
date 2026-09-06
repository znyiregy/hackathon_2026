# Digital Deutschland

Eine KI-gestützte Vorbereitungs- und Qualitätssicherungsschicht für die
Verwaltungsarbeit deutscher Architekturbüros. Der MVP deckt einen bewusst engen,
real schmerzhaften Fall ab: **Nutzungsänderung Wohnen → Ferienhaus in Bonn.**

Das Produkt reicht **niemals** etwas bei einer Behörde ein und trifft **keine**
rechtliche Aussage. Es benennt Anforderungen, Belege und offene Fragen.

## Das Prinzip

> Aufgabe der KI sind Extraktion und Formulierung.
> Aufgabe des Systems sind Vergleich und Urteil.

Das Modell liest Dokumente und formuliert Befunde. Deterministischer Code
vergleicht Werte, wertet Regeln aus und entscheidet über Schweregrade. Diese
Trennung macht das Produkt vertrauenswürdig genug für haftungsrelevante Arbeit.

## Zwei Oberflächen

| Oberfläche | Ort | Stand |
|---|---|---|
| **Next.js** | `web/` | Die Oberfläche für die Vorführung |
| Dash | `src/frontend/` | Älterer Chat-Prototyp, läuft weiter |

Beide sprechen mit demselben Motor. Die Next.js-Oberfläche stellt den
Assistenten in den Vordergrund und zeigt daneben die Akte, die sich mitfüllt.

## Aufbau

```text
web/            Next.js-Oberfläche (Deutsch, mobil-tauglich)
  app/          Seiten: Projekte, Projekt, externer Upload, Regelwerk
  components/   Assistent (Hauptfläche) und Akte (Reiter)
  e2e/          Playwright-Tests für den kritischen Pfad
src/backend/
  assistent.py      LangGraph-Agent, der die Architektin durch den Fall führt
  auswertung.py     Dokument lesen: Typ, Qualität, Fakten mit Herkunft
  regeln.py         Deterministisch: Vergleich, Anforderungen, Prüfung
  katalog.py        Kuratiertes Anforderungs- und Faktenmodell (Bonn)
  vorgang_service.py  Aufnahme und Neubewertung
  erzeugung.py      Übertragungsblatt, Entwürfe, Paket, Prüfprotokoll
  vorschau.py       Quellseite rendern und Fundstelle markieren
  store.py          In-Memory-Ablage (Prototyp: Neustart löscht alles)
  agent.py          Chat-Agent des Dash-Prototyps
src/frontend/   Dash-Oberfläche (Chat mit Dossier-Ansicht)
```

## Einrichten

Backend:

```bash
conda env create -f environment.yml
conda activate hackathon
cp .env.example .env
```

`OPENAI_API_KEY`, `OPENAI_MODEL` und `REASONING_EFFORT` in `.env` setzen. Das
Modell muss Bildeingabe und Function Calling beherrschen.

Oberfläche (braucht Node 20 oder neuer):

```bash
cd web && npm install
```

## Starten

```bash
conda activate hackathon
uvicorn src.backend.api:app --reload --port 8000
```

In einem zweiten Terminal:

```bash
cd web && npm run build && npx next start -p 3000
```

Dann <http://127.0.0.1:3000> öffnen.

**Für Vorführungen den Produktions-Build nehmen, nicht `npm run dev`** — im
Entwicklungsmodus hydriert React in manchen eingebetteten Browsern nicht.

Die alte Dash-Oberfläche startet mit `python -m src.frontend.app` auf Port 8050.
Die API-Dokumentation liegt unter <http://127.0.0.1:8000/docs>.

### Von einem Handy aus testen

`NEXT_PUBLIC_BACKEND_URL` auf die LAN-Adresse setzen und dieselbe Adresse in
`.env` unter `CORS_ORIGINS` erlauben:

```bash
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://192.168.1.228:3000
```

Nach jeder Änderung an `NEXT_PUBLIC_BACKEND_URL` neu bauen — der Wert wird beim
Bauen fest eingesetzt, ein Neustart allein genügt nicht.

## Tests

Backend — ohne KI, ohne Kosten, ohne Schlüssel:

```bash
conda activate hackathon
pytest -q
```

Oberfläche — echter Browser, kritischer Pfad, Desktop und Handy:

```bash
cd web && npm run e2e
```

Der Browser-Test setzt das Backend auf Netzwerkebene ab (`web/e2e/backend.ts`),
ruft also nie OpenAI. Geprüft wird der Weg, den auch die Vorführung nimmt:
Projekt anlegen → Unterlagen hochladen → Assistent meldet die Änderung →
Widerspruch erscheint → lösen → Paket bleibt gesperrt, solange Kritisches offen
ist. Dazu die externe Upload-Seite, das Verhalten bei ausgefallenem Backend und
zwei Mobil-Prüfungen.

## Was die Anwendung kann

| Fläche | Inhalt |
|---|---|
| **Assistent** | Führt das Gespräch, fragt nach dem nächsten Schritt, erzeugt Upload-Links |
| **Überblick** | Kennzahlen, nächster sinnvoller Schritt, beteiligte Ämter |
| **Unterlagen** | Typ, Qualität, Benennungsvorschlag; Unsicheres steht oben |
| **Angaben** | ~35 typisierte Fakten mit Herkunft, einzeln bestätigbar |
| **Passt nicht** | Beide Werte nebeneinander mit der Seite, auf der sie stehen |
| **Checkliste** | Was das Verfahren verlangt, was belegt ist, was fehlt |
| **Prüfung** | Befunde nach Schweregrad, mit Freigabetor |
| **Antrag** | Betriebsbeschreibung, Anschreiben, Begründungsgerüst — mit Lücken statt Erfindungen |
| **Fertig machen** | Werte zum Abtippen ins Amtsportal, Dateiliste, Protokoll |
| **Externer Upload** | Ohne Login, fürs Handy, mit sofortiger Qualitätsrückmeldung |

### Was das Farbsystem bedeutet

Die Farben tragen Bedeutung, sie sind keine Gestaltungsentscheidung:

| Farbe | Bedeutung |
|---|---|
| Bernstein | KI-Vorschlag — noch nicht von einem Menschen bestätigt |
| Grau | Bestätigte, geprüfte Angabe |
| Rot | Fehlt, passt nicht zusammen, oder sperrt den Folgeschritt |
| Grün | Erledigt / bereit |

## REST-Schnittstelle

`GET /health` liefert `{"status": "ok"}`.

Die Vorgangs-Schnittstelle liegt unter `/api/vorgaenge`; die vollständige
Beschreibung steht unter `/docs`.

Der Dash-Prototyp nutzt daneben `POST /chat`. Unterstützte Uploads sind TXT, MD,
CSV, JSON, PDF, PNG und JPEG, höchstens 10 MiB je Anfrage und 10 Seiten je PDF.
Dateiinhalte gelangen nie in den Kontext des Hauptagenten — er sieht nur
Dateinamen und kann eine Datei über `analyze_file` auswerten lassen. Die Antwort
eines `submit_result`-Werkzeugs trägt zusätzlich ein strukturiertes `result` für
die Bonn-Beuel-Dossieransicht mit `file_renaming`, `checklist_status`,
`next_steps` und `conflicts`; gewöhnliche Nachrichten liefern `result: null`.

## Grenzen des Prototyps

- **Der Zustand liegt im Arbeitsspeicher.** Ein Neustart des Backends löscht
  alle Vorgänge. Während einer Vorführung nicht neu starten.
- **Kein Login, keine Rollen.** Bewusst so entschieden; für ein Produkt, das
  Grundbuchauszüge verarbeitet, muss beides nachgeholt werden.
- **Nur Bonn, nur die Nutzungsänderung.** Anforderungs- und Faktenmodell sind
  handkuratiert und müssen von einer bauvorlageberechtigten Person geprüft
  werden, bevor man ihnen traut.
- **Live-Auswertung schwankt.** Dieselben Unterlagen können bei zwei Läufen
  leicht unterschiedliche Fakten ergeben. Den Demo-Ablauf vorher einmal
  durchspielen.
