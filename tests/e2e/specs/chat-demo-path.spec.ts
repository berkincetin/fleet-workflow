import { test, expect } from "@playwright/test";

// The Sprint 4 demo path (TRD §13.3, task 4.4 AC): login -> chat -> a
// grounded, cited answer. Runs against the real dev stack (Keycloak, API,
// Qdrant, LiteLLM) — no mocks — using the seeded `builder` user and the
// seeded `support_copilot` agent + its cs-help-center/cs-procedures KB
// (apps/api/fleet_api/seed.py's seed_support_copilot(), fleet_rag/seed_docs.py).
test("login, chat, and receive a grounded cited answer", async ({ page }) => {
  await page.goto("/chat");

  // Unauthenticated: the (app) layout shows a sign-in prompt instead of the
  // chat window (lib/auth.ts gates on a real session); the actual sign-in
  // button lives in the always-visible NavBar.
  await expect(page.getByText(/sign in to continue|devam etmek için giriş yapın/i)).toBeVisible();
  await page.getByRole("button", { name: /sign in|giriş yap/i }).click();

  // Real Keycloak login form (login.ftl) — username/password fields. Wait
  // for the form itself rather than a specific URL: Keycloak's auth endpoint
  // redirects through a couple of intermediate URLs before landing on
  // login-actions/authenticate, and the exact one it settles on isn't load-
  // bearing here — only that the login form renders.
  await page.locator("#username").waitFor({ state: "visible" });
  await page.locator("#username").fill("builder");
  await page.locator("#password").fill("builder");
  await page.locator("#kc-login").click();

  // Back on the app, now authenticated — the chat window renders. h1 is the
  // page title; the ChatWindow card also has an h3 with the same text.
  await expect(page.getByRole("heading", { name: "Chat", level: 1 })).toBeVisible({
    timeout: 30_000,
  });

  const agentSelect = page.getByRole("main").getByRole("combobox");
  await expect(agentSelect).toBeVisible();
  await agentSelect.selectOption({ label: "support_copilot" });

  const input = page.getByPlaceholder(/ask a question|bir soru sorun/i);
  await input.fill("Trink sat süreci nasıl işliyor?");
  await page.getByRole("button", { name: /^send$|^gönder$/i }).click();

  // The streamed answer renders (real SSE token events -> React state).
  const assistantBubble = page.locator("div.self-start").last();
  await expect(assistantBubble).toContainText(/ekspertiz/i, { timeout: 30_000 });

  // A citation count is shown — the structural grounding guardrail (§9)
  // produced >=1 citation resolving to a chunk actually retrieved.
  await expect(assistantBubble.getByText(/citation/i)).toBeVisible();

  // Feedback buttons render on the grounded answer.
  await expect(assistantBubble.getByRole("button", { name: /thumbs up/i })).toBeVisible();
});
