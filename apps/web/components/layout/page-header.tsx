import { HelpCircle } from "lucide-react";

/**
 * Shared page header (task 13.2): the page's name, one sentence saying what
 * the screen is *for*, and a collapsed "how to use it" walkthrough.
 *
 * Built on <details>/<summary> rather than React state so it stays a server
 * component and works before hydration — the explanatory layer is exactly the
 * thing a first-time user needs on the first paint.
 */
export function PageHeader({
  title,
  intro,
  howToLabel,
  howTo,
  actions,
}: {
  title: string;
  intro: string;
  howToLabel?: string;
  howTo?: string[];
  actions?: React.ReactNode;
}) {
  return (
    <header className="flex flex-col gap-3">
      {/* The header sits on the section gradient with its accent as a left
          rail. Colour here is redundant with the sidebar's active row and the
          top-bar hairline — deliberately, since it is decorative: the title
          text carries the meaning on its own. */}
      <div className="relative overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border)] bg-[image:var(--gradient-header)] p-4 md:p-5">
        <span
          aria-hidden="true"
          className="absolute inset-y-0 left-0 w-1 bg-[var(--section)]"
        />
        <div className="flex flex-wrap items-start justify-between gap-3 pl-2">
          <div className="flex flex-col gap-1">
            <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
            <p className="max-w-2xl text-sm text-[var(--muted-foreground)]">{intro}</p>
          </div>
          {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
        </div>
      </div>

      {howTo && howTo.length > 0 && howToLabel && (
        <details className="group rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-2)]">
          <summary className="flex cursor-pointer list-none items-center gap-2 px-3 py-2 text-sm font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)]">
            <HelpCircle className="h-4 w-4 text-[var(--section)]" aria-hidden="true" />
            {howToLabel}
          </summary>
          <ol className="flex list-decimal flex-col gap-1.5 px-3 pb-3 pl-8 text-sm text-[var(--muted-foreground)]">
            {howTo.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </details>
      )}
    </header>
  );
}
