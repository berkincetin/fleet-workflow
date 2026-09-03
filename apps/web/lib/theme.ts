/**
 * Theme resolution (task 13.1).
 *
 * Three states, mirrored by app/globals.css: "system" renders no `data-theme`
 * attribute at all and lets `prefers-color-scheme` decide; "light"/"dark"
 * stamp the attribute and win over the OS. The choice is a cookie rather than
 * localStorage so the *server* render already carries the right attribute —
 * with localStorage the first paint would be the OS theme and flash.
 */

export const themes = ["system", "light", "dark"] as const;
export type Theme = (typeof themes)[number];

export const THEME_COOKIE = "fleet_theme";
export const defaultTheme: Theme = "system";

export function parseTheme(value: string | undefined): Theme {
  return themes.includes(value as Theme) ? (value as Theme) : defaultTheme;
}

/** The `data-theme` attribute value, or undefined for "system". */
export function themeAttribute(theme: Theme): "light" | "dark" | undefined {
  return theme === "system" ? undefined : theme;
}
