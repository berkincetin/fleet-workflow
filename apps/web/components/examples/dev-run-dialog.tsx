"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { useSession } from "next-auth/react";
import { browserFleetClient } from "@/lib/fleet-client-browser";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import type { components } from "@fleet/shared";

type TicketOut = components["schemas"]["TicketOut"];

export function DevRunDialog({ initialTicketKey }: { initialTicketKey?: string }) {
  const t = useTranslations("examples");
  const { data: session } = useSession();
  const [open, setOpen] = useState(false);
  const [tickets, setTickets] = useState<TicketOut[]>([]);
  const [ticketKey, setTicketKey] = useState(initialTicketKey ?? "");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ status: string; reason?: string } | null>(null);

  useEffect(() => {
    if (!open || tickets.length > 0) return;
    const client = browserFleetClient(session?.accessToken);
    client.GET("/v1/dev-agent/tickets").then(({ data }) => {
      if (data) {
        setTickets(data);
        if (!ticketKey && data[0]) setTicketKey(data[0].key);
      }
    });
  }, [open, session?.accessToken, tickets.length, ticketKey]);

  async function run() {
    if (!ticketKey) return;
    setBusy(true);
    setResult(null);
    const client = browserFleetClient(session?.accessToken);
    const { data, error } = await client.POST("/v1/dev-agent/runs", {
      body: { ticket_key: ticketKey },
    });
    setBusy(false);
    if (error || !data) {
      setResult({ status: "blocked", reason: "n8n_unreachable" });
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
          <DialogTitle>{t("selectTicket")}</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-3">
          <Select value={ticketKey} onValueChange={setTicketKey}>
            <SelectTrigger>
              <SelectValue placeholder={t("selectTicket")} />
            </SelectTrigger>
            <SelectContent>
              {tickets.map((ticket) => (
                <SelectItem key={ticket.key} value={ticket.key}>
                  {ticket.key} — {ticket.summary}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button size="sm" onClick={run} disabled={busy || !ticketKey}>
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
