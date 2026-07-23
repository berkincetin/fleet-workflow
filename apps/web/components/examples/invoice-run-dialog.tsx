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

export function InvoiceRunDialog() {
  const t = useTranslations("examples");
  const tAuto = useTranslations("automations");
  const { data: session } = useSession();
  const inputRef = useRef<HTMLInputElement>(null);
  const { show } = useToast();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  async function run() {
    const file = inputRef.current?.files?.[0];
    if (!file) return;
    setBusy(true);
    const client = browserFleetClient(session?.accessToken);
    const { data, error } = await client.POST("/v1/workflows/invoice-intake/run", {
      body: { file: file as unknown as string },
      bodySerializer: () => {
        const form = new FormData();
        form.append("file", file);
        return form;
      },
    });
    setBusy(false);
    if (error || !data) {
      show(tAuto("runUnreachable"), "error");
      return;
    }
    if (data.status === "accepted") {
      show(tAuto("runQueuedForApproval"), "success");
      setOpen(false);
    } else if (data.status === "workflow_inactive") {
      show(tAuto("runInactive"), "error");
    } else {
      show(tAuto("runUnreachable"), "error");
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">{t("tryIt")}</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("uploadInvoiceImage")}</DialogTitle>
          <DialogDescription>{tAuto("invoiceUploadHint")}</DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-3">
          <input
            ref={inputRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            className="text-sm"
            disabled={busy}
          />
          <Button size="sm" onClick={run} disabled={busy}>
            {t("tryIt")}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
