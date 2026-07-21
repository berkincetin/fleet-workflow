"use client";

import { useLocale } from "next-intl";
import { useRouter } from "next/navigation";
import { locales, type Locale } from "@/i18n/locales";

export function LocaleSwitcher() {
  const locale = useLocale();
  const router = useRouter();

  function setLocale(next: Locale) {
    document.cookie = `fleet_locale=${next}; path=/; max-age=31536000`;
    router.refresh();
  }

  return (
    <select
      aria-label="Language"
      value={locale}
      onChange={(e) => setLocale(e.target.value as Locale)}
      className="rounded-md border border-[var(--border)] bg-[var(--background)] px-2 py-1 text-sm"
    >
      {locales.map((l) => (
        <option key={l} value={l}>
          {l.toUpperCase()}
        </option>
      ))}
    </select>
  );
}
