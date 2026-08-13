import { fleetClient } from "@/lib/fleet-client";
import { BudgetsAdmin } from "@/components/admin/budgets-admin";

export default async function AdminBudgetsPage() {
  const client = await fleetClient();
  const { data: budgets } = await client.GET("/v1/admin/budgets");

  return <BudgetsAdmin initialBudgets={budgets ?? []} />;
}
