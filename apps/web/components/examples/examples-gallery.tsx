"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useSession } from "next-auth/react";
import { browserFleetClient } from "@/lib/fleet-client-browser";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { ExampleCard } from "@/components/examples/example-card";
import { CreateExampleDialog } from "@/components/examples/create-example-dialog";
import type { components } from "@fleet/shared";

type AgentSummary = components["schemas"]["AgentSummaryOut"];
type ExampleOut = components["schemas"]["ExampleOut"];

export function ExamplesGallery({
  agents,
  initialExamples,
  initialAgentName,
}: {
  agents: AgentSummary[];
  initialExamples: ExampleOut[];
  initialAgentName?: string;
}) {
  const t = useTranslations("examples");
  const { data: session } = useSession();
  const [examples, setExamples] = useState(initialExamples);
  const defaultTab = initialAgentName ?? agents[0]?.name ?? "";
  const [activeTab, setActiveTab] = useState(defaultTab);

  async function refresh() {
    const client = browserFleetClient(session?.accessToken);
    const { data } = await client.GET("/v1/examples");
    if (data) setExamples(data);
  }

  if (agents.length === 0) return null;

  return (
    <Tabs value={activeTab} onValueChange={setActiveTab}>
      <TabsList>
        {agents.map((a) => (
          <TabsTrigger key={a.name} value={a.name}>
            {a.name}
          </TabsTrigger>
        ))}
      </TabsList>
      {agents.map((a) => {
        const agentExamples = examples.filter((e) => e.agent_name === a.name);
        return (
          <TabsContent key={a.name} value={a.name}>
            <div className="mb-3 flex justify-end">
              <CreateExampleDialog agentName={a.name} onCreated={refresh} />
            </div>
            {agentExamples.length === 0 ? (
              <p className="text-sm text-[var(--muted-foreground)]">{t("noExamples")}</p>
            ) : (
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {agentExamples.map((ex) => (
                  <ExampleCard key={ex.id} example={ex} />
                ))}
              </div>
            )}
          </TabsContent>
        );
      })}
    </Tabs>
  );
}
