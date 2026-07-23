import { fleetClient } from "@/lib/fleet-client";
import { AgentsAdmin } from "@/components/admin/agents-admin";

export default async function AdminAgentsPage() {
  const client = await fleetClient();
  const { data: agents } = await client.GET("/v1/admin/agents");
  const { data: readOnly } = await client.GET("/v1/admin/agents/global/read-only");

  return (
    <AgentsAdmin
      initialAgents={agents ?? []}
      initialGlobalReadOnly={readOnly?.enabled ?? false}
    />
  );
}
