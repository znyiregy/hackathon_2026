import type { Page, Route } from "@playwright/test";

/**
 * A stand-in backend, served from the browser's network layer.
 *
 * It holds just enough state to make the critical path behave like the real
 * thing: uploading a document produces a conflict, resolving the conflict
 * clears it, and the package can only be frozen once nothing critical is open.
 */

const BACKEND = "http://127.0.0.1:8000";

interface Zustand {
  angelegt: boolean;
  dokumente: unknown[];
  konfliktOffen: boolean;
  faktBestaetigt: boolean;
  eingefroren: boolean;
  assistentAufrufe: number;
}

export function neuerZustand(): Zustand {
  return {
    angelegt: false,
    dokumente: [],
    konfliktOffen: false,
    faktBestaetigt: false,
    eingefroren: false,
    assistentAufrufe: 0,
  };
}

const VORGANG_ID = "testvorgang01";

/** Ein winziges echtes JPEG, damit der Browser wirklich ein Bild lädt. */
const SEITENBILD =
  "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s7+9+H/BD2/kYlFbdFH9nf3vw/4Ie38jEorboo/s7+9+H/BD2/kZ2n/69v8Ad/qK0aKK7qFL2UOW9zKcuZ3CiiityAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigD//2Q==";

function dokument(name: string, typ: string, unklar = false) {
  return {
    id: `dok-${name}`,
    dateiname: name,
    mime_type: "application/pdf",
    groesse_bytes: 123456,
    seiten: 1,
    typ,
    typ_unklar: unklar,
    qualitaet: "gut",
    qualitaet_begruendung: "Gut lesbar.",
    status: "gelesen",
    namensvorschlag: `2024-03-12_${typ}_Test_V01.pdf`,
    zusammenfassung: `Testlesung für ${name}.`,
    fehler: "",
    hochgeladen_am: "2026-09-05T10:00:00Z",
    quelle: "buero",
  };
}

function kennzahlen(zustand: Zustand) {
  return {
    dokumente: zustand.dokumente.length,
    dokumente_zu_pruefen: 0,
    dokumente_unbrauchbar: 0,
    fakten_gesamt: 35,
    fakten_bestaetigt: zustand.faktBestaetigt ? 7 : 6,
    konflikte_kritisch: zustand.konfliktOffen ? 1 : 0,
    konflikte_warnung: 0,
    konflikte_hinweis: 0,
    anforderungen_gesamt: 13,
    anforderungen_belegt: zustand.dokumente.length > 0 ? 2 : 0,
    anforderungen_fehlend: zustand.dokumente.length > 0 ? 5 : 7,
  };
}

function detail(zustand: Zustand) {
  return {
    id: VORGANG_ID,
    aktenzeichen: "DD-2026-001",
    adresse: "Am Weiher 7, 53229 Bonn",
    strasse: "Am Weiher 7",
    plz: "53229",
    ort: "Bonn",
    bisherige_nutzung: "Wohnnutzung",
    geplante_nutzung: "Ferienwohnung",
    vermietungstage: 120,
    angelegt_am: "2026-09-05T10:00:00Z",
    geaendert_am: "2026-09-05T10:00:00Z",
    naechster_schritt: zustand.konfliktOffen
      ? "Lösen Sie die 1 kritischen Widersprüche (Eigentümer), bevor Antragsinhalte entstehen."
      : "Bestätigen Sie die restlichen Projektdaten — 25 Pflichtangaben sind offen.",
    kennzahlen: kennzahlen(zustand),
    verfahren: [
      {
        schluessel: "bauordnungsrecht",
        bezeichnung: "Bauordnungsrechtliche Nutzungsänderung",
        behoerde: "Bauaufsichtsamt Bonn",
        status: "in_bearbeitung",
        kritisch: false,
        erlaeuterung: "Vereinfachtes Verfahren nach § 64 BauO NRW.",
      },
      {
        schluessel: "zweckentfremdung",
        bezeichnung: "Zweckentfremdung",
        behoerde: "Amt für Soziales und Wohnen (50-52)",
        status: "kritisch",
        kritisch: true,
        erlaeuterung:
          "Geplante Vermietung 120 Tage im Kalenderjahr überschreitet die Schwelle von 90 Tagen.",
      },
    ],
    eingefroren_am: zustand.eingefroren ? "2026-09-05T12:00:00Z" : null,
    paket_hash: zustand.eingefroren ? "a".repeat(64) : null,
  };
}

function fakten(zustand: Zustand) {
  return {
    kategorien: ["Grundstück", "Eigentum"],
    fakten: [
      {
        id: "f1",
        schluessel: "flurstueck",
        bezeichnung: "Flurstück",
        kategorie: "Grundstück",
        wert: "1477",
        einheit: "",
        status: zustand.faktBestaetigt ? "bestaetigt" : "ki_entwurf",
        pflicht: true,
        konfidenz: 0.95,
        herkunft: [
          {
            dokument_id: "dok-flurkarte.pdf",
            dateiname: "flurkarte.pdf",
            seite: 1,
            zitat: "Flurstück: 1477",
          },
        ],
        bestaetigt_von: zustand.faktBestaetigt ? "Architektin" : null,
        bestaetigt_am: null,
        notiz: "",
      },
      {
        id: "f2",
        schluessel: "eigentuemer",
        bezeichnung: "Eigentümer",
        kategorie: "Eigentum",
        wert: zustand.konfliktOffen ? "Jennifer Hönig-Singh" : "Jennifer Hönig-Singh",
        einheit: "",
        status: zustand.konfliktOffen ? "konflikt" : "bestaetigt",
        pflicht: true,
        konfidenz: null,
        herkunft: [],
        bestaetigt_von: null,
        bestaetigt_am: null,
        notiz: "",
      },
    ],
  };
}

function konflikte(zustand: Zustand) {
  if (!zustand.konfliktOffen) return { konflikte: [] };
  return {
    konflikte: [
      {
        id: "k1",
        schluessel: "eigentuemer",
        bezeichnung: "Eigentümer",
        schweregrad: "kritisch",
        werte: [
          {
            wert: "Jennifer Hönig-Singh",
            dokument_id: "d1",
            dateiname: "nutzungsaufstellung.pdf",
            seite: 1,
          },
          {
            wert: "Gerold Brämer",
            dokument_id: "d2",
            dateiname: "bauschein.pdf",
            seite: 1,
          },
        ],
        hinweis:
          "Abweichende Eigentümerangaben müssen über den aktuellen Grundbuchauszug geklärt werden.",
        geklaert: false,
        gewaehlter_wert: null,
      },
    ],
  };
}

function befunde(zustand: Zustand) {
  const liste = [
    {
      id: "b1",
      schweregrad: "kritisch",
      beobachtung:
        "Geplante Vermietung von 120 Tagen überschreitet die Schwelle von 90 Tagen im Kalenderjahr.",
      grundlage: "Zweckentfremdungssatzung der Bundesstadt Bonn.",
      beleg: "Deterministische Regel auf die geplanten Vermietungstage.",
      massnahme: "Zweckentfremdungsgenehmigung beantragen.",
    },
  ];
  if (zustand.konfliktOffen) {
    liste.unshift({
      id: "b0",
      schweregrad: "kritisch",
      beobachtung: "Eigentümer: widersprüchliche Angaben in den Unterlagen.",
      grundlage: "Dokumentübergreifender Vergleich geprüfter Fakten.",
      beleg: "Jennifer Hönig-Singh · Gerold Brämer",
      massnahme: "Kanonischen Wert wählen.",
    });
  }
  return { befunde: liste, freigabe_moeglich: false };
}

/** Install the stand-in backend on a page. Returns the mutable state. */
export async function backendStellen(page: Page): Promise<Zustand> {
  const zustand = neuerZustand();

  const json = (route: Route, koerper: unknown, status = 200) =>
    route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify(koerper),
    });

  await page.route(`${BACKEND}/api/**`, async (route) => {
    const url = new URL(route.request().url());
    const pfad = url.pathname;
    const methode = route.request().method();

    if (methode === "OPTIONS") {
      return route.fulfill({ status: 204 });
    }

    if (pfad === "/api/vorgaenge" && methode === "GET") {
      if (!zustand.angelegt) return json(route, []);
      const d = detail(zustand);
      return json(route, [
        {
          id: d.id,
          aktenzeichen: d.aktenzeichen,
          adresse: d.adresse,
          bisherige_nutzung: d.bisherige_nutzung,
          geplante_nutzung: d.geplante_nutzung,
          naechster_schritt: d.naechster_schritt,
          dokumente_zu_pruefen: 0,
          konflikte_kritisch: d.kennzahlen.konflikte_kritisch,
          anforderungen_fehlend: d.kennzahlen.anforderungen_fehlend,
          geaendert_am: d.geaendert_am,
        },
      ]);
    }

    if (pfad === "/api/vorgaenge" && methode === "POST") {
      zustand.angelegt = true;
      return json(route, detail(zustand), 201);
    }

    if (pfad.endsWith("/dokumente") && methode === "POST") {
      zustand.dokumente = [
        dokument("flurkarte.pdf", "flurkarte"),
        dokument("bauschein.pdf", "bauschein"),
      ];
      // Zwei Unterlagen, die sich beim Eigentümer widersprechen.
      zustand.konfliktOffen = true;
      return json(route, { dokumente: zustand.dokumente, abgelehnt: [] });
    }

    if (pfad.endsWith("/dokumente") && methode === "GET") {
      return json(route, { dokumente: zustand.dokumente, abgelehnt: [] });
    }

    if (pfad.includes("/seite/")) {
      return json(route, {
        bild_base64: SEITENBILD,
        mime_type: "image/jpeg",
        seite: 1,
        seiten_gesamt: 1,
        markiert: true,
        dateiname: "flurkarte.pdf",
      });
    }

    if (pfad.endsWith("/fakten")) return json(route, fakten(zustand));

    if (pfad.includes("/fakten/") && pfad.endsWith("/bestaetigen")) {
      zustand.faktBestaetigt = true;
      return json(route, fakten(zustand).fakten[0]);
    }

    if (pfad.endsWith("/konflikte")) return json(route, konflikte(zustand));

    if (pfad.includes("/konflikte/") && pfad.endsWith("/loesen")) {
      zustand.konfliktOffen = false;
      return json(route, konflikte(zustand));
    }

    if (pfad.endsWith("/anforderungen")) {
      return json(route, {
        anforderungen: [
          {
            id: "a1",
            bezeichnung: "Aktueller Grundbuchauszug",
            pflicht: true,
            status: "offen",
            rechtsgrundlage: "§ 1 BauPrüfVO NRW",
            beleg_dokument_ids: [],
            hinweis: "Höchstens drei Monate alt.",
          },
          {
            id: "a2",
            bezeichnung: "Amtlicher Lageplan / Auszug Flurkarte",
            pflicht: true,
            status: zustand.dokumente.length > 0 ? "belegt" : "offen",
            rechtsgrundlage: "§ 3 BauPrüfVO NRW",
            beleg_dokument_ids: [],
            hinweis: "",
          },
        ],
      });
    }

    if (pfad.endsWith("/pruefung")) return json(route, befunde(zustand));

    if (pfad.endsWith("/paket/einfrieren")) {
      return json(route, {
        eingefroren: false,
        paket_hash: null,
        begruendung:
          "Es sind noch kritische Befunde offen. Das Paket kann nicht eingefroren werden.",
      });
    }

    if (pfad.endsWith("/paket")) {
      return json(route, {
        manifest: zustand.dokumente.map((_, index) => ({
          dateiname: `2024-03-12_dokument_${index}_V01.pdf`,
          urspruenglich: `dokument_${index}.pdf`,
          typ: "flurkarte",
          groesse_bytes: 123456,
          pruefsumme: "abc123def456",
        })),
        eingefroren_am: null,
        paket_hash: null,
        freigabe_moeglich: false,
        offene_kritische: 1,
      });
    }

    if (pfad.endsWith("/uebertragungsblatt")) {
      return json(route, {
        felder: [
          {
            bezeichnung: "Straße und Hausnummer",
            wert: "Am Weiher 7",
            klasse: "fakt",
            quelle: "Ihre Eingabe",
            hinweis: "",
          },
          {
            bezeichnung: "Flurstück",
            wert: "1477",
            klasse: zustand.faktBestaetigt ? "fakt" : "entwurf",
            quelle: "flurkarte.pdf",
            hinweis: zustand.faktBestaetigt ? "" : "Noch nicht bestätigt.",
          },
          {
            bezeichnung: "Grundbuchblatt",
            wert: "",
            klasse: "fehlt",
            quelle: "",
            hinweis: "Noch kein Wert. Im Faktenblatt ergänzen.",
          },
        ],
        vollstaendig: false,
        portal_url: "https://www.bauportal.nrw.de",
        hinweis: "Digital Deutschland übermittelt nichts an eine Behörde.",
      });
    }

    if (pfad.endsWith("/artefakte")) {
      return json(route, {
        artefakte: [
          {
            schluessel: "betriebsbeschreibung",
            bezeichnung: "Betriebs- und Nutzungsbeschreibung",
            zweck: "Die lästigste Schreibarbeit des Antrags.",
            bereit: true,
            fehlende_voraussetzungen: [],
          },
          {
            schluessel: "anschreiben",
            bezeichnung: "Anschreiben an die Bauaufsicht",
            zweck: "Begleitschreiben zur Einreichung.",
            bereit: false,
            fehlende_voraussetzungen: ["Flurstück"],
          },
        ],
      });
    }

    if (pfad.endsWith("/erzeugen")) {
      return json(route, {
        schluessel: "betriebsbeschreibung",
        bezeichnung: "Betriebs- und Nutzungsbeschreibung",
        entwurf:
          "Die Ferienwohnung im 1. Obergeschoss wird mit maximal [Gästezahl ergänzen] Gästen belegt.",
        luecken: ["Gästezahl ergänzen"],
        klasse: "entwurf",
      });
    }

    if (pfad.endsWith("/protokoll")) {
      return json(route, { eintraege: [] });
    }

    if (pfad.endsWith("/assistent")) {
      zustand.assistentAufrufe += 1;
      return json(route, {
        antwort:
          "Es fehlen derzeit fünf Pflichtunterlagen. Soll ich für die Eigentümerin einen Upload-Link erzeugen?",
        nachrichten: [
          { rolle: "werkzeug", inhalt: "…", werkzeug: "vorgangsstand" },
          { rolle: "werkzeug", inhalt: "…", werkzeug: "fehlende_unterlagen" },
          {
            rolle: "assistent",
            inhalt:
              "Es fehlen derzeit fünf Pflichtunterlagen. Soll ich für die Eigentümerin einen Upload-Link erzeugen?",
            werkzeug: null,
          },
        ],
      });
    }

    if (pfad.startsWith("/api/upload/")) {
      if (pfad.includes("abgelaufen")) {
        return json(route, { detail: "Dieser Link ist nicht mehr gültig." }, 404);
      }
      if (methode === "POST") {
        return json(route, { dokumente: [], abgelehnt: [] });
      }
      return json(route, {
        adresse: "Am Weiher 7, 53229 Bonn",
        angefordert: ["Grundbuchauszug (alle Seiten)"],
        gueltig_bis: "2026-09-08T10:00:00Z",
      });
    }

    if (pfad.endsWith(`/vorgaenge/${VORGANG_ID}`)) {
      return json(route, detail(zustand));
    }

    return json(route, { detail: `Unerwarteter Pfad ${pfad}` }, 500);
  });

  return zustand;
}

/** Simulate the backend being unreachable. */
export async function backendAus(page: Page) {
  await page.route(`${BACKEND}/api/**`, (route) => route.abort("failed"));
}

export { VORGANG_ID };
