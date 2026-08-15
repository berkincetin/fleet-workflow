"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useSession } from "next-auth/react";
import { browserFleetClient } from "@/lib/fleet-client-browser";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

export function CreateExampleDialog({
  agentName,
  onCreated,
}: {
  agentName: string;
  onCreated: () => void;
}) {
  const t = useTranslations("examples");
  const tCommon = useTranslations("common");
  const { data: session } = useSession();
  const { show } = useToast();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  const [question, setQuestion] = useState("");
  const [ticketKey, setTicketKey] = useState("");
  const [vendor, setVendor] = useState("");
  const [poNumber, setPoNumber] = useState("");
  const [amount, setAmount] = useState("");
  const [candidateName, setCandidateName] = useState("");

  function buildPayload(): Record<string, unknown> {
    const id = `user-${Date.now()}`;
    if (agentName === "support_copilot" || agentName === "analytics") {
      return { id, question };
    }
    if (agentName === "dev_agent") {
      return { id, ticket_key: ticketKey };
    }
    if (agentName === "hr_agent") {
      return { id, candidate_name: candidateName };
    }
    return {
      id,
      vendor,
      po_number: poNumber,
      amount,
      expect_vendor: vendor,
      expect_po_number: poNumber,
      expect_amount: Number(amount) || 0,
      expect_validation_ok: true,
    };
  }

  async function create() {
    setBusy(true);
    const client = browserFleetClient(session?.accessToken);
    const { error } = await client.POST("/v1/examples", {
      body: { agent_name: agentName, payload: buildPayload() },
    });
    setBusy(false);
    if (error) {
      show(t("createError"), "error");
      return;
    }
    show(t("createSuccess"), "success");
    setOpen(false);
    setQuestion("");
    setTicketKey("");
    setVendor("");
    setPoNumber("");
    setAmount("");
    setCandidateName("");
    onCreated();
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          {t("addExample")}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("addExampleTitle")}</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-3">
          {(agentName === "support_copilot" || agentName === "analytics") && (
            <label className="flex flex-col gap-1 text-sm">
              {t("question")}
              <Input value={question} onChange={(e) => setQuestion(e.target.value)} />
            </label>
          )}
          {agentName === "dev_agent" && (
            <label className="flex flex-col gap-1 text-sm">
              {t("ticketKey")}
              <Input value={ticketKey} onChange={(e) => setTicketKey(e.target.value)} />
            </label>
          )}
          {agentName === "hr_agent" && (
            <label className="flex flex-col gap-1 text-sm">
              {t("candidateName")}
              <Input value={candidateName} onChange={(e) => setCandidateName(e.target.value)} />
            </label>
          )}
          {agentName === "invoice_agent" && (
            <>
              <label className="flex flex-col gap-1 text-sm">
                {t("vendor")}
                <Input value={vendor} onChange={(e) => setVendor(e.target.value)} />
              </label>
              <label className="flex flex-col gap-1 text-sm">
                {t("poNumber")}
                <Input value={poNumber} onChange={(e) => setPoNumber(e.target.value)} />
              </label>
              <label className="flex flex-col gap-1 text-sm">
                {t("amount")}
                <Input value={amount} onChange={(e) => setAmount(e.target.value)} />
              </label>
            </>
          )}
          <Button size="sm" onClick={create} disabled={busy}>
            {tCommon("create")}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
