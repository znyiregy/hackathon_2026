# DIGITAL DEUTSCHLAND
## Produkt-, UX-, KI- und Technik-Blueprint

**Version:** 1.0 · **Stand:** 5. September 2026 · **Umfang:** MVP — Nutzungsänderung Wohnnutzung → Ferienhaus, Bonn / NRW

> **Bitte zuerst lesen.** Vor vier Tagen, am 1. September 2026, hat sich die rechtliche und verfahrensmäßige Grundlage dieses MVP verschoben. Das *Dritte Gesetz zur Änderung der BauO NRW 2018* („BauCode NRW“) ist in Kraft getreten, die elektronische Einreichung ist nach § 70 BauO NRW verpflichtend geworden, eine Genehmigungsfiktion wurde eingeführt und die Genehmigungsfreistellung wurde ausgeweitet. Jeder Blueprint, der auf Annahmen von vor September beruht, ist in Teilen bereits überholt. Teil 0 erklärt, was das ändert — und es ändert das Produkt, nicht nur dessen Inhalt.
>
> Alles in diesem Dokument, was deutsches Recht berührt, ist **Input für die Produktgestaltung, keine Rechtsberatung**. Jede regulatorische Aussage hier muss von einer bauvorlageberechtigten Person überprüft werden, bevor sie im Produkt kodiert wird.

---

# TEIL 0 — WAS SICH AM 1. SEPTEMBER 2026 GEÄNDERT HAT (VOR TEIL 1 LESEN)

Drei Änderungen sind so gewichtig, dass sie das Produkt umformen.

**1. Die elektronische Einreichung ist jetzt Pflicht.** Seit dem 1. September 2026 verlangt § 70 Abs. 1 BauO NRW, den Bauantrag bei der unteren Bauaufsichtsbehörde elektronisch einzureichen; hat die Behörde einen elektronischen Zugang eröffnet, ist ausschließlich dieser zu nutzen. In NRW ist der Zugang das Bauportal.NRW (EfA-Dienst „Digitale Baugenehmigung“) mit Authentifizierung über BundID oder Mein Unternehmenskonto. Mehrere NRW-Behörden nehmen bereits gar keine Papieranträge mehr an. Unterschriften entfallen zugunsten klar benannter Verantwortlicher.

**Produktkonsequenz — das ist die wichtigste strategische Erkenntnis dieses Dokuments.** Das MVP, wie es in der Vorlage beschrieben ist, endet bei *„PDF-Formulare und Einreichungspaket erzeugen“*. Dieser Output verliert rapide an Wert. Die Architektin wird Ihr PDF nicht ausdrucken und zur Post bringen; sie wird die Daten in einen Portalassistenten neu eintippen, der eine eigene Feldstruktur, eigene Validierungen und eigene Upload-Regeln hat. Erzeugt Digital Deutschland ein schönes PDF-Paket, macht die Architektin die Portalarbeit trotzdem ein zweites Mal.

Digital Deutschland muss deshalb als **Vorbereitungs- und Qualitätssicherungsschicht vor dem Bauportal.NRW** positioniert werden, nicht als Formulargenerator. Seine Outputs sind:

- ein **validierter, strukturierter Datensatz**, dessen Felder 1:1 auf die Felder des Portalassistenten abbilden, aufbereitet als kopierfertiges „Portal-Übertragungsblatt“ (später als XBau-kompatibler Export);
- ein **Bauvorlagenpaket** in den Formaten, Benennungen und PDF/A-Konventionen, die das Portal akzeptiert;
- das **Vollständigkeits- und Konsistenzurteil**, das darüber entscheidet, ob der Upload eine Nachforderung auslöst.

Das ist eine *bessere* Position als Formularerzeugung, denn das Portal erzeugt Formulare bereits — und wird niemals dokumentübergreifende Widerspruchsfreiheit prüfen.

**2. Genehmigungsfiktion (§ 74 BauO NRW n.F.).** Im vereinfachten Verfahren gilt die Genehmigung unter bestimmten, von der Bauherrschaft bestimmten Bedingungen als erteilt, wenn die Behörde nicht innerhalb der gesetzlichen Frist entscheidet. Auf die Fiktion kann per Erklärung verzichtet werden.

**Produktkonsequenz:** Vollständigkeit im Moment der Einreichung wird finanziell entscheidend, weil ein unvollständiger Antrag die Frist über Nachforderungen zurücksetzt oder hemmt. Der Wert der Frage „löst das eine Rückfrage aus?“ steigt deutlich. Das ist Rückenwind für USP 2 — und es ist das Verkaufsargument: *Jede Nachforderung kostet Wochen einer Fiktionsfrist, die gerade wertvoll geworden ist.* Es eröffnet zugleich eine spätere Produktfläche: **Fristenberechnung und Fiktionsüberwachung.**

**3. Erweiterte Genehmigungsfreistellung (§ 63 BauO NRW n.F.).** Mehr Vorhaben sind genehmigungsfrei, darunter Umbauten und Dachgeschossänderungen im unbeplanten Innenbereich. §§ 47 und 59 erleichtern die Umnutzung von Bestandsgebäuden.

**Produktkonsequenz:** Die *erste* Frage des Produkts lautet nicht mehr „wie füllen wir den Antrag aus?“, sondern **„welches Verfahren gilt überhaupt — verfahrensfrei, Genehmigungsfreistellung, vereinfachtes Verfahren oder volles Verfahren?“** Eine Nutzungsänderung Wohnen → Ferienhaus wird fast immer im vereinfachten Verfahren landen (weil für die neue Nutzung andere öffentlich-rechtliche Anforderungen in Betracht kommen als für die bisherige — Stellplätze, Brandschutz, planungsrechtliche Kategorie — genau der Test, der Nutzungsänderungen selten verfahrensfrei macht). Das Produkt muss das aber **feststellen**, nicht unterstellen.

**4. Die Formulare sind gerade in Bewegung.** Die Vordrucke zur VV BauPrüfVO wurden als Anlagen zu einem Runderlass vom 15. Dezember 2021 veröffentlicht (MBl. NRW 2022 Nr. 2). Ob und wann sie für den BauCode neu herausgegeben werden, ist genau die Art von Änderung, die in den nächsten Wochen still passieren wird. Die Architektenkammer NRW stellt die aktuellen Formulare bereit und hat auf die Änderung hingewiesen. Es gibt keine bessere Live-Demonstration von USP 3 als diesen Moment.

---

# TEIL 1 — MANAGEMENT SUMMARY

Digital Deutschland ist eine KI-gestützte Vorbereitungs- und Qualitätssicherungsschicht für die Verwaltungsarbeit deutscher Architekturbüros. Sie nimmt das unstrukturierte Ausgangsmaterial eines Projekts — abfotografierte Baugenehmigungen aus den 1960ern, eingescannte Grundrisse, Wohnflächenberechnungen in Word, E-Mails vom Bauamt, einen Grundbuchauszug, den die Eigentümerin als vier Handyfotos geschickt hat — und macht daraus einen kleinen Satz **geprüfter Projektfakten mit Herkunftsnachweis**. Auf dieser Grundlage beantwortet sie die einzigen drei Fragen, die über den Erfolg eines Antrags entscheiden:

1. **Ist er vollständig?** Welche Bauvorlagen und Nachweise verlangt *dieses* Verfahren, welche liegen vor, welche fehlen?
2. **Ist er widerspruchsfrei?** Sagen Antrag, Pläne, Grundstücksunterlagen und Beschreibungen dasselbe über Eigentümer, Flurstück, Flächen und geplante Nutzung?
3. **Ist er aktuell — und ist es das ganze Bild?** Werden die geltenden Regeln und die aktuellen Formulare verwendet — und wurden alle Parallelverfahren erkannt, nicht nur das eine, nach dem gefragt wurde?

Das MVP belegt das an einem bewusst engen, real schmerzhaften Fall: **Umnutzung einer Wohneinheit in Bonn zur Ferienhausnutzung.**

Dieser Fall ist gut gewählt — aus einem Grund, den die Vorlage unterschätzt. In Bonn ist das nicht ein Antrag. Es ist eine **Konstellation**: eine bauordnungsrechtliche Nutzungsänderung beim Bauaufsichtsamt, eine planungsrechtliche Zulässigkeitsfrage (eine Ferienwohnung ist rechtlich *kein* Wohnen), eine **Zweckentfremdungsgenehmigung** beim Amt für Soziales und Wohnen nach der Bonner Zweckentfremdungssatzung, eine **Wohnraum-Identitätsnummer** und — in einer Wohnungseigentümergemeinschaft — eine privatrechtliche Zustimmungsfrage, die keine Behörde je aufwerfen wird, die das Projekt aber nach der Genehmigung zerstören kann.

Wer nur den Bauantrag vorbereitet, kann ihn genehmigt bekommen und trotzdem einen Bauherrn haben, der nicht vermieten darf. **Diese Lücke ist der am besten verteidigbare Wert von Digital Deutschland.** Kein Dokumentenmanagement-Produkt und kein Portal schließt sie.

**Das Versprechen:** *Digital Deutschland macht aus unstrukturierten Projektinformationen einen widerspruchsfreien, vollständigen, portalreifen Antrag — und sagt der Architektin, was die Behörde (und die andere Behörde, an die niemand gedacht hat) fragen wird.*

---

# TEIL 2 — PRODUKTVISION

Das langfristige Produkt ist eine **administrative Betriebsschicht für deutsche Architekturbüros**: das System, das festhält, was an einem Projekt wahr ist, weiß, was jedes Verfahren verlangt, und die Arbeit des Büros prüft, bevor eine Behörde es tut.

Drei Eigenschaften definieren es — und sie sollten ab dem ersten Commit gelten:

**Fakten, nicht Dateien, sind das primäre Objekt.** Dokumente sind Belege. Der dauerhafte Wert ist die geprüfte, belegte Aussage — *„Flurstück 143/2, Gemarkung Dottendorf, Flur 12, aus der Liegenschaftskarte vom 12.03.2024, Seite 1, bestätigt durch die Architektin am 04.09.2026.“* Jede nachgelagerte Fähigkeit (Antragserzeugung, Konflikterkennung, Prüfung, spätere Verfahren, spätere Projekte am selben Grundstück) konsumiert Fakten.

**Anforderungen werden modelliert, nicht geprompted.** Für jedes Verfahren hält das System ein maschinenlesbares Anforderungsmodell: welche Dokumente, welche Fakten, welche Bedingungen — mit Quellenangabe und Gültigkeitsdatum. Das ist ein kuratierter Bestand, von Menschen gepflegt, versioniert wie Code. Es ist der Burggraben — und der Grund, warum das Produkt nicht degradiert, wenn sich das Modell ändert.

**Aufgabe der KI sind Extraktion und Formulierung; Aufgabe des Systems sind Vergleich und Urteil.** LLMs lesen Dokumente und formulieren Befunde. Deterministischer Code vergleicht Werte, wertet Regeln aus und entscheidet über Schweregrade. Diese Trennung macht das Produkt vertrauenswürdig genug für haftungsrelevante Arbeit.

Ausbaupfade in kaufmännisch sinnvoller Reihenfolge: weitere Nutzungsänderungen → Bauvoranfragen und Vorbescheide → vollständige Bauanträge → weitere Kommunen in Rhein-Sieg / Köln-Bonn → Nachforderungsbearbeitung sowie Fristen- und Fiktionsüberwachung → XBau-native Einreichung.

---

# TEIL 3 — MVP-DEFINITION

## 3.1 Das MVP in einem Absatz

Für ein Ein- oder Mehrfamilienhaus in Bonn, das als Ferienhaus / Ferienwohnung genutzt werden soll, nimmt Digital Deutschland die Projektunterlagen auf, extrahiert und verifiziert rund 30 Projektfakten mit Herkunftsnachweis, bestimmt die einschlägige Bonner Genehmigungskonstellation, prüft die Vollständigkeit gegen ein kuratiertes Anforderungsmodell, erkennt Widersprüche über alle Dokumente und erzeugten Inhalte hinweg, erstellt ein Portal-Übertragungsblatt sowie Entwürfe für Betriebs- und Nutzungsbeschreibung, verifiziert Formular- und Regelstand gegen ein kuratiertes Quellenregister und führt eine strukturierte Vor-Einreichungsprüfung durch, die genau benennt, was eine Behörde voraussichtlich rückfragen würde.

## 3.2 Die Genehmigungskonstellation, die das MVP modellieren muss

| # | Strang | Behörde (Bonn) | Auslöser | Behandlung im MVP |
|---|---|---|---|---|
| 1 | Bauordnungsrechtliche Nutzungsänderung | Bauaufsichtsamt / Bauordnungsamt | Neue Nutzung wird an anderen öffentlich-rechtlichen Anforderungen gemessen als die bisherige | **Vollständig**: Fakten, Vollständigkeit, Erzeugung, Prüfung |
| 2 | Bauplanungsrechtliche Zulässigkeit | über 1, ggf. Stadtplanungsamt | Ferienwohnung ist kein Wohnen (§ 13a BauNVO; BVerwG 4 C 5.16 vom 18.10.2017); Zulässigkeit hängt vom B-Plan bzw. § 34 BauGB ab, häufig Ausnahme oder Befreiung (§ 31 BauGB) erforderlich | **Vollständig als Risikobewertung**: Regime bestimmen, Frage markieren, Begründungsgerüst entwerfen. Niemals Zulässigkeit behaupten. |
| 3 | Zweckentfremdung | Amt für Soziales und Wohnen (50-52), Abt. Wohnen | Bonner Zweckentfremdungssatzung: Kurzzeitvermietung für mehr als drei Monate, längstens 90 Tage im Kalenderjahr, ist Zweckentfremdung und genehmigungspflichtig; seit 1. Juli 2022 erfasst die Satzung Wohnraum insgesamt, einschließlich Eigenheimen und Eigentumswohnungen | **Erkennen und quantifizieren**: deterministische Regel auf geplante Vermietungstage, Anforderungscheckliste, Negativattest-Option. Keine Erzeugung im MVP. |
| 4 | Wohnraum-Identitätsnummer | dieselbe | Anzeige-/Registrierungspflicht vor Überlassung; muss in jedem Inserat sichtbar angegeben werden | **Checklistenpunkt + expliziter Hinweis** |
| 5 | Privatrecht (WEG / Teilungserklärung, Miteigentum, Erbengemeinschaft) | keine | Eine Genehmigung überwindet weder Teilungserklärung noch Rechte der Miteigentümer | **Risikohinweis mit Belegdokument** |
| 6 | Gewerbe, Beherbergungs-/Übernachtungsabgabe, Meldepflichten | verschiedene | Gewerbliche Vermietung | **Hinweisblatt „Folgepflichten“**, keine Automatisierung |

Stränge 1 und 2 sind das MVP-Produkt. Strang 3 ist eine **erstklassige deterministische Checkliste**, weil dort der Bauherr real Schaden nimmt und weil die Regel sauber kodierbar ist. Stränge 4–6 sind einseitige Hinweise mit Quellenangabe.

**Warum dieser Zuschnitt richtig ist:** Er hält das Engineering auf einer Erzeugungspipeline fokussiert und fängt zugleich die Erkenntnis ein, die das Produkt fachkundig statt bürokratisch wirken lässt. Eine Architektin, die liest „Sie haben den Bauantrag im Griff — aber ohne Zweckentfremdungsgenehmigung darf Ihr Bauherr ab Tag 91 nicht vermieten“, wird dem Rest des Produkts glauben.

## 3.3 Ausdrückliche MVP-Grenzen

- **Nur Bonn.** Nicht NRW, nicht Deutschland. Anforderungs- und Quellenmodelle sind kommunenspezifisch und handkuratiert.
- **Ein Verfahrensfokus:** vereinfachtes Baugenehmigungsverfahren (§ 64). Das System **stellt fest**, ob der Fall außerhalb liegt (großer Sonderbau, z. B. Beherbergungsstätte oberhalb der Schwellen) und **hält dann mit Erklärung an**, statt zu erzeugen.
- **Keine Einreichung.** Digital Deutschland übermittelt niemals etwas an eine Behörde.
- **Keine rechtlichen Schlussfolgerungen.** Das System nennt Anforderungen, Belege und offene Fragen. Es sagt nie, dass etwas zulässig oder genehmigungsfähig ist.
- **Ein Mandant pro Büro im Datenmodell, ein Büro im Pilotbetrieb.**

## 3.4 Eine Alternative, die zehn Minuten Diskussion wert ist

> **ANNAHME HINTERFRAGT — ist der Bauantrag das richtige erste Artefakt?**
>
> Bei Wohnen → Ferienhaus ist das entscheidende Risiko nicht die formale Vollständigkeit, sondern die **planungsrechtliche Zulässigkeit**. Setzt der B-Plan ein reines oder allgemeines Wohngebiet fest und lässt die Nutzung nicht zu, rettet kein noch so guter Antrag das Projekt. Architekten begegnen dem mit einer **Bauvoranfrage / einem Vorbescheid (§ 77 BauO NRW)** — einer viel kleineren Einreichung, die eine einzige verbindliche Frage beantwortet.
>
> Ein „Voranfrage-first“-MVP wäre rund 40 % des Bauumfangs (kein vollständiger Bauvorlagensatz, kein Erhebungsbogen, deutlich weniger Erzeugung), würde dieselben drei USPs liefern und träfe den Moment, in dem die Architektin am unsichersten und am wenigsten bereit ist, Stunden zu investieren.
>
> **Empfehlung:** Anforderungsmodell und Fakten-/Konfliktkern so bauen, dass *beide* Verfahren Konfigurationen derselben Engine sind — und die Voranfrage-Konfiguration zuerst ausliefern, falls das Pilotbüro bestätigt, dass Voranfragen in seiner Ferienwohnungsarbeit häufig sind. Diese Entscheidung fällt im ersten Pilotgespräch, nicht im Code.

---

# TEIL 4 — NUTZERPROFILE

**Anja, 41 — Projektarchitektin (Hauptnutzerin).** Führt 6–12 parallele Vorgänge. Bauvorlageberechtigt, also persönlich haftend für das, was sie unterschreibt. Ihr eigentliches Problem ist nicht die Ablage, sondern *„was übersehe ich, und was werden sie fragen?“* Sie hat eine Nachforderung erlebt, die sechs Wochen gekostet hat. Sie verwirft jedes Werkzeug, das ihr je selbstbewusst etwas Falsches gesagt hat. Sie arbeitet auf Deutsch. Sie liest kein Dashboard; sie liest eine Ausnahmeliste.

**Gestaltungsfolge:** Die Oberfläche muss eine Ausnahmeliste sein, kein Statusbildschirm. Jede KI-Aussage muss einen Klick von ihrer Quelle entfernt sein. Das System muss sichtbar bereit sein zu sagen: „Ich weiß es nicht.“

**Markus, 56 — Büroinhaber (Käufer).** Interessiert sich für Kapazität, Haftung und dafür, ob neue Mitarbeitende Einreichungen in Partnerqualität erzeugen können. Kauft „weniger Rückfragen“, nicht „KI“. Fragt im ersten Gespräch: *Wo liegen die Daten, wer verarbeitet sie, und was passiert, wenn etwas falsch ist?* Die DSGVO- und Haftungsantwort muss vor der Demo stehen.

**Bauzeichnerin / Werkstudent — die tatsächlich hochladende Person.** Erledigt Aufnahme und Benennung. Profitiert am meisten von Automatisierung, hat die geringste Befugnis, KI-Ergebnisse zu akzeptieren. **Gestaltungsfolge:** Das Freigabemodell muss trennen zwischen *wer hochladen und korrigieren darf* und *wer einen Fakt bestätigen und ein Paket freigeben darf*.

**Frau Weber, 68 — Eigentümerin (externe Beitragende).** Schickt um 22:40 vier Handyfotos eines Grundbuchauszugs, auf dem Kopf, mit Daumen im Bild. Sie darf das Wort „Konflikt“ nie sehen. Ihre Oberfläche ist ein Bildschirm, große Schaltflächen, ausschließlich Deutsch.

**Der Behördenprüfer (simuliert, nie imitiert).** Ein Sachbearbeiter mit Warteschlange, einer aus BauPrüfVO und interner Praxis abgeleiteten Prüfliste und einem starken Anreiz, eine gebündelte Nachforderung zu stellen, statt um Unklarheiten herumzudenken. **Gestaltungsfolge:** Simuliert werden *Prüfliste und Anreiz*, nicht die Person. Die richtige Frage lautet nie „was würde ein strenger Beamter sagen?“, sondern „welcher Punkt der Prüfliste lässt sich aus diesen Unterlagen nicht abhaken?“

---

# TEIL 5 — DURCHGÄNGIGE NUTZERREISE

1. **Anja legt einen Vorgang an**, ausgehend von einer Adresse. Sie beantwortet fünf Fragen: Adresse, ggf. Gemarkung/Flur/Flurstück, bisherige Nutzung, geplante Nutzung und ob die geplante Vermietung 90 Tage im Kalenderjahr übersteigt. (Die letzte Frage ist nicht kosmetisch — sie steuert den Zweckentfremdungszweig.)
2. **Das System schlägt die Genehmigungskonstellation** und die Verfahrensart vor, jeder Punkt mit Quelle und als *ungeprüft* markiert.
3. **Anja erzeugt einen Upload-Link** und schickt ihn an Frau Weber. Parallel zieht sie ihren eigenen Ordner hinein.
4. **Die Aufnahme läuft.** Jedes Dokument erhält Typ, Qualitätsurteil, extrahierte Fakten und einen Benennungsvorschlag. Unsichere Fälle landen in einer Prüfliste.
5. **Die Anforderungsliste füllt sich selbst.** 17 erforderliche Punkte; 9 belegt, 4 teilweise, 4 offen. Jeder belegte Punkt nennt Dokument und Seite.
6. **Das Faktenblatt wird geprüft.** Anja arbeitet rund 30 Fakten durch. Die meisten sind ein Klick. Drei haben Konflikte.
7. **Konflikte werden gelöst.** Sie wählt kanonische Werte; das System dokumentiert wer, wann und auf welcher Grundlage entschieden hat.
8. **Die Antragsinhalte entstehen** — Portal-Übertragungsblatt, Entwurf der Betriebs-/Nutzungsbeschreibung, Begründungsgerüst für Ausnahme/Befreiung, Anschreiben. Alles Faktische wird aus geprüften Fakten eingesetzt, nicht vom Modell geschrieben.
9. **Aktualitätsprüfung.** Verwendete Formulare und Regeln werden gegen das Quellenregister verifiziert; alles Veraltete oder nicht Verifizierbare wird markiert.
10. **Einreichungsprüfung.** Befunde mit Schweregrad, Beleg, betroffenen Dokumenten und Korrekturaktion.
11. **Anja korrigiert, prüft erneut, friert das Paket ein.** Das Einfrieren erzeugt einen unveränderlichen, gehashten, auditierten Stand mit einem Prüfprotokoll, das sie aus Haftungsgründen zur Akte nimmt.
12. **Sie reicht selbst über das Bauportal.NRW ein**, mit dem Übertragungsblatt daneben.

**Zu validierende Zeitbehauptung im Pilotbetrieb:** Schritte 4–7 kosten eine erfahrene Architektin heute 3–6 Stunden reines administratives Lesen pro Projekt. Das ist die Zahl, die das MVP bewegen muss.

---

# TEIL 6 — MVP-FUNKTIONSUMFANG

## MUSS (ohne diese kein MVP)

| Funktion | Warum tragend |
|---|---|
| Vorgangsanlage mit strukturierter Erfassung | Steuert das gesamte Anforderungsmodell |
| Mehrfach-Upload (Architektin) + tokenisierter externer Upload (Eigentümer) | Ohne externen Upload wird die Aufnahmequalität nie an der Realität getestet |
| OCR + PDF-Textextraktion + DOCX-Parsing + Bildvorverarbeitung | Die Grundfähigkeit |
| Dokumentqualitätsbewertung mit explizitem Urteil „unbrauchbar — bessere Vorlage anfordern“ | Verhindert stilles Garbage-in |
| Dokumenttyperkennung in eine **Bonn-NÄ-spezifische Taxonomie** | Speist Anforderungen, nicht Ablage |
| Faktenextraktion mit Herkunft (Dokument, Seite, Bildbereich) für ~30 definierte Fakten | Der Kernwert |
| **Anforderungsmodell + Anforderungsliste** (deterministisch, kuratiert) | Das Rückgrat. Begründung in Teil 26 |
| Faktenbestätigung mit Quellvorschau | Vertrauen |
| **Konflikt-Engine** (deterministischer Vergleich, typisierte Normalisierung) | USP 1 |
| Zweckentfremdungs-90-Tage-Regel + Parallelverfahrens-Checkliste | Die differenzierende Erkenntnis |
| Portal-Übertragungsblatt (strukturiert, kopierfertig) | Der Output, der nach dem 1.9.2026 tatsächlich nutzbar ist |
| Betriebs-/Nutzungsbeschreibung aus geprüften Fakten | Die lästigste Schreibarbeit |
| **Quellenregister + Formularstandsprüfung** mit kuratierten Einträgen und Gültigkeitsfenstern | USP 3, ehrlich zugeschnitten |
| **Einreichungsprüfung** mit typisierten Befunden | USP 2 |
| Paket-Einfrieren + Prüfprotokoll + Audit-Trail | Haftung — und der Grund, warum ein Büro einführt |
| Deutsche Oberfläche | Nicht verhandelbar |

## SOLLTE (Wochen nach dem MVP)

Dublettenerkennung per Hash und Near-Hash; einfache Versionsgruppierung (gleicher Typ + gleicher Titel + anderes Datum, menschlich bestätigt); Erzeugung des Zweckentfremdungsantrags; PDF/A-Normalisierung des Pakets; Nachforderungsverfolgung; zweite Kommune; Fristen- und Fiktionsüberwachung.

## SPÄTER

XBau-Export; Bauvoranfrage-Konfiguration; Planinhaltsextraktion (Maße und Raumbezeichnungen aus Zeichnungen); Regeländerungsüberwachung mit automatisiertem Diffing; Mehrbüro-Mandantenfähigkeit mit feiner Rollenlogik; Erzeugung von Nachforderungsantworten.

## NICHT IM UMFANG — nicht bauen

BIM/IFC jeglicher Art · Projektmanagement, Zeiterfassung, Rechnungsstellung, CRM · Bauphasenfunktionen · eine mobile App (die Eigentümerseite ist eine responsive Webseite; das genügt) · automatische Einreichung bei irgendeiner Behörde · jede rechtliche Schlussfolgerung · eigenes Modelltraining oder Fine-Tuning · ein Knowledge Graph · Vektor-/semantische Suche · E-Mail-Postfach-Aufnahme · generisches Dokumentenmanagement für Nicht-NÄ-Arbeit · bundesweite Regelabdeckung · granulare Enterprise-Berechtigungen · Nachbarbeteiligung · alles, was Statik oder Brandschutznachweise erzeugt.

Begründungen für die vier verlockendsten dieser Punkte stehen in Teil 26.

---

# TEIL 7 — USP 1: DOKUMENTÜBERGREIFENDE KONSISTENZ-ENGINE

## 7.1 Das Konzept, korrigiert

Die Vorlage beschreibt Konflikterkennung als „finde, wo Dokumente sich widersprechen“. Naiv gebaut ergibt das eine Fehlalarm-Maschine, die Architekten in Woche zwei abschalten. Die wichtigste Designentscheidung in USP 1 ist: **was zählt überhaupt als Widerspruch?**

Nehmen Sie das Beispiel der Vorlage: 92,4 m² in einem Dokument, 96,2 m² in einem anderen. In einer echten deutschen Bauakte ist das sehr oft **kein** Widerspruch. Es ist Wohnfläche nach WoFlV (Balkone zu 25 %, Dachschrägen gemindert) versus Nutzfläche nach DIN 277 versus Brutto-Grundfläche. Drei richtige Zahlen, drei verschiedene Definitionen. Wer das als Konflikt meldet, lehrt die Architektin, dass das Werkzeug ihre Fachwelt nicht versteht.

**Deshalb: Fakten sind typisiert, und Typen tragen Definitionen.** `wohnflaeche_woflv` und `nutzflaeche_din277` sind verschiedene Fakten. Sie werden nie miteinander verglichen. Jeder wird nur mit anderen Aussagen desselben typisierten Fakts verglichen, und ihr *Verhältnis* wird über eine Fachregel geprüft (Wohnfläche ≤ Nutzfläche, mit Plausibilitätsband), die einen **Hinweis** oder eine **Rückfrage** erzeugt, nie einen **kritischen** Befund.

Dieselbe Disziplin gilt überall:
- **Adresse**: vor dem Vergleich normalisieren (Straße/Str./Str, ß/ss, Ordinalformen). `Musterstraße 12` vs. `Musterstr. 12` → identisch, kein Befund. `12` vs. `21` → kritisch.
- **Namen**: Groß-/Kleinschreibung, Titel, Leerzeichen normalisieren; Vergleich per Editierdistanz *und* semantischer Prüfung. `Max Mustermann` vs. `Maria Mustermann` → kritisch. `Müller` vs. `Mueller` → identisch. Eine **Erbengemeinschaft** im Grundbuch, während der Antrag eine Person nennt → kritisch, ausdrücklich als *Vertretungs-/Berechtigungsproblem* markiert, nicht als Tippfehler.
- **Flurstück**: exakter Vergleich eines normalisierten Flurstückskennzeichens (Gemarkung + Flur + Flurstück, `143/2` ≠ `143`). Zifferndreher sind der klassische OCR- und der klassische menschliche Fehler; jede Flurstücksabweichung ist kritisch, und der Quellausschnitt wird immer gezeigt.
- **Nutzungsbezeichnung**: Vergleich gegen ein kontrolliertes Vokabular mit rechtlicher Hierarchie — `Wohnnutzung`, `Ferienwohnung`, `Ferienhaus`, `Beherbergungsbetrieb` sind rechtlich verschiedene Kategorien, und der Unterschied zwischen „eine Wohnung“ und „das gesamte Gebäude“ verändert den ganzen Antrag. Dieser Vergleich ist semantisch und die einzige Stelle, an der ein Modellaufruf seinen Preis wert ist — stets gefolgt von einer menschlichen Entscheidung.

## 7.2 Architektur

```
Dokumente ──► Extraktion (LLM, schemagebunden) ──► FactAssertion-Zeilen
                                                        │
                                  ┌─────────────────────┘
                                  ▼
                      NORMALISIERUNG (deterministisch, pro Faktentyp)
                                  │
                                  ▼
                      GRUPPIERUNG nach (Projekt, Faktentyp, [Bezug])
                                  │
                                  ▼
                      VERGLEICH (deterministische Regeln pro Typ)
                                  │
                      ┌───────────┴───────────┐
                      ▼                       ▼
                keine Abweichung         Abweichung
                      │                       │
                      │            Schweregradregeln (deterministisch)
                      │                       │
                      │            Erläuterung (LLM, optional,
                      │             auf die zwei Werte begrenzt)
                      ▼                       ▼
                kanonischer Wert       Konfliktsatz → Konfliktzentrum
```

**Das LLM entscheidet niemals, dass ein Konflikt vorliegt.** Es extrahiert Werte und formuliert allenfalls die Erläuterung. Erkennung, Schweregrad und Auswahl des kanonischen Werts sind Code und menschliche Entscheidung. Genau das macht einen Befund verteidigbar, wenn eine Architektin ihn anzweifelt — und das wird sie.

## 7.3 Die Vergleichsflächen

Die Engine vergleicht fünf Populationen, in dieser Reihenfolge:

1. **Quelle ↔ Quelle** — der klassische Fall.
2. **Quelle ↔ kanonischer Fakt** — hat ein neu hochgeladenes Dokument etwas bereits Bestätigtes entwertet? (Der wertvollste und am häufigsten vergessene Check: die Eigentümerin lädt drei Tage nach der Bestätigung einen korrigierten Grundbuchauszug hoch.)
3. **Kanonischer Fakt ↔ erzeugter Inhalt** — ist die Betriebsbeschreibung vom Faktenblatt abgedriftet?
4. **Erzeugt ↔ erzeugt** — stimmt das Übertragungsblatt mit dem Anschreiben überein?
5. **Kanonischer Fakt ↔ Regelbedingung** — z. B. geplante Vermietungstage gegen die 90-Tage-Schwelle; Bettenzahl gegen die Sonderbau-Schwelle. **Diese Befunde beeindrucken Architekten am meisten, weil sie gar keine Vergleiche sind — hier wendet das System eine Regel auf einen Fakt an.**

## 7.4 Schweregradmodell

| Schweregrad | Definition | Beispiel | Verhalten |
|---|---|---|---|
| **KRITISCH** | Materieller Widerspruch in einem rechtlich wirksamen Fakt | Zwei verschiedene Flurstücke; Eigentümer ≠ Bauherr ohne Vollmacht | **Sperrt das Einfrieren des Pakets** |
| **WARNUNG** | Abweichung mit plausibler harmloser Erklärung | 92,4 vs. 96,2 m² über verschiedene Definitionen; zwei Daten für denselben Plan | Muss mit Begründung erledigt werden |
| **HINWEIS** | Normalisierte Abweichung oder bekannte harmlose Variante | Str. vs. Straße | Standardmäßig eingeklappt, auf Wunsch sichtbar |

Das Sperren bei KRITISCH ist eine starke Setzung und bewusst gewählt: Sie macht aus einem Ratgeber eine Kontrolle.

## 7.5 Was USP 1 niemals tun darf

Niemals still einen kanonischen Wert wählen. Niemals einen Konflikt lösen, indem „dem neueren Dokument vertraut“ wird. Niemals einen Konflikt verschweigen, weil die Konfidenz niedrig war — **geringe Extraktionskonfidenz ist selbst ein Befund** („dieser Wert konnte nicht zuverlässig gelesen werden; bitte an der Quelle prüfen“), kein Grund zu schweigen.

---

# TEIL 8 — USP 2: EINREICHUNGSPRÜFUNG („BEHÖRDENSIMULATION“)

## 8.1 Umbenennen

Nennen Sie es **„Prüfsimulation“** oder besser **„Einreichungsprüfung“** — nicht „Behördenprüfung“ und niemals „Genehmigungsprognose“. Der Name setzt die Haftungserwartung. Ein Werkzeug, das eine Genehmigung vorherzusagen scheint, kann eine Architektin nicht verteidigen.

## 8.2 Das Rahmenwerk, nicht die Persona

Die Prüfung ist eine **Checklisten-Engine über vier Schichten**, in dieser Reihenfolge ausgeführt, jede mit typisierten Befunden:

**Schicht A — Vollständigkeit (deterministisch).** Jeder Punkt des Anforderungsmodells für diese Verfahrensart wird bewertet: erfüllt / teilweise erfüllt / fehlt / nicht anwendbar, mit dem Beleg, der ihn erfüllt. Reiner Code — und die Schicht mit den wertvollsten Befunden. Auch die, die in der Vorlage unterschätzt wird.

**Schicht B — Konsistenz (deterministisch).** Alle offenen KRITISCH- und WARNUNG-Konflikte, erneut über das Kandidatenpaket gerechnet.

**Schicht C — Formale und rechtliche Prüfpunkte (Regelwerk + kuratierte Kriterien).** Ein kuratierter Katalog von Prüfpunkten aus BauPrüfVO, Bonner Anforderungen und den bekannten Fehlermustern dieses Verfahrens. Jeder Punkt ist eine kleine Regel mit Fundstelle. Beispiele — sämtlich vor der Kodierung mit einer bauvorlageberechtigten Person zu verifizieren:

- Ist der Entwurfsverfasser bauvorlageberechtigt und benannt?
- Ist die Bauherrschaft mit den Verfügungsberechtigten im Grundbuch identisch, oder liegt eine Vollmacht vor? (Erbengemeinschaft: sind *alle* Mitglieder erfasst?)
- Nennt die Betriebsbeschreibung Gäste, Betten, Vermietungszeiträume, An- und Abreise, Stellplätze und Abfall? Eine Nutzungsänderung ohne bauliche Änderung wird fast ausschließlich an diesem Dokument beurteilt.
- Ist die Stellplatzfrage beantwortet — Bedarf nach der einschlägigen Satzung, Nachweis der Herstellung oder Ablöseantrag?
- Sind Rettungswege und die brandschutzrechtlichen Folgen der geänderten Nutzung behandelt, und überschreitet der Fall die Schwelle zum Sonderbau (Beherbergungsstätte)?
- Ist die bauplanungsrechtliche Grundlage bestimmt (B-Plan mit Gebietsart oder § 34 BauGB), und liegt bei erforderlicher Ausnahme/Befreiung nach § 31 BauGB eine Begründung vor?
- Sind Rohbau-/Herstellungskosten angegeben (sie bestimmen die Gebühr und werden bei Nutzungsänderungen regelmäßig vergessen)?
- Ist der Erhebungsbogen für die Baustatistik beigefügt, soweit erforderlich?
- Sind Pläne maßstäblich, bemaßt, vom Entwurfsverfasser unterzeichnet, und entsprechen die Bestands-/Neubaukennzeichnungen (üblicherweise gelb/rot) der beschriebenen Änderung?

**Schicht D — Klarheit und Belegbarkeit (LLM, eng geführt).** Der einzige echt generative Teil: Auf Basis der geprüften Fakten und der erzeugten Beschreibungen werden Aussagen identifiziert, die mehrdeutig sind, durch keinen Beleg im Projekt gestützt werden oder von einem normalen Leser auf zwei Arten verstanden werden können. Das Modell erhält Text und Faktenbasis und wird *ausschließlich* nach Befunden dieser drei Arten gefragt, in festem Schema, jeweils mit wörtlichem Zitat der beanstandeten Stelle. Es wird ausdrücklich angewiesen, dass es kein Dokument außerhalb der Faktenbasis kennt und nicht über Recht schlussfolgern darf.

## 8.3 Ausgabeformat

Der Score muss weg. Eine „Einreichungsreife 72/100“ ist nicht falsifizierbar, erzeugt Scheinsicherheit und wird das Erste sein, was Ihnen vorgehalten wird, wenn ein Antrag mit 91/100 eine Nachforderung erhält. Ersetzen durch **Zählungen und ein binäres Tor**:

```
EINREICHUNGSPRÜFUNG — Vorgang 2026-014
Stand: 05.09.2026, 14:22 · Regelstand: Bonn-NÄ v1.4 (gültig ab 01.09.2026)

EINREICHUNGSSPERRE AKTIV — 2 kritische Punkte offen

Vollständigkeit      13 von 17 Pflichtunterlagen belegt · 2 offen · 2 nicht anwendbar
Konsistenz           2 kritisch · 4 Warnungen · 11 Hinweise
Prüfpunkte           23 geprüft · 3 nicht beantwortbar
Formularstand        1 Formular nicht verifizierbar (Quelle geprüft 05.09.2026)
Parallelverfahren    1 Verfahren erforderlich, nicht begonnen (Zweckentfremdung)

Diese Prüfung ersetzt keine bauaufsichtliche Prüfung und keine Rechtsberatung.
```

## 8.4 Befundschema

Jeder Befund trägt: `id`, `schweregrad`, `schicht`, `kategorie`, `titel`, `beobachtung` (was das System sieht), `grundlage` (Regel + Fundstelle + Gültigkeitsdatum der Fundstelle), `beleg` (Dokument, Seite, Bildbereich oder Fakt-ID), `betroffene_artefakte`, `empfohlene_massnahme`, `aktionslink`, `status`, `erledigt_von`, `erledigt_am`, `erledigungsbegruendung`.

**`grundlage` ist verpflichtend.** Ein Befund ohne nachvollziehbare Grundlage wird nicht angezeigt. Diese eine Einschränkung eliminiert die meisten Wege, auf denen eine LLM-Prüfung schiefgeht.

## 8.5 Verbotene Ausgaben

Im Schema hart kodiert und durch einen Nachfilter erzwungen: keine Aussage, dass ein Antrag genehmigt werden wird, genehmigungsfähig oder zulässig ist oder einer Norm entspricht; keine Genehmigungswahrscheinlichkeit; keine Zeitschätzung für die behördliche Entscheidung; keine erfundene Fundstelle. Ein Befund, dessen `grundlage` nicht gegen das Register auflösbar ist, wird verworfen und als Modellfehler protokolliert.

---

# TEIL 9 — USP 3: REGEL- UND FORMULARINTELLIGENZ

## 9.1 Ehrlich sein, was baubar ist

„Die KI prüft laufend die aktuelle Rechtslage“ ist auf MVP-Ebene ein Versprechen, das sich nicht sicher halten lässt. Live-Websuche im Schlussfolgerungspfad erzeugt selbstbewusste Zitate der falschen Fassung, und deutsche Verwaltungsquellen sind genau das PDF-hinter-Runderlass-Material, an dem naives Retrieval scheitert.

**Baubar und wirklich differenzierend ist ein kuratiertes Quellenregister mit Überwachung.** Die Intelligenz steckt im *Pflegeprozess*, nicht im Modell.

## 9.2 Architektur

**Das Register (menschlich kuratiert, versioniert, ~40–80 Einträge für das Bonn-MVP).** Jeder Eintrag:

```yaml
id: bonn-zweckentfremdungssatzung-2022
jurisdiction: [DE, NRW, Bonn]
topic: [zweckentfremdung, kurzzeitvermietung]
title: Satzung zum Schutz und Erhalt von Wohnraum im Gebiet der Bundesstadt Bonn
authority: Bundesstadt Bonn (Rat), Amt 50-52
legal_basis: § 12 Abs. 1 WohnStG NRW
url: https://www.bonn.de/.../zweckentfremdungssatzung.php
document_hash: sha256:…
in_force_from: 2022-07-01
in_force_until: 2027-06-30      # § 17 Abs. 2: tritt fünf Jahre nach Inkrafttreten außer Kraft
verified_by: <Kurator>
verified_at: 2026-09-05
next_review_due: 2026-12-05
supersedes: bonn-zweckentfremdungssatzung-2013
rules_derived: [zw-90-tage, zw-genehmigungspflicht, zw-wohnraum-id, zw-negativattest]
```

Das Feld `in_force_until` ist keine Dekoration. **Die Bonner Zweckentfremdungssatzung tritt nach ihren eigenen Bestimmungen am 30. Juni 2027 außer Kraft.** Ein Produkt, das zu Ferienwohnungen in Bonn berät und das nicht weiß, wendet im nächsten Sommer selbstbewusst eine außer Kraft getretene Satzung an. Jede Regel muss ein Gültigkeitsfenster tragen, und das System muss die Anwendung einer abgelaufenen Regel verweigern — es muss sagen: „Regelstand abgelaufen, Prüfung erforderlich.“

**Überwachung (deterministisch, nächtlich).** Jede registrierte URL abrufen, Inhalt hashen, gegen den gespeicherten Hash diffen. Bei Änderung: Kuratoraufgabe mit Diff erzeugen. **Niemals automatische Übernahme einer geänderten Quelle in die Regelbasis.** Ein menschlicher Kurator (anfangs Sie oder ein kooperierender Architekt) prüft und versioniert die Änderung. Regulatorische Inhalte werden wie Software ausgeliefert: `Regelstand Bonn-NÄ v1.4`, mit Changelog.

**Regelanwendung (deterministisch).** Regeln sind kleine, typisierte Prädikate über Fakten:

```
regel zw-90-tage:
  wenn: geplante_vermietungstage_pro_jahr > 90
  dann: befund(
    schweregrad = KRITISCH_PARALLELVERFAHREN,
    titel = "Zweckentfremdungsgenehmigung erforderlich",
    grundlage = bonn-zweckentfremdungssatzung-2022 § 7 Abs. 2 Nr. 2,
    aktion = checkliste_oeffnen(zweckentfremdung))
  unbekannt_wenn: geplante_vermietungstage_pro_jahr ist null
                  → befund(schweregrad = FEHLENDE_ANGABE, ...)
```

Man beachte `unbekannt_wenn`. **Fehlende Eingaben müssen einen Befund erzeugen, kein Schweigen.** Hier scheitern die meisten Regelwerke still.

## 9.3 Formularstand

1. Das Anforderungsmodell benennt den erforderlichen Vordruck über seine Register-ID (z. B. die einschlägige Anlage zur VV BauPrüfVO für das vereinfachte Verfahren, die Betriebsbeschreibungsanlage und den Erhebungsbogen der Baustatistik).
2. Das Register hält die maßgebliche URL (MHKBD-Seite „Anlagen zur VV BauPrüfVO“ und die Formularseite der Architektenkammer NRW), den Dateihash, die auf dem Formular gedruckte Versionskennung und das Datum der letzten menschlichen Prüfung.
3. Lädt die Architektin ein ausgefülltes Formular hoch, wird dessen Versionskennung extrahiert und verglichen.
4. Drei mögliche Urteile und keine weiteren: **verifiziert aktuell** (Hash entspricht einem menschlich geprüften Registereintrag), **veraltet** (entspricht einem bekannten überholten Eintrag), **nicht verifizierbar** (keine Übereinstimmung — menschliche Prüfung erforderlich, mit Deep-Link zur Quelle).

**Niemals eine Version erfinden. Niemals ein Formular still ersetzen. Niemals die hochgeladene Datei überschreiben.**

## 9.4 Die Demo, die das verkauft

Heute befinden sich die VV-BauPrüfVO-Vordrucke genau in dem Zustand, für den dieses System gebaut ist: Der BauCode ist am 1. September 2026 in Kraft getreten, und ob jeder Vordruck entsprechend neu herausgegeben wurde, ist exakt die Frage, die ein Kurator klären muss und ein Modell nicht raten darf. Zeigen Sie ein Formular mit der Markierung **nicht verifizierbar — Quelle zuletzt geprüft 05.09.2026, Änderung der BauO NRW zum 01.09.2026 erkannt** samt Link zur Ministeriumsseite. Dieser eine Bildschirm überzeugt mehr als jede Behauptung juristischer Intelligenz, weil er zeigt, dass das Produkt die Grenzen seines eigenen Wissens kennt.

---

# TEIL 10 — DOKUMENTENINTELLIGENZ

## 10.1 Pipeline

Die 18-stufige lineare Pipeline der Vorlage ist eine gute Inventarliste und ein schlechter Ausführungsplan. Sequenziell ausgeführt ist sie langsam und setzt LLM-Stufen auf den kritischen Pfad des Uploads. Umstrukturieren in vier Phasen mit expliziter Nebenläufigkeit:

```
PHASE A — SYNCHRON (< 2 s, blockiert die Upload-Antwort)
  MIME-/Endungsvalidierung · Größenlimit · Magic-Byte-Prüfung ·
  Malware-Scan · SHA-256 · Exakt-Dublettenprüfung · Original unveränderlich ablegen ·
  Job einreihen · „empfangen“ zurückmelden

PHASE B — PARALLEL JE DOKUMENT (Hintergrund-Worker, 5–60 s)
  ├─ technische Metadaten (Seiten, DPI, EXIF, Producer, Erstell-/Änderungsdatum)
  ├─ Qualitätsbewertung (Unschärfe, Schräglage, Kontrast, Auflösung, Anschnitt)
  ├─ Textebenen-Erkennung ──► native Extraktion  ODER  Vorverarbeitung + OCR
  └─ Thumbnails + Seitenrasterung

PHASE C — SEQUENZIELL JE DOKUMENT (LLM, 5–30 s)
  Klassifikation ──► typspezifisches Extraktionsschema ──► Faktaussagen
  mit Herkunft ──► Konfidenzbewertung ──► Benennungsvorschlag

PHASE D — PROJEKTWEIT, ENTPRELLT (nach einer Ruhephase ausgelöst)
  Near-Duplicate-Erkennung · Versionskandidaten ·
  Faktennormalisierung · Neuberechnung der Konflikte ·
  Neubewertung der Anforderungsliste · Benachrichtigung
```

Das Entprellen in Phase D ist wichtig: Wenn Frau Weber in 90 Sekunden 14 Fotos hochlädt, muss die projektweite Analyse **einmal** laufen, nachdem sie fertig ist, nicht vierzehnmal. Wird das falsch gemacht, flackert die Konfliktliste und die Architektin verliert das Vertrauen.

## 10.2 Umgang mit schlechten Vorlagen

Die Qualitätsbewertung läuft *vor* der OCR und steuert eine Entscheidung, nicht nur ein Label:

| Signal | Messung | Aktion |
|---|---|---|
| Schräglage | Hough-Transformation, dominanter Winkel | Auto-Entzerrung < 15°, sonst markieren |
| Unschärfe | Varianz des Laplace-Operators, je Seitenbereich | Unter Schwelle → Bereich als unlesbar markieren, keine Zahlen extrahieren |
| Auflösung | effektive DPI im Textbereich | < 200 DPI → OCR mit Warnung; < 120 DPI → **numerische Extraktion verweigern** |
| Kontrast / Schatten | lokales Histogramm | CLAHE + adaptive Schwellwertbildung, dann erneut messen |
| Anschnitt | Text berührt den Rand | Hinweis „Seite möglicherweise angeschnitten“ — kritisch bei Flächentabellen |
| Mehrere Seiten auf einem Foto | Seitengrenzenerkennung | Trennvorschlag, Mensch bestätigt |
| Handschrift | modellmarkierter Bereich | **Niemals automatisch in einen Fakt übernehmen.** Ausschnitt zeigen, Mensch tippt den Wert |
| Stempel/Unterschriften | nur Erkennung | Als Dokumenteigenschaft erfasst (relevant: ist der Plan unterschrieben?) |

Die wichtigste Zeile dieser Tabelle ist die zur Handschrift. Handgeschriebene Flurstücksnummern, handschriftliche Korrekturen auf Genehmigungen der 1970er und handschriftliche Flächenangaben sind häufig — und genau dort geraten halluzinierte Ziffern in ein Rechtsdokument.

**Der Notausgang.** Jedes Dokument kann im Zustand **„Quelle unbrauchbar — bessere Vorlage anfordern“** enden, was eine gezielte Rückfrage an den Hochladenden erzeugt („Bitte fotografieren Sie Seite 2 des Grundbuchauszugs erneut, flach und bei Tageslicht“). Das ist eine Funktion, kein Fehler, und gehört sichtbar in die Demo.

## 10.3 Klassifikationstaxonomie

> **ANNAHME HINTERFRAGT — die vorgeschlagene 12-Ordner-Taxonomie ist ein Aktenschrank, keine Arbeitshilfe.**
>
> Kategorien wie `07_Technical` und `12_Archive` sagen der Architektin nichts darüber, ob ihr Antrag einreichungsreif ist. Klassifikation muss **verfahrensrelevant** sein: Der Typ eines Dokuments zählt, weil er eine Anforderung erfüllt, Fakten trägt — oder keines von beidem.

Ersetzen durch eine flache Typliste, an das Anforderungsmodell gebunden:

**Nachweise für das Verfahren:** `bauantragsformular`, `betriebsbeschreibung`, `baubeschreibung`, `lageplan_amtlich`, `liegenschaftskarte`, `bauzeichnung_grundriss`, `bauzeichnung_schnitt`, `bauzeichnung_ansicht`, `flaechenberechnung`, `stellplatznachweis`, `brandschutz_unterlage`, `erhebungsbogen_statistik`, `vollmacht`, `kostenberechnung`

**Bestand und Recht:** `baugenehmigung_alt`, `bauschein_bestandsplan`, `grundbuchauszug`, `teilungserklaerung_weg`, `flurkarte`, `kaufvertrag_auszug`, `denkmal_unterlage`

**Behördliches:** `behoerdenschreiben`, `nachforderung`, `bescheid`, `negativattest`, `zweckentfremdung_unterlage`

**Sonstiges:** `foto_bestand`, `korrespondenz`, `unklar`, `unbrauchbar`

`unklar` ist ein vollwertiger Typ und geht an einen Menschen. Ein Klassifikator, der immer rät, ist schlechter als einer, der zugibt.

**Ordner sind eine *Sicht*, erzeugt aus Typ + Status.** Das Büro behält seine eigene Serverstruktur; das MVP exportiert beim Einfrieren einen Ordnerbaum, erzwingt aber während der Arbeit keinen. Das vermeidet den Kampf gegen bestehende Gewohnheiten — ein echter Einführungskiller.

## 10.4 Benennung

`JJJJ-MM-TT_Dokumenttyp_Detail_Vnn.ext`, wobei das Datum das **Datum des Dokuments** ist, sofern mit hoher Konfidenz extrahiert, sonst das Eingangsdatum **mit Kennzeichnung**: `2026-09-04-E_Grundbuchauszug_Blatt4711.pdf` (`-E` = Eingangsdatum, kein Dokumentdatum). Niemals ein Datum erfinden. Der Originaldateiname bleibt immer in den Metadaten und immer sichtbar. Umbenennung ist ein **Vorschlag** bis zur Annahme, und Annahme ist sammelbar.

## 10.5 Versionierung

> **ANNAHME HINTERFRAGT — automatische Versionserkennung ist eine Falle.**
>
> Zu erkennen, dass `Grundriss_neu.pdf` und `Grundriss_final.pdf` Versionen derselben Zeichnung sind, verlangt visuellen Planvergleich. Das ist teuer, auf gescanntem und gedrehtem Material unzuverlässig, und eine falsche Gruppierung kann den gültigen Plan verstecken — der gefährlichste Fehlermodus dieses Produkts.

MVP-Ansatz: **Kandidatengruppierung, menschliche Bestätigung, keine automatische Ablösung.** Kandidaten gruppieren nach `dokumenttyp` + normalisiertem Titel/Geschoss + Maßstab, sortieren nach extrahiertem Plandatum (aus dem Plankopf), dann Uploaddatum, und anzeigen: *„Diese 3 Dokumente könnten Versionen desselben Plans sein. Bitte bestätigen und die gültige Fassung markieren.“* Nur ein Mensch setzt `ist_aktuell`. Abgelöste Dokumente werden nie gelöscht oder versteckt; sie werden markiert und aus dem Paket ausgeschlossen.

Dazu ein deterministisches Sicherheitsnetz mit echtem Wert: **Sind zwei Dokumente desselben Typs beide als aktuell markiert und weichen ihre Fakten ab, ist das automatisch ein Konflikt.**

---

# TEIL 11 — PROJEKTWISSENSMODELL

## 11.1 Der Faktenkatalog (MVP: ~30 typisierte Fakten)

Nicht „alles, was die KI findet“ — eine **geschlossene, kuratierte Liste**, denn nur eine geschlossene Liste macht Vollständigkeit messbar.

**Grundstück:** `adresse_strasse_hnr`, `plz`, `ortsteil`, `gemarkung`, `flur`, `flurstueck`, `grundbuchblatt`, `grundstuecksgroesse_m2`

**Personen:** `eigentuemer` (mehrwertig; Typ unterscheidet natürliche Person / Erbengemeinschaft / juristische Person), `bauherrschaft`, `entwurfsverfasser`, `bauvorlageberechtigung_nachweis`, `vollmacht_vorhanden`

**Gebäude (Bestand):** `baujahr`, `gebaeudeklasse`, `anzahl_wohneinheiten`, `anzahl_geschosse`, `bestandsgenehmigung_datum`, `bestandsgenehmigung_az`, `genehmigte_nutzung`

**Flächen:** `wohnflaeche_woflv_m2`, `nutzflaeche_din277_m2`, `brutto_grundflaeche_m2` — jeweils mit ausdrücklicher `bezugseinheit` (Gesamtgebäude / bestimmte Einheit)

**Vorhaben:** `bisherige_nutzung`, `geplante_nutzung` (kontrolliertes Vokabular), `umfang_der_aenderung` (Einheit / Gesamtgebäude), `bauliche_aenderungen_geplant` (bool), `anzahl_gaeste_max`, `anzahl_betten`, `anzahl_schlafraeume`, `geplante_vermietungstage_pro_jahr`, `stellplaetze_vorhanden`, `stellplaetze_erforderlich`

**Planungsrecht:** `bplan_nummer`, `bplan_gebietsart`, `beurteilung_nach` (B-Plan / § 34 / § 35), `ausnahme_befreiung_erforderlich`

**Verfahren:** `verfahrensart`, `zustaendige_behoerde`, `aktenzeichen`

Rund ein Drittel davon wird in keinem Dokument stehen und muss von der Architektin eingetragen werden. **Sagen Sie das in der Oberfläche** — ein leeres Feld, das kein Dokument füllen kann, ist kein KI-Versagen, sondern eine Aufgabe, und genau diese Rahmung macht das Werkzeug ehrlich.

## 11.2 Faktenmodell

Zwei Ebenen, deren Trennung wesentlich ist:

**`fact_assertion`** — eine Zeile je (Dokument, extrahierter Wert). Unveränderlich. Felder: `document_id`, `page`, `bbox`, `text_snippet`, `fact_type`, `raw_value`, `normalized_value`, `unit`, `extraction_confidence`, `extractor_version`, `model_version`, `prompt_version`, `created_at`.

**`project_fact`** — eine Zeile je (Projekt, Faktentyp, Bezug). Veränderlich, auditiert. Felder: `canonical_value`, `unit`, `status` ∈ {unbelegt, vorgeschlagen, bestätigt, strittig, manuell}, `selected_assertion_id` (nullable — null bei manueller Eingabe), `verified_by`, `verified_at`, `conflict_id`, `last_changed_reason`.

Konfidenz ist **keine** einzelne Zahl aus dem Modell. Sie wird deterministisch zusammengesetzt aus: Selbstauskunft des Modells (schwaches Signal, stark abgewertet), Qualitätswert des Quelldokuments, Extraktionsmethode (nativer Text > saubere OCR > degradierte OCR > Handschrift = nie automatisch), Übereinstimmung über unabhängige Dokumente hinweg und Formatgültigkeit (entspricht ein Flurstück dem erwarteten Muster?). Nur Fakten mit hoher Gesamtkonfidenz aus nativen Textquellen werden vorausgewählt; alles andere wartet auf einen Menschen.

## 11.3 Herkunfts-UX

Ein Klick auf einen Wert öffnet die Quellseite mit hervorgehobenem Bereich. Das ist kein Nice-to-have, sondern die **eine Funktion, die Skepsis in Akzeptanz verwandelt**. `bbox` wird bei der Extraktion für jede Aussage gespeichert; eine fehlende bbox gilt als Defekt. Stammt der Wert von einem Menschen, zeigt die Herkunft, wer ihn wann eingetragen hat.

## 11.4 Entitäten und Beziehungen

> **ANNAHME HINTERFRAGT — kein Knowledge Graph im MVP.**
>
> Es gibt ~30 Faktentypen, ~8 Entitätstypen und ein Projekt. Eine Graphdatenbank bringt hier nichts, was vier relationale Tabellen nicht auch leisten, und kostet eine Abfragesprache, die um 2 Uhr nachts niemand debuggt. Bauen Sie das relationale Modell. Neu bewerten, wenn projektübergreifendes Schließen (dasselbe Grundstück, mehrere Verfahren, mehrere Jahre) real wird.

---

# TEIL 12 — ORDNER- UND DOKUMENTARCHITEKTUR

Arbeitszustand = flache Dokumentliste mit typisierten Filtern und gespeicherten Sichten (Alle · Zu prüfen · Nachweise · Bestand · Behörde · Unbrauchbar). Die Ordnerhierarchie entsteht erst beim Einfrieren des Pakets:

```
2026-014_Kirschblütenweg-7_Nutzungsänderung_Ferienhaus/
├── 00_Prüfprotokoll/         # erzeugt: Befunde, Konfliktprotokoll, Regelstand, Audit
├── 01_Antrag/                # Übertragungsblatt, Formulare, Kostenberechnung
├── 02_Beschreibungen/        # Bau-/Betriebs-/Nutzungsbeschreibung, Begründung
├── 03_Zeichnungen/           # nur gültige Fassungen
├── 04_Grundstück_und_Recht/  # Liegenschaftskarte, Grundbuch, Vollmacht, WEG
├── 05_Nachweise/             # Stellplätze, Brandschutz, Flächen
├── 06_Behördenkorrespondenz/
├── 07_Parallelverfahren/     # Zweckentfremdungs-Checkliste + Belege
└── 99_Nicht_eingereicht/     # abgelöst, Dubletten, unbrauchbar — aufbewahrt, nie gelöscht
```

`00_Prüfprotokoll` ist das Haftungsartefakt des Büros und der Grund, warum der Inhaber unterschreibt. `99_Nicht_eingereicht` ist der Grund, warum die Architektin dem Einfrieren traut: Es wurde nichts weggeworfen.

Jedes eingefrorene Paket wird inhaltsgehasht und ist unveränderlich. Ein neues Einfrieren erzeugt `_V02`, überschreibt nie.

---

# TEIL 13 — ANTRAGSERZEUGUNG

## 13.1 Drei Inhaltsklassen, in der Oberfläche visuell unterschieden

| Klasse | Quelle | Editierbar | Kennzeichnung |
|---|---|---|---|
| **Übernommen** | Geprüfte Projektfakten, deterministisch eingesetzt | Nur über Änderung des Fakts | Grau, mit Faktenlink |
| **Vorlage** | Textbaustein mit Platzhaltern | Ja | Neutral |
| **Entwurf (KI)** | LLM-formulierte Prosa | Ja, mit ausdrücklicher Annahme | Bernsteinfarbener Randbalken bis zur Annahme |

**Kein Feld wird je von einem LLM mit einem Wert gefüllt.** Das Modell schreibt Sätze; das System setzt Werte ein. Ist ein Fakt ungeprüft, erscheint der Platzhalter als `[Angabe fehlt: Flurstück]` in Rot und sperrt das Einfrieren. Das ist der Unterschied zwischen einem Werkzeug, das entwirft, und einem, das erfindet.

## 13.2 Im MVP erzeugte Artefakte

1. **Portal-Übertragungsblatt** — jedes Feld, das der Bauportal.NRW-Assistent abfragt, in dessen Reihenfolge, mit Wert, Status und Herkunft. Feld für Feld kopierbar. *Der wertvollste Output nach dem 1. September 2026 — zuerst bauen.*
2. **Betriebs-/Nutzungsbeschreibung** — das entscheidende Dokument bei einer Nutzungsänderung mit wenig oder keiner Baumaßnahme. Strukturierte Vorlage: Nutzungsbeschreibung, Gäste, Betten, Räume, Vermietungsmuster und Saison, An-/Abreise und Schlüsselübergabe, Reinigung und Abfall, lärmrelevantes Verhalten, Stellplätze, kein Personal vor Ort, Notfallkontakt. Fakten eingesetzt, Bindetexte entworfen, Architektin bearbeitet.
3. **Begründung für Ausnahme/Befreiung** (nur Gerüst, falls der planungsrechtliche Zweig es verlangt) — Struktur und die zu beantwortenden Fragen, niemals die rechtliche Argumentation.
4. **Anschreiben** an das Bauaufsichtsamt.
5. **Vollständigkeitsnachweis / Prüfprotokoll** — die Selbstdokumentation des Pakets.

Nicht im MVP: das Bauantrags-PDF selbst (erzeugt das Portal), die Baubeschreibung über die Vorlage hinaus, jeder Nachweis, der einen Ingenieur erfordert.

---

# TEIL 14 — PRÜFKRITERIEN-RAHMENWERK

Prüfpunkte sind Daten, nicht Code. Jeder lebt im Anforderungsmodell in dieser Form:

```yaml
id: nae-bonn-betriebsbeschreibung-inhalt
verfahren: [nutzungsaenderung_ferienhaus_bonn]
schicht: C
schweregrad_bei_verstoss: WARNUNG
titel: Betriebsbeschreibung unvollständig
prueft:
  alle_vorhanden:
    - fakt: anzahl_gaeste_max
    - fakt: anzahl_betten
    - fakt: geplante_vermietungstage_pro_jahr
    - abschnitt: betriebsbeschreibung.anreise_abreise
    - abschnitt: betriebsbeschreibung.stellplaetze
grundlage:
  quelle: nrw-baupruefvo
  hinweis: "Betriebsbeschreibung bei gewerblicher Nutzung"
  geprueft_am: 2026-09-05
  geprueft_von: <Kurator>
empfohlene_massnahme: "Angaben ergänzen"
aktion: oeffne(betriebsbeschreibung, abschnitt)
```

Der MVP-Katalog umfasst rund **35–50 Punkte** in fünf Kategorien: Antragsberechtigung und Vertretung · Grundstück und Bestand · Planungsrecht · Bauordnungsrecht der neuen Nutzung (Stellplätze, Brandschutz/Rettungswege, Barrierefreiheitsprüfung, Sonderbau-Schwelle) · Formalia und Vollständigkeit. Dazu der Parallelverfahrensblock.

**Jeder Punkt muss von einer bauvorlageberechtigten Person verfasst oder geprüft werden.** Planen Sie das ausdrücklich ein: 3–5 Tage Expertenzeit — und das wertvollste geistige Eigentum im MVP. Lassen Sie den Katalog nicht von einem Modell schreiben.

---

# TEIL 15 — REGULATORISCHE WISSENSARCHITEKTUR

## 15.1 Quellenhierarchie (erzwungen, nicht empfohlen)

| Stufe | Quellen | Verwendung |
|---|---|---|
| 1 | Gesetze und Verordnungen von recht.nrw.de, Bundesrecht; kommunale Satzungen aus dem Bonner Ortsrecht | Regeln dürfen abgeleitet werden |
| 2 | Ministeriumsseiten und amtliche Vordrucke (MHKBD, Bauportal.NRW); die Serviceseiten der zuständigen Behörde | Regeln und Formulare |
| 3 | Hinweise und Formulare der Architektenkammer NRW | Bestätigung; Signale zum Formularstand |
| 4 | Kommentare, Kanzlei-Briefings, Fachpresse | **Nur Überwachungssignal.** Kann eine Kuratorprüfung auslösen. Nie eine `grundlage` |

Stufe 4 ist die Stelle, an der ein naives Produkt kippt. Eine weit verbreitete Sekundäraussage — etwa, Wohnungen in Ein- oder Zweifamilienhäusern seien von den Bonner Zweckentfremdungsregeln ausgenommen — kann dem Primärtext widersprechen (§ 4 Abs. 1 der Satzung von 2022 erstreckt den Anwendungsbereich ab 1. Juli 2022 auf Wohnraum insgesamt, einschließlich Eigenheimen und Eigentumswohnungen). **Die Primärquelle gewinnt immer, und ein Widerspruch einer Stufe-4-Quelle zu einer Stufe-1-Quelle ist ein Kuratoralarm, keine Regeländerung.**

## 15.2 Regel-Lebenszyklus

`entdeckt → kuratiert → geprüft (Fachperson) → veröffentlicht (Regelstand vX.Y) → überwacht → geändert/abgelaufen`

Jedes Projekt speichert den `Regelstand`, unter dem es geprüft wurde. Eine erneute Prüfung unter neuerem Regelstand zeigt einen Diff: *„Seit Ihrer letzten Prüfung haben sich 2 Regeln geändert.“* Das ist eine echte, verteidigbare „lebende Regelbasis“ — und anders als Live-Websuche auditierbar.

## 15.3 Anwendbarkeit

Eine Regel gilt nur, wenn `jurisdiction ⊆ projekt.jurisdiction` UND `verfahren` passt UND `heute ∈ [in_force_from, in_force_until]` UND `next_review_due > heute`. Fällt eine Bedingung aus, wird die Regel **nicht still übersprungen** — sie erzeugt einen Befund `PRÜFUNG_ERFORDERLICH`. Schweigen ist der Fehlermodus, der eine Nachforderung produziert.

---

# TEIL 16 — KI- / LANDGRAPH- / LUNA-ARCHITEKTUR

*(„Landgraph“ ist hier die zustandsbehaftete Graph-Orchestrierungsschicht, „Luna“ das LLM hinter einer API. Die Argumentation gilt für jedes äquivalente Paar.)*

## 16.1 Verantwortungsteilung

**Deterministische Backend-Dienste — ohne Modell:**
Dateihandling, Hashing, Malware-Scan, Bildvorverarbeitung, OCR-Aufruf, jede Normalisierung, jeder Vergleich, jede Regelauswertung, jede Schweregradzuweisung, jede Anforderungsbewertung, jede Konfidenzzusammensetzung, Template-Rendering, Paketbau, Audit-Logging, Formular-Hash-Überwachung.

**Luna (LLM) — nur vier Aufgaben:**
1. Dokumentklassifikation (schemagebunden, `unklar` immer verfügbar)
2. Typspezifische Faktenextraktion mit Seiten-/Bereichsanker
3. Formulierung von Betriebsbeschreibung, Anschreiben, Begründungsgerüsten
4. Befunde der Schicht D (Mehrdeutigkeit, unbelegte Aussagen) in festem Schema

**Landgraph — Orchestrierung der drei wirklich zustandsbehafteten, verzweigenden, menschlich unterbrechbaren Abläufe:**
1. `document_understanding` (klassifizieren → Schema wählen → extrahieren → Selbstprüfung → Konfidenztor → Menschknoten)
2. `application_preparation` (Anforderungen auflösen → Faktentor → Erzeugung je Artefakt → Konsistenzschleife → Freigabeknoten)
3. `submission_review` (Schicht A → B → C → D → aggregieren → Tor)

> **ANNAHME HINTERFRAGT — die Aufnahme nicht in Landgraph orchestrieren.**
>
> Phasen A, B und D sind eine Job-Warteschlange: Retries, Backoff, Idempotenz, Nebenläufigkeitsgrenzen. Das ist Celery-/RQ-/Sidekiq-Terrain. In einem Graph-Framework bringt es ein hübscheres Diagramm und kostet Observability und günstige horizontale Skalierung. Nutzen Sie Landgraph dort, wo sein echter Vorteil liegt — dauerhafter Zustand über menschliche Unterbrechungen hinweg. Das sind drei Abläufe, nicht achtzehn.

## 16.2 Agenten: überwiegend nein

Von den acht vorgeschlagenen Agenten rechtfertigen **zwei** eine graphbasierte, mehrstufige Behandlung (Dokumentverständnis, Einreichungsprüfung). Zwei sind einzelne zustandslose LLM-Aufrufe hinter einer Serviceschnittstelle (Klassifikation, Erzeugung). **Vier sind gar keine KI** (Konflikterkennung, Regelverifikation, Einreichungs-QA, Projektfaktenverwaltung), und sie als Agenten zu bauen wäre aktiv schädlich: nichtdeterministisch, nicht auditierbar und unfähig, dieselbe Eingabe zweimal gleich zu beantworten. Eine Architektin wird eine Prüfung wiederholen, um zu sehen, ob die Antwort stabil ist. Sie muss es sein.

## 16.3 Disziplin bei strukturierten Ausgaben

Jeder Luna-Aufruf: JSON-Schema auf API-Ebene erzwungen; Validierung gegen ein Pydantic-Modell; ein Reparaturversuch mit dem Validierungsfehler; beim zweiten Fehlschlag Weiterleitung an den Menschen unter Aufbewahrung der Rohausgabe. Zu jedem Aufruf protokollieren: `prompt_version`, `model_version`, `input_hash`, `output_hash`, `latency`, `tokens`, `validation_result`. Dieses Protokoll beantwortet drei Monate später die Frage „warum hat es das gesagt?“ — und ist die Basis der Regressionssuite.

Extraktionsausgaben müssen `page` und `bbox` enthalten. **Eine Extraktion ohne Anker wird verworfen**, denn ein nicht verankerter Fakt ist nicht überprüfbar und damit nicht vertrauenswürdig.

## 16.4 Evaluation

Den Goldstandard vor der Pipeline aufbauen: 30 echte (anonymisierte) oder realistische Dokumente mit handgelabelter Wahrheit für Typ und jeden Fakt. Jede Prompt- oder Modelländerung läuft dagegen. Je Faktentyp verfolgen: Precision, Recall und — die entscheidende Zahl — die **Rate selbstbewusst falscher Extraktionen**. Ein Übersehen kostet eine Minute. Ein selbstbewusster Fehler kann eine Genehmigung kosten.

---

# TEIL 17 — DATENBANKMODELL

Postgres. Vierzehn Tabellen für das MVP; die 19er-Liste der Vorlage enthält vier, die es noch nicht geben sollte.

```
organizations(id, name, created_at)
users(id, org_id→organizations, email, name, role, bauvorlageberechtigt bool, ...)
projects(id, org_id→organizations, aktenzeichen, Adressfelder, gemarkung, flur,
         flurstueck, verfahrensart, regelstand_version, status, created_by, ...)
documents(id, project_id→projects, storage_key_original, sha256, mime, size,
          original_filename, proposed_filename, accepted_filename,
          doc_type, doc_type_confidence, quality_score, quality_flags jsonb,
          ocr_status, page_count, is_current bool, superseded_by→documents,
          uploaded_by, upload_source enum(architect|external_link), created_at)
document_pages(id, document_id→documents, page_no, text, storage_key_raster, dpi)
fact_assertions(id, document_id→documents, page_no, bbox jsonb, fact_type,
                raw_value, normalized_value, unit, confidence numeric,
                extractor_version, model_version, created_at)
project_facts(id, project_id→projects, fact_type, scope, canonical_value, unit,
              status, selected_assertion_id→fact_assertions, verified_by→users,
              verified_at, UNIQUE(project_id, fact_type, scope))
conflicts(id, project_id→projects, fact_type, severity, status, canonical_choice,
          resolved_by→users, resolved_at, resolution_note, first_detected_at)
conflict_members(conflict_id→conflicts, assertion_id→fact_assertions, value)
requirements(id, verfahren, code, title, kind, condition jsonb, basis_source_id,
             regelstand_from, regelstand_to)
requirement_status(project_id→projects, requirement_id→requirements, status,
                   satisfied_by_document_id→documents, evaluated_at)
reviews(id, project_id→projects, run_at, regelstand_version, blocking bool,
        summary jsonb, run_by→users)
review_findings(id, review_id→reviews, severity, layer, category, title,
                observation, basis jsonb, evidence jsonb, recommended_action,
                status, resolved_by→users, resolved_at, dismissal_reason)
regulatory_sources(id, jurisdiction[], topic[], title, url, content_hash,
                   in_force_from, in_force_until, verified_by, verified_at,
                   next_review_due, supersedes→regulatory_sources)
upload_links(id, project_id→projects, token_hash, created_by→users, expires_at,
             max_files, max_bytes, revoked_at, use_count, last_used_at)
audit_log(id, org_id, project_id, actor_type enum(user|system|model), actor_id,
          action, object_type, object_id, before jsonb, after jsonb, at)
```

**Noch nicht:** `properties` (die Adresse am Projekt genügt, bis es wiederkehrende Grundstücke gibt), `document_entities` (durch Assertions abgedeckt), `processing_jobs` (gehört der Queue), `application_packages`/`application_documents` (ein eingefrorenes Paket ist eine Manifestzeile plus Storage-Präfix; erst zu Tabellen ausbauen, wenn Paketversionierung real wird).

**Mandantentrennung:** `org_id` auf jeder Wurzeltabelle, durchgesetzt per Postgres Row-Level Security an eine Session-Variable gebunden *und* durch eine Repository-Schicht, die Abfragen ohne Org-Scope verweigert. Doppelt gesichert — diese Daten sind vertraulich und personenbezogen.

**Indizes:** `documents(project_id, doc_type)`, `documents(sha256)`, `fact_assertions(document_id)`, `fact_assertions(fact_type)`, `project_facts(project_id, status)`, `conflicts(project_id, status, severity)`, `review_findings(review_id, severity, status)`, `audit_log(project_id, at DESC)`, `upload_links(token_hash)`.

---

# TEIL 18 — API-DESIGN

REST, JSON, Cursor-Pagination, RFC-9457-Problemdetails für Fehler. Session-Auth für die App; ein separater unauthentifizierter Namensraum für externe Uploads.

**Projekte**
- `POST /api/projects` — {adresse, gemarkung?, flur?, flurstueck?, bisherige_nutzung, geplante_nutzung, vermietungstage_pro_jahr?} → 201. Validiert das Nutzungsvokabular; löst Anforderungssatz und Genehmigungskonstellation auf. `403` bei überschrittenem Kontingent.
- `GET /api/projects?status=&q=` · `GET /api/projects/{id}` (mit Zählern: offene Konflikte, fehlende Nachweise, ungeprüfte Fakten)
- `PATCH /api/projects/{id}` — auditierte Feldänderungen

**Dokumente**
- `POST /api/projects/{id}/documents` — multipart, ≤ 50 Dateien, ≤ 50 MB je Datei. Liefert je Datei angenommen/abgelehnt mit Grund. `409` bei exakter Dublette, mit Link auf das vorhandene Dokument.
- `GET /api/projects/{id}/documents?type=&status=` · `GET /api/documents/{id}` · `GET /api/documents/{id}/pages/{n}/raster`
- `PATCH /api/documents/{id}` — {doc_type, accepted_filename, is_current} — **nur diese drei; alles andere ist abgeleitet**
- `POST /api/documents/{id}/reprocess` · `POST /api/documents/{id}/request-better-source` → erzeugt eine gezielte Nachforderung an den Hochladenden

**Fakten und Konflikte**
- `GET /api/projects/{id}/facts` — kanonische Werte, Status, Herkunft, Konfliktbezüge
- `PUT /api/projects/{id}/facts/{fact_type}` — {wert, quelle: assertion_id | "manuell", notiz} → setzt `bestätigt`/`manuell`, auditiert, stößt Konflikt- und Anforderungsneubewertung an
- `GET /api/projects/{id}/conflicts?severity=&status=`
- `POST /api/conflicts/{id}/resolve` — {gewaehlte_assertion_id | manueller_wert, notiz} → `422`, wenn das Projekt eingefroren ist

**Anforderungen, Erzeugung, Prüfung**
- `GET /api/projects/{id}/requirements` — die Anforderungsliste mit Belegen
- `POST /api/projects/{id}/artifacts` — {art: uebertragungsblatt|betriebsbeschreibung|anschreiben|begruendung} → `422` mit Liste der fehlenden geprüften Fakten, falls Voraussetzungen fehlen. **Dieser Fehler ist eine Funktion:** Er sagt der Architektin genau, was als Nächstes zu tun ist.
- `GET /api/projects/{id}/artifacts/{id}` · `PATCH .../artifacts/{id}` (Inhaltsänderungen, versioniert)
- `POST /api/projects/{id}/reviews` → 202 + Lauf-ID; `GET /api/reviews/{id}` → Befunde
- `POST /api/findings/{id}/dismiss` — {begruendung} — **Begründung verpflichtend, Mindestlänge erzwungen**
- `POST /api/projects/{id}/freeze` → `409`, wenn ein KRITISCH-Befund oder ein ungelöster kritischer Konflikt offen ist, mit Auflistung der Blocker; sonst wird das unveränderliche Paket erzeugt
- `GET /api/projects/{id}/packages/{version}/download`

**Externer Upload (eigener Origin, keine Session)**
- `POST /api/projects/{id}/upload-links` — {gueltig_tage ≤ 30, max_dateien ≤ 50, hinweis} → Token wird **einmalig** zurückgegeben
- `GET /api/u/{token}` → {projektbezeichnung (nur Adresse), Hinweise, Limits} — **niemals** Projektinterna
- `POST /api/u/{token}/files` — multipart, Rate-Limit je Token, Dateigrößenlimit, MIME-Allowlist
- `POST /api/u/{token}/complete` → benachrichtigt die Architektin
- `DELETE /api/projects/{id}/upload-links/{link_id}` — sofortiger Widerruf

Autorisierung: Jede App-Route ist über `org_id` + Projektmitgliedschaft begrenzt. Faktenbestätigung und Paketfreigabe erfordern zusätzlich `rolle ∈ {architekt, inhaber}` — die Bauzeichnerin darf hochladen, Typen korrigieren und vorschlagen, aber nicht bestätigen oder freigeben.

---

# TEIL 19 — UI / UX

Durchgängig deutsche Oberfläche. Gestaltungsprinzip: **Der Bildschirm zeigt, was noch nicht in Ordnung ist.** Alles Erledigte klappt zu.

## 19.1 Vorgangsübersicht (Dashboard)

Eine Zeile je Vorgang: Adresse, Verfahrensart und drei Zähler — `Zu prüfen`, `Konflikte`, `Fehlende Nachweise`. Sortiert nach dem, was blockiert. Keine Diagramme, keine Prozentwerte, kein „KI-Insights“-Panel.
*Leerzustand:* eine Schaltfläche, „Vorgang anlegen“. *Ladezustand:* Skeleton-Zeilen. *Fehler:* inline mit Wiederholen, nie ein Modal.

## 19.2 Vorgang – Übersicht

Vier Karten, jede verlinkt ihre Fläche: **Unterlagen** (n gesamt · n zu prüfen · n unbrauchbar) · **Projektdaten** (n von 30 bestätigt) · **Konflikte** (Schweregrad-Chips) · **Verfahren** (Konstellation mit Status je Strang, der Zweckentfremdungsstrang gut sichtbar). Darunter eine deterministisch berechnete Zeile in Klartext: „Nächster sinnvoller Schritt“.

## 19.3 Dokumenteneingang

Geteilte Ansicht: Liste links, Seitenvorschau rechts. Je Zeile: Miniatur, Namensvorschlag (inline editierbar), Typ-Chip (editierbar), Qualitätsbadge, Status. Sammelaktionen: Namen übernehmen, Typen übernehmen, bessere Vorlage anfordern. Filter-Chips bilden die Prüfliste. **Unsichere Fälle stehen oben; nichts wird vergraben.**
*KI-Unsicherheitszustand:* Der Typ-Chip zeigt `unklar` in Bernstein mit „Bitte einordnen“ — nie ein stiller Rateversuch.

## 19.4 Verarbeitung

Je Dokument Phasenhaken (Empfangen → Geprüft → Text erkannt → Eingeordnet → Daten gelesen) mit realistischen Laufzeiten je Phase. Fehler sind sichtbar und wiederholbar. Nie ein Spinner ohne Phasennamen.

## 19.5 Projektdaten (Faktenblatt)

Nach Kategorien gruppiert. Je Zeile: Bezeichnung, Wert, Status-Chip, Quellen-Chip. Ein Klick auf den Quellen-Chip öffnet die Seite mit hervorgehobenem Bereich — **das ist die Vertrauensfunktion; geben Sie ihr das Animationsbudget.** Bestätigen ist ein Tastendruck; `Alle offensichtlichen bestätigen` bestätigt nur Fakten mit hoher Gesamtkonfidenz aus nativem Text und sagt genau, wie viele. Fakten ohne mögliche Dokumentquelle erscheinen als Aufgabe: „Von Ihnen einzutragen“.

## 19.6 Konfliktzentrum

```
KONFLIKTE                                                   2 kritisch · 4 Warnungen

🔴  Flurstück                                                          KRITISCH
    Zwei unterschiedliche Angaben in den Unterlagen.

    WERT A   143/2      Liegenschaftskarte_2024-03-12.pdf, S. 1   [Quelle öffnen]
    WERT B   143        Bauantrag_Entwurf.pdf, S. 1               [Quelle öffnen]

    Hinweis: Ein abweichendes Flurstück führt regelmäßig zu einer Nachforderung.

    [ 143/2 übernehmen ]  [ 143 übernehmen ]  [ Eigener Wert ]  [ Quelle prüfen ]

🟠  Wohnfläche / Nutzfläche                                            WARNUNG
    92,4 m² (Wohnfläche n. WoFlV) vs. 96,2 m² (Nutzfläche n. DIN 277).
    Unterschiedliche Bezugsgrößen — häufig kein Widerspruch.
    [ Als geklärt markieren ]  [ Beide übernehmen ]
```

Beide Quellausschnitte werden nebeneinander in lesbarer Größe gezeigt. Die Entscheidung wird mit Person, Zeitstempel und Notiz protokolliert.

## 19.7 Anforderungsliste

Der in der Vorlage am schwächsten spezifizierte und in der Praxis nützlichste Bildschirm. Eine Checkliste der für dieses Verfahren erforderlichen Nachweise, je mit Status, dem erfüllenden Dokument und der Rechtsgrundlage im Tooltip. Fehlende Punkte haben eine Schaltfläche „Anfordern“, die die Nachricht an den Eigentümer vorbereitet. Dieser Bildschirm allein würde das Produkt verkaufen.

## 19.8 Antragsvorbereitung

Links: Artefaktliste. Rechts: Editor mit den drei visuell unterschiedenen Inhaltsklassen (grau = aus geprüftem Fakt, bernsteinfarbener Rand = KI-Entwurf vor Annahme, neutral = Vorlage). Fehlende Fakten erscheinen als rote Inline-Platzhalter mit Link ins Faktenblatt. Nichts wird erzeugt, bevor die Voraussetzungen erfüllt sind, und der Fehler nennt genau, was zu tun ist.

## 19.9 Regel- und Formularstand

Eine Tabelle aller angewandten Regeln und Formulare mit Quelle, letztem Prüfdatum, Gültigkeitsfenster und „Quelle öffnen“. Alles, was in den nächsten 90 Tagen abläuft, ist hervorgehoben. Dieser Bildschirm macht die Ehrlichkeit des Produkts sichtbar.

## 19.10 Einreichungsprüfung

Befunde nach Schweregrad gruppiert, aufklappbar zu Beobachtung / Grundlage / Beleg / Maßnahme. Eine feste Kopfzeile zeigt das Freigabetor. Erneute Prüfung mit einem Klick, mit Diff zum vorherigen Lauf.

## 19.11 Einreichungspaket

Ordnervorschau, Manifest, Hash, Prüfprotokoll-Download und — prominent — das **Portal-Übertragungsblatt** mit Kopierschaltflächen je Feld sowie einem Link zum Bauportal.NRW. Ein ausblendbarer Hinweis, dass die Einreichung im Portal erfolgt und Handlung der Architektin ist.

## 19.12 Externe Upload-Seite

Eine Spalte, keine Navigation, kein Branding über eine dezente Marke hinaus:

```
Unterlagen hochladen

Kirschblütenweg 7, 53129 Bonn

Bitte laden Sie die angeforderten Unterlagen hoch.
Fotos sind in Ordnung — bitte flach, gut beleuchtet und vollständig.

Angefragt:
  · Grundbuchauszug (alle Seiten)
  · Alte Baugenehmigung, falls vorhanden
  · Wohnflächenberechnung

[ Foto aufnehmen ]      [ Dateien auswählen ]

hochgeladen: Grundbuch_1.jpg ✓  Grundbuch_2.jpg ✓

[ Absenden ]
```

Sofortige clientseitige Qualitätsrückmeldung („Das Foto ist unscharf — bitte erneut aufnehmen“) noch vor Abschluss des Uploads ist mehr wert als jede serverseitige Pipeline, weil die Eigentümerin noch vor dem Dokument steht.

---

# TEIL 20 — SICHERHEIT UND DSGVO

## 20.1 Technische Anforderungen (bauen)

Hosting und Verarbeitung in der EU, auf deutscher oder EU-Infrastruktur, mit dokumentierter Liste der Unterauftragsverarbeiter. TLS 1.3 im Transport; AES-256 im Ruhezustand; Objektspeicher mit serverseitiger Verschlüsselung und ohne öffentlichen Zugriff. Argon2id für Passwort-Hashing, TOTP-2FA verfügbar, kurze Sessions. Mandantentrennung auf Zeilenebene (Teil 17). Datenminimierung an der Prompt-Grenze: **nur die für die aktuelle Extraktion nötigen Seiten gehen an das Modell**, nie das ganze Projekt. Malware-Scan bei jedem Upload, auch extern. Unveränderliches, nur anfügbares Audit-Log über jede KI-Entscheidung und jede menschliche Korrektur. Projektbezogener Export und harte Löschung inklusive abgeleiteter Artefakte, Raster-Caches und vektorisierter Kopien. Backups verschlüsselt, retentionsbegrenzt, Restore getestet. Secrets im verwalteten Speicher. Tokenisierte Upload-Links: zweckgebunden, gehasht gespeichert, ablaufend, widerrufbar, ratenbegrenzt, nur Upload, ohne Lesepfad auf Projektdaten.

## 20.2 Was eine Rechts-, keine Engineering-Frage ist

Ausdrücklich markiert, zu klären mit einer/einem Datenschutzbeauftragten und — für die berufsrechtlichen Teile — mit der Architektenkammer:

- Ob eine DSFA (Art. 35 DSGVO) erforderlich ist. Bei systematischer automatisierter Verarbeitung personenbezogener Daten aus Grundbuchunterlagen, Korrespondenz und ggf. Dritten (Nachbarn, Voreigentümer) — von „ja“ ausgehen und einplanen.
- Auftragsverarbeitungsvertrag mit dem LLM-Anbieter: Datenort, Aufbewahrung und vertraglicher Ausschluss des Trainings mit Kundendaten. Ist dieser Ausschluss für das gewählte Modell nicht erreichbar, muss die Architektur ein selbst gehostetes oder EU-ansässiges Modell für die Extraktion tragen. **Die LLM-Schnittstelle vom ersten Tag an austauschbar gestalten.**
- Rechtsgrundlage für die Verarbeitung von Daten Dritter, die nicht Kunde sind (Daten der Eigentümerin über die Architektin; in Altunterlagen genannte Dritte).
- Die berufsrechtliche Verschwiegenheitspflicht der Architektin und die Frage, ob die Weitergabe an einen Auftragsverarbeiter eine Mandantenzustimmung im Architektenvertrag erfordert.
- Aufbewahrung: Bauakten werden üblicherweise viele Jahre aufbewahrt; das ist eine Pflicht des Büros, kein SaaS-Standardwert.
- Haftungsverteilung in den AGB und — getrennt davon — ob die Ausgaben des Produkts als Rechtsdienstleistung im Sinne des RDG verstanden werden könnten. Das ist der Punkt, der das Unternehmen erledigen kann, und der Grund, warum jeder Befund „prüfen“ sagt und nie „ist zulässig“. **Fachliche Stellungnahme vor dem Start einholen, nicht danach.**

Digital Deutschland leistet keine Rechtsberatung und darf auch nicht so wirken.

---

# TEIL 21 — FEHLERMODI

| # | Fehler | Prävention | Erkennung | Menschliches Tor | UX-Behandlung |
|---|---|---|---|---|---|
| 1 | **Zifferndreher in Flurstück/Aktenzeichen** (143/2 → 143) | Formatvalidierung; nativer Text bevorzugt; keine Extraktion unter DPI-Schwelle | Dokumentübergreifender Vergleich; formatgeprüft | Immer vor jeder Verwendung bestätigt | Quellausschnitt bei der Bestätigung |
| 2 | **Deutsche Zahl-/Datumsformate** (92,4 → 924; 03.09.26 falsch geparst) | Locale-bewusste Parser; Einheit bei jedem numerischen Fakt Pflicht | Plausibilitätsbänder je Faktentyp | Werte außerhalb des Bands immer menschlich geprüft | „Wert unplausibel — bitte prüfen“ |
| 3 | **Halluzinierter Fakt ohne Quelle** | Anker (Seite+bbox) verpflichtend; unverankerte Ausgabe verworfen | Automatische Nachvalidierung | entfällt — vor der Anzeige verworfen | Erreicht die Nutzerin nie |
| 4 | **Falscher Flächenkonflikt** (WoFlV vs. DIN 277) | Typisierte Fakten mit Definitionen; nie kreuzweise verglichen | Fachliche Beziehungsregeln | Erledigung mit Begründung | WARNUNG mit Erläuterung, nicht KRITISCH |
| 5 | **Fehlklassifikation** (Bestandsplan als Entwurfsplan) | `unklar` stets erlaubt; Konfidenztor | Anforderungserfüllung wirkt falsch; Prüfliste | Typänderung ist ein Klick | Bernstein-Chip, nicht still |
| 6 | **Falsche Fassung als aktuell** | Keine automatische Ablösung; Mensch bestätigt | Zwei aktuelle Dokumente eines Typs mit abweichenden Fakten → Auto-Konflikt | Verpflichtend | „Bitte gültige Fassung bestätigen“ |
| 7 | **Erfundene oder veraltete Regel** | Modell darf nicht zitieren; nur Registereinträge sind `grundlage` | Befunde mit unauflösbarer Grundlage werden verworfen und protokolliert | Kurator | Regelstand steht in jeder Prüfung |
| 8 | **Veraltetes Formular** | Hash- + Versionskennungsvergleich | Nächtlicher Überwachungs-Diff | Kurator verifiziert | Nur drei Urteile; „nicht verifizierbar“ ist legitim |
| 9 | **Übersehener Konflikt (falsch negativ)** | Geschlossener Faktenkatalog; jeder Fakt verglichen; Extraktions-Recall gemessen | Goldstandard-Regression; Post-Mortems zu echten Nachforderungen | — | Nie „keine Widersprüche“ behaupten; „keine Widersprüche in den geprüften Angaben“ |
| 10 | **Scheinsicherheit durch einen sauberen Bericht** | Kein Score; ausdrückliche Nennung dessen, was *nicht* geprüft wurde | — | — | Die Fußzeile listet ungeprüfte Bereiche namentlich |
| 11 | **Übersehenes Parallelverfahren** | Konstellation bei Vorgangsanlage aus strukturierter Erfassung aufgelöst, nicht aus Dokumenten | `unbekannt_wenn`-Befunde bei fehlenden Eingaben | Architektin bestätigt die Konstellation | Zweckentfremdungsstrang immer sichtbar |
| 12 | **Eigentümer lädt fremde Unterlagen / falsches Grundstück hoch** | Adresse steht auf der Upload-Seite | Adress-/Flurstücksabgleich gegen Projektfakten → sofortiger Konflikt | Architektin | „Diese Unterlage betrifft möglicherweise ein anderes Grundstück“ |
| 13 | **Bösartiger Upload über den öffentlichen Link** | MIME-Allowlist, Größen- und Anzahllimits, Malware-Scan, Rate-Limiting, kein Ausführungspfad, isolierter Speicher | Scanner + Anomaliealarme | Link widerrufen | Für den Hochladenden unsichtbar |
| 14 | **Prompt Injection aus Dokumentinhalten** | Dokumenttext wird als Daten in einem abgegrenzten Kanal übergeben; Systemanweisungen werden nie aus Inhalten abgeleitet; Ausgabe schemagebunden | Schemavalidierung; Mustererkennung verdächtiger Anweisungen | — | Dokument zur Prüfung markiert |
| 15 | **Modell- oder Anbieterausfall** | Queue mit Backoff; Degraded Mode (deterministische Prüfungen laufen weiter) | Health Checks | — | „KI-Verarbeitung verzögert — Prüfungen laufen weiter“ |
| 16 | **Stille Regression nach Modellupdate** | Modellversion gepinnt; Goldstandard-Gate in CI | Automatisierte Evaluation | Release-Tor | Version steht im Prüfprotokoll |

**Fehler 10 verdient Nachdruck.** Der wahrscheinlichste Weg, auf dem dieses Produkt einer Architektin schadet, ist nicht, falsch zu liegen, sondern beruhigend zu wirken. Jeder Bericht muss seine eigenen Grenzen in klarem Deutsch nennen, und das Einfrier-Artefakt muss sie festhalten.

---

# TEIL 22 — HUMAN-IN-THE-LOOP-MODELL

| Klasse | Beispiele | Regel |
|---|---|---|
| **Vollautomatisch** | Hash, Dublettenerkennung, Metadaten, Qualitätsbewertung, Thumbnails, OCR, Normalisierung, Vergleich, Regelauswertung, Überwachungs-Diffs | Keine Freigabe |
| **Automatisch, umkehrbar, sichtbar** | Namensvorschlag, Ordnervorschlag, Dokumenttyp bei hoher Konfidenz, Near-Duplicate-Gruppierung | Standardmäßig übernommen mit Sammel-Undo; jede Änderung auditiert |
| **Vorgeschlagen, nie ohne Mensch angewandt** | Jeder Projektfakt; Versionsbeziehungen; kanonischer Wert bei Konflikt; Inhalt jedes erzeugten Artefakts | Ausdrückliche Bestätigung mit Person und Zeitstempel |
| **Nur Architektin (bauvorlageberechtigt)** | Verfahrensart bestätigen, KI-Entwurf annehmen, KRITISCH-Befund erledigen, Paket einfrieren | Rollengebunden; Erledigung erfordert schriftliche Begründung |
| **Niemals Sache des Systems** | Einreichung; jede rechtliche Schlussfolgerung; jede Aussage zur Genehmigungsfähigkeit; Kommunikation mit einer Behörde | Gar nicht implementiert |

Zwei strukturelle Regeln: **Ein KRITISCH-Befund sperrt das Einfrieren** (nur durch eine Architektin mit Begründung erledigbar, die ins Prüfprotokoll wandert); und **jeder KI-stammende Wert, der in ein erzeugtes Artefakt gelangt, hat genau eine menschliche Bestätigung durchlaufen** — nicht mehr, nicht weniger. Mehr wäre Theater, weniger wäre fahrlässig.

---

# TEIL 23 — MVP-DEMO: DAS BONNER SZENARIO

## 23.1 Szenario (synthetisch)

Ein Zweifamilienhaus, **Kirschblütenweg 7, 53129 Bonn-Dottendorf**, Gemarkung Dottendorf, Flur 12, Flurstück 143/2, Baujahr 1963. Die obere Einheit (ca. 92 m²) wurde 2024 von einer **Erbengemeinschaft aus drei Geschwistern** geerbt. Eine Schwester, Frau Weber, will sie ganzjährig als **Ferienhaus** vermieten, rund 200 Nächte im Jahr. Das Architekturbüro soll die Nutzungsänderung vorbereiten. Das Grundstück liegt im Geltungsbereich eines B-Plans, der ein **Allgemeines Wohngebiet** festsetzt. Es existiert eine **Teilungserklärung**, weil das Haus 1998 in zwei Sondereigentumseinheiten aufgeteilt wurde.

Jedes dieser Details ist eine Mine, und die Demo zündet sie der Reihe nach.

## 23.2 Der Datensatz aus 26 Dokumenten

| # | Dateiname | Typ | Qualität | Eingebautes Problem |
|---|---|---|---|---|
| 1 | `IMG_8392.jpg` | Grundbuchauszug S.1 | Handyfoto, 8° schief | Nennt drei Eigentümer (Erbengemeinschaft) |
| 2 | `IMG_8393.jpg` | Grundbuchauszug S.2 | Schattig, Daumen im Bild | — |
| 3 | `IMG_8394.jpg` | Grundbuchauszug S.3 | Unteres Drittel unscharf | Abt.-II-Eintrag teils unlesbar |
| 4 | `Scan001.pdf` | Baugenehmigung 1963 | Reines Bild-PDF, frakturartige Überschriften | Genehmigte Nutzung: „Zweifamilienhaus“ |
| 5 | `Scan002.pdf` | Bestandsplan 1963 | Blasser Blaupausen-Scan | Handschriftliche Raumflächen |
| 6 | `Grundriss_OG_neu.pdf` | Grundriss | Sauberer Vektor | Flurstück **143** im Plankopf ⚠ |
| 7 | `Grundriss_OG_final.pdf` | Grundriss | Sauberer Vektor, 3 Wochen später | Gleicher Plan, kleine Änderung — Versionskandidat |
| 8 | `Grundriss_EG.pdf` | Grundriss | Sauber | — |
| 9 | `Schnitt_AA.pdf` | Schnitt | Sauber | — |
| 10 | `Ansichten.pdf` | Ansichten | Sauber | — |
| 11 | `Wohnflaeche.docx` | Flächenberechnung | Word | **92,4 m² Wohnfläche n. WoFlV** |
| 12 | `Flaechen_Architekt.xlsx→pdf` | Flächenberechnung | Sauber | **96,2 m² Nutzfläche n. DIN 277** ⚠ (harmlos) |
| 13 | `Liegenschaftskarte.pdf` | Liegenschaftskarte | Amtlich, sauber | Flurstück **143/2** ✓ |
| 14 | `Teilungserklaerung_1998.pdf` | WEG-Unterlage | Scan, 40 S. | Sondereigentum „zu Wohnzwecken“ ⚠⚠ |
| 15 | `Brief_Bauamt.jpg` | Behördenschreiben | Foto eines Briefs | Rückfrage von 2019 zu einem früheren Vorhaben |
| 16 | `mail_eigentuemer.pdf` | Korrespondenz | Gedruckte E-Mail | Nennt „ganzjährig, ca. 200 Nächte“ ⚠⚠⚠ |
| 17 | `Bauantrag_Entwurf_2021.pdf` | Antragsformular | Ausgefülltes Formular der 2021er Fassung | **Veraltetes Formular** ⚠ |
| 18 | `Betriebsbeschreibung_Entwurf.docx` | Betriebsbeschreibung | Entwurf | Sagt „Ferienwohnung“, 4 Gäste |
| 19 | `Foto_Strasse.jpg` | Bestandsfoto | Handy | — |
| 20 | `Foto_Stellplatz.jpg` | Bestandsfoto | Handy | Zeigt **einen** Stellplatz |
| 21 | `Foto_Treppenhaus.jpg` | Bestandsfoto | Dunkel | Rettungswegrelevanz |
| 22 | `Scan001 (1).pdf` | Dublette von #4 | — | **Exakte Dublette** |
| 23 | `grundriss_og_neu_kopie.pdf` | Dublette von #6 | — | **Near-Duplicate, anderer Name** |
| 24 | `Notiz.jpg` | Handschriftliche Notiz | Handschrift | „ca. 6 Betten?“ — darf NICHT automatisch extrahiert werden |
| 25 | `Energieausweis.pdf` | Sonstiges | Sauber | Nicht erforderlich — muss als Nicht-Nachweis eingeordnet werden |
| 26 | `Kaufvertrag_Auszug.pdf` | Vertragsauszug | Scan, teils geschwärzt | Nennt nur eine der Geschwister ⚠ |

## 23.3 Die eingebauten Befunde und was jeder beweist

| Befund | Schweregrad | Beweist |
|---|---|---|
| Flurstück 143 vs. 143/2 (#6, #17 gegen #13) | KRITISCH | USP 1 am klassischsten Nachforderungsauslöser |
| Bauherrschaft = eine Person, Grundbuch = Erbengemeinschaft (#1 gegen #17, #26) | KRITISCH | Das System liest *Berechtigung*, nicht nur Namen |
| 200 Vermietungsnächte > 90 (#16) | KRITISCH-PARALLELVERFAHREN | **Der entscheidende Befund.** Zweckentfremdungsgenehmigung erforderlich — ein Verfahren, an das im Raum niemand gedacht hat |
| Teilungserklärung beschränkt Sondereigentum auf Wohnzwecke (#14) | WARNUNG (privatrechtlich) | Das System markiert ein Risiko, das keine Behörde aufwirft |
| Allgemeines Wohngebiet + Ferienwohnung ≠ Wohnen | WARNUNG | Planungsrechtliche Zulässigkeit als Frage aufgeworfen, nie beantwortet |
| Formularfassung 2021 (#17) | FORMULAR NICHT VERIFIZIERBAR | USP 3, live, wegen der Änderung zum 1.9.2026 |
| 92,4 vs. 96,2 m² (#11 gegen #12) | WARNUNG mit Erläuterung | Das System versteht die Fachwelt und ruft **nicht** „Wolf“ |
| Zwei aktuelle Grundrisse (#6, #7) | Versionsrückfrage | Ehrliche Unsicherheit statt Rateversuch |
| Dubletten (#22, #23) | HINWEIS | Ordnung |
| Handschriftliches „6 Betten?“ (#24) | Eingabeaufgabe | Das System weigert sich zu raten |
| Ein Stellplatz, Bedarf unbekannt (#20) | FEHLENDE ANGABE | `unbekannt_wenn` erzeugt einen Befund, kein Schweigen |
| Grundbuch S. 3 teils unlesbar (#3) | Bessere Vorlage anfordern | Qualitätsworkflow mit Ein-Klick-Anfrage |

Zwölf vorführbare Momente aus sechsundzwanzig Dateien. Das ist die Demo.

## 23.4 Demoskript (12 Minuten)

**0:00 – 1:00 · Das Problem.** Ein Screenshot des echten Projektordners des Büros. „So sieht Dienstagmorgen aus.“

**1:00 – 2:00 · Vorgang anlegen.** Fünf Felder. Sobald „ca. 200 Nächte/Jahr“ eingetragen ist, zeigt das System die Genehmigungskonstellation: **zwei Verfahren, nicht eines.** *Erster Wow-Moment, in den ersten zwei Minuten, bevor irgendeine KI gelaufen ist.*

**2:00 – 3:30 · Upload.** 20 Dateien hineinziehen; den Link an „Frau Weber“ auf ein Handy im Bild schicken; sie fotografiert das Grundbuch schlecht, und die Seite sagt ihr, dass das dritte Foto unscharf ist. Echt, menschlich, einprägsam.

**3:30 – 5:00 · Verarbeitung.** Live. Dateien landen typisiert und benannt. Zwei gehen in die Prüfung. Eine wird als unbrauchbar markiert, samt erzeugter Nachforderung.

**5:00 – 6:30 · Anforderungsliste.** 13 von 17 belegt, jeweils mit Beleg. Vier offen. „Das macht sie heute mit Kaffee und Textmarker.“

**6:30 – 8:00 · Faktenblatt und Herkunft.** Fakten bestätigen; einen Wert anklicken; die Grundbuchseite öffnet sich mit hervorgehobenem Bereich. *Zweiter Wow-Moment — hier stirbt die Skepsis.*

**8:00 – 9:30 · Konfliktzentrum.** Den Flurstückskonflikt mit beiden Ausschnitten nebeneinander lösen. Dann zeigen, wie der Flächen-„Konflikt“ korrekt als zwei verschiedene Definitionen erklärt wird. *Dritter Wow-Moment: das Werkzeug, das weiß, was kein Problem ist.*

**9:30 – 10:30 · Antragsvorbereitung.** Betriebsbeschreibung erzeugt; Fakten grau, KI-Prosa bernstein. Absichtlich einen bestätigten Fakt löschen, um zu zeigen, wie die Erzeugung mit präziser Begründung verweigert.

**10:30 – 11:30 · Einreichungsprüfung.** Die Befundliste, angeführt vom Zweckentfremdungsbefund und der Vertretungslücke der Erbengemeinschaft. Dann der Regel- und Formularstand mit dem 2021er Formular als *nicht verifizierbar* seit dem 1. September 2026. *Vierter Wow-Moment.*

**11:30 – 12:00 · Paket und Übertragungsblatt.** Einfrieren durch die zwei kritischen Befunde blockiert. Lösen. Einfrieren. Prüfprotokoll und Portal-Übertragungsblatt zeigen. Schluss mit: *„Sie reichen im Bauportal ein. Wir sorgen dafür, dass nichts zurückkommt.“*
