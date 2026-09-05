"use client";

import Image from "next/image";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { api, BackendFehler, dateiLesen } from "@/lib/api";
import stil from "./upload.module.css";

interface Seite {
  adresse: string;
  angefordert: string[];
  gueltig_bis: string;
}

/** The external contributor's page: one column, no navigation, no case detail.
 *  She must never see the word "Konflikt" or anything about the procedure. */
export default function UploadSeite() {
  const parameter = useParams<{ token: string }>();
  const token = parameter.token;

  const [seite, setSeite] = useState<Seite | null>(null);
  const [abgelaufen, setAbgelaufen] = useState(false);
  const [gewaehlt, setGewaehlt] = useState<File[]>([]);
  const [warnungen, setWarnungen] = useState<string[]>([]);
  const [laeuft, setLaeuft] = useState(false);
  const [fertig, setFertig] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const dateiRef = useRef<HTMLInputElement>(null);
  const kameraRef = useRef<HTMLInputElement>(null);

  const laden = useCallback(async () => {
    try {
      setSeite(await api.uploadSeite(token));
      setFehler(null);
    } catch (ausnahme) {
      // Nur ein echtes 404/410 heißt "abgelaufen". Ein ausgefallener Motor
      // darf nicht als ungültiger Link erscheinen — sonst gibt die
      // Eigentümerin auf, obwohl ihr Link in Ordnung ist.
      const status = ausnahme instanceof BackendFehler ? ausnahme.status : undefined;
      if (status === 404 || status === 410) {
        setAbgelaufen(true);
      } else {
        setFehler(
          "Die Seite ist gerade nicht erreichbar. Bitte versuchen Sie es in ein paar Minuten noch einmal.",
        );
      }
    }
  }, [token]);

  useEffect(() => {
    // Daten beim Aufruf holen. Der Zustand wird erst im Promise-Callback
    // gesetzt, nicht synchron — die Regel kann das statisch nicht sehen.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void laden();
  }, [laden]);

  /** Immediate client-side quality feedback — worth more than any server
   *  pipeline, because she is still standing in front of the document. */
  function pruefeQualitaet(dateien: File[]): string[] {
    const meldungen: string[] = [];
    for (const datei of dateien) {
      if (datei.size < 60_000 && datei.type.startsWith("image/")) {
        meldungen.push(
          `${datei.name} ist sehr klein — das Foto ist wahrscheinlich unscharf. Bitte noch einmal aufnehmen.`,
        );
      }
      if (datei.size > 9_000_000) {
        meldungen.push(`${datei.name} ist sehr groß und lädt eventuell langsam.`);
      }
    }
    return meldungen;
  }

  function hinzufuegen(liste: FileList | null) {
    if (!liste) return;
    const neu = Array.from(liste);
    setGewaehlt((bisher) => [...bisher, ...neu]);
    setWarnungen((bisher) => [...bisher, ...pruefeQualitaet(neu)]);
  }

  async function absenden() {
    if (gewaehlt.length === 0) return;
    setLaeuft(true);
    setFehler(null);
    try {
      const gelesen = await Promise.all(gewaehlt.map(dateiLesen));
      await api.uploadExtern(token, gelesen);
      setFertig(true);
    } catch (ausnahme) {
      setFehler(
        ausnahme instanceof BackendFehler
          ? ausnahme.message
          : "Das Hochladen hat nicht geklappt. Bitte versuchen Sie es noch einmal.",
      );
    } finally {
      setLaeuft(false);
    }
  }

  if (abgelaufen) {
    return (
      <Huelle>
        <h1>Dieser Link ist nicht mehr gültig</h1>
        <p>
          Bitte wenden Sie sich an das Architekturbüro, das Ihnen den Link
          geschickt hat. Sie erhalten dann einen neuen.
        </p>
      </Huelle>
    );
  }

  if (fertig) {
    return (
      <Huelle>
        <h1>Vielen Dank</h1>
        <p>
          Ihre Unterlagen sind angekommen. Das Architekturbüro meldet sich, wenn
          noch etwas fehlt. Sie müssen nichts weiter tun.
        </p>
      </Huelle>
    );
  }

  if (!seite) {
    return (
      <Huelle>
        {fehler ? (
          <>
            <h1>Gerade nicht erreichbar</h1>
            <p role="alert">{fehler}</p>
            <button
              className={`knopf-primaer ${stil.gross}`}
              onClick={() => void laden()}
            >
              Erneut versuchen
            </button>
          </>
        ) : (
          <p>Einen Moment…</p>
        )}
      </Huelle>
    );
  }

  return (
    <Huelle>
      <h1>Unterlagen hochladen</h1>
      <p className={stil.adresse}>{seite.adresse}</p>

      <p>
        Bitte laden Sie die angeforderten Unterlagen hoch. Fotos sind in Ordnung
        — bitte flach hinlegen, gut beleuchten und das ganze Blatt aufnehmen.
      </p>

      {seite.angefordert.length > 0 && (
        <div className={stil.angefordert}>
          <span className="label">Angefragt</span>
          <ul>
            {seite.angefordert.map((eintrag) => (
              <li key={eintrag}>{eintrag}</li>
            ))}
          </ul>
        </div>
      )}

      <div className={stil.knoepfe}>
        <button
          className={`knopf-primaer ${stil.gross}`}
          onClick={() => kameraRef.current?.click()}
        >
          Foto aufnehmen
        </button>
        <button
          className={`knopf-sekundaer ${stil.gross}`}
          onClick={() => dateiRef.current?.click()}
        >
          Dateien auswählen
        </button>
      </div>

      <input
        ref={kameraRef}
        type="file"
        accept="image/*"
        capture="environment"
        multiple
        hidden
        onChange={(e) => hinzufuegen(e.target.files)}
      />
      <input
        ref={dateiRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg"
        multiple
        hidden
        onChange={(e) => hinzufuegen(e.target.files)}
      />

      {warnungen.map((warnung, index) => (
        <div key={`${index}-${warnung}`} className="alarm alarm-entwurf" role="alert">
          {warnung}
        </div>
      ))}

      {gewaehlt.length > 0 && (
        <ul className={stil.liste}>
          {gewaehlt.map((datei, index) => (
            <li key={`${datei.name}-${index}`}>
              <span>{datei.name}</span>
              <button
                className="knopf-leise"
                onClick={() =>
                  setGewaehlt((bisher) =>
                    bisher.filter((_, position) => position !== index),
                  )
                }
                aria-label={`${datei.name} entfernen`}
              >
                Entfernen
              </button>
            </li>
          ))}
        </ul>
      )}

      {fehler && (
        <div className="alarm alarm-kritisch" role="alert">
          {fehler}
        </div>
      )}

      <button
        className={`knopf-primaer ${stil.gross} ${stil.absenden}`}
        disabled={gewaehlt.length === 0 || laeuft}
        onClick={() => void absenden()}
      >
        {laeuft ? "Wird gesendet…" : "Absenden"}
      </button>
    </Huelle>
  );
}

function Huelle({ children }: { children: React.ReactNode }) {
  return (
    <main className={stil.huelle}>
      <div className={stil.marke}>
        <Image src="/logo.png" alt="" width={640} height={344} priority />
        <span>Digital Deutschland</span>
      </div>
      {children}
    </main>
  );
}
