import { fleetClient } from "@/lib/fleet-client";
import { UsersAdmin } from "@/components/admin/users-admin";

export default async function AdminUsersPage() {
  const client = await fleetClient();
  const [{ data: users }, { data: departments }] = await Promise.all([
    client.GET("/v1/admin/users"),
    client.GET("/v1/admin/departments"),
  ]);

  return <UsersAdmin initialUsers={users ?? []} departments={departments ?? []} />;
}
