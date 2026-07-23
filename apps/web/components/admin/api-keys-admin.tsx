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

type ApiKeyOut = components["schemas"]["ApiKeyOut"];

const AVAILABLE_SCOPES = ["pg_ro", "slack_post", "invoice_intake"];

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
          <div className="rounded-md border border-amber-500/40 bg-amber-50 p-3 text-sm dark:bg-amber-950">
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
      </CardContent>
    </Card>
  );
}
