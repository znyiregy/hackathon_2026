"use client";

import { useCallback, useEffect, useState } from "react";

import { BackendFehler } from "@/lib/api";
import {
  erzeugung,
  type Artefakt,
  type ArtefaktInfo,
  type Paket,
  type Uebertragungsblatt,
} from "@/lib/erzeugung";
import stil from "./Antrag.module.css";

function fehlertext(ausnahme: unknown, ersatz: string): string {
  return ausnahme instanceof BackendFehler ? ausnahme.message : ersatz;
}

/** Antragsvorbereitung: what can be drafted, and the drafts themselves.
 *  Nothing is generated before its preconditions are confirmed. */
export function Antragsvorbereitung({
  vorgangId,
  stand,
}: {
  vorgangId: string;
  stand: number;
}) {
  const [infos, setInfos] = useState<ArtefaktInfo[] | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [entwuerfe, setEntwuerfe] = useState<Record<string, Artefakt>>({});
  const [laeuft, setLaeuft] = useState<string | null>(null);

  const laden = useCallback(async () => {
    try {
      setInfos((await erzeugung.artefakte(vorgangId)).artefakte);
      setFehler(null);
    } catch (ausnahme) {
      setFehler(fehlertext(ausnahme, "Die Artefaktliste konnte nicht geladen werden."));
    }
  }, [vorgangId]);

  useEffect(() => {
    // Daten beim Aufruf holen. Der Zustand wird erst im Promise-Callback
    // gesetzt, nicht synchron — die Regel kann das statisch nicht sehen.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void laden();
  }, [laden, stand]);

  async function erzeugen(schluessel: string) {
    setLaeuft(schluessel);
    setFehler(null);
    try {
      const artefakt = await erzeugung.erzeugen(vorgangId, schluessel);
      setEntwuerfe((bisher) => ({ ...bisher, [schluessel]: artefakt }));
    } catch (ausnahme) {
      setFehler(fehlertext(ausnahme, "Der Entwurf konnte nicht erzeugt werden."));
    } finally {
      setLaeuft(null);
    }
  }

  if (fehler && !infos) {
    return <div className="alarm alarm-kritisch">{fehler}</div>;
  }
  if (!infos) {
    return (
      <p style={{ color: "var(--tinte-leise)", fontSize: "0.9rem" }}>
        Wird geladen…
      </p>
    );
  }

  return (
    <div className={stil.raster}>
      <div className="alarm alarm-entwurf">
        Alles Faktische wird aus bestätigten Projektdaten eingesetzt, nicht vom
        Modell erfunden. Lücken erscheinen als Platzhalter in eckigen Klammern.
      </div>

      {fehler && <div className="alarm alarm-kritisch">{fehler}</div>}

      {infos.map((info) => {
        const entwurf = entwuerfe[info.schluessel];
        return (
          <div
            key={info.schluessel}
            className={`balken ${stil.artefakt} ${
              info.bereit ? "balken-bestaetigt" : "balken-kritisch"
            }`}
          >
            <div className={stil.kopf}>
              <strong>{info.bezeichnung}</strong>
              <button
                className={`knopf-primaer ${stil.klein}`}
                disabled={!info.bereit || laeuft !== null}
                onClick={() => void erzeugen(info.schluessel)}
              >
                {laeuft === info.schluessel
                  ? "Wird geschrieben…"
                  : entwurf
                    ? "Neu erzeugen"
                    : "Entwurf erzeugen"}
              </button>
            </div>

            <p className={stil.zweck}>{info.zweck}</p>

            {!info.bereit && (
              <div className={stil.gesperrt}>
                <span className="chip chip-kritisch">Voraussetzung fehlt</span>{" "}
                Bestätigen Sie zuerst:{" "}
                {info.fehlende_voraussetzungen.join(", ")}.
              </div>
            )}

            {entwurf && (
              <>
                <div className={stil.entwurf}>{entwurf.entwurf}</div>
                {entwurf.luecken.length > 0 && (
                  <div className={stil.luecken}>
                    <span className="label">Noch zu füllen:</span>
                    {entwurf.luecken.map((luecke) => (
                      <span key={luecke} className="chip chip-kritisch">
                        {luecke}
                      </span>
                    ))}
                  </div>
                )}
                <div className={stil.knopfreihe}>
                  <button
                    className={`knopf-sekundaer ${stil.klein}`}
                    onClick={() =>
                      void navigator.clipboard?.writeText(entwurf.entwurf)
                    }
                  >
                    Text kopieren
                  </button>
                </div>
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}

/** The submission package: transfer sheet, manifest, freeze, audit record. */
export function Paketansicht({
  vorgangId,
  stand,
  onAenderung,
}: {
  vorgangId: string;
  stand: number;
  onAenderung: () => void;
}) {
  const [blatt, setBlatt] = useState<Uebertragungsblatt | null>(null);
  const [paket, setPaket] = useState<Paket | null>(null);
  const [protokoll, setProtokoll] = useState<string | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [kopiert, setKopiert] = useState<string | null>(null);

  const laden = useCallback(async () => {
    try {
      const [b, p] = await Promise.all([
        erzeugung.uebertragungsblatt(vorgangId),
        erzeugung.paket(vorgangId),
      ]);
      setBlatt(b);
      setPaket(p);
      setFehler(null);
    } catch (ausnahme) {
      setFehler(fehlertext(ausnahme, "Das Paket konnte nicht geladen werden."));
    }
  }, [vorgangId]);

  useEffect(() => {
    // Daten beim Aufruf holen. Der Zustand wird erst im Promise-Callback
    // gesetzt, nicht synchron — die Regel kann das statisch nicht sehen.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void laden();
  }, [laden, stand]);

  async function kopieren(bezeichnung: string, wert: string) {
    try {
      await navigator.clipboard?.writeText(wert);
      setKopiert(bezeichnung);
      window.setTimeout(() => setKopiert(null), 1500);
    } catch {
      setFehler("Kopieren ist in diesem Browser nicht möglich.");
    }
  }

  if (fehler && !blatt) return <div className="alarm alarm-kritisch">{fehler}</div>;
  if (!blatt || !paket) {
    return (
      <p style={{ color: "var(--tinte-leise)", fontSize: "0.9rem" }}>
        Wird geladen…
      </p>
    );
  }

  return (
    <div className={stil.raster}>
      <div className="alarm alarm-entwurf">
        <strong>Die Einreichung erfolgt durch Sie im Bauportal.NRW.</strong>{" "}
        {blatt.hinweis}{" "}
        <a href={blatt.portal_url} target="_blank" rel="noopener noreferrer">
          Bauportal.NRW öffnen
        </a>
      </div>

      {fehler && <div className="alarm alarm-kritisch">{fehler}</div>}

      <div>
        <div className={stil.blattKopf}>
          <span className="label">Portal-Übertragungsblatt</span>
          <span className="label">
            {blatt.vollstaendig
              ? "alle Felder bestätigt"
              : "noch nicht vollständig bestätigt"}
          </span>
        </div>

        <div className={stil.manifest}>
          {blatt.felder.map((feld) => (
            <div
              key={feld.bezeichnung}
              className={`balken ${stil.feld} ${
                feld.klasse === "fakt"
                  ? "balken-bestaetigt"
                  : feld.klasse === "entwurf"
                    ? "balken-entwurf"
                    : "balken-kritisch"
              }`}
            >
              <div>
                <div className={stil.feldName}>{feld.bezeichnung}</div>
                {feld.wert ? (
                  <div className={stil.feldWert}>{feld.wert}</div>
                ) : (
                  <div className={stil.feldLeer}>{feld.hinweis}</div>
                )}
              </div>
              {feld.wert && (
                <button
                  className={`knopf-sekundaer ${stil.klein} ${stil.kopieren}`}
                  onClick={() => void kopieren(feld.bezeichnung, feld.wert)}
                >
                  {kopiert === feld.bezeichnung ? "Kopiert" : "Kopieren"}
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      <div>
        <span className="label">Paketinhalt</span>
        <div className={stil.manifest} style={{ marginTop: "0.35rem" }}>
          {paket.manifest.length === 0 && (
            <p style={{ color: "var(--tinte-leise)", fontSize: "0.9rem" }}>
              Noch keine Unterlagen im Paket.
            </p>
          )}
          {paket.manifest.map((eintrag) => (
            <div key={eintrag.dateiname} className={stil.zeile}>
              <div className={stil.dateiname}>{eintrag.dateiname}</div>
              <div className={stil.meta}>
                ursprünglich {eintrag.urspruenglich} · {eintrag.typ} ·{" "}
                {Math.round(eintrag.groesse_bytes / 1024)} KB · sha256:
                {eintrag.pruefsumme}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div
        className={`alarm ${paket.freigabe_moeglich ? "" : "alarm-kritisch"}`}
      >
        <strong>
          {paket.eingefroren_am
            ? "Paket ist eingefroren."
            : paket.freigabe_moeglich
              ? "Das Paket kann eingefroren werden."
              : `Freigabe gesperrt — ${paket.offene_kritische} kritische Befunde offen.`}
        </strong>
        {paket.paket_hash && (
          <div className={stil.meta} style={{ marginTop: "0.3rem" }}>
            Prüfsumme: {paket.paket_hash}
          </div>
        )}
        <div className={stil.knopfreihe}>
          <button
            className={`knopf-sekundaer ${stil.klein}`}
            onClick={async () => {
              try {
                const datei = await erzeugung.pruefprotokoll(vorgangId);
                setProtokoll(datei.text);
              } catch (ausnahme) {
                setFehler(
                  fehlertext(ausnahme, "Das Prüfprotokoll konnte nicht geladen werden."),
                );
              }
            }}
          >
            Prüfprotokoll anzeigen
          </button>
          <button
            className={`knopf-sekundaer ${stil.klein}`}
            onClick={async () => {
              await laden();
              onAenderung();
            }}
          >
            Aktualisieren
          </button>
        </div>
        {protokoll && <pre className={stil.protokoll}>{protokoll}</pre>}
      </div>
    </div>
  );
}
