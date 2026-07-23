"use client";

import * as React from "react";
import * as ToastPrimitive from "@radix-ui/react-toast";
import { cn } from "@/lib/utils";

type ToastVariant = "default" | "success" | "error";

type ToastMessage = {
  id: number;
  title: string;
  variant: ToastVariant;
};

const ToastContext = React.createContext<{
  show: (title: string, variant?: ToastVariant) => void;
} | null>(null);

export function useToast() {
  const ctx = React.useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}

const variantClass: Record<ToastVariant, string> = {
  default: "border-[var(--border)] bg-[var(--background)]",
  success: "border-green-600/40 bg-green-50 text-green-900 dark:bg-green-950 dark:text-green-200",
  error: "border-red-600/40 bg-red-50 text-red-900 dark:bg-red-950 dark:text-red-200",
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [messages, setMessages] = React.useState<ToastMessage[]>([]);
  const nextId = React.useRef(0);

  const show = React.useCallback((title: string, variant: ToastVariant = "default") => {
    const id = nextId.current++;
    setMessages((prev) => [...prev, { id, title, variant }]);
  }, []);

  return (
    <ToastContext.Provider value={{ show }}>
      <ToastPrimitive.Provider swipeDirection="right">
        {children}
        {messages.map((m) => (
          <ToastPrimitive.Root
            key={m.id}
            duration={4000}
            onOpenChange={(open) => {
              if (!open) {
                setMessages((prev) => prev.filter((x) => x.id !== m.id));
              }
            }}
            className={cn(
              "rounded-md border px-4 py-3 text-sm shadow-md data-[state=open]:animate-in data-[state=closed]:animate-out",
              variantClass[m.variant],
            )}
          >
            <ToastPrimitive.Title>{m.title}</ToastPrimitive.Title>
          </ToastPrimitive.Root>
        ))}
        <ToastPrimitive.Viewport className="fixed bottom-4 right-4 z-50 flex w-80 flex-col gap-2 outline-none" />
      </ToastPrimitive.Provider>
    </ToastContext.Provider>
  );
}
