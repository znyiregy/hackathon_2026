"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  api,
  BackendFehler,
  type Anforderung,
  type Befund,
  type Dokument,
  type Fakt,
  type Konflikt,
  type VorgangDetail,
} from "@/lib/api";
import { Antragsvorbereitung, Paketansicht } from "./Antrag";
import stil from "./Akte.module.css";

type Reiter =
  | "uebersicht"
  | "unterlagen"
  | "projektdaten"
  | "widersprueche"
  | "anforderungen"
  | "pruefung"
  | "antrag"
  | "paket";

const REITER: { id: Reiter; label: string }[] = [
  { id: "uebersicht", label: "Übersicht" },
  { id: "unterlagen", label: "Unterlagen" },
  { id: "projektdaten", label: "Projektdaten" },
  { id: "widersprueche", label: "Widersprüche" },
  { id: "anforderungen", label: "Anforderungen" },
  { id: "pruefung", label: "Prüfung" },
  { id: "antrag", label: "Antrag" },
  { id: "paket", label: "Paket" },
];

export function Akte({
  vorgang,
  stand,
  onAenderung,
}: {
  vorgang: VorgangDetail;
  stand: number;
  onAenderung: () => void;
}) {
  const [reiter, setReiter] = useState<Reiter>("uebersicht");
  const zahlen = vorgang.kennzahlen;

  function tastatur(ereignis: React.KeyboardEvent) {
    const index = REITER.findIndex((eintrag) => eintrag.id === reiter);
    const ziel =
      ereignis.key === "ArrowRight"
        ? (index + 1) % REITER.length
        : ereignis.key === "ArrowLeft"
          ? (index - 1 + REITER.length) % REITER.length
          : ereignis.key === "Home"
            ? 0
            : ereignis.key === "End"
              ? REITER.length - 1
              : null;
    if (ziel === null) return;
    ereignis.preventDefault();
    setReiter(REITER[ziel].id);
    document.getElementById(`reiter-${REITER[ziel].id}`)?.focus();
  }

  return (
    <section className={stil.akte}>
      <div className={stil.reiter} role="tablist" aria-label="Bereiche der Akte" onKeyDown={tastatur}>
        {REITER.map((eintrag) => {
          const zaehler =
            eintrag.id === "widersprueche"
              ? zahlen.konflikte_kritisch
              : eintrag.id === "anforderungen"
                ? zahlen.anforderungen_fehlend
                : eintrag.id === "unterlagen"
                  ? zahlen.dokumente_zu_pruefen
                  : 0;
          return (
            <button
              key={eintrag.id}
              id={`reiter-${eintrag.id}`}
              role="tab"
              type="button"
              aria-selected={reiter === eintrag.id}
              aria-controls="akte-panel"
              tabIndex={reiter === eintrag.id ? 0 : -1}
              className={`${stil.reiterKnopf} ${
                reiter === eintrag.id ? stil.reiterAktiv : ""
              }`}
              onClick={(ereignis) => {
                setReiter(eintrag.id);
                ereignis.currentTarget.scrollIntoView({
                  inline: "nearest",
                  block: "nearest",
                });
              }}
            >
              {eintrag.label}
              {zaehler > 0 && (
                <span className={stil.punkt}>
                  {zaehler}
                  <span className="nur-vorlesen"> offen</span>
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div
        className={stil.inhalt}
        id="akte-panel"
        role="tabpanel"
        aria-labelledby={`reiter-${reiter}`}
        tabIndex={0}
      >
        {reiter === "uebersicht" && <Uebersicht vorgang={vorgang} />}
        {reiter === "unterlagen" && (
          <Unterlagen
            vorgangId={vorgang.id}
            stand={stand}
            onAenderung={onAenderung}
          />
        )}
        {reiter === "projektdaten" && (
          <Projektdaten
            vorgangId={vorgang.id}
            stand={stand}
            onAenderung={onAenderung}
          />
        )}
        {reiter === "widersprueche" && (
          <Widersprueche
            vorgangId={vorgang.id}
            stand={stand}
            onAenderung={onAenderung}
          />
        )}
        {reiter === "anforderungen" && (
          <Anforderungen vorgangId={vorgang.id} stand={stand} />
        )}
        {reiter === "pruefung" && (
          <Pruefung
            vorgangId={vorgang.id}
            stand={stand}
            onAenderung={onAenderung}
          />
        )}
        {reiter === "antrag" && (
          <Antragsvorbereitung vorgangId={vorgang.id} stand={stand} />
        )}
        {reiter === "paket" && (
          <Paketansicht
            vorgangId={vorgang.id}
            stand={stand}
            onAenderung={onAenderung}
          />
        )}
      </div>
    </section>
  );
}

// -- Übersicht ------------------------------------------------------------

function Uebersicht({ vorgang }: { vorgang: VorgangDetail }) {
  const z = vorgang.kennzahlen;
  return (
    <div className={stil.stapelWeit}>
      <div className={`balken balken-entwurf ${stil.feld}`}>
        <span className="label">Nächster sinnvoller Schritt</span>
        <p>{vorgang.naechster_schritt}</p>
        <span className={stil.quelle}>
          Deterministisch aus dem Vorgangsstand berechnet, nicht generiert.
        </span>
      </div>

      <div className={stil.kacheln}>
        <Kachel
          titel="Unterlagen"
          gross={`${z.dokumente}`}
          zeilen={[
            `${z.dokumente_zu_pruefen} einzuordnen`,
            `${z.dokumente_unbrauchbar} nicht auswertbar`,
          ]}
        />
        <Kachel
          titel="Projektdaten"
          gross={`${z.fakten_bestaetigt} / ${z.fakten_gesamt}`}
          zeilen={["bestätigt"]}
        />
        <Kachel
          titel="Widersprüche"
          gross={`${z.konflikte_kritisch}`}
          zeilen={[
            `${z.konflikte_warnung} Warnungen`,
            `${z.konflikte_hinweis} Hinweise`,
          ]}
          warnend={z.konflikte_kritisch > 0}
        />
        <Kachel
          titel="Anforderungen"
          gross={`${z.anforderungen_belegt} / ${z.anforderungen_gesamt}`}
          zeilen={[`${z.anforderungen_fehlend} Pflichtunterlagen fehlen`]}
          warnend={z.anforderungen_fehlend > 0}
        />
      </div>

      <div>
        <span className="label">Genehmigungskonstellation</span>
        <div className={stil.straenge}>
          {vorgang.verfahren.map((strang) => (
            <div
              key={strang.schluessel}
              className={`balken ${stil.feld} ${
                strang.kritisch ? "balken-kritisch" : ""
              }`}
            >
              <div className={stil.strangKopf}>
                <strong>{strang.bezeichnung}</strong>
                {strang.kritisch && (
                  <span className="chip chip-kritisch">kritisch</span>
                )}
              </div>
              <div className={stil.quelle}>{strang.behoerde}</div>
              <p>{strang.erlaeuterung}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Kachel({
  titel,
  gross,
  zeilen,
  warnend,
}: {
  titel: string;
  gross: string;
  zeilen: string[];
  warnend?: boolean;
}) {
  return (
    <div className={stil.kachel}>
      <span className="label">{titel}</span>
      <div
        className={stil.kachelWert}
        style={{ color: warnend ? "var(--rot)" : "var(--tinte)" }}
      >
        {gross}
      </div>
      {zeilen.map((zeile) => (
        <div key={zeile} className={stil.kachelZeile}>
          {zeile}
        </div>
      ))}
    </div>
  );
}

// -- Ladehilfe ------------------------------------------------------------

function useDaten<T>(laden: () => Promise<T>, stand: number) {
  const [daten, setDaten] = useState<T | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [laedt, setLaedt] = useState(false);
  // Die Ladefunktion wird bei jedem Render neu gebildet; über die Ref bleibt
  // `holen` trotzdem stabil. Zuweisung im Effect, nicht im Render-Rumpf.
  const ladenRef = useRef(laden);
  useEffect(() => {
    ladenRef.current = laden;
  });
  // Läuft eine ältere Anfrage länger als eine neuere, darf ihre Antwort den
  // frischeren Stand nicht überschreiben — sonst springt ein gerade
  // bestätigter Fakt sichtbar zurück auf "KI-Entwurf".
  const laufendeNummer = useRef(0);

  const holen = useCallback(async () => {
    const nummer = ++laufendeNummer.current;
    setLaedt(true);
    try {
      const ergebnis = await ladenRef.current();
      if (nummer !== laufendeNummer.current) return;
      setDaten(ergebnis);
      setFehler(null);
    } catch (ausnahme) {
      if (nummer !== laufendeNummer.current) return;
      // Die bereits geladenen Daten bleiben stehen; der Fehler erscheint als
      // Banner darüber, statt den ganzen Reiter zu leeren.
      setFehler(
        ausnahme instanceof BackendFehler
          ? ausnahme.message
          : "Konnte nicht geladen werden.",
      );
    } finally {
      if (nummer === laufendeNummer.current) setLaedt(false);
    }
  }, []);

  useEffect(() => {
    // Daten beim Aufruf holen. Der Zustand wird erst im Promise-Callback
    // gesetzt, nicht synchron — die Regel kann das statisch nicht sehen.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void holen();
  }, [holen, stand]);

  return { daten, fehler, laedt, neuLaden: holen };
}

/** Error banner that keeps the data below it visible. */
function Fehlerband({
  text,
  onErneut,
}: {
  text: string;
  onErneut?: () => void;
}) {
  return (
    <div className="alarm alarm-kritisch" role="alert">
      {text}
      {onErneut && (
        <>
          {" "}
          <button className="knopf-leise" onClick={onErneut}>
            Erneut versuchen
          </button>
        </>
      )}
    </div>
  );
}

/** German labels for values the backend keeps as machine-readable keys. */
const STATUS_TEXT: Record<string, string> = {
  belegt: "belegt",
  teilweise: "teilweise belegt",
  offen: "offen",
  nicht_pruefbar: "nicht prüfbar",
  kritisch: "kritisch",
  warnung: "Warnung",
  hinweis: "Hinweis",
  gut: "gut lesbar",
  eingeschraenkt: "eingeschränkt lesbar",
  unbrauchbar: "nicht auswertbar",
};

function statusText(wert: string): string {
  return STATUS_TEXT[wert] ?? wert;
}

function Leer({ text }: { text: string }) {
  return <p className={stil.leer}>{text}</p>;
}

// -- Unterlagen -----------------------------------------------------------

function Unterlagen({
  vorgangId,
  stand,
  onAenderung,
}: {
  vorgangId: string;
  stand: number;
  onAenderung: () => void;
}) {
  const { daten, fehler, neuLaden } = useDaten(
    () => api.dokumente(vorgangId),
    stand,
  );
  if (!daten)
    return fehler ? (
      <Fehlerband text={fehler} onErneut={() => void neuLaden()} />
    ) : (
      <Leer text="Wird geladen…" />
    );
  if (daten.dokumente.length === 0)
    return <Leer text="Es sind noch keine Unterlagen aufgenommen." />;

  // Unsichere Fälle stehen oben; nichts wird vergraben.
  const sortiert = [...daten.dokumente].sort(
    (a, b) => Number(b.typ_unklar) - Number(a.typ_unklar),
  );

  return (
    <div className={stil.stapel}>
      {sortiert.map((dokument) => (
        <DokumentZeile
          key={dokument.id}
          vorgangId={vorgangId}
          dokument={dokument}
          onAenderung={onAenderung}
        />
      ))}
    </div>
  );
}

function DokumentZeile({
  vorgangId,
  dokument,
  onAenderung,
}: {
  vorgangId: string;
  dokument: Dokument;
  onAenderung: () => void;
}) {
  const [typ, setTyp] = useState(dokument.typ ?? "");
  const [fehler, setFehler] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState(false);

  const klasse =
    dokument.qualitaet === "unbrauchbar"
      ? "balken-kritisch"
      : dokument.typ_unklar
        ? "balken-entwurf"
        : "balken-bestaetigt";

  return (
    <div className={`balken ${klasse} ${stil.dokument}`}>
      <div className={stil.dokumentKopf}>
        <strong>{dokument.dateiname}</strong>
        {dokument.typ_unklar && (
          <span className="chip chip-entwurf">unklar · bitte einordnen</span>
        )}
        {dokument.qualitaet === "unbrauchbar" && (
          <span className="chip chip-kritisch">nicht auswertbar</span>
        )}
        {dokument.quelle === "extern" && (
          <span className="chip chip-bestaetigt">extern</span>
        )}
      </div>

      {dokument.namensvorschlag && (
        <div className={stil.vorschlag}>
          <span className="label">Benennungsvorschlag</span>{" "}
          {dokument.namensvorschlag}
        </div>
      )}
      {dokument.zusammenfassung && (
        <p className={stil.fliess}>{dokument.zusammenfassung}</p>
      )}
      {dokument.fehler && <p className={stil.fliess}>{dokument.fehler}</p>}

      <div className={stil.aktion}>
        <input
          value={typ}
          onChange={(e) => setTyp(e.target.value)}
          placeholder="Dokumenttyp"
          aria-label="Dokumenttyp"
        />
        <button
          className="knopf-sekundaer"
          disabled={!typ.trim() || typ === dokument.typ || laeuft}
          onClick={async () => {
            setLaeuft(true);
            setFehler(null);
            try {
              await api.dokumentAendern(vorgangId, dokument.id, {
                typ: typ.trim(),
              });
              onAenderung();
            } catch (ausnahme) {
              setFehler(
                ausnahme instanceof BackendFehler
                  ? ausnahme.message
                  : "Der Typ konnte nicht übernommen werden.",
              );
            } finally {
              setLaeuft(false);
            }
          }}
        >
          {laeuft ? "Wird übernommen…" : "Typ übernehmen"}
        </button>
      </div>
      {fehler && <Fehlerband text={fehler} />}
    </div>
  );
}

// -- Projektdaten ---------------------------------------------------------

function Projektdaten({
  vorgangId,
  stand,
  onAenderung,
}: {
  vorgangId: string;
  stand: number;
  onAenderung: () => void;
}) {
  const { daten, fehler, neuLaden } = useDaten(
    () => api.fakten(vorgangId),
    stand,
  );
  if (!daten)
    return fehler ? (
      <Fehlerband text={fehler} onErneut={() => void neuLaden()} />
    ) : (
      <Leer text="Wird geladen…" />
    );

  const gruppen = daten.kategorien
    .map((kategorie) => ({
      kategorie,
      fakten: daten.fakten.filter((fakt) => fakt.kategorie === kategorie),
    }))
    .filter((gruppe) => gruppe.fakten.length > 0);

  return (
    <div className={stil.stapelWeit}>
      {gruppen.map((gruppe) => (
        <div key={gruppe.kategorie}>
          <span className="label">{gruppe.kategorie}</span>
          <div className={stil.stapel} style={{ marginTop: "0.35rem" }}>
            {gruppe.fakten.map((fakt) => (
              <FaktZeile
                key={fakt.schluessel}
                vorgangId={vorgangId}
                fakt={fakt}
                onBestaetigt={onAenderung}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function FaktZeile({
  vorgangId,
  fakt,
  onBestaetigt,
}: {
  vorgangId: string;
  fakt: Fakt;
  onBestaetigt: () => void;
}) {
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const klasse =
    fakt.status === "bestaetigt"
      ? "balken-bestaetigt"
      : fakt.status === "konflikt"
        ? "balken-kritisch"
        : fakt.status === "ki_entwurf"
          ? "balken-entwurf"
          : "";

  const quelle = fakt.herkunft[0];

  return (
    <div className={`balken ${klasse} ${stil.fakt}`}>
      <div className={stil.faktOben}>
        <span className={stil.faktName}>{fakt.bezeichnung}</span>
        <span className={stil.faktWert}>
          {fakt.wert ? `${fakt.wert} ${fakt.einheit}`.trim() : "—"}
        </span>
      </div>
      <div className={stil.faktUnten}>
        {fakt.status === "ki_entwurf" && (
          <span className="chip chip-entwurf">KI-Entwurf</span>
        )}
        {fakt.status === "bestaetigt" && (
          <span className="chip chip-bestaetigt">bestätigt</span>
        )}
        {fakt.status === "konflikt" && (
          <span className="chip chip-kritisch">Widerspruch</span>
        )}
        {fakt.status === "offen" && !fakt.wert && (
          <span className="chip chip-bestaetigt">von Ihnen einzutragen</span>
        )}
        {quelle && (
          <span className={stil.faktQuelle}>
            {quelle.dateiname}
            {quelle.seite ? `, S. ${quelle.seite}` : ""}
          </span>
        )}
        {fakt.status !== "bestaetigt" && fakt.wert && (
          <button
            className="knopf-leise"
            disabled={laeuft}
            onClick={async () => {
              setLaeuft(true);
              setFehler(null);
              try {
                await api.faktBestaetigen(vorgangId, fakt.schluessel);
                onBestaetigt();
              } catch (ausnahme) {
                setFehler(
                  ausnahme instanceof BackendFehler
                    ? ausnahme.message
                    : "Die Angabe konnte nicht bestätigt werden.",
                );
              } finally {
                setLaeuft(false);
              }
            }}
          >
            {laeuft ? "…" : "Bestätigen"}
          </button>
        )}
      </div>
      {quelle?.zitat && (
        // Das Zitat ist der Beleg des Produkts — es darf nicht in einem
        // Maus-Tooltip verschwinden, den Touch und Tastatur nie erreichen.
        <details className={stil.beleg}>
          <summary>Beleg anzeigen</summary>
          <blockquote>{quelle.zitat}</blockquote>
        </details>
      )}
      {fehler && <Fehlerband text={fehler} />}
    </div>
  );
}

// -- Widersprüche ---------------------------------------------------------

function Widersprueche({
  vorgangId,
  stand,
  onAenderung,
}: {
  vorgangId: string;
  stand: number;
  onAenderung: () => void;
}) {
  const { daten, fehler, neuLaden } = useDaten(
    () => api.konflikte(vorgangId),
    stand,
  );
  if (!daten)
    return fehler ? (
      <Fehlerband text={fehler} onErneut={() => void neuLaden()} />
    ) : (
      <Leer text="Wird geladen…" />
    );

  const offen = daten.konflikte.filter((konflikt) => !konflikt.geklaert);
  if (offen.length === 0)
    return <Leer text="Es sind keine Widersprüche offen." />;

  return (
    <div className={stil.stapel}>
      {offen.map((konflikt) => (
        <KonfliktKarte
          key={konflikt.id}
          vorgangId={vorgangId}
          konflikt={konflikt}
          onGeloest={onAenderung}
        />
      ))}
    </div>
  );
}

function KonfliktKarte({
  vorgangId,
  konflikt,
  onGeloest,
}: {
  vorgangId: string;
  konflikt: Konflikt;
  onGeloest: () => void;
}) {
  const [laeuft, setLaeuft] = useState(false);
  const [eigener, setEigener] = useState("");
  const [fehler, setFehler] = useState<string | null>(null);

  async function loesen(wert: string) {
    if (!wert.trim()) return;
    setLaeuft(true);
    setFehler(null);
    try {
      await api.konfliktLoesen(vorgangId, konflikt.id, wert.trim());
      onGeloest();
    } catch (ausnahme) {
      setFehler(
        ausnahme instanceof BackendFehler
          ? ausnahme.message
          : "Der Widerspruch konnte nicht geschlossen werden.",
      );
    } finally {
      setLaeuft(false);
    }
  }

  return (
    <div
      className={`balken ${
        konflikt.schweregrad === "kritisch"
          ? "balken-kritisch"
          : "balken-entwurf"
      } ${stil.konflikt}`}
    >
      <div className={stil.konfliktKopf}>
        <strong>{konflikt.bezeichnung}</strong>
        <span
          className={`chip ${
            konflikt.schweregrad === "kritisch"
              ? "chip-kritisch"
              : "chip-entwurf"
          }`}
        >
          {statusText(konflikt.schweregrad)}
        </span>
      </div>

      <div className={stil.werte}>
        {konflikt.werte.map((wert, index) => (
          <div key={index} className={stil.wert}>
            <span className="label">Wert {String.fromCharCode(65 + index)}</span>
            <div className={stil.wertZahl}>{wert.wert}</div>
            <div className={stil.wertQuelle}>
              {wert.dateiname}
              {wert.seite ? `, S. ${wert.seite}` : ""}
            </div>
          </div>
        ))}
      </div>

      {konflikt.hinweis && (
        <p className={stil.konfliktHinweis}>{konflikt.hinweis}</p>
      )}

      <div className={stil.knopfreihe}>
        {konflikt.werte.map((wert, index) => (
          <button
            key={index}
            className={`knopf-sekundaer ${stil.klein}`}
            disabled={laeuft}
            onClick={() => void loesen(wert.wert)}
          >
            {wert.wert} übernehmen
          </button>
        ))}
      </div>

      <div className={stil.knopfreihe}>
        <input
          value={eigener}
          onChange={(e) => setEigener(e.target.value)}
          placeholder="Eigener Wert"
          aria-label="Eigener Wert"
        />
        <button
          className={`knopf-sekundaer ${stil.klein}`}
          disabled={laeuft || !eigener.trim()}
          onClick={() => void loesen(eigener)}
        >
          Übernehmen
        </button>
      </div>
      {fehler && <Fehlerband text={fehler} />}
    </div>
  );
}

// -- Anforderungen --------------------------------------------------------

function Anforderungen({
  vorgangId,
  stand,
}: {
  vorgangId: string;
  stand: number;
}) {
  const { daten, fehler, neuLaden } = useDaten(
    () => api.anforderungen(vorgangId),
    stand,
  );
  if (!daten)
    return fehler ? (
      <Fehlerband text={fehler} onErneut={() => void neuLaden()} />
    ) : (
      <Leer text="Wird geladen…" />
    );

  const reihenfolge: Record<string, number> = {
    offen: 0,
    teilweise: 1,
    nicht_pruefbar: 2,
    belegt: 3,
  };
  const sortiert = [...daten.anforderungen].sort(
    (a, b) =>
      Number(b.pflicht) - Number(a.pflicht) ||
      reihenfolge[a.status] - reihenfolge[b.status],
  );

  return (
    <div className={stil.stapel}>
      {sortiert.map((anforderung: Anforderung) => (
        <div
          key={anforderung.id}
          className={`balken ${stil.anforderung} ${
            anforderung.status === "belegt"
              ? "balken-bereit"
              : anforderung.status === "teilweise"
                ? "balken-entwurf"
                : anforderung.pflicht
                  ? "balken-kritisch"
                  : ""
          }`}
        >
          <div className={stil.anforderungOben}>
            <span>{anforderung.bezeichnung}</span>
            <span
              className={`chip ${
                anforderung.status === "belegt"
                  ? "chip-bereit"
                  : anforderung.status === "teilweise"
                    ? "chip-entwurf"
                    : anforderung.pflicht
                      ? "chip-kritisch"
                      : "chip-bestaetigt"
              }`}
            >
              {statusText(anforderung.status)}
            </span>
          </div>
          <div className={stil.grundlage}>
            {anforderung.rechtsgrundlage}
            {!anforderung.pflicht && " · empfohlen"}
          </div>
          {anforderung.hinweis && (
            <div className={stil.grundlage}>{anforderung.hinweis}</div>
          )}
        </div>
      ))}
    </div>
  );
}

// -- Prüfung --------------------------------------------------------------

function Pruefung({
  vorgangId,
  stand,
  onAenderung,
}: {
  vorgangId: string;
  stand: number;
  onAenderung: () => void;
}) {
  const { daten, fehler, neuLaden } = useDaten(
    () => api.pruefung(vorgangId),
    stand,
  );
  const [paket, setPaket] = useState<string | null>(null);
  const [begruendung, setBegruendung] = useState("");
  const [aktionsfehler, setAktionsfehler] = useState<string | null>(null);
  const [friert, setFriert] = useState(false);

  if (!daten)
    return fehler ? (
      <Fehlerband text={fehler} onErneut={() => void neuLaden()} />
    ) : (
      <Leer text="Wird geladen…" />
    );

  return (
    <div className={stil.stapel}>
      {fehler && <Fehlerband text={fehler} onErneut={() => void neuLaden()} />}
      <div
        className={`alarm ${daten.freigabe_moeglich ? "" : "alarm-kritisch"}`}
      >
        <strong>
          {daten.freigabe_moeglich
            ? "Freigabe möglich."
            : "Freigabe gesperrt — kritische Befunde offen."}
        </strong>{" "}
        {daten.befunde.length} Befund(e).
        <div className={stil.pruefkopfKnoepfe}>
          <button className="knopf-sekundaer" onClick={() => void neuLaden()}>
            Erneut prüfen
          </button>
          <button
            className="knopf-primaer"
            disabled={!daten.freigabe_moeglich || friert}
            onClick={async () => {
              setFriert(true);
              setAktionsfehler(null);
              try {
                const ergebnis = await api.paketEinfrieren(vorgangId);
                setPaket(ergebnis.paket_hash);
                setBegruendung(ergebnis.begruendung);
                onAenderung();
              } catch (ausnahme) {
                setAktionsfehler(
                  ausnahme instanceof BackendFehler
                    ? ausnahme.message
                    : "Das Paket konnte nicht eingefroren werden.",
                );
              } finally {
                setFriert(false);
              }
            }}
          >
            {friert ? "Wird eingefroren…" : "Paket einfrieren"}
          </button>
        </div>
        {paket && (
          <div className={stil.pruefsumme}>
            Prüfsumme: {paket.slice(0, 32)}…
          </div>
        )}
        {begruendung && (
          <div style={{ marginTop: "0.4rem" }}>{begruendung}</div>
        )}
        {aktionsfehler && <Fehlerband text={aktionsfehler} />}
      </div>

      {daten.befunde.map((befund: Befund) => (
        <details
          key={befund.id}
          className={`balken ${stil.befund} ${
            befund.schweregrad === "kritisch"
              ? "balken-kritisch"
              : befund.schweregrad === "warnung"
                ? "balken-entwurf"
                : ""
          }`}
        >
          <summary>
            <span
              className={`chip ${
                befund.schweregrad === "kritisch"
                  ? "chip-kritisch"
                  : befund.schweregrad === "warnung"
                    ? "chip-entwurf"
                    : "chip-bestaetigt"
              }`}
            >
              {statusText(befund.schweregrad)}
            </span>{" "}
            {befund.beobachtung}
          </summary>
          <dl>
            {befund.grundlage && (
              <>
                <dt className="label">Grundlage</dt>
                <dd>{befund.grundlage}</dd>
              </>
            )}
            {befund.beleg && (
              <>
                <dt className="label">Beleg</dt>
                <dd>{befund.beleg}</dd>
              </>
            )}
            {befund.massnahme && (
              <>
                <dt className="label">Maßnahme</dt>
                <dd>{befund.massnahme}</dd>
              </>
            )}
          </dl>
        </details>
      ))}
    </div>
  );
}
