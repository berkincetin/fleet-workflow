import { Inbox } from "lucide-react";

/**
 * Directive empty state (task 13.2). An empty list must say what the missing
 * thing *is* and what the reader should do next — "No documents." on its own
 * tells a first-time user nothing, so `title` + `description` are required and
 * `action` is expected wherever the reader can actually create the thing.
 */
export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  action,
}: {
  icon?: typeof Inbox;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-[var(--radius-lg)] border border-dashed border-[var(--border-strong)] bg-[var(--surface-2)] px-6 py-10 text-center">
      <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--surface-3)] text-[var(--muted-foreground)]">
        <Icon className="h-5 w-5" aria-hidden="true" />
      </span>
      <div className="flex flex-col gap-1">
        <p className="text-sm font-medium">{title}</p>
        <p className="max-w-md text-sm text-[var(--muted-foreground)]">{description}</p>
      </div>
      {action}
    </div>
  );
}
