import * as React from "react";
import { cn } from "@/lib/utils";

export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-9 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-1 text-sm",
        className,
      )}
      {...props}
    />
  );
}
