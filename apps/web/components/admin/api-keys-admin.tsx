"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useSession } from "next-auth/react";
import { browserFleetClient } from "@/lib/fleet-client-browser";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import type { components } from "@fleet/shared";
import { KeyRound } from "lucide-react";
import { EmptyState } from "@/components/layout/empty-state";

type ApiKeyOut = components["schemas"]["ApiKeyOut"];

// Mirrors the `require_scope(...)` names used across routers/service.py
// and routers/invoice_agent.py — the automation-recipe actions added in
// task 13.4 need their own scopes here or an n8n key cannot be issued for
// a recipe that uses them.
const AVAILABLE_SCOPES = [
  "pg_ro",
  "slack_post",
  "invoice_intake",
  "agent_run",
  "email_send",
  "notify",
];

export function ApiKeysAdmin({ initialKeys }: { initialKeys: ApiKeyOut[] }) {
  const t = useTranslations("admin");
  const { data: session } = useSession();
  const [keys, setKeys] = useState(initialKeys);
  const [name, setName] = useState("");
  const [scopes, setScopes] = useState<string[]>([]);
  const [rawKey, setRawKey] = useState<string | null>(null);

  function toggleScope(scope: string) {
    setScopes((prev) => (prev.includes(scope) ? prev.filter((s) => s !== scope) : [...prev, scope]));
  }

  async function issueKey() {
    if (!name.trim()) return;
    const client = browserFleetClient(session?.accessToken);
    const { data, error } = await client.POST("/v1/admin/api-keys", {
      body: { name: name.trim(), scopes },
    });
    if (error || !data) return;
    setRawKey(data.raw_key);
    setKeys((prev) => [...prev, data]);
    setName("");
    setScopes([]);
  }

  async function revokeKey(key: ApiKeyOut) {
    const client = browserFleetClient(session?.accessToken);
    const { error } = await client.POST("/v1/admin/api-keys/{key_id}/revoke", {
      params: { path: { key_id: key.id } },
    });
    if (error) return;
    setKeys((prev) =>
      prev.map((k) => (k.id === key.id ? { ...k, revoked_at: new Date().toISOString() } : k)),
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("apiKeysTitle")}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {rawKey && (
          <div className="rounded-[var(--radius-md)] border border-[var(--warning)] bg-[var(--warning-bg)] p-3 text-sm text-[var(--warning-fg)]">
            <p className="mb-1 font-medium">{t("keyShownOnce")}</p>
            <code className="break-all">{rawKey}</code>
          </div>
        )}

        <div className="flex flex-wrap items-end gap-2">
          <Input placeholder={t("name")} value={name} onChange={(e) => setName(e.target.value)} />
          <div className="flex gap-2">
            {AVAILABLE_SCOPES.map((scope) => (
              <button
                key={scope}
                type="button"
                onClick={() => toggleScope(scope)}
                className={`rounded-full px-2 py-1 text-xs ${
                  scopes.includes(scope)
                    ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
                    : "border border-[var(--border)] text-[var(--muted-foreground)]"
                }`}
              >
                {scope}
              </button>
            ))}
          </div>
          <Button size="sm" onClick={issueKey}>
            {t("issueKey")}
          </Button>
        </div>

        {keys.length === 0 ? (
          <EmptyState
            icon={KeyRound}
            title={t("emptyKeysTitle")}
            description={t("emptyKeysDesc")}
          />
        ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("name")}</TableHead>
              <TableHead>{t("scopes")}</TableHead>
              <TableHead></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {keys.map((key) => (
              <TableRow key={key.id}>
                <TableCell>{key.name}</TableCell>
                <TableCell>{key.scopes.join(", ")}</TableCell>
                <TableCell className="flex justify-end">
                  {key.revoked_at ? (
                    <Badge variant="error">{t("revoked")}</Badge>
                  ) : (
                    <Button size="sm" variant="outline" onClick={() => revokeKey(key)}>
                      {t("revoke")}
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        )}
      </CardContent>
    </Card>
  );
}
