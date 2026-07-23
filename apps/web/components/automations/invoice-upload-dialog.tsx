"use client";

import { useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { useSession } from "next-auth/react";
import { browserFleetClient } from "@/lib/fleet-client-browser";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from "@/components/ui/dialog";

export function InvoiceUploadDialog({ disabled }: { disabled?: boolean }) {
  const t = useTranslations("automations");
  const tCommon = useTranslations("common");
  const { data: session } = useSession();
  const inputRef = useRef<HTMLInputElement>(null);
  const { show } = useToast();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  async function handleUpload() {
    const file = inputRef.current?.files?.[0];
    if (!file) return;

    setBusy(true);
    const client = browserFleetClient(session?.accessToken);
    const { data, error } = await client.POST("/v1/workflows/invoice-intake/run", {
      // Same File-through-FormData pattern as knowledge/upload-form.tsx.
      body: { file: file as unknown as string },
      bodySerializer: () => {
        const form = new FormData();
        form.append("file", file);
        return form;
      },
    });
    setBusy(false);

    if (error) {
      show(t("runUnreachable"), "error");
      return;
    }
    if (data?.status === "accepted") {
      show(t("runQueuedForApproval"), "success");
      setOpen(false);
    } else if (data?.status === "workflow_inactive") {
      show(t("runInactive"), "error");
    } else {
      show(t("runUnreachable"), "error");
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" disabled={disabled}>
          {t("invoiceUpload")}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("invoiceIntakeTitle")}</DialogTitle>
          <DialogDescription>{t("invoiceUploadHint")}</DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-3">
          <input
            ref={inputRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            className="text-sm"
            disabled={busy}
          />
          <Button size="sm" onClick={handleUpload} disabled={busy}>
            {busy ? tCommon("loading") : t("invoiceUpload")}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
