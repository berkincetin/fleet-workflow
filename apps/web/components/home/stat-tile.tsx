import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

/**
 * One number on the Home dashboard (task 13.1). Every tile is a link — the
 * dashboard's job is to be the shortest route to the screen that acts on the
 * number, not a read-only report.
 */
export function StatTile({
  label,
  value,
  hint,
  href,
  tone = "default",
  icon: Icon,
}: {
  label: string;
  value: string;
  hint: string;
  href: string;
  tone?: "default" | "attention";
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <Link href={href} className="group block">
      <Card className="flex h-full flex-col gap-2 p-4 transition-colors hover:border-[var(--border-strong)]">
        <div className="flex items-center justify-between gap-2">
          <span className="flex items-center gap-2 text-sm text-[var(--muted-foreground)]">
            <Icon className="h-4 w-4" />
            {label}
          </span>
          <ArrowRight className="h-3.5 w-3.5 text-[var(--muted-foreground)] opacity-0 transition-opacity group-hover:opacity-100" />
        </div>
        <p
          className={cn(
            "text-2xl font-semibold tabular-nums",
            tone === "attention" ? "text-[var(--warning)]" : "text-[var(--foreground)]",
          )}
        >
          {value}
        </p>
        <p className="text-xs text-[var(--muted-foreground)]">{hint}</p>
      </Card>
    </Link>
  );
}
