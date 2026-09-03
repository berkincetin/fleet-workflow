import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

/**
 * One number on the Home dashboard (task 13.1, recoloured in 13.7). Every tile
 * is a link — the dashboard's job is to be the shortest route to the screen
 * that acts on the number, not a read-only report.
 *
 * `tone` picks the tile's colour family, which is the section accent of
 * wherever it links to (approvals → work, automations → automation, …) plus
 * `attention` for a count that wants acting on. The colour is carried by the
 * icon chip and a top rail, never by the number alone: the value and its hint
 * both stay in the plain foreground tokens so the tile reads identically to
 * someone who cannot separate the hues.
 */
const TONES = {
  work: { bg: "bg-[var(--section-work-bg)]", fg: "text-[var(--section-work-fg)]", rail: "bg-[var(--section-work)]" },
  automation: { bg: "bg-[var(--section-automation-bg)]", fg: "text-[var(--section-automation-fg)]", rail: "bg-[var(--section-automation)]" },
  knowledge: { bg: "bg-[var(--section-knowledge-bg)]", fg: "text-[var(--section-knowledge-fg)]", rail: "bg-[var(--section-knowledge)]" },
  admin: { bg: "bg-[var(--section-admin-bg)]", fg: "text-[var(--section-admin-fg)]", rail: "bg-[var(--section-admin)]" },
  attention: { bg: "bg-[var(--warning-bg)]", fg: "text-[var(--warning-fg)]", rail: "bg-[var(--warning)]" },
} as const;

export type StatTone = keyof typeof TONES;

export function StatTile({
  label,
  value,
  hint,
  href,
  tone = "work",
  icon: Icon,
}: {
  label: string;
  value: string;
  hint: string;
  href: string;
  tone?: StatTone;
  icon: React.ComponentType<{ className?: string }>;
}) {
  const c = TONES[tone];
  return (
    <Link href={href} className="group block">
      <Card className="relative flex h-full flex-col gap-3 overflow-hidden p-4 transition-all hover:border-[var(--border-strong)] hover:shadow-[var(--shadow-md)]">
        <span aria-hidden="true" className={cn("absolute inset-x-0 top-0 h-1", c.rail)} />
        <div className="flex items-start justify-between gap-2">
          <span
            aria-hidden="true"
            className={cn(
              "flex h-9 w-9 items-center justify-center rounded-[var(--radius-md)]",
              c.bg,
              c.fg,
            )}
          >
            <Icon className="h-4.5 w-4.5" />
          </span>
          <ArrowRight className="h-3.5 w-3.5 text-[var(--muted-foreground)] opacity-0 transition-opacity group-hover:opacity-100" />
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-sm text-[var(--muted-foreground)]">{label}</span>
          <p className="text-2xl font-semibold tabular-nums text-[var(--foreground)]">{value}</p>
          <p className="text-xs text-[var(--muted-foreground)]">{hint}</p>
        </div>
      </Card>
    </Link>
  );
}
