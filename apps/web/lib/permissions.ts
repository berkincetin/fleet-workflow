/**
 * Client-side mirror of apps/api/fleet_api/rbac.py's ROLE_PERMISSIONS
 * (task 6.5.5). Nav-gating only — hiding a link is a courtesy, not a
 * security boundary; the API's `require_permission` is the real gate no
 * matter what this computes. Keep this in sync with rbac.py by hand; there
 * is no shared source between Python and TS for this small a table.
 */

export type Permission =
  | "chat"
  | "upload"
  | "manage_agents"
  | "approve"
  | "manage_dept"
  | "manage_platform";

const ROLE_PERMISSIONS: Record<string, Permission[]> = {
  member: ["chat", "upload"],
  builder: ["chat", "upload", "manage_agents"],
  approver: ["chat", "upload", "approve"],
  dept_admin: ["chat", "upload", "manage_agents", "approve", "manage_dept"],
  platform_admin: [
    "chat",
    "upload",
    "manage_agents",
    "approve",
    "manage_dept",
    "manage_platform",
  ],
};

export function permissionsFor(roles: string[] | undefined): Set<Permission> {
  const granted = new Set<Permission>();
  for (const role of roles ?? []) {
    for (const perm of ROLE_PERMISSIONS[role] ?? []) {
      granted.add(perm);
    }
  }
  return granted;
}

export function can(roles: string[] | undefined, permission: Permission): boolean {
  return permissionsFor(roles).has(permission);
}
