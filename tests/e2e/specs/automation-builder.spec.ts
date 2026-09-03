import { test, expect, type Page, type APIRequestContext } from "@playwright/test";

// Task 13.5 AC: "a `builder` defines, saves and runs an automation end to end
// from the browser and sees the run in n8n"; "a `member` can view but not
// edit". Runs against the real stack (Keycloak, Fleet API, n8n) — the recipe
// really is compiled, deployed over n8n's REST API and executed by the n8n
// worker, which then calls back into Fleet.
//
// The recipe deliberately uses `pg.query` + `http.notify` only: both are fast
// and deterministic, so the spec proves the *builder* path without making an
// e2e run depend on model latency. The Langfuse leg of the AC needs an
// `agent.run` step and is verified in the sprint's manual AC pass instead.

const N8N_BASE = process.env.E2E_N8N_BASE_URL ?? "http://localhost:5678";
const N8N_API_KEY = process.env.FLEET_N8N_API_KEY ?? "";

async function login(page: Page, user: string) {
  await page.goto("/automations");
  await page.getByRole("button", { name: /sign in|giriş yap/i }).click();
  await page.locator("#username").waitFor({ state: "visible" });
  await page.locator("#username").fill(user);
  await page.locator("#password").fill(user);
  await page.locator("#kc-login").click();
  await expect(
    page.getByRole("heading", { name: /^automations$|^otomasyonlar$/i, level: 1 }),
  ).toBeVisible({ timeout: 30_000 });
}

async function n8nWorkflow(request: APIRequestContext, name: string) {
  const resp = await request.get(`${N8N_BASE}/api/v1/workflows`, {
    headers: { "X-N8N-API-KEY": N8N_API_KEY },
  });
  const body = await resp.json();
  return (body.data ?? []).find((w: { name: string }) => w.name === name);
}

test("a builder defines, saves, activates and runs an automation from the browser", async ({
  page,
  request,
}) => {
  test.skip(!N8N_API_KEY, "FLEET_N8N_API_KEY is required to assert against n8n");

  const name = `e2e-${Date.now().toString(36)}`;
  await login(page, "builder");

  // --- define
  await page.getByRole("link", { name: /new automation|yeni otomasyon/i }).first().click();
  await expect(page).toHaveURL(/\/automations\/new$/);

  await page.getByLabel(/^name$|^ad$/i).fill(name);
  await page.getByLabel(/^description$|^açıklama$/i).fill("playwright e2e recipe");

  // Manual trigger is the default; the first step defaults to pg.query.
  await page
    .getByLabel(/sql query|sql sorgusu/i)
    .fill("SELECT COUNT(*) AS n FROM fixture_sales");

  // A second step that reuses the first step's output.
  await page.getByRole("button", { name: /add step|adım ekle/i }).first().click();
  const actionSelects = page.getByLabel(/^action$|^işlem$/i);
  await actionSelects.last().selectOption("http.notify");
  await page.getByLabel(/^title$|^başlık$/i).fill("e2e sales check");
  await page
    .getByLabel(/^message$|^mesaj$/i)
    .last()
    .fill("rows: {{steps.step1.row_count}}");

  // --- preview: the server compiles it and describes it back in plain language.
  // Scoped to the summary list — the action labels also appear in every step's
  // <option> list, so an unscoped text match is ambiguous.
  await page.getByRole("button", { name: /^preview$|^önizle$/i }).click();
  const summary = page.getByRole("listitem");
  await expect(
    summary.filter({ hasText: /when run by hand|elle çalıştırıldığında/i }),
  ).toBeVisible();
  await expect(summary.filter({ hasText: /database query|veritabanı sorgusu/i })).toBeVisible();
  await expect(summary.filter({ hasText: /record a note|kayıt düş/i })).toBeVisible();

  // --- save -> deployed to n8n
  await page
    .getByRole("button", { name: /^new automation$|^yeni otomasyon$/i })
    .last()
    .click();
  await expect(page).toHaveURL(/\/automations$/, { timeout: 30_000 });

  await expect(page.getByTestId(`recipe-${name}`)).toBeVisible({ timeout: 30_000 });

  const workflow = await n8nWorkflow(request, `fleet-recipe-${name}`);
  expect(workflow, "the recipe was not deployed to n8n").toBeTruthy();

  try {
    // --- activate + run
    const scope = page.getByTestId(`recipe-${name}`);
    await scope.getByRole("button", { name: /^activate$|^etkinleştir$/i }).click();
    await expect(scope.getByText(/^active$|^etkin$/i)).toBeVisible({ timeout: 15_000 });

    await scope.getByRole("button", { name: /run now|şimdi çalıştır/i }).click();
    // `.first()` — a Radix toast renders both the visible node and an
    // aria-live announcement carrying the same text.
    await expect(
      page.getByText(/request accepted|istek kabul edildi|kuyruğa/i).first(),
    ).toBeVisible({ timeout: 15_000 });

    // --- n8n really ran it
    // n8n 1.71's executions list omits `status` per row, so success is read
    // from the server-side filter instead of the row body.
    await expect
      .poll(
        async () => {
          const resp = await request.get(
            `${N8N_BASE}/api/v1/executions?workflowId=${workflow.id}&status=success`,
            { headers: { "X-N8N-API-KEY": N8N_API_KEY } },
          );
          const body = await resp.json();
          return (body.data ?? []).length;
        },
        { timeout: 60_000, intervals: [2000] },
      )
      .toBeGreaterThan(0);
  } finally {
    // --- clean up: delete removes the n8n workflow too
    const scope = page.getByTestId(`recipe-${name}`);
    await scope.getByRole("button", { name: /^delete$|^sil$/i }).click();
    // In-app confirmation dialog, not window.confirm.
    const confirm = page.getByRole("dialog");
    await expect(confirm).toBeVisible();
    await confirm.getByRole("button", { name: /^delete$|^sil$/i }).click();
    await expect(
      page.getByText(/automation deleted|otomasyon silindi/i).first(),
    ).toBeVisible({ timeout: 15_000 });
  }

  expect(await n8nWorkflow(request, `fleet-recipe-${name}`)).toBeFalsy();
});

test("a member sees the automations page but gets no builder affordances", async ({ page }) => {
  await login(page, "user1");

  // No "New automation" entry point anywhere on the page or in the sidebar.
  await expect(page.getByRole("link", { name: /new automation|yeni otomasyon/i })).toHaveCount(0);

  // And the route itself refuses, rather than only being hidden.
  await page.goto("/automations/new");
  await expect(
    page.getByText(/you do not have access|bu sayfaya erişiminiz yok/i),
  ).toBeVisible();
});
