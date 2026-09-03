import { test, expect, type Page } from "@playwright/test";

// Task 13.1 AC: "nav filters correctly for each of user1/approver/builder/admin"
// and the theme switch works. The sidebar hides a link as a courtesy only — the
// API is the real gate — so these assertions are about what a user is *offered*,
// which is the thing the shell is responsible for.

async function login(page: Page, user: string) {
  await page.goto("/");
  await page.getByRole("button", { name: /sign in|giriş yap/i }).click();
  await page.locator("#username").waitFor({ state: "visible" });
  await page.locator("#username").fill(user);
  await page.locator("#password").fill(user);
  await page.locator("#kc-login").click();
  await expect(page.getByRole("complementary")).toBeVisible({ timeout: 30_000 });
}

function sidebar(page: Page) {
  return page.getByRole("complementary");
}

const ALWAYS = [/^home$|^ana sayfa$/i, /^chat$|^sohbet$/i, /^automations$|^otomasyonlar$/i];

test.describe("role-aware navigation", () => {
  test("member sees the shared screens and neither Approvals nor Admin", async ({ page }) => {
    await login(page, "user1");
    for (const label of ALWAYS) {
      await expect(sidebar(page).getByRole("link", { name: label })).toBeVisible();
    }
    await expect(sidebar(page).getByRole("link", { name: /approvals|onaylar/i })).toHaveCount(0);
    await expect(sidebar(page).getByRole("link", { name: /^admin$|^yönetim$/i })).toHaveCount(0);
    await expect(
      sidebar(page).getByRole("link", { name: /new automation|yeni otomasyon/i }),
    ).toHaveCount(0);
  });

  test("approver additionally sees Approvals, but not Admin or the builder", async ({ page }) => {
    await login(page, "approver");
    await expect(sidebar(page).getByRole("link", { name: /approvals|onaylar/i })).toBeVisible();
    await expect(sidebar(page).getByRole("link", { name: /^admin$|^yönetim$/i })).toHaveCount(0);
    await expect(
      sidebar(page).getByRole("link", { name: /new automation|yeni otomasyon/i }),
    ).toHaveCount(0);
  });

  test("builder sees Admin and the automation builder, but not Approvals", async ({ page }) => {
    await login(page, "builder");
    await expect(
      sidebar(page).getByRole("link", { name: /new automation|yeni otomasyon/i }),
    ).toBeVisible();
    await expect(sidebar(page).getByRole("link", { name: /^admin$|^yönetim$/i })).toBeVisible();
    await expect(sidebar(page).getByRole("link", { name: /approvals|onaylar/i })).toHaveCount(0);
  });

  test("platform admin sees every group and the platform-only admin tabs", async ({ page }) => {
    await login(page, "admin");
    for (const label of [
      /^home$|^ana sayfa$/i,
      /approvals|onaylar/i,
      /new automation|yeni otomasyon/i,
      /^admin$|^yönetim$/i,
    ]) {
      await expect(sidebar(page).getByRole("link", { name: label })).toBeVisible();
    }
    // Services is a MANAGE_PLATFORM tab — the deferred 7.3 screen (task 13.3).
    await page.goto("/admin/agents");
    await expect(page.getByRole("link", { name: /^services$|^servisler$/i })).toBeVisible();
  });
});

test("the theme switch flips data-theme and survives a reload", async ({ page }) => {
  await login(page, "user1");
  const root = page.locator("html");

  // "system" renders no attribute at all, so prefers-color-scheme decides.
  await expect(root).not.toHaveAttribute("data-theme", /.*/);

  await page.getByRole("radio", { name: /dark theme|koyu tema/i }).click();
  await expect(root).toHaveAttribute("data-theme", "dark");

  // The choice is a cookie, so the *server* render already carries it — no
  // flash of the wrong theme on reload.
  await page.reload();
  await expect(root).toHaveAttribute("data-theme", "dark");

  await page.getByRole("radio", { name: /light theme|açık tema/i }).click();
  await expect(root).toHaveAttribute("data-theme", "light");

  await page.getByRole("radio", { name: /system theme|sistem teması/i }).click();
  await expect(root).not.toHaveAttribute("data-theme", /.*/);
});
