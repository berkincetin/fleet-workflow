import { test, expect, type Page } from "@playwright/test";

// Task 13.1 AC, re-verified after the 13.7 recolour: "light and dark both
// legible". Sprint 13 proved this with Lighthouse, which is not installed on
// every machine; this walks the *rendered* DOM instead and computes WCAG
// contrast for every text node against its real painted background, so it
// catches exactly the failure a palette change causes — a token pair that
// looked fine in the CSS and is unreadable on screen.
//
// It is not a replacement for a full a11y audit (labels, roles, landmarks are
// Lighthouse's job); it is the colour half, which is the half this sprint put
// at risk.

const SCREENS = [
  { path: "/", user: "admin" },
  { path: "/guide", user: "admin" },
  { path: "/automations", user: "admin" },
  { path: "/automations/new", user: "admin" },
  { path: "/chat", user: "admin" },
  { path: "/approvals", user: "admin" },
  { path: "/scenarios", user: "admin" },
  { path: "/knowledge", user: "admin" },
];

async function login(page: Page, user: string) {
  await page.goto("/");
  const signIn = page.getByRole("button", { name: /sign in|giriş yap/i });
  if (await signIn.isVisible().catch(() => false)) {
    await signIn.click();
    await page.locator("#username").waitFor({ state: "visible" });
    await page.locator("#username").fill(user);
    await page.locator("#password").fill(user);
    await page.locator("#kc-login").click();
    await page.waitForURL(/localhost:3000/, { timeout: 30_000 });
  }
}

/**
 * Every visible text node's foreground vs. the nearest ancestor that actually
 * paints a background. Returns the failures only.
 *
 * Thresholds are WCAG AA: 4.5:1 for body text, 3:1 for large text (>=24px, or
 * >=18.66px bold), which is the same split Lighthouse applies.
 */
type Rgb = { r: number; g: number; b: number; a: number };
type Failure = {
  text: string;
  ratio: number;
  required: number;
  color: string;
  background: string;
};

const AUDIT = (): Failure[] => {
  const parse = (c: string): Rgb | null => {
    const m = c.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(/[,\s/]+/).filter(Boolean).map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const lum = ({ r, g, b }: Rgb) => {
    const f = (v: number) => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const ratio = (a: Rgb, b: Rgb) => {
    const [l1, l2] = [lum(a), lum(b)].sort((x, y) => y - x);
    return (l1 + 0.05) / (l2 + 0.05);
  };
  // Flatten a translucent colour over whatever is behind it.
  const over = (fg: Rgb, bg: Rgb): Rgb => ({
    r: fg.r * fg.a + bg.r * (1 - fg.a),
    g: fg.g * fg.a + bg.g * (1 - fg.a),
    b: fg.b * fg.a + bg.b * (1 - fg.a),
    a: 1,
  });
  // The nearest ancestor chain that actually paints something opaque.
  const bgOf = (el: Element): Rgb => {
    let node: Element | null = el;
    let acc: Rgb | null = null;
    while (node) {
      const c = parse(getComputedStyle(node).backgroundColor);
      if (c && c.a > 0) acc = acc ? over(acc, c) : c;
      if (acc && acc.a >= 1) return acc;
      node = node.parentElement;
    }
    return acc ?? { r: 255, g: 255, b: 255, a: 1 };
  };

  const failures: Failure[] = [];
  for (const el of Array.from(document.querySelectorAll("*"))) {
    // Only elements carrying their own text — otherwise a wrapper is blamed
    // for the colours of everything nested inside it.
    const own = Array.from(el.childNodes)
      .filter((n) => n.nodeType === 3)
      .map((n) => (n.textContent ?? "").trim())
      .join(" ")
      .trim();
    if (!own) continue;

    const s = getComputedStyle(el);
    if (s.visibility === "hidden" || s.display === "none" || Number(s.opacity) === 0) continue;
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) continue;

    const fg = parse(s.color);
    if (!fg) continue;
    const bg = bgOf(el);
    const flat = fg.a < 1 ? over(fg, bg) : fg;

    const px = parseFloat(s.fontSize);
    const bold = Number(s.fontWeight) >= 700;
    const large = px >= 24 || (bold && px >= 18.66);
    const required = large ? 3 : 4.5;
    const r = ratio(flat, bg);
    if (r < required) {
      failures.push({
        text: own.slice(0, 40),
        ratio: Math.round(r * 100) / 100,
        required,
        color: s.color,
        background: `rgb(${Math.round(bg.r)} ${Math.round(bg.g)} ${Math.round(bg.b)})`,
      });
    }
  }
  return failures;
};

for (const theme of ["light", "dark"] as const) {
  test(`text contrast meets WCAG AA in ${theme} mode`, async ({ page }) => {
    await login(page, "admin");
    // Pin the theme the way the app itself does, so this measures the real
    // painted palette rather than whatever the runner's OS prefers.
    await page.context().addCookies([
      { name: "fleet_theme", value: theme, url: "http://localhost:3000" },
    ]);

    const problems: Record<string, unknown[]> = {};
    for (const screen of SCREENS) {
      await page.goto(screen.path);
      await page.waitForLoadState("networkidle");
      await expect(page.locator("main")).toBeVisible();
      const failures = await page.evaluate(AUDIT);
      if (failures.length > 0) problems[screen.path] = failures;
    }

    expect(problems, `contrast failures in ${theme}: ${JSON.stringify(problems, null, 2)}`)
      .toEqual({});
  });
}
