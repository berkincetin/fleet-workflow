"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useSession } from "next-auth/react";
import { browserFleetClient } from "@/lib/fleet-client-browser";
import { useToast } from "@/components/ui/toast";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import type { components } from "@fleet/shared";
import { Bot } from "lucide-react";
import { EmptyState } from "@/components/layout/empty-state";

type AgentOut = components["schemas"]["AgentOut"];

export function AgentsAdmin({
  initialAgents,
  initialGlobalReadOnly,
}: {
  initialAgents: AgentOut[];
  initialGlobalReadOnly: boolean;
}) {
  const t = useTranslations("admin");
  const { data: session } = useSession();
  const { show } = useToast();
  const [agents, setAgents] = useState(initialAgents);
  const [globalReadOnly, setGlobalReadOnly] = useState(initialGlobalReadOnly);
  const [newName, setNewName] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);

  async function togglePause(agent: AgentOut) {
    setBusyId(agent.id);
    const client = browserFleetClient(session?.accessToken);
    const path =
      agent.status === "active" ? "/v1/admin/agents/{agent_id}/pause" : "/v1/admin/agents/{agent_id}/resume";
    const { error } = await client.POST(path, { params: { path: { agent_id: agent.id } } });
    setBusyId(null);
    if (error) {
      show(t("noAccess"), "error");
      return;
    }
    setAgents((prev) =>
      prev.map((a) =>
        a.id === agent.id ? { ...a, status: a.status === "active" ? "paused" : "active" } : a,
      ),
    );
  }

  async function createAgent() {
    if (!newName.trim()) return;
    const client = browserFleetClient(session?.accessToken);
    const { data, error } = await client.POST("/v1/admin/agents", {
      body: {
        name: newName.trim(),
        reasoning_model: "reasoning",
        utility_model: "utility",
        sensitivity: "internal",
        semantic_cache: false,
        semantic_cache_threshold: 0.95,
        max_context_tokens: 8000,
      },
    });
    if (error || !data) return;
    setAgents((prev) => [...prev, data]);
    setNewName("");
  }

  async function deleteAgent(agent: AgentOut) {
    setBusyId(agent.id);
    const client = browserFleetClient(session?.accessToken);
    const { error } = await client.DELETE("/v1/admin/agents/{agent_id}", {
      params: { path: { agent_id: agent.id } },
    });
    setBusyId(null);
    if (error) return;
    setAgents((prev) => prev.filter((a) => a.id !== agent.id));
  }

  async function toggleGlobalReadOnly() {
    const client = browserFleetClient(session?.accessToken);
    const next = !globalReadOnly;
    const { error } = await client.PUT("/v1/admin/agents/global/read-only", {
      body: { enabled: next },
    });
    if (!error) setGlobalReadOnly(next);
  }

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>{t("globalReadOnly")}</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-between">
          <p className="text-sm text-[var(--muted-foreground)]">{t("globalReadOnlyDesc")}</p>
          <Button size="sm" variant={globalReadOnly ? "default" : "outline"} onClick={toggleGlobalReadOnly}>
            {globalReadOnly ? t("statusActive") : t("statusPaused")}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("agentsTitle")}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="flex gap-2">
            <Input
              placeholder={t("createAgent")}
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
            />
            <Button size="sm" onClick={createAgent}>
              {t("createAgent")}
            </Button>
          </div>

          {agents.length === 0 ? (
            <EmptyState
              icon={Bot}
              title={t("emptyAgentsTitle")}
              description={t("emptyAgentsDesc")}
            />
          ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("name")}</TableHead>
                <TableHead>{t("statusActive")}</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {agents.map((agent) => (
                <TableRow key={agent.id}>
                  <TableCell>{agent.name}</TableCell>
                  <TableCell>
                    {agent.status === "active" ? (
                      <Badge variant="success">{t("statusActive")}</Badge>
                    ) : (
                      <Badge variant="pending">{t("statusPaused")}</Badge>
                    )}
                  </TableCell>
                  <TableCell className="flex justify-end gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={busyId === agent.id}
                      onClick={() => togglePause(agent)}
                    >
                      {agent.status === "active" ? t("pause") : t("resume")}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={busyId === agent.id}
                      onClick={() => deleteAgent(agent)}
                    >
                      {t("deleteAgent")}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
