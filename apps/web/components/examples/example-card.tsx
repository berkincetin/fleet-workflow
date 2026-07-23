"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DevRunDialog } from "@/components/examples/dev-run-dialog";
import { InvoiceRunDialog } from "@/components/examples/invoice-run-dialog";
import type { components } from "@fleet/shared";

type ExampleOut = components["schemas"]["ExampleOut"];

function exampleTitle(example: ExampleOut): string {
  const p = example.payload;
  if (typeof p.question === "string") return p.question;
  if (typeof p.ticket_key === "string") return String(p.ticket_key);
  if (typeof p.vendor === "string") return `${p.vendor} — ${p.po_number ?? ""}`;
  return example.case_id;
}

export function ExampleCard({ example }: { example: ExampleOut }) {
  const t = useTranslations("examples");

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-normal">{exampleTitle(example)}</CardTitle>
      </CardHeader>
      <CardContent className="flex items-center justify-between">
        <span className="text-xs text-[var(--muted-foreground)]">{example.source}</span>
        {(example.agent_name === "support_copilot" || example.agent_name === "analytics") && (
          <Link
            href={`/chat?agent=${example.agent_name}&prefill=${encodeURIComponent(
              String(example.payload.question ?? ""),
            )}`}
          >
            <Button size="sm">{t("tryIt")}</Button>
          </Link>
        )}
        {example.agent_name === "dev_agent" && (
          <DevRunDialog initialTicketKey={String(example.payload.ticket_key ?? "")} />
        )}
        {example.agent_name === "invoice_agent" && <InvoiceRunDialog />}
      </CardContent>
    </Card>
  );
}
