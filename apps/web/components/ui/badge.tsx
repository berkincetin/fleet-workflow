import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
  {
    variants: {
      variant: {
        default: "bg-[var(--muted)] text-[var(--muted-foreground)]",
        success: "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300",
        pending: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
        error: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
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
