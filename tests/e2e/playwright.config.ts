import { defineConfig, devices } from "@playwright/test";

// Runs against the real dev stack (make dev) + a running web app, not a
// Playwright-managed webServer — the demo path needs the real Keycloak/API/
// Qdrant stack behind it, which docker-compose already owns (TRD §13.3).
//
// The web app MUST be started via `next build && next start` (a production
// build), not `next dev`: dev mode's fast-refresh/React DevTools
// instrumentation was observed to desync a controlled <input>'s DOM value
// from its React state under Playwright's synthetic input events (the
// button stayed disabled after typing even though the DOM showed the typed
// text) — reproduced consistently in dev, absent in a production build.
// CI's e2e job builds+starts the app for exactly this reason.
export default defineConfig({
  testDir: "./specs",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: process.env.E2E_WEB_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
});
