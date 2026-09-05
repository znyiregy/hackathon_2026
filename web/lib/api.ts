// Typed client for the Digital Deutschland backend.
// Every call goes through `anfrage` so error handling stays in one place.

export const BACKEND =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://127.0.0.1:8000";

export class BackendFehler extends Error {
  /** HTTP status, when the request reached the backend at all. */
  readonly status?: number;

  constructor(nachricht: string, status?: number) {
    super(nachricht);
    this.status = status;
  }
}

/** Escape a value before it becomes a path segment.
 *  `useParams` hands back decoded values, so an id containing `/` would
 *  otherwise silently address a different endpoint. */
export function segment(wert: string): string {
  return encodeURIComponent(wert);
}

/** Reading a document can take a while; the assistant waits on a model. */
const ZEITLIMIT_MS = 90_000;

export async function anfrage<T>(
  pfad: string,
  init?: RequestInit & { zeitlimit?: number },
): Promise<T> {
  const { zeitlimit = ZEITLIMIT_MS, ...rest } = init ?? {};
  // Ohne eigenes Zeitlimit hängt die Oberfläche unbegrenzt, wenn der Motor
  // nicht antwortet — mit deaktivierter Eingabe und ohne Ausweg.
  const abbruch = new AbortController();
  const uhr = setTimeout(() => abbruch.abort(), zeitlimit);
  const signal = rest.signal
    ? AbortSignal.any([rest.signal, abbruch.signal])
    : abbruch.signal;

  let antwort: Response;
  try {
    antwort = await fetch(`${BACKEND}${pfad}`, {
      ...rest,
      signal,
      // Content-Type nur bei Rumpf — sonst wird aus jedem GET ein Preflight.
      headers: rest.body
        ? { "Content-Type": "application/json", ...(rest.headers ?? {}) }
        : (rest.headers ?? {}),
      cache: "no-store",
    });
  } catch {
    if (rest.signal?.aborted) throw new BackendFehler("Abgebrochen.");
    if (abbruch.signal.aborted) {
      throw new BackendFehler(
        "Der Motor antwortet gerade nicht. Bitte erneut versuchen.",
      );
    }
    throw new BackendFehler(
      "Der Motor ist nicht erreichbar. Läuft das Backend auf Port 8000?",
    );
  } finally {
    clearTimeout(uhr);
  }

  if (antwort.status === 204) return undefined as T;

  if (!antwort.ok) {
    let detail = `Der Motor hat mit ${antwort.status} geantwortet.`;
    try {
      const koerper = await antwort.json();
      if (typeof koerper?.detail === "string") detail = koerper.detail;
    } catch {
      // Keep the status-based message.
    }
    throw new BackendFehler(detail, antwort.status);
  }
  return (await antwort.json()) as T;
}

// -- Typen ----------------------------------------------------------------

export type FaktStatus = "ki_entwurf" | "bestaetigt" | "offen" | "konflikt";
export type Schweregrad = "kritisch" | "warnung" | "hinweis";
export type AnforderungStatus =
  | "belegt"
  | "teilweise"
  | "offen"
  | "nicht_pruefbar";
export type Qualitaet = "gut" | "eingeschraenkt" | "unbrauchbar";

export interface Herkunft {
  dokument_id: string;
  dateiname: string;
  seite: number | null;
  zitat: string;
}

export interface Fakt {
  id: string;
  schluessel: string;
  bezeichnung: string;
  kategorie: string;
  wert: string | null;
  einheit: string;
  status: FaktStatus;
  pflicht: boolean;
  konfidenz: number | null;
  herkunft: Herkunft[];
  bestaetigt_von: string | null;
  bestaetigt_am: string | null;
  notiz: string;
}

export interface KonfliktWert {
  wert: string;
  dokument_id: string;
  dateiname: string;
  seite: number | null;
}

export interface Konflikt {
  id: string;
  schluessel: string;
  bezeichnung: string;
  schweregrad: Schweregrad;
  werte: KonfliktWert[];
  hinweis: string;
  geklaert: boolean;
  gewaehlter_wert: string | null;
}

export interface Anforderung {
  id: string;
  bezeichnung: string;
  pflicht: boolean;
  status: AnforderungStatus;
  rechtsgrundlage: string;
  beleg_dokument_ids: string[];
  hinweis: string;
}

export interface Dokument {
  id: string;
  dateiname: string;
  mime_type: string;
  groesse_bytes: number;
  seiten: number | null;
  typ: string | null;
  typ_unklar: boolean;
  qualitaet: Qualitaet | null;
  qualitaet_begruendung: string;
  status: string;
  namensvorschlag: string | null;
  zusammenfassung: string;
  fehler: string;
  hochgeladen_am: string;
  quelle: "buero" | "extern";
}

export interface Befund {
  id: string;
  schweregrad: Schweregrad;
  beobachtung: string;
  grundlage: string;
  beleg: string;
  massnahme: string;
}

export interface Verfahrensstrang {
  schluessel: string;
  bezeichnung: string;
  behoerde: string;
  status: string;
  kritisch: boolean;
  erlaeuterung: string;
}

export interface VorgangZeile {
  id: string;
  aktenzeichen: string;
  adresse: string;
  bisherige_nutzung: string;
  geplante_nutzung: string;
  naechster_schritt: string;
  dokumente_zu_pruefen: number;
  konflikte_kritisch: number;
  anforderungen_fehlend: number;
  geaendert_am: string;
}

export interface Kennzahlen {
  dokumente: number;
  dokumente_zu_pruefen: number;
  dokumente_unbrauchbar: number;
  fakten_gesamt: number;
  fakten_bestaetigt: number;
  konflikte_kritisch: number;
  konflikte_warnung: number;
  konflikte_hinweis: number;
  anforderungen_gesamt: number;
  anforderungen_belegt: number;
  anforderungen_fehlend: number;
}

export interface VorgangDetail {
  id: string;
  aktenzeichen: string;
  adresse: string;
  strasse: string;
  plz: string;
  ort: string;
  bisherige_nutzung: string;
  geplante_nutzung: string;
  vermietungstage: number;
  angelegt_am: string;
  geaendert_am: string;
  naechster_schritt: string;
  kennzahlen: Kennzahlen;
  verfahren: Verfahrensstrang[];
  eingefroren_am: string | null;
  paket_hash: string | null;
}

export interface AssistentNachricht {
  rolle: string;
  inhalt: string;
  werkzeug: string | null;
}

export interface Datei {
  name: string;
  mime_type: string;
  content_base64: string;
}

export interface AbgelehnteDatei {
  name: string;
  grund: string;
}

export interface DokumenteAntwort {
  dokumente: Dokument[];
  abgelehnt?: AbgelehnteDatei[];
}

export interface UploadLink {
  token: string;
  empfaenger: string;
  angefordert: string[];
  gueltig_bis: string;
  widerrufen: boolean;
}

// -- Aufrufe --------------------------------------------------------------

export const api = {
  vorgaenge: () => anfrage<VorgangZeile[]>("/api/vorgaenge"),

  vorgangAnlegen: (koerper: {
    strasse: string;
    plz: string;
    ort: string;
    bisherige_nutzung: string;
    geplante_nutzung: string;
    vermietungstage: number;
  }) =>
    anfrage<VorgangDetail>("/api/vorgaenge", {
      method: "POST",
      body: JSON.stringify(koerper),
    }),

  vorgang: (id: string) => anfrage<VorgangDetail>(`/api/vorgaenge/${segment(id)}`),

  vorgangLoeschen: (id: string) =>
    anfrage<void>(`/api/vorgaenge/${segment(id)}`, { method: "DELETE" }),

  dokumente: (id: string) =>
    anfrage<DokumenteAntwort>(`/api/vorgaenge/${segment(id)}/dokumente`),

  hochladen: (id: string, dateien: Datei[]) =>
    anfrage<DokumenteAntwort>(`/api/vorgaenge/${segment(id)}/dokumente`, {
      method: "POST",
      body: JSON.stringify({ dateien }),
    }),

  dokumentAendern: (
    id: string,
    dokumentId: string,
    koerper: { typ?: string; namensvorschlag?: string },
  ) =>
    anfrage<DokumenteAntwort>(
      `/api/vorgaenge/${segment(id)}/dokumente/${segment(dokumentId)}`,
      { method: "PATCH", body: JSON.stringify(koerper) },
    ),

  fakten: (id: string) =>
    anfrage<{ fakten: Fakt[]; kategorien: string[] }>(
      `/api/vorgaenge/${segment(id)}/fakten`,
    ),

  faktBestaetigen: (id: string, schluessel: string, wert?: string) =>
    anfrage<Fakt>(`/api/vorgaenge/${segment(id)}/fakten/${segment(schluessel)}/bestaetigen`, {
      method: "POST",
      body: JSON.stringify({ wert: wert ?? null }),
    }),

  konflikte: (id: string) =>
    anfrage<{ konflikte: Konflikt[] }>(`/api/vorgaenge/${segment(id)}/konflikte`),

  konfliktLoesen: (id: string, konfliktId: string, wert: string, notiz = "") =>
    anfrage<{ konflikte: Konflikt[] }>(
      `/api/vorgaenge/${segment(id)}/konflikte/${segment(konfliktId)}/loesen`,
      { method: "POST", body: JSON.stringify({ wert, notiz }) },
    ),

  anforderungen: (id: string) =>
    anfrage<{ anforderungen: Anforderung[] }>(
      `/api/vorgaenge/${segment(id)}/anforderungen`,
    ),

  pruefung: (id: string) =>
    anfrage<{ befunde: Befund[]; freigabe_moeglich: boolean }>(
      `/api/vorgaenge/${segment(id)}/pruefung`,
    ),

  paketEinfrieren: (id: string) =>
    anfrage<{
      eingefroren: boolean;
      paket_hash: string | null;
      begruendung: string;
    }>(`/api/vorgaenge/${segment(id)}/paket/einfrieren`, { method: "POST" }),

  protokoll: (id: string) =>
    anfrage<{
      eintraege: {
        id: string;
        zeitpunkt: string;
        akteur: string;
        aktion: string;
        detail: string;
      }[];
    }>(`/api/vorgaenge/${segment(id)}/protokoll`),

  uploadLinks: (id: string) =>
    anfrage<UploadLink[]>(`/api/vorgaenge/${segment(id)}/upload-links`),

  uploadLinkAnlegen: (
    id: string,
    koerper: { empfaenger: string; angefordert: string[] },
  ) =>
    anfrage<UploadLink>(`/api/vorgaenge/${segment(id)}/upload-links`, {
      method: "POST",
      body: JSON.stringify(koerper),
    }),

  uploadSeite: (token: string) =>
    anfrage<{ adresse: string; angefordert: string[]; gueltig_bis: string }>(
      `/api/upload/${segment(token)}`,
    ),

  uploadExtern: (token: string, dateien: Datei[]) =>
    anfrage<DokumenteAntwort>(`/api/upload/${segment(token)}`, {
      method: "POST",
      body: JSON.stringify({ dateien }),
    }),

  assistent: (id: string, nachricht: string) =>
    anfrage<{ antwort: string; nachrichten: AssistentNachricht[] }>(
      `/api/vorgaenge/${segment(id)}/assistent`,
      { method: "POST", body: JSON.stringify({ nachricht }) },
    ),
};

/** Read a browser File into the base64 shape the backend expects. */
export function dateiLesen(datei: File): Promise<Datei> {
  return new Promise((aufloesen, ablehnen) => {
    const leser = new FileReader();
    leser.onerror = () =>
      ablehnen(new BackendFehler(`${datei.name} konnte nicht gelesen werden.`));
    leser.onload = () => {
      const ergebnis = String(leser.result ?? "");
      const komma = ergebnis.indexOf(",");
      aufloesen({
        name: datei.name,
        mime_type: datei.type || "application/octet-stream",
        content_base64: komma >= 0 ? ergebnis.slice(komma + 1) : ergebnis,
      });
    };
    leser.readAsDataURL(datei);
  });
}
