"use client";

import { useEffect, useRef, useState } from "react";

import {
  api,
  BackendFehler,
  dateiLesen,
  type AssistentNachricht,
} from "@/lib/api";
import stil from "./Assistent.module.css";

interface Eintrag {
  rolle: "architektin" | "assistent" | "werkzeug" | "system";
  inhalt: string;
  werkzeug?: string | null;
}

const WERKZEUG_TEXT: Record<string, string> = {
  vorgangsstand: "Nachgesehen, wie das Projekt steht",
  widersprueche: "Nachgesehen, was nicht zusammenpasst",
  offene_projektdaten: "Nachgesehen, welche Angaben fehlen",
  fehlende_unterlagen: "Nachgesehen, welche Unterlagen fehlen",
  dokumentenliste: "Die Unterlagen durchgesehen",
  fakt_bestaetigen: "Angabe bestätigt",
  widerspruch_loesen: "Unstimmigkeit geklärt",
  upload_link_erzeugen: "Link zum Hochladen erstellt",
  einreichungspruefung_ausfuehren: "Alles noch einmal durchgeprüft",
};

const ERSTE_FRAGE =
  "Guten Tag. Ziehen Sie Ihre Unterlagen einfach hier hinein. " +
  "Ich lese jede Datei und sage Ihnen danach, was noch fehlt.";

const VORSCHLAEGE = [
  "Wie steht es gerade?",
  "Was fehlt noch?",
  "Wo passt etwas nicht zusammen?",
  "Prüf bitte alles durch.",
];

export function Assistent({
  vorgangId,
  onAenderung,
}: {
  vorgangId: string;
  onAenderung: () => void;
}) {
  const [verlauf, setVerlauf] = useState<Eintrag[]>([
    { rolle: "assistent", inhalt: ERSTE_FRAGE },
  ]);
  const [eingabe, setEingabe] = useState("");
  const [laeuft, setLaeuft] = useState(false);
  const [phase, setPhase] = useState("");
  const [ueberzogen, setUeberzogen] = useState(false);
  const endeRef = useRef<HTMLDivElement>(null);
  const dateiRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const sanft = !window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    endeRef.current?.scrollIntoView({
      behavior: sanft ? "smooth" : "auto",
      block: "nearest",
    });
  }, [verlauf, laeuft]);

  function anhaengen(eintrag: Eintrag) {
    setVerlauf((bisher) => [...bisher, eintrag]);
  }

  async function senden(text: string) {
    const nachricht = text.trim();
    if (!nachricht || laeuft) return;
    anhaengen({ rolle: "architektin", inhalt: nachricht });
    setEingabe("");
    setLaeuft(true);
    setPhase("Denkt nach");
    try {
      const antwort = await api.assistent(vorgangId, nachricht);
      for (const teil of antwort.nachrichten as AssistentNachricht[]) {
        if (teil.rolle === "werkzeug") {
          anhaengen({
            rolle: "werkzeug",
            inhalt:
              WERKZEUG_TEXT[teil.werkzeug ?? ""] ??
              `Werkzeug ${teil.werkzeug ?? ""} ausgeführt`,
            werkzeug: teil.werkzeug,
          });
        } else {
          anhaengen({ rolle: "assistent", inhalt: teil.inhalt });
        }
      }
      onAenderung();
    } catch (ausnahme) {
      anhaengen({
        rolle: "system",
        inhalt:
          ausnahme instanceof BackendFehler
            ? ausnahme.message
            : "Der Assistent konnte nicht antworten.",
      });
    } finally {
      setLaeuft(false);
      setPhase("");
    }
  }

  async function dateienAufnehmen(dateien: FileList | null) {
    if (!dateien || dateien.length === 0 || laeuft) return;
    const liste = Array.from(dateien);
    setLaeuft(true);
    try {
      setPhase(`Liest ${liste.length} Datei(en)`);
      const gelesen = await Promise.all(liste.map(dateiLesen));
      const ergebnis = await api.hochladen(vorgangId, gelesen);
      onAenderung();

      // Die Erfolgsmeldung entsteht erst hier — sonst behauptet der Verlauf
      // einen Upload, der gerade fehlgeschlagen ist.
      anhaengen({
        rolle: "architektin",
        inhalt: `${liste.length} Datei(en) hochgeladen: ${liste
          .map((datei) => datei.name)
          .join(", ")}`,
      });

      for (const abgelehnt of ergebnis.abgelehnt ?? []) {
        anhaengen({
          rolle: "system",
          inhalt: `${abgelehnt.name} konnte ich nicht lesen: ${abgelehnt.grund}`,
        });
      }

      const hochgeladen = new Set(liste.map((datei) => datei.name));
      for (const dokument of ergebnis.dokumente) {
        if (!hochgeladen.has(dokument.dateiname)) continue;
        const typ = dokument.typ_unklar
          ? "Was ist das? Bitte kurz sagen"
          : (dokument.typ ?? "unbekannt");
        anhaengen({
          rolle: "werkzeug",
          inhalt: `${dokument.dateiname} → ${typ}`,
        });
      }

      setPhase("Wertet aus");
      await senden(
        "Ich habe gerade Unterlagen hochgeladen. Was hat sich geändert, und " +
          "was soll ich als Nächstes tun?",
      );
    } catch (ausnahme) {
      anhaengen({
        rolle: "system",
        inhalt:
          ausnahme instanceof BackendFehler
            ? ausnahme.message
            : "Die Dateien konnten nicht gelesen werden.",
      });
      setLaeuft(false);
      setPhase("");
    } finally {
      if (dateiRef.current) dateiRef.current.value = "";
    }
  }

  return (
    <section
      className={`${stil.assistent} ${ueberzogen ? stil.ueberzogen : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setUeberzogen(true);
      }}
      onDragLeave={(e) => {
        // Ohne diese Prüfung flackert die Hervorhebung über jedem Kindelement.
        if (!e.currentTarget.contains(e.relatedTarget as Node | null)) {
          setUeberzogen(false);
        }
      }}
      onDrop={(e) => {
        e.preventDefault();
        setUeberzogen(false);
        void dateienAufnehmen(e.dataTransfer.files);
      }}
    >
      <header className={stil.kopf}>
        <span className="label">Assistent</span>
        <span className={stil.hinweis}>
          Sie bestätigen jede Angabe · nichts geht von allein ans Amt
        </span>
      </header>

      <div className={stil.verlauf} role="log" aria-live="polite" aria-relevant="additions text">
        {verlauf.map((eintrag, index) => (
          <Blase key={index} eintrag={eintrag} />
        ))}
        {laeuft && (
          <div className={stil.phase} role="status" aria-live="polite">
            <span className="tippen">
              <span />
              <span />
              <span />
            </span>
            {phase || "Arbeitet"}…
          </div>
        )}
        <div ref={endeRef} />
      </div>

      {verlauf.length <= 2 && !laeuft && (
        <div className={stil.vorschlaege}>
          {VORSCHLAEGE.map((vorschlag) => (
            <button
              key={vorschlag}
              className={`knopf-sekundaer ${stil.klein}`}
              onClick={() => void senden(vorschlag)}
            >
              {vorschlag}
            </button>
          ))}
        </div>
      )}

      <form
        className={stil.eingabezeile}
        onSubmit={(e) => {
          e.preventDefault();
          void senden(eingabe);
        }}
      >
        <button
          type="button"
          className={`knopf-sekundaer ${stil.anhang}`}
          onClick={() => dateiRef.current?.click()}
          disabled={laeuft}
          aria-label="Dateien hochladen"
          title="Dateien hochladen"
        >
          ＋
        </button>
        <input
          ref={dateiRef}
          type="file"
          multiple
          accept=".pdf,.png,.jpg,.jpeg,.txt,.md,.csv,.json"
          hidden
          onChange={(e) => void dateienAufnehmen(e.target.files)}
        />
        <textarea
          value={eingabe}
          onChange={(e) => setEingabe(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void senden(eingabe);
            }
          }}
          placeholder="Frage stellen…"
          rows={1}
          readOnly={laeuft}
          aria-busy={laeuft}
        />
        <button
          className="knopf-primaer"
          type="submit"
          disabled={laeuft || !eingabe.trim()}
        >
          Senden
        </button>
      </form>
    </section>
  );
}

function Blase({ eintrag }: { eintrag: Eintrag }) {
  if (eintrag.rolle === "werkzeug") {
    return (
      <div className={stil.werkzeug}>
        <span className="label">✓ {eintrag.inhalt}</span>
      </div>
    );
  }

  if (eintrag.rolle === "system") {
    return (
      <div className="alarm alarm-kritisch" role="alert">
        {eintrag.inhalt}
      </div>
    );
  }

  const eigen = eintrag.rolle === "architektin";
  return (
    <div className={`${stil.blase} ${eigen ? stil.eigen : stil.fremd}`}>
      {eintrag.inhalt}
    </div>
  );
}
