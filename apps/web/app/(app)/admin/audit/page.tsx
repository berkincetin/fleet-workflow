import { fleetClient } from "@/lib/fleet-client";
import { AuditExplorer } from "@/components/admin/audit-explorer";

export default async function AdminAuditPage() {
  const client = await fleetClient();
  const { data: rows } = await client.GET("/v1/admin/audit", {
    params: { query: { limit: 100 } },
  });

  return <AuditExplorer initialRows={rows ?? []} />;
}
