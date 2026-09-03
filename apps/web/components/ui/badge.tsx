import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

// Every variant paints from the token pairs in globals.css — before task 13.1
// `success`/`pending` referenced bare Tailwind palette classes that had no
// place in the token system and no dark-mode counterpart in it.
const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
  {
    variants: {
      variant: {
        default: "bg-[var(--surface-2)] text-[var(--muted-foreground)]",
        success: "bg-[var(--success-bg)] text-[var(--success-fg)]",
        pending: "bg-[var(--warning-bg)] text-[var(--warning-fg)]",
        error: "bg-[var(--danger-bg)] text-[var(--danger-fg)]",
        info: "bg-[var(--info-bg)] text-[var(--info-fg)]",
        accent: "bg-[var(--accent-soft)] text-[var(--accent-foreground)]",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant, className }))} {...props} />;
}
