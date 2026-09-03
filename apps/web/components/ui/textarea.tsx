import * as React from "react";
import { cn } from "@/lib/utils";

export function Textarea({ className, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "w-full rounded-[var(--radius-md)] border border-[var(--border-strong)] bg-[var(--surface)] p-2 text-sm placeholder:text-[var(--muted-foreground)]",
        className,
      )}
      {...props}
    />
  );
}
