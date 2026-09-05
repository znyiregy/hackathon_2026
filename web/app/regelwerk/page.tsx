"use client";

import { Rahmen } from "@/components/Rahmen";
import stil from "./regelwerk.module.css";

/** Curated source register. This screen makes the product's honesty visible:
 *  every rule states where it came from and how long it was last verified. */
const QUELLEN = [
  {
    gegenstand: "BauO NRW — vereinfachtes Verfahren",
    fundstelle: "§ 64 BauO NRW",
    stand: "01.09.2026",
    geprueft: "05.09.2026",
    hinweis:
      "Dritte Änderung der BauO NRW 2018 („BauCode NRW“) in Kraft seit 01.09.2026.",
    frisch: true,
  },
  {
    gegenstand: "Elektronische Einreichung verpflichtend",
    fundstelle: "§ 70 Abs. 1 BauO NRW",
    stand: "01.09.2026",
    geprueft: "05.09.2026",
    hinweis:
      "Zugang ist das Bauportal.NRW. Digital Deutschland reicht nichts ein — das bleibt Ihre Handlung.",
    frisch: true,
  },
  {
    gegenstand: "Genehmigungsfiktion",
    fundstelle: "§ 74 BauO NRW n. F.",
    stand: "01.09.2026",
    geprueft: "05.09.2026",
    hinweis:
      "Vollständigkeit bei Einreichung wird finanziell entscheidend, weil Nachforderungen die Frist hemmen.",
    frisch: true,
  },
  {
    gegenstand: "Ferienwohnung ist kein Wohnen",
    fundstelle: "§ 13a BauNVO · BVerwG 4 C 5.16 vom 18.10.2017",
    stand: "18.10.2017",
    geprueft: "05.09.2026",
    hinweis:
      "Zulässigkeit hängt vom B-Plan bzw. § 34 BauGB ab. Das System behauptet nie Zulässigkeit.",
    frisch: false,
  },
  {
    gegenstand: "Zweckentfremdungssatzung Bonn",
    fundstelle: "Satzung der Bundesstadt Bonn, Fassung seit 01.07.2022",
    stand: "01.07.2022",
    geprueft: "05.09.2026",
    hinweis:
      "Erfasst Wohnraum insgesamt, einschließlich Eigenheimen und Eigentumswohnungen. Schwelle: 90 Tage im Kalenderjahr.",
    frisch: false,
  },
  {
    gegenstand: "Vordrucke zur VV BauPrüfVO",
    fundstelle: "Runderlass vom 15.12.2021, MBl. NRW 2022 Nr. 2",
    stand: "15.12.2021",
    geprueft: "05.09.2026",
    hinweis:
      "Neuausgabe für den BauCode steht aus. Formularstand vor Einreichung erneut prüfen.",
    frisch: false,
    warnung: true,
  },
];

export default function Regelwerk() {
  return (
    <Rahmen>
      <h1>Regel- und Formularstand</h1>
      <p className={stil.unterzeile}>
        Jede angewandte Regel mit Fundstelle, Gültigkeitsstand und letzter
        Prüfung. Was nicht verifizierbar ist, steht hier als nicht verifiziert.
      </p>

      <div className="alarm alarm-entwurf" style={{ margin: "1.2rem 0" }}>
        <strong>Kein Rechtsrat.</strong> Diese Angaben sind Input für die
        Antragsvorbereitung. Jede regulatorische Aussage muss von einer
        bauvorlageberechtigten Person geprüft werden.
      </div>

      <div className={stil.tabelleHuelle}>
        <table className={stil.tabelle}>
          <thead>
            <tr>
              <th>Gegenstand</th>
              <th>Fundstelle</th>
              <th>Stand</th>
              <th>Zuletzt geprüft</th>
            </tr>
          </thead>
          <tbody>
            {QUELLEN.map((quelle) => (
              <tr key={quelle.gegenstand}>
                <td>
                  <strong>{quelle.gegenstand}</strong>
                  {quelle.frisch && (
                    <span className="chip chip-entwurf" style={{ marginLeft: 6 }}>
                      neu seit 01.09.2026
                    </span>
                  )}
                  {quelle.warnung && (
                    <span className="chip chip-kritisch" style={{ marginLeft: 6 }}>
                      Neuausgabe erwartet
                    </span>
                  )}
                  <div className={stil.hinweis}>{quelle.hinweis}</div>
                </td>
                <td className={stil.mono}>{quelle.fundstelle}</td>
                <td className={stil.mono}>{quelle.stand}</td>
                <td className={stil.mono}>{quelle.geprueft}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Rahmen>
  );
}
