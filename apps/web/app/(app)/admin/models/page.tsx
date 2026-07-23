import { fleetClient } from "@/lib/fleet-client";
import { ModelsAdmin } from "@/components/admin/models-admin";

export default async function AdminModelsPage() {
  const client = await fleetClient();
  const { data: models } = await client.GET("/v1/admin/models");

  return <ModelsAdmin initialModels={models ?? []} />;
}
