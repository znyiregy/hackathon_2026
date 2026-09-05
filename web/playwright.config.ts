import { defineConfig, devices } from "@playwright/test";

/**
 * End-to-end tests for the critical path.
 *
 * These drive a real browser against a real frontend. The backend is stubbed
 * at the network layer (see e2e/backend.ts), so the tests never call OpenAI,
 * never cost anything, and never fail because a model phrased something
 * differently. What they prove is that the screens, the flow between them and
 * the error handling actually work.
 *
 * Run with:  npm run e2e
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "line" : [["list"]],

  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "retain-on-failure",
    locale: "de-DE",
  },

  projects: [
    {
      name: "desktop",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "mobil",
      use: { ...devices["Pixel 7"] },
    },
  ],

  // Its own port, so a running dev server is never disturbed.
  webServer: {
    command: "npx next start -p 3100",
    url: "http://127.0.0.1:3100",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
