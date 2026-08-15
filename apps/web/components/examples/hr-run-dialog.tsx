"use client";

import { useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { useSession } from "next-auth/react";
import { browserFleetClient } from "@/lib/fleet-client-browser";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      resolve(result.split(",")[1] ?? "");
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export function HrRunDialog() {
  const t = useTranslations("examples");
  const { data: session } = useSession();
  const inputRef = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [criteria, setCriteria] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ status: string; reason?: string } | null>(null);

  async function run() {
    const file = inputRef.current?.files?.[0];
    if (!file) return;
    setBusy(true);
    setResult(null);
    const image_base64 = await fileToBase64(file);
    const client = browserFleetClient(session?.accessToken);
    const { data, error } = await client.POST("/v1/hr-agent/runs", {
      body: {
        image_base64,
        criteria: criteria
          .split(",")
          .map((c) => c.trim())
          .filter(Boolean),
      },
    });
    setBusy(false);
    if (error || !data) {
      setResult({ status: "blocked", reason: "gateway_unreachable" });
      return;
    }
    setResult({ status: data.status, reason: (data.detail as { reason?: string })?.reason });
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">{t("tryIt")}</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("uploadCvImage")}</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-3">
          <input
            ref={inputRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            className="text-sm"
            disabled={busy}
          />
          <Input
            placeholder={t("criteriaPlaceholder")}
            value={criteria}
            onChange={(e) => setCriteria(e.target.value)}
            disabled={busy}
          />
          <Button size="sm" onClick={run} disabled={busy}>
            {t("tryIt")}
          </Button>
          {result && (
            <p className="text-sm">
              {result.status === "pending_approval"
                ? t("pendingApproval")
                : t("blocked", { reason: result.reason ?? "" })}
            </p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
