import { fleetClient } from "@/lib/fleet-client";
import { CostDashboard } from "@/components/admin/cost-dashboard";

export default async function AdminCostPage() {
  const client = await fleetClient();
  const { data: summary } = await client.GET("/v1/admin/cost/summary", {
    params: { query: { days: 30 } },
  });

  return <CostDashboard initialSummary={summary ?? null} />;
}
