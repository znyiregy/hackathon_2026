// Client for Antragsvorbereitung and the submission package.
// Kept apart from lib/api.ts so the two areas stay independently readable.

import { anfrage, segment } from "./api";

/** Content class of a value — the three the UI must keep visually apart. */
export type Inhaltsklasse = "fakt" | "entwurf" | "vorlage" | "fehlt";

export interface PortalFeld {
  bezeichnung: string;
  wert: string;
  klasse: Inhaltsklasse;
  quelle: string;
  hinweis: string;
}

export interface Uebertragungsblatt {
  felder: PortalFeld[];
  vollstaendig: boolean;
  portal_url: string;
  hinweis: string;
}

export interface ArtefaktInfo {
  schluessel: string;
  bezeichnung: string;
  zweck: string;
  bereit: boolean;
  fehlende_voraussetzungen: string[];
}

export interface Artefakt {
  schluessel: string;
  bezeichnung: string;
  entwurf: string;
  luecken: string[];
  klasse: string;
}

export interface ManifestEintrag {
  dateiname: string;
  urspruenglich: string;
  typ: string;
  groesse_bytes: number;
  pruefsumme: string;
}

export interface Paket {
  manifest: ManifestEintrag[];
  eingefroren_am: string | null;
  paket_hash: string | null;
  freigabe_moeglich: boolean;
  offene_kritische: number;
}

export interface Pruefprotokoll {
  name: string;
  mime_type: string;
  content_base64: string;
  text: string;
}

export const erzeugung = {
  uebertragungsblatt: (id: string) =>
    anfrage<Uebertragungsblatt>(`/api/vorgaenge/${segment(id)}/uebertragungsblatt`),

  artefakte: (id: string) =>
    anfrage<{ artefakte: ArtefaktInfo[] }>(`/api/vorgaenge/${segment(id)}/artefakte`),

  erzeugen: (id: string, schluessel: string) =>
    anfrage<Artefakt>(`/api/vorgaenge/${segment(id)}/artefakte/${segment(schluessel)}/erzeugen`, {
      method: "POST",
    }),

  paket: (id: string) => anfrage<Paket>(`/api/vorgaenge/${segment(id)}/paket`),

  pruefprotokoll: (id: string) =>
    anfrage<Pruefprotokoll>(`/api/vorgaenge/${segment(id)}/pruefprotokoll`),
};
