"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useSession } from "next-auth/react";
import { browserFleetClient } from "@/lib/fleet-client-browser";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import type { components } from "@fleet/shared";
import { ScrollText } from "lucide-react";
import { EmptyState } from "@/components/layout/empty-state";

type AuditRowOut = components["schemas"]["AuditRowOut"];

export function AuditExplorer({ initialRows }: { initialRows: AuditRowOut[] }) {
  const t = useTranslations("admin");
  const { data: session } = useSession();
  const [rows, setRows] = useState(initialRows);
  const [actor, setActor] = useState("");
  const [action, setAction] = useState("");

  async function search() {
    const client = browserFleetClient(session?.accessToken);
    const { data, error } = await client.GET("/v1/admin/audit", {
      params: {
        query: {
          limit: 100,
          ...(actor.trim() ? { actor: actor.trim() } : {}),
          ...(action.trim() ? { action: action.trim() } : {}),
        },
      },
    });
    if (error || !data) return;
    setRows(data);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("auditTitle")}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-wrap items-end gap-2">
          <Input placeholder={t("auditActor")} value={actor} onChange={(e) => setActor(e.target.value)} />
          <Input placeholder={t("auditAction")} value={action} onChange={(e) => setAction(e.target.value)} />
          <Button size="sm" onClick={search}>
            {t("auditSearch")}
          </Button>
        </div>

        {rows.length === 0 ? (
          <EmptyState
            icon={ScrollText}
            title={t("emptyAuditTitle")}
            description={t("emptyAuditDesc")}
          />
        ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("auditTime")}</TableHead>
              <TableHead>{t("auditActor")}</TableHead>
              <TableHead>{t("auditAction")}</TableHead>
              <TableHead></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.id}>
                <TableCell className="whitespace-nowrap text-xs text-[var(--muted-foreground)]">
                  {new Date(row.ts).toLocaleString()}
                </TableCell>
                <TableCell>{row.actor}</TableCell>
                <TableCell className="font-mono text-xs">{row.action}</TableCell>
                <TableCell className="text-right">
                  {row.langfuse_url && (
                    <a
                      href={row.langfuse_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-[var(--link)] underline"
                    >
                      {t("auditTrace")}
                    </a>
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
