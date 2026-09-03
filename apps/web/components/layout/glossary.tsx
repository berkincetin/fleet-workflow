"use client";

import { useTranslations } from "next-intl";

/**
 * Inline glossary (task 13.2).
 *
 * `write:external`, `sensitivity: pii`, `risk_class` and HITL are platform
 * vocabulary, not English or Turkish — every place the UI shows one, it wraps
 * it here so the reader can get the one-sentence meaning without leaving the
 * page. <details> keeps it keyboard-operable and hydration-free.
 */

export const GLOSSARY_TERMS = [
  "writeExternal",
  "sensitivityPii",
  "riskClass",
  "hitl",
] as const;

export type GlossaryKey = (typeof GLOSSARY_TERMS)[number];

export function GlossaryTerm({ term }: { term: GlossaryKey }) {
  const t = useTranslations("glossary");

  return (
    <details className="relative inline-block align-baseline">
      <summary className="cursor-help list-none border-b border-dotted border-[var(--muted-foreground)] font-mono text-[0.8125rem] text-[var(--foreground)]">
        {t(`${term}.term`)}
      </summary>
      <span className="absolute left-0 top-full z-30 mt-1 block w-64 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-3 text-xs font-normal leading-relaxed text-[var(--muted-foreground)] shadow-[var(--shadow-lg)]">
        {t(`${term}.definition`)}
      </span>
    </details>
  );
}

/** The whole vocabulary as a block — used on the pages where several of these
 * terms appear at once (approvals, the automation builder's preview). */
export function GlossaryList({ terms = GLOSSARY_TERMS }: { terms?: readonly GlossaryKey[] }) {
  const t = useTranslations("glossary");

  return (
    <details className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-2)]">
      <summary className="cursor-pointer list-none px-3 py-2 text-sm font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)]">
        {t("title")}
      </summary>
      <dl className="flex flex-col gap-2 px-3 pb-3 text-sm">
        {terms.map((term) => (
          <div key={term} className="flex flex-col gap-0.5">
            <dt className="font-mono text-[0.8125rem] text-[var(--foreground)]">
              {t(`${term}.term`)}
            </dt>
            <dd className="text-[var(--muted-foreground)]">{t(`${term}.definition`)}</dd>
          </div>
        ))}
      </dl>
    </details>
  );
}
