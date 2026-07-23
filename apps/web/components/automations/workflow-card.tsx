"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useSession } from "next-auth/react";
import { browserFleetClient } from "@/lib/fleet-client-browser";
import { useToast } from "@/components/ui/toast";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { InvoiceUploadDialog } from "@/components/automations/invoice-upload-dialog";
import { can } from "@/lib/permissions";
import type { components } from "@fleet/shared";

type WorkflowOut = components["schemas"]["WorkflowOut"];

export function WorkflowCard({
  workflow,
  roles,
}: {
  workflow: WorkflowOut;
  roles: string[] | undefined;
}) {
  const t = useTranslations("automations");
  const tCommon = useTranslations("common");
  const { data: session } = useSession();
  const { show } = useToast();
  const [state, setState] = useState(workflow);
  const [busy, setBusy] = useState(false);

  const isInvoice = state.slug === "invoice-intake";
  const canOperate = can(roles, "manage_agents");

  async function toggleActive() {
    if (!state.reachable) return;
    setBusy(true);
    const client = browserFleetClient(session?.accessToken);
    const path = state.active
      ? "/v1/workflows/{slug}/deactivate"
      : "/v1/workflows/{slug}/activate";
    const { data, error } = await client.POST(path, {
      params: { path: { slug: state.slug } },
    });
    setBusy(false);
    if (error || !data || data.status !== "accepted") {
      show(t("runUnreachable"), "error");
      return;
    }
    setState((prev) => ({ ...prev, active: !prev.active }));
  }

  async function runWeeklySummary() {
    setBusy(true);
    const client = browserFleetClient(session?.accessToken);
    const { data, error } = await client.POST("/v1/workflows/weekly-summary/run");
    setBusy(false);
    if (error || !data) {
      show(t("runUnreachable"), "error");
      return;
    }
    if (data.status === "accepted") {
      show(t("runAccepted"), "success");
    } else if (data.status === "workflow_inactive") {
      show(t("runInactive"), "error");
    } else {
      show(t("runUnreachable"), "error");
    }
  }

  const title = isInvoice ? t("invoiceIntakeTitle") : t("weeklySummaryTitle");
  const desc = isInvoice ? t("invoiceIntakeDesc") : t("weeklySummaryDesc");

  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between gap-2">
        <CardTitle>{title}</CardTitle>
        {!state.reachable ? (
          <Badge variant="error">{t("statusInactive")}</Badge>
        ) : state.auth_error ? (
          <Badge variant="error">{t("statusInactive")}</Badge>
        ) : state.active ? (
          <Badge variant="success">{t("statusActive")}</Badge>
        ) : (
          <Badge variant="pending">{t("statusInactive")}</Badge>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <p className="text-sm text-[var(--muted-foreground)]">{desc}</p>

        {!state.reachable && <p className="text-sm text-[var(--danger)]">{t("n8nDown")}</p>}
        {state.reachable && state.auth_error && (
          <p className="text-sm text-[var(--danger)]">{t("n8nAuthError")}</p>
        )}

        <p className="text-xs text-[var(--muted-foreground)]">
          {t("lastRun")}:{" "}
          {state.last_run ? `${state.last_run.status} (${state.last_run.at})` : t("neverRun")}
        </p>

        <div className="flex flex-wrap items-center gap-2">
          {isInvoice ? (
            <InvoiceUploadDialog disabled={!state.reachable || state.active === false} />
          ) : (
            <Button
              size="sm"
              onClick={runWeeklySummary}
              disabled={busy || !state.reachable || !canOperate}
            >
              {tCommon("runNow")}
            </Button>
          )}
          {canOperate && state.reachable && !state.auth_error && (
            <Button size="sm" variant="outline" onClick={toggleActive} disabled={busy}>
              {state.active ? t("deactivate") : t("activate")}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
