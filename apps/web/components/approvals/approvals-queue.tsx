"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { useTranslations } from "next-intl";
import { browserFleetClient } from "@/lib/fleet-client-browser";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { components } from "@fleet/shared";

type ApprovalOut = components["schemas"]["ApprovalOut"];

export function ApprovalsQueue({ initialApprovals }: { initialApprovals: ApprovalOut[] }) {
  const t = useTranslations("approvals");
  const { data: session } = useSession();
  const [approvals, setApprovals] = useState(initialApprovals);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editValue, setEditValue] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);

  function startEdit(approval: ApprovalOut) {
    setEditingId(approval.id);
    setEditValue(JSON.stringify(approval.payload, null, 2));
    setError(null);
  }

  function cancelEdit() {
    setEditingId(null);
    setEditValue("");
  }

  async function decide(
    approval: ApprovalOut,
    decision: "approve" | "reject",
    editedPayload?: Record<string, unknown>,
  ) {
    setError(null);
    setBusyId(approval.id);
    const client = browserFleetClient(session?.accessToken);
    const { error: apiError } = await client.POST("/v1/approvals/{approval_id}/decide", {
      params: { path: { approval_id: approval.id } },
      body: { decision, edited_payload: editedPayload ?? null },
    });
    setBusyId(null);
    if (apiError) {
      setError(t("decideError"));
      return;
    }
    setApprovals((prev) => prev.filter((a) => a.id !== approval.id));
    setEditingId(null);
  }

  async function saveEditAndApprove(approval: ApprovalOut) {
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(editValue);
    } catch {
      setError(t("invalidJson"));
      return;
    }
    await decide(approval, "approve", parsed);
  }

  if (approvals.length === 0) {
    return <p className="text-sm text-[var(--muted-foreground)]">{t("noPending")}</p>;
  }

  return (
    <div className="flex flex-col gap-4">
      {error && <p className="text-sm text-red-600">{error}</p>}
      {approvals.map((approval) => (
        <Card key={approval.id} className="flex flex-col gap-3 p-4">
          <div className="flex items-center gap-2">
            <Badge>{approval.action}</Badge>
            <span className="text-xs text-[var(--muted-foreground)]">
              {t("agent")} #{approval.agent_id} · run {approval.run_id.slice(0, 8)}
            </span>
          </div>

          {editingId === approval.id ? (
            <textarea
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              rows={8}
              className="w-full rounded-md border border-[var(--border)] bg-transparent p-2 font-mono text-xs"
            />
          ) : (
            <pre className="overflow-x-auto rounded-md bg-[var(--muted)] p-2 text-xs">
              {JSON.stringify(approval.payload, null, 2)}
            </pre>
          )}

          <div className="flex gap-2">
            {editingId === approval.id ? (
              <>
                <Button
                  size="sm"
                  onClick={() => saveEditAndApprove(approval)}
                  disabled={busyId === approval.id}
                >
                  {t("save")}
                </Button>
                <Button size="sm" variant="outline" onClick={cancelEdit}>
                  {t("cancel")}
                </Button>
              </>
            ) : (
              <>
                <Button
                  size="sm"
                  onClick={() => decide(approval, "approve")}
                  disabled={busyId === approval.id}
                >
                  {t("approve")}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => startEdit(approval)}
                  disabled={busyId === approval.id}
                >
                  {t("editPayload")}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => decide(approval, "reject")}
                  disabled={busyId === approval.id}
                >
                  {t("reject")}
                </Button>
              </>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
}
