"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { api, BackendFehler, type Seitenvorschau } from "@/lib/api";
import stil from "./Quellvorschau.module.css";

/**
 * The page a claim came from, with the sentence marked on it.
 *
 * A filename and a quote as text ask the Architektin to believe the system.
 * Showing her the page lets her check — and checking is the point of a tool
 * she is personally liable for. The page is fetched only when she opens it,
 * because rendering a PDF page is not free.
 */
export function Quellvorschau({
  vorgangId,
  dokumentId,
  dateiname,
  seite,
  zitat,
  offenAnfangs = false,
}: {
  vorgangId: string;
  dokumentId: string;
  dateiname: string;
  seite: number | null;
  zitat: string;
  offenAnfangs?: boolean;
}) {
  const [offen, setOffen] = useState(offenAnfangs);
  const [bild, setBild] = useState<Seitenvorschau | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [laedt, setLaedt] = useState(false);
  const [lupe, setLupe] = useState(false);
  const geladen = useRef(false);

  const laden = useCallback(async () => {
    if (geladen.current) return;
    geladen.current = true;
    setLaedt(true);
    setFehler(null);
    try {
      setBild(await api.seitenvorschau(vorgangId, dokumentId, seite ?? 1, zitat));
    } catch (ausnahme) {
      geladen.current = false;
      setFehler(
        ausnahme instanceof BackendFehler
          ? ausnahme.message
          : "Die Seite konnte nicht geladen werden.",
      );
    } finally {
      setLaedt(false);
    }
  }, [vorgangId, dokumentId, seite, zitat]);

  useEffect(() => {
    if (!offen) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void laden();
  }, [offen, laden]);

  // Escape schließt die Lupe — sonst sitzt man mit der Tastatur fest.
  useEffect(() => {
    if (!lupe) return;
    const zu = (ereignis: KeyboardEvent) => {
      if (ereignis.key === "Escape") setLupe(false);
    };
    window.addEventListener("keydown", zu);
    return () => window.removeEventListener("keydown", zu);
  }, [lupe]);

  const bereich = `quelle-${dokumentId}-${seite ?? 1}`;

  return (
    <div className={stil.huelle}>
      <button
        type="button"
        className={stil.knopf}
        aria-expanded={offen}
        aria-controls={bereich}
        onClick={() => setOffen((wert) => !wert)}
      >
        <span className={stil.pfeil} aria-hidden="true">
          {offen ? "▾" : "▸"}
        </span>
        <span>
          Quelle{offen ? " schließen" : " öffnen"}:{" "}
          <span className={stil.datei}>{dateiname}</span>
          {seite ? `, S. ${seite}` : ""}
        </span>
      </button>

      {offen && (
        <div className={stil.koerper} id={bereich}>
          {zitat && <blockquote className={stil.zitat}>{zitat}</blockquote>}

          {laedt && <div className={stil.laedt}>Seite wird dargestellt…</div>}

          {fehler && (
            <div className="alarm alarm-kritisch" role="alert">
              {fehler}{" "}
              <button
                className="knopf-leise"
                onClick={() => {
                  geladen.current = false;
                  void laden();
                }}
              >
                Erneut versuchen
              </button>
            </div>
          )}

          {bild && (
            <>
              {/* Kein next/image: die Seite kommt als base64 aus dem Motor,
                  nicht von einem Server, den der Bildoptimierer kennt. */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                className={stil.blatt}
                src={`data:${bild.mime_type};base64,${bild.bild_base64}`}
                alt={`Seite ${bild.seite} von ${bild.dateiname}`}
                onClick={() => setLupe(true)}
              />
              <div className={stil.fusszeile}>
                <span>
                  Seite {bild.seite} von {bild.seiten_gesamt}
                </span>
                <span>
                  {bild.markiert
                    ? "Fundstelle markiert · zum Vergrößern klicken"
                    : "Scan ohne Textebene — nicht markierbar · zum Vergrößern klicken"}
                </span>
              </div>
            </>
          )}
        </div>
      )}
      {lupe && bild && (
        <div
          className={stil.lupe}
          role="dialog"
          aria-modal="true"
          aria-label={`${bild.dateiname}, Seite ${bild.seite}`}
        >
          <div className={stil.lupeKopf}>
            <span className={stil.lupeName}>
              {bild.dateiname} · Seite {bild.seite} von {bild.seiten_gesamt}
              {bild.markiert ? " · Fundstelle markiert" : ""}
            </span>
            <button
              type="button"
              className={stil.lupeSchliessen}
              onClick={() => setLupe(false)}
              autoFocus
            >
              Schließen
            </button>
          </div>
          <div className={stil.lupeRahmen}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              className={stil.lupeBild}
              src={`data:${bild.mime_type};base64,${bild.bild_base64}`}
              alt={`Seite ${bild.seite} von ${bild.dateiname}`}
              onClick={() => setLupe(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
}

/** Two source pages next to each other — what makes a conflict checkable. */
export function Quellenvergleich({ children }: { children: React.ReactNode }) {
  return <div className={stil.gegenueber}>{children}</div>;
}
