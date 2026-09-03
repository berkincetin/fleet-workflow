"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { Monitor, Moon, Sun } from "lucide-react";
import { THEME_COOKIE, themes, type Theme } from "@/lib/theme";
import { cn } from "@/lib/utils";

const ICONS: Record<Theme, typeof Sun> = {
  system: Monitor,
  light: Sun,
  dark: Moon,
};

/**
 * Segmented system/light/dark control. Writes the cookie and flips
 * `data-theme` on <html> immediately (so the switch is instant), then
 * refreshes so the next server render agrees with what the browser shows.
 */
export function ThemeSwitcher({ value }: { value: Theme }) {
  const t = useTranslations("theme");
  const router = useRouter();

  function select(next: Theme) {
    document.cookie = `${THEME_COOKIE}=${next}; path=/; max-age=31536000; samesite=lax`;
    const root = document.documentElement;
    if (next === "system") {
      root.removeAttribute("data-theme");
    } else {
      root.setAttribute("data-theme", next);
    }
    router.refresh();
  }

  return (
    <div
      role="radiogroup"
      aria-label={t("label")}
      className="inline-flex rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-0.5"
    >
      {themes.map((theme) => {
        const Icon = ICONS[theme];
        const active = value === theme;
        return (
          <button
            key={theme}
            type="button"
            role="radio"
            aria-checked={active}
            aria-label={t(theme)}
            title={t(theme)}
            onClick={() => select(theme)}
            className={cn(
              "flex h-7 w-7 items-center justify-center rounded-[var(--radius-sm)] transition-colors",
              active
                ? "bg-[var(--surface-2)] text-[var(--foreground)]"
                : "text-[var(--muted-foreground)] hover:text-[var(--foreground)]",
            )}
          >
            <Icon className="h-3.5 w-3.5" aria-hidden="true" />
          </button>
        );
      })}
    </div>
  );
}
