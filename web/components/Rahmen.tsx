"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import stil from "./Rahmen.module.css";

const NAVIGATION = [
  { href: "/", label: "Vorgänge" },
  { href: "/regelwerk", label: "Regel- und Formularstand" },
];

/** App shell: wordmark, navigation, and the person the work is attributed to.
 *  The sidebar collapses into a top bar below 900 px. */
export function Rahmen({ children }: { children: React.ReactNode }) {
  const pfad = usePathname();
  const [offen, setOffen] = useState(false);

  return (
    <div className={stil.huelle}>
      <aside className={`${stil.seitenleiste} ${offen ? stil.offen : ""}`}>
        <div className={stil.marke}>
          <Link href="/" onClick={() => setOffen(false)}>
            <span className={stil.markeName}>
              Digital
              <br />
              Deutschland
            </span>
          </Link>
          <div className="label" style={{ marginTop: "0.4rem" }}>
            Bauantragsassistenz
          </div>
          <button
            className={`knopf-leise ${stil.menue}`}
            onClick={() => setOffen((wert) => !wert)}
            aria-expanded={offen}
            aria-label={offen ? "Navigation schließen" : "Navigation öffnen"}
          >
            {offen ? "✕" : "☰"}
          </button>
        </div>

        <nav className={stil.navigation}>
          {NAVIGATION.map((eintrag) => {
            const aktiv =
              eintrag.href === "/"
                ? pfad === "/" || pfad.startsWith("/vorgang")
                : pfad.startsWith(eintrag.href);
            return (
              <Link
                key={eintrag.href}
                href={eintrag.href}
                className={`${stil.navEintrag} ${aktiv ? stil.aktiv : ""}`}
                onClick={() => setOffen(false)}
              >
                {eintrag.label}
              </Link>
            );
          })}
        </nav>

        <div className={stil.person}>
          <div className={stil.personKreis}>AM</div>
          <div>
            <div className={stil.personName}>Dr. Anna Müller</div>
            <div className="label">Architektin · bauvorlageberechtigt</div>
          </div>
        </div>
      </aside>

      <main className={stil.inhalt}>{children}</main>
    </div>
  );
}
