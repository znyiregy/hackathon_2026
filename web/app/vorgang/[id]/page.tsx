"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { Akte } from "@/components/Akte";
import { Assistent } from "@/components/Assistent";
import { Rahmen } from "@/components/Rahmen";
import { api, BackendFehler, type VorgangDetail } from "@/lib/api";
import stil from "./vorgang.module.css";

export default function VorgangSeite() {
  const parameter = useParams<{ id: string }>();
  const id = parameter.id;

  const [vorgang, setVorgang] = useState<VorgangDetail | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  // Counter bumped after every change, so the Akte reloads what it shows.
  const [stand, setStand] = useState(0);
  const [ansicht, setAnsicht] = useState<"assistent" | "akte">("assistent");

  const laden = useCallback(async () => {
    try {
      setVorgang(await api.vorgang(id));
      setFehler(null);
    } catch (ausnahme) {
      setFehler(
        ausnahme instanceof BackendFehler
          ? ausnahme.message
          : "Der Vorgang konnte nicht geladen werden.",
      );
    }
  }, [id]);

  useEffect(() => {
    // Daten beim Aufruf holen. Der Zustand wird erst im Promise-Callback
    // gesetzt, nicht synchron — die Regel kann das statisch nicht sehen.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void laden();
  }, [laden]);

  const aktualisieren = useCallback(() => {
    setStand((wert) => wert + 1);
    void laden();
  }, [laden]);

  if (fehler) {
    return (
      <Rahmen>
        <div className="alarm alarm-kritisch">
          <strong>Nicht geladen.</strong> {fehler}{" "}
          <button className="knopf-leise" onClick={() => void laden()}>
            Erneut versuchen
          </button>
        </div>
        <p style={{ marginTop: "1rem" }}>
          <Link href="/">Zurück zur Vorgangsübersicht</Link>
        </p>
      </Rahmen>
    );
  }

  if (!vorgang) {
    return (
      <Rahmen>
        <div className={`karte ${stil.skelett}`} aria-hidden="true" />
      </Rahmen>
    );
  }

  return (
    <Rahmen>
      <header className={stil.kopf}>
        <Link href="/" className={stil.zurueck}>
          ← Vorgangsübersicht
        </Link>
        <div className="label">{vorgang.aktenzeichen}</div>
        <h1>{vorgang.adresse}</h1>
        <p className={stil.unterzeile}>
          Nutzungsänderung {vorgang.bisherige_nutzung} →{" "}
          {vorgang.geplante_nutzung} · geplante Vermietung{" "}
          {vorgang.vermietungstage} Tage im Kalenderjahr
        </p>
      </header>

      <div className={stil.umschalter} role="tablist">
        <button
          role="tab"
          aria-selected={ansicht === "assistent"}
          className={ansicht === "assistent" ? stil.umschalterAktiv : ""}
          onClick={() => setAnsicht("assistent")}
        >
          Assistent
        </button>
        <button
          role="tab"
          aria-selected={ansicht === "akte"}
          className={ansicht === "akte" ? stil.umschalterAktiv : ""}
          onClick={() => setAnsicht("akte")}
        >
          Akte
          {vorgang.kennzahlen.konflikte_kritisch > 0 && (
            <span className={stil.punkt}>
              {vorgang.kennzahlen.konflikte_kritisch}
            </span>
          )}
        </button>
      </div>

      <div className={stil.buehne}>
        <div
          className={`${stil.spalte} ${
            ansicht === "assistent" ? stil.sichtbar : ""
          }`}
        >
          <Assistent vorgangId={id} onAenderung={aktualisieren} />
        </div>
        <div
          className={`${stil.spalte} ${ansicht === "akte" ? stil.sichtbar : ""}`}
        >
          <Akte vorgang={vorgang} stand={stand} onAenderung={aktualisieren} />
        </div>
      </div>
    </Rahmen>
  );
}
