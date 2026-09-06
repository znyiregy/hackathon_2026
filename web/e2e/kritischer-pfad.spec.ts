import { expect, test } from "@playwright/test";

import { backendAus, backendStellen, VORGANG_ID } from "./backend";

/**
 * Open the Akte and switch to a tab.
 *
 * Below 1050px the assistant and the Akte share the screen through a
 * switcher, because the assistant is the primary surface and must not be
 * squeezed. The same walk therefore needs one extra tap on a phone.
 */
async function reiterOeffnen(page: import("@playwright/test").Page, name: string | RegExp) {
  // Kein exact: der Umschalter trägt eine Zahl, sobald etwas offen ist —
  // dann heißt er "Zum Projekt 1" und eine exakte Suche ginge ins Leere.
  const umschalter = page.getByRole("tab", { name: /^Zum Projekt/ });
  if (await umschalter.isVisible()) {
    await umschalter.click();
  }
  await page.getByRole("tab", { name }).click();
}

/**
 * The critical path, end to end in a real browser.
 *
 * This is the walk the demo takes and the walk an Architektin takes on her
 * first real case: create a Vorgang → upload documents → the assistant reports
 * what changed → a conflict appears → resolve it → the package stays locked
 * because something critical is still open.
 */
test.describe("Kritischer Pfad", () => {
  test("Vorgang anlegen, Unterlagen hochladen, Widerspruch lösen", async ({
    page,
  }) => {
    const zustand = await backendStellen(page);

    // -- 1. Leere Übersicht ------------------------------------------------
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: "Meine Projekte" }),
    ).toBeVisible();
    await expect(page.getByText("Noch kein Projekt")).toBeVisible();

    // -- 2. Vorgang anlegen ------------------------------------------------
    await page.getByRole("button", { name: "Projekt anlegen" }).first().click();
    await page
      .getByRole("textbox", { name: "Adresse" })
      .fill("Am Weiher 7");

    // Die Zweckentfremdungs-Warnung erscheint bei über 90 Tagen sofort —
    // das ist der Punkt, den sonst keine Behörde prüft.
    await expect(
      page.getByText(/zusätzlich eine Erlaubnis von einem zweiten Amt/),
    ).toBeVisible();

    await page
      .getByRole("button", { name: "Projekt anlegen", exact: true })
      .last()
      .click();

    // -- 3. Der Assistent ist die Hauptfläche ------------------------------
    await expect(page).toHaveURL(new RegExp(`/vorgang/${VORGANG_ID}`));
    await expect(
      page.getByRole("heading", { name: "Am Weiher 7, 53229 Bonn" }),
    ).toBeVisible();
    await expect(page.getByText(/Guten Tag\. Ziehen Sie Ihre Unterlagen/)).toBeVisible();

    // Der kritische Parallelstrang steht sichtbar in der Akte.
    await reiterOeffnen(page, "Überblick");
    await expect(page.getByText("Zweckentfremdung").first()).toBeVisible();
    await expect(page.getByText("kritisch").first()).toBeVisible();

    // -- 4. Assistent antwortet und zeigt seine Werkzeuge ------------------
    const assistentUmschalter = page.getByRole("tab", { name: "Assistent" });
    if (await assistentUmschalter.isVisible()) await assistentUmschalter.click();
    await page.getByRole("button", { name: "Was fehlt noch?" }).click();
    await expect(
      page.getByText(/Es fehlen derzeit fünf Pflichtunterlagen/),
    ).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/Nachgesehen, wie das Projekt steht/)).toBeVisible();
    expect(zustand.assistentAufrufe).toBeGreaterThan(0);

    // -- 5. Unterlagen hochladen ------------------------------------------
    await page.setInputFiles('input[type="file"][multiple]', [
      {
        name: "flurkarte.pdf",
        mimeType: "application/pdf",
        buffer: Buffer.from("%PDF-1.4 testinhalt"),
      },
    ]);
    await expect(page.getByText(/flurkarte\.pdf → flurkarte/)).toBeVisible({
      timeout: 20_000,
    });

    // -- 6. Der Widerspruch ist da ----------------------------------------
    await reiterOeffnen(page, /Passt nicht/);
    // An die Akte gebunden: auf dem Handy liegt der Assistent daneben und
    // enthält teils dieselben Wörter.
    const akte = page.getByRole("tabpanel");
    await expect(akte.getByText("Eigentümer").first()).toBeVisible();
    await expect(akte.getByText("Gerold Brämer").first()).toBeVisible();
    await expect(akte.getByText("Jennifer Hönig-Singh").first()).toBeVisible();
    // Beide Quellen werden genannt — das ist der Beleg, nicht die Behauptung.
    await expect(akte.getByText("bauschein.pdf").first()).toBeVisible();

    // -- 7. Widerspruch lösen ---------------------------------------------
    await page
      .getByRole("button", { name: "Jennifer Hönig-Singh übernehmen" })
      .click();
    await expect(
      akte.getByText("Alles passt zusammen."),
    ).toBeVisible({ timeout: 10_000 });
    expect(zustand.konfliktOffen).toBe(false);

    // -- 8. Freigabe bleibt gesperrt, weil Kritisches offen ist ------------
    await reiterOeffnen(page, /Prüfung/);
    await expect(page.getByText(/Noch nicht fertig/)).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Alles festschreiben" }),
    ).toBeDisabled();

    // Die Zweckentfremdung ist der Grund und wird benannt.
    await expect(page.getByText(/braucht Bonn dafür eine zusätzliche Erlaubnis/)).toBeVisible();
  });

  test("Projektdaten bestätigen", async ({ page }) => {
    await backendStellen(page);
    await page.goto(`/vorgang/${VORGANG_ID}`);

    await reiterOeffnen(page, "Angaben");
    await expect(page.getByText("Flurstück").first()).toBeVisible();
    await expect(page.getByText("KI-Vorschlag").first()).toBeVisible();

    // Die Quelle steht neben jedem Wert; die Seite selbst prüft der eigene
    // Test unter "Quellvorschau".
    await expect(
      page.getByRole("button", { name: /Wo steht das\?/ }).first(),
    ).toBeVisible();

    await page.getByRole("button", { name: "Bestätigen" }).first().click();
    // Der Status-Chip wechselt von "KI-Entwurf" auf "bestätigt".
    await expect(
      page.locator(".chip-bestaetigt", { hasText: "bestätigt" }).first(),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("Antragsentwurf entsteht erst, wenn die Grundlagen stehen", async ({
    page,
  }) => {
    await backendStellen(page);
    await page.goto(`/vorgang/${VORGANG_ID}`);

    await reiterOeffnen(page, "Antrag");

    // Was noch nicht kann, sagt auch warum.
    await expect(page.getByText("geht noch nicht")).toBeVisible();
    await expect(page.getByText(/Bestätigen Sie zuerst: Flurstück/)).toBeVisible();

    await page.getByRole("button", { name: "Text schreiben" }).first().click();
    await expect(page.getByText(/Die Ferienwohnung im 1. Obergeschoss/)).toBeVisible({
      timeout: 15_000,
    });
    // Lücken sind sichtbar markiert, nicht stillschweigend erfunden.
    await expect(page.getByText("Gästezahl ergänzen").first()).toBeVisible();
  });

  test("Portal-Übertragungsblatt trennt bestätigt, Entwurf und fehlend", async ({
    page,
  }) => {
    await backendStellen(page);
    await page.goto(`/vorgang/${VORGANG_ID}`);

    await reiterOeffnen(page, "Fertig machen");
    await expect(page.getByText(/Werte tippen Sie ins Amtsportal/)).toBeVisible();
    await expect(page.getByText("Am Weiher 7").first()).toBeVisible();
    await expect(
      page.getByText("Noch kein Wert. Im Faktenblatt ergänzen."),
    ).toBeVisible();

    // Das Produkt reicht nie selbst ein und sagt das auch.
    await expect(
      page.getByText(/Abschicken müssen Sie selbst/),
    ).toBeVisible();
  });
});

test.describe("Externe Upload-Seite", () => {
  test("ohne Login bedienbar, ohne Details zum Vorgang", async ({ page }) => {
    await backendStellen(page);
    await page.goto("/upload/testtoken123");

    await expect(
      page.getByRole("heading", { name: "Unterlagen hochladen" }),
    ).toBeVisible();
    await expect(page.getByText("Am Weiher 7, 53229 Bonn").first()).toBeVisible();
    await expect(page.getByText("Grundbuchauszug (alle Seiten)")).toBeVisible();

    // Frau Weber darf das Wort "Konflikt" nie sehen.
    await expect(page.getByText(/Widerspruch|Konflikt/)).toHaveCount(0);
    // Und es gibt keinen Login.
    await expect(page.getByText(/Anmelden|Passwort/)).toHaveCount(0);

    await expect(page.getByRole("button", { name: "Absenden" })).toBeDisabled();
  });

  test("abgelaufener Link meldet neutral, ohne Fehlercode", async ({ page }) => {
    await backendStellen(page);
    await page.goto("/upload/abgelaufen");

    await expect(
      page.getByRole("heading", { name: "Dieser Link ist nicht mehr gültig" }),
    ).toBeVisible();
    await expect(page.getByText(/404|Fehler|error/i)).toHaveCount(0);
  });
});

test.describe("Wenn der Motor aus ist", () => {
  test("die Übersicht sagt es und bietet einen erneuten Versuch", async ({
    page,
  }) => {
    await backendAus(page);
    await page.goto("/");

    await expect(page.getByText(/Motor ist nicht erreichbar/)).toBeVisible({
      timeout: 15_000,
    });
    await expect(
      page.getByRole("button", { name: "Erneut versuchen" }),
    ).toBeVisible();
  });

  test("die Upload-Seite behauptet nicht, der Link sei ungültig", async ({
    page,
  }) => {
    await backendAus(page);
    await page.goto("/upload/testtoken123");

    // Ein ausgefallener Motor ist kein abgelaufener Link — sonst gibt die
    // Eigentümerin auf, obwohl mit ihrem Link alles in Ordnung ist.
    await expect(
      page.getByRole("heading", { name: "Gerade nicht erreichbar" }),
    ).toBeVisible({ timeout: 15_000 });
    await expect(
      page.getByRole("heading", { name: "Dieser Link ist nicht mehr gültig" }),
    ).toHaveCount(0);
  });
});

test.describe("Mobil", () => {
  test("keine Seite schiebt sich seitlich auf", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "mobil", "Nur im Mobil-Projekt sinnvoll.");
    await backendStellen(page);

    for (const pfad of ["/", `/vorgang/${VORGANG_ID}`, "/upload/testtoken123", "/regelwerk"]) {
      await page.goto(pfad);
      await page.waitForLoadState("networkidle");

      // Ein waagerechter Überlauf ist auf dem Handy immer ein Fehler: die
      // Nutzerin schiebt die Seite versehentlich zur Seite und verliert den
      // Bezug. Eine reine 1fr-Rasterspalte war hier schon einmal die Ursache.
      const masse = await page.evaluate(() => ({
        viewport: document.documentElement.clientWidth,
        dokument: document.documentElement.scrollWidth,
      }));
      expect(masse.dokument, `Waagerechter Überlauf auf ${pfad}`).toBeLessThanOrEqual(
        masse.viewport + 1,
      );
    }
  });

  test("alle Reiter der Akte sind erreichbar und groß genug", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "mobil", "Nur im Mobil-Projekt sinnvoll.");
    await backendStellen(page);
    await page.goto(`/vorgang/${VORGANG_ID}`);
    await page.getByRole("tab", { name: /^Zum Projekt/ }).click();

    for (const name of ["Überblick", "Angaben", "Passt nicht", "Checkliste", "Prüfung", "Antrag", "Fertig machen"]) {
      const reiter = page.getByRole("tab", { name: new RegExp(`^${name}`) });
      await expect(reiter).toBeVisible();
      const kasten = await reiter.boundingBox();
      // 44px ist die Mindestgröße, die sich mit dem Daumen sicher treffen lässt.
      expect(kasten!.height, `${name} ist zu klein zum Antippen`).toBeGreaterThanOrEqual(44);
      await reiter.click();
    }
  });
});

test.describe("Quellvorschau", () => {
  test("jede Behauptung ist einen Klick von ihrer Seite entfernt", async ({
    page,
  }) => {
    await backendStellen(page);
    await page.goto(`/vorgang/${VORGANG_ID}`);
    await reiterOeffnen(page, "Angaben");

    // Die Quelle steht als Name da, das Blatt kommt erst auf Wunsch —
    // eine PDF-Seite zu rendern ist nicht umsonst.
    const oeffnen = page.getByRole("button", { name: /Wo steht das\?/ }).first();
    await expect(oeffnen).toBeVisible();
    expect(await page.getByRole("tabpanel").locator("img").count()).toBe(0);

    await oeffnen.click();

    // Das Zitat und die Seite selbst erscheinen.
    await expect(page.getByText("Flurstück: 1477").first()).toBeVisible({
      timeout: 15_000,
    });
    const blatt = page.getByRole("tabpanel").locator("img").first();
    await expect(blatt).toBeVisible();
    await expect(page.getByText(/Stelle ist gelb markiert/).first()).toBeVisible();

    // Und lässt sich zum Lesen aufziehen — in der schmalen Spalte wäre eine
    // Bauzeichnung sonst nicht zu entziffern.
    await blatt.click();
    const lupe = page.getByRole("dialog");
    await expect(lupe).toBeVisible();
    await expect(lupe.getByText(/flurkarte\.pdf/)).toBeVisible();

    // Escape muss schließen, sonst sitzt man mit der Tastatur fest.
    await page.keyboard.press("Escape");
    await expect(lupe).toHaveCount(0);
  });

  test("beim Widerspruch stehen beide Quellen nebeneinander", async ({ page }) => {
    await backendStellen(page);
    await page.goto(`/vorgang/${VORGANG_ID}`);

    // Erst hochladen, damit der Widerspruch entsteht.
    await page.setInputFiles('input[type="file"][multiple]', [
      {
        name: "flurkarte.pdf",
        mimeType: "application/pdf",
        buffer: Buffer.from("%PDF-1.4 test"),
      },
    ]);
    await expect(page.getByText(/flurkarte\.pdf →/)).toBeVisible({
      timeout: 20_000,
    });

    await reiterOeffnen(page, /Passt nicht/);
    const akte = page.getByRole("tabpanel");

    // Zwei Quellen, jede einzeln aufklappbar — das macht die Entscheidung
    // überhaupt erst treffbar.
    const quellen = akte.getByRole("button", { name: /Wo steht das\?/ });
    await expect(quellen).toHaveCount(2);
    await expect(quellen.filter({ hasText: "bauschein.pdf" })).toHaveCount(1);
    await expect(
      quellen.filter({ hasText: "nutzungsaufstellung.pdf" }),
    ).toHaveCount(1);
  });
});

test.describe("Wenn die Anfrage den Motor nicht erreicht", () => {
  test("sagt die Meldung, dass das Frontend geantwortet hat", async ({ page }) => {
    // Genau das passiert, wenn NEXT_PUBLIC_BACKEND_URL leer ist: die Anfrage
    // landet auf dem Frontend-Server, der den Pfad nicht kennt und mit einer
    // HTML-Seite und 404 antwortet. Die alte Meldung ("Der Motor hat mit 404
    // geantwortet") schickte einen Kollegen auf die falsche Fährte.
    await page.route("http://127.0.0.1:8000/api/**", (route) =>
      route.fulfill({
        status: 404,
        contentType: "text/html",
        body: "<html><body>404 - This page could not be found.</body></html>",
      }),
    );

    await page.goto("/");

    await expect(
      page.getByText(/nicht beim Motor angekommen, sondern beim Frontend/),
    ).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/NEXT_PUBLIC_BACKEND_URL/)).toBeVisible();

    // Die alte, irreführende Formulierung darf nicht mehr auftauchen.
    await expect(page.getByText("Der Motor hat mit 404 geantwortet.")).toHaveCount(0);
  });
});
