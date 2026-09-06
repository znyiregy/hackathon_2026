"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { Rahmen } from "@/components/Rahmen";
import { api, BackendFehler, type VorgangZeile } from "@/lib/api";
import stil from "./page.module.css";

export default function Vorgangsuebersicht() {
  const router = useRouter();
  const [zeilen, setZeilen] = useState<VorgangZeile[] | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [formularOffen, setFormularOffen] = useState(false);

  const laden = useCallback(async () => {
    try {
      setZeilen(await api.vorgaenge());
      setFehler(null);
    } catch (ausnahme) {
      setFehler(
        ausnahme instanceof BackendFehler
          ? ausnahme.message
          : "Die Projekte konnten nicht geladen werden.",
      );
    }
  }, []);

  useEffect(() => {
    // Daten beim Aufruf holen. Der Zustand wird erst im Promise-Callback
    // gesetzt, nicht synchron — die Regel kann das statisch nicht sehen.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void laden();
  }, [laden]);

  return (
    <Rahmen>
      <header className={stil.kopf}>
        <div>
          <h1>Meine Projekte</h1>
          <p className={stil.unterzeile}>
            Oben steht, wo es gerade klemmt.
          </p>
        </div>
        <button
          className="knopf-primaer"
          onClick={() => setFormularOffen((wert) => !wert)}
        >
          {formularOffen ? "Abbrechen" : "Neues Projekt"}
        </button>
      </header>

      {fehler && (
        <div className="alarm alarm-kritisch" style={{ marginBottom: "1rem" }}>
          <strong>Nicht geladen.</strong> {fehler}{" "}
          <button className="knopf-leise" onClick={() => void laden()}>
            Erneut versuchen
          </button>
        </div>
      )}

      {formularOffen && (
        <NeuerVorgang
          onAngelegt={(id) => router.push(`/vorgang/${id}`)}
          onAbbrechen={() => setFormularOffen(false)}
        />
      )}

      {zeilen === null && !fehler && (
        <div className={stil.liste}>
          {[0, 1].map((index) => (
            <div
              key={index}
              className={`karte ${stil.skelett}`}
              aria-hidden="true"
            />
          ))}
        </div>
      )}

      {zeilen?.length === 0 && !formularOffen && (
        <div className={`karte ${stil.leer}`}>
          <h2>Noch kein Projekt</h2>
          <p style={{ color: "var(--tinte-weich)", margin: 0 }}>
            Legen Sie eins an. Der Assistent fragt Sie dann Schritt für Schritt
            durch.
          </p>
          <button
            className="knopf-primaer"
            onClick={() => setFormularOffen(true)}
          >
            Projekt anlegen
          </button>
        </div>
      )}

      <div className={stil.liste}>
        {zeilen?.map((zeile) => (
          <Link
            key={zeile.id}
            href={`/vorgang/${zeile.id}`}
            className={stil.zeile}
          >
            <div className={stil.zeileKopf}>
              <div>
                <span className="label">{zeile.aktenzeichen}</span>
                <h2>{zeile.adresse}</h2>
                <p className={stil.unterzeile}>
                  Aus {zeile.bisherige_nutzung} wird{" "}
                  {zeile.geplante_nutzung}
                </p>
              </div>
              <div className={stil.zaehler}>
                <Zaehler
                  wert={zeile.dokumente_zu_pruefen}
                  label="noch anzusehen"
                  art="entwurf"
                />
                <Zaehler
                  wert={zeile.konflikte_kritisch}
                  label="passt nicht zusammen"
                  art="kritisch"
                />
                <Zaehler
                  wert={zeile.anforderungen_fehlend}
                  label="fehlt noch"
                  art="kritisch"
                />
              </div>
            </div>
            <div className={stil.schritt}>
              <span className="label">Als Nächstes</span>
              <span>{zeile.naechster_schritt}</span>
            </div>
          </Link>
        ))}
      </div>
    </Rahmen>
  );
}

function Zaehler({
  wert,
  label,
  art,
}: {
  wert: number;
  label: string;
  art: "entwurf" | "kritisch";
}) {
  const stumm = wert === 0;
  return (
    <div className={stil.zaehlerFeld}>
      <div
        className={stil.zaehlerWert}
        style={{
          color: stumm
            ? "var(--tinte-leise)"
            : art === "kritisch"
              ? "var(--rot)"
              : "var(--bernstein-tinte)",
        }}
      >
        {wert}
      </div>
      <div className="label">{label}</div>
    </div>
  );
}

function NeuerVorgang({
  onAngelegt,
  onAbbrechen,
}: {
  onAngelegt: (id: string) => void;
  onAbbrechen: () => void;
}) {
  const [strasse, setStrasse] = useState("");
  const [plz, setPlz] = useState("53129");
  const [ort, setOrt] = useState("Bonn");
  const [bisher, setBisher] = useState("Wohnnutzung");
  const [geplant, setGeplant] = useState("Ferienhaus");
  const [tage, setTage] = useState(120);
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  async function absenden(ereignis: React.FormEvent) {
    ereignis.preventDefault();
    if (!strasse.trim()) {
      setFehler("Bitte geben Sie die Adresse an.");
      return;
    }
    setLaeuft(true);
    setFehler(null);
    try {
      const vorgang = await api.vorgangAnlegen({
        strasse: strasse.trim(),
        plz: plz.trim(),
        ort: ort.trim(),
        bisherige_nutzung: bisher,
        geplante_nutzung: geplant,
        vermietungstage: tage,
      });
      onAngelegt(vorgang.id);
    } catch (ausnahme) {
      setFehler(
        ausnahme instanceof BackendFehler
          ? ausnahme.message
          : "Das Projekt konnte nicht angelegt werden.",
      );
      setLaeuft(false);
    }
  }

  return (
    <form className={`karte ${stil.formular}`} onSubmit={absenden}>
      <h2>Neues Projekt</h2>
      <p className={stil.hinweis}>
        Sechs kurze Angaben genügen.
      </p>

      <div className={stil.raster}>
        <label>
          <span className="label">Adresse</span>
          <input
            value={strasse}
            onChange={(e) => setStrasse(e.target.value)}
            placeholder="Kirschblütenweg 7"
            autoFocus
          />
        </label>
        <label>
          <span className="label">PLZ</span>
          <input value={plz} onChange={(e) => setPlz(e.target.value)} />
        </label>
        <label>
          <span className="label">Ort</span>
          <input value={ort} onChange={(e) => setOrt(e.target.value)} />
        </label>
        <label>
          <span className="label">Wie wird es heute genutzt?</span>
          <input value={bisher} onChange={(e) => setBisher(e.target.value)} />
        </label>
        <label>
          <span className="label">Wie soll es genutzt werden?</span>
          <input value={geplant} onChange={(e) => setGeplant(e.target.value)} />
        </label>
        <label>
          <span className="label">An wie vielen Tagen im Jahr vermietet?</span>
          <input
            type="number"
            min={0}
            max={366}
            value={tage}
            onChange={(e) => setTage(Number(e.target.value))}
          />
        </label>
      </div>

      {tage > 90 && (
        <div className="alarm alarm-entwurf">
          <strong>Achtung, mehr als 90 Tage.</strong> Dann brauchen Sie
          zusätzlich eine Erlaubnis von einem zweiten Amt. Das Bauamt sagt
          Ihnen das nicht.
        </div>
      )}

      {fehler && <div className="alarm alarm-kritisch">{fehler}</div>}

      <div className={stil.knoepfe}>
        <button className="knopf-primaer" type="submit" disabled={laeuft}>
          {laeuft ? "Einen Moment…" : "Projekt anlegen"}
        </button>
        <button
          className="knopf-sekundaer"
          type="button"
          onClick={onAbbrechen}
          disabled={laeuft}
        >
          Abbrechen
        </button>
      </div>
    </form>
  );
}
