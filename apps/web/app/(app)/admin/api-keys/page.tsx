import { fleetClient } from "@/lib/fleet-client";
import { ApiKeysAdmin } from "@/components/admin/api-keys-admin";

export default async function AdminApiKeysPage() {
  const client = await fleetClient();
  const { data: keys } = await client.GET("/v1/admin/api-keys");

  return <ApiKeysAdmin initialKeys={keys ?? []} />;
}
