import { test, expect, type Page, type APIRequestContext } from "@playwright/test";

// Task 13.7: the in-app examples — the Guide's walkthroughs, the ready-made
// automation templates, and the chat starter questions.
//
// What these assert is specifically the thing unit tests cannot: that a
// template's pre-filled values survive the round trip through the *server's*
// compiler. `test_recipe_templates.py` proves a template stays inside the
// action/table/channel allowlists by reading the files; only a live run proves
// the API accepts it and n8n deploys it unedited. A template that looked
// plausible and 422'd on save would be worse than no template at all.

const N8N_BASE = process.env.E2E_N8N_BASE_URL ?? "http://localhost:5678";
const N8N_API_KEY = process.env.FLEET_N8N_API_KEY ?? "";

async function login(page: Page, user: string, landing: RegExp) {
  await page.getByRole("button", { name: /sign in|giriş yap/i }).click();
  await page.locator("#username").waitFor({ state: "visible" });
  await page.locator("#username").fill(user);
  await page.locator("#password").fill(user);
  await page.locator("#kc-login").click();
  await expect(page.getByRole("heading", { name: landing, level: 1 })).toBeVisible({
    timeout: 30_000,
  });
}

async function n8nWorkflow(request: APIRequestContext, name: string) {
  const resp = await request.get(`${N8N_BASE}/api/v1/workflows`, {
    headers: { "X-N8N-API-KEY": N8N_API_KEY },
  });
  const body = await resp.json();
  return (body.data ?? []).find((w: { name: string }) => w.name === name);
}

test("the guide is readable by a plain member and its walkthroughs link into real screens", async ({
  page,
}) => {
  await page.goto("/guide");
  await login(page, "user1", /^guide$|^rehber$/i);

  // All four walkthroughs render, each with its numbered steps — the copy is
  // resolved from dynamic i18n keys, so a missing one shows up as a raw key.
  // Matched as headings: each walkthrough's title also appears inside its own
  // intro sentence, so a bare text match is ambiguous.
  for (const title of [
    /ask an agent|bir ajana soru sorun/i,
    /add a document|bilgi bankasına belge/i,
    /build an automation|otomasyon kurun/i,
    /approval gate|onay akışını görün/i,
  ]) {
    await expect(page.getByRole("heading", { name: title })).toBeVisible();
  }
  // Every walkthrough renders its numbered steps.
  await expect(page.getByRole("listitem").first()).toBeVisible();

  // No unresolved i18n key leaked into the page.
  await expect(page.locator("body")).not.toContainText("guide.walkthroughs");

  // The first walkthrough's button really lands on Chat with the agent picked.
  await page.getByRole("link", { name: /open chat|sohbeti aç/i }).click();
  await expect(page).toHaveURL(/\/chat\?agent=support_copilot/);
  await expect(page.getByRole("heading", { name: /^chat$|^sohbet$/i, level: 1 })).toBeVisible();
});

test("chat starters fill the composer for the selected agent", async ({ page }) => {
  await page.goto("/chat?agent=support_copilot");
  await login(page, "user1", /^chat$|^sohbet$/i);

  // The starter chips are the agent's own suggested questions.
  const starter = page.getByRole("button", { name: /cancel my order|siparişimi nasıl iptal/i });
  await expect(starter).toBeVisible();

  const question = (await starter.textContent())?.trim() ?? "";
  expect(question.length).toBeGreaterThan(0);

  await starter.click();
  // Clicking a suggestion loads it into the composer rather than sending it —
  // the reader still gets to edit before committing.
  await expect(page.getByPlaceholder(/.+/).first()).toHaveValue(question);
});

test("a template pre-fills the builder and the server accepts it unedited", async ({
  page,
  request,
}) => {
  test.skip(!N8N_API_KEY, "FLEET_N8N_API_KEY is required to assert against n8n");

  await page.goto("/automations/new");
  await login(page, "builder", /^new automation$|^yeni otomasyon$/i);

  // The gallery is offered on a blank start.
  await expect(page.getByText(/ready-made automations|hazır otomasyonlar/i)).toBeVisible();

  // The approval-teaching template is flagged as such *before* it is opened.
  const emailCard = page.getByRole("link", {
    name: /monthly report email|aylık rapor e-postası/i,
  });
  await expect(emailCard).toContainText(/needs approval|onay gerekir/i);

  // Pick the digest template; the form arrives filled in.
  await page.getByRole("link", { name: /weekly sales digest|haftalık satış özeti/i }).click();
  await expect(page).toHaveURL(/\?template=weeklySalesDigest/);

  // Once a template is chosen the gallery steps aside rather than inviting a
  // stray click that would discard the seeded draft.
  await expect(page.getByText(/ready-made automations|hazır otomasyonlar/i)).toHaveCount(0);

  await expect(page.getByLabel(/sql query|sql sorgusu/i)).toContainText(/fixture_sales/i);

  // Rename to something unique so the run does not collide with a real recipe.
  const name = `e2e-tpl-${Date.now().toString(36)}`;
  const nameField = page.getByLabel(/^name$|^ad$/i);
  await nameField.fill("");
  await nameField.fill(name);

  // --- the assertion that matters: the server compiles the template as-is.
  await page.getByRole("button", { name: /^preview$|^önizle$/i }).click();
  const summary = page.getByRole("listitem");
  await expect(summary.filter({ hasText: /database query|veritabanı sorgusu/i })).toBeVisible();
  await expect(summary.filter({ hasText: /slack/i })).toBeVisible();
  // A schedule template must describe itself as scheduled, not manual. The
  // summary prints the cron expression itself ("On schedule: 0 9 * * 1"), so
  // that is what this asserts — the template's own cron, unedited.
  await expect(
    summary.filter({ hasText: /on schedule|zamanlama/i }).first(),
  ).toContainText("0 9 * * 1");

  await page
    .getByRole("button", { name: /^new automation$|^yeni otomasyon$/i })
    .last()
    .click();
  await expect(page).toHaveURL(/\/automations$/, { timeout: 30_000 });
  await expect(page.getByTestId(`recipe-${name}`)).toBeVisible({ timeout: 30_000 });

  try {
    const workflow = await n8nWorkflow(request, `fleet-recipe-${name}`);
    expect(workflow, "the template was not deployed to n8n").toBeTruthy();
  } finally {
    const scope = page.getByTestId(`recipe-${name}`);
    await scope.getByRole("button", { name: /^delete$|^sil$/i }).click();
    const confirm = page.getByRole("dialog");
    await expect(confirm).toBeVisible();
    await confirm.getByRole("button", { name: /^delete$|^sil$/i }).click();
    await expect(
      page.getByText(/automation deleted|otomasyon silindi/i).first(),
    ).toBeVisible({ timeout: 15_000 });
  }
});
