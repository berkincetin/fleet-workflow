"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useSession } from "next-auth/react";
import { browserFleetClient } from "@/lib/fleet-client-browser";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import type { components } from "@fleet/shared";

type UserOut = components["schemas"]["UserOut"];
type DepartmentOut = components["schemas"]["DepartmentOut"];

const ASSIGNABLE_ROLES = ["member", "builder", "approver", "dept_admin", "platform_admin"] as const;

export function UsersAdmin({
  initialUsers,
  departments,
}: {
  initialUsers: UserOut[];
  departments: DepartmentOut[];
}) {
  const t = useTranslations("admin");
  const { data: session } = useSession();
  const [users, setUsers] = useState(initialUsers);
  const [pendingRole, setPendingRole] = useState<Record<number, string>>({});

  const deptName = (id: number | null) =>
    id == null ? t("noDepartment") : (departments.find((d) => d.id === id)?.name ?? id);

  async function setDept(user: UserOut, deptId: number | null) {
    const client = browserFleetClient(session?.accessToken);
    const { data, error } = await client.PATCH("/v1/admin/users/{user_id}", {
      params: { path: { user_id: user.id } },
      body: { dept_id: deptId },
    });
    if (error || !data) return;
    setUsers((prev) => prev.map((u) => (u.id === user.id ? data : u)));
  }

  async function addRole(user: UserOut) {
    const role = pendingRole[user.id];
    if (!role) return;
    const client = browserFleetClient(session?.accessToken);
    const { data, error } = await client.POST("/v1/admin/users/{user_id}/roles", {
      params: { path: { user_id: user.id } },
      body: { role, dept_id: user.dept_id ?? null },
    });
    if (error || !data) return;
    setUsers((prev) =>
      prev.map((u) => (u.id === user.id ? { ...u, roles: [...u.roles, data] } : u)),
    );
  }

  async function removeRole(user: UserOut, roleId: number) {
    const client = browserFleetClient(session?.accessToken);
    const { error } = await client.DELETE("/v1/admin/users/{user_id}/roles/{role_id}", {
      params: { path: { user_id: user.id, role_id: roleId } },
    });
    if (error) return;
    setUsers((prev) =>
      prev.map((u) =>
        u.id === user.id ? { ...u, roles: u.roles.filter((r) => r.id !== roleId) } : u,
      ),
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("usersTitle")}</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("name")}</TableHead>
              <TableHead>{t("department")}</TableHead>
              <TableHead>{t("roles")}</TableHead>
              <TableHead></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell>{user.display_name}</TableCell>
                <TableCell>
                  <Select
                    value={user.dept_id != null ? String(user.dept_id) : "none"}
                    onValueChange={(v) => setDept(user, v === "none" ? null : Number(v))}
                  >
                    <SelectTrigger className="w-40">
                      <SelectValue>{deptName(user.dept_id)}</SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">{t("noDepartment")}</SelectItem>
                      {departments.map((d) => (
                        <SelectItem key={d.id} value={String(d.id)}>
                          {d.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell>
                  <div className="flex flex-wrap gap-1">
                    {user.roles.map((r) => (
                      <Badge key={r.id} className="flex items-center gap-1">
                        {t(`roleNames.${r.role}` as never)}
                        <button
                          type="button"
                          aria-label={t("removeRole")}
                          onClick={() => removeRole(user, r.id)}
                          className="ml-1 text-xs opacity-70 hover:opacity-100"
                        >
                          ×
                        </button>
                      </Badge>
                    ))}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Select
                      value={pendingRole[user.id] ?? ""}
                      onValueChange={(v) => setPendingRole((prev) => ({ ...prev, [user.id]: v }))}
                    >
                      <SelectTrigger className="w-40">
                        <SelectValue placeholder={t("addRole")} />
                      </SelectTrigger>
                      <SelectContent>
                        {ASSIGNABLE_ROLES.map((role) => (
                          <SelectItem key={role} value={role}>
                            {t(`roleNames.${role}`)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Button size="sm" variant="outline" onClick={() => addRole(user)}>
                      {t("addRole")}
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
