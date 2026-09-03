import { getTranslations } from "next-intl/server";
import { auth } from "@/lib/auth";
import { fleetClient } from "@/lib/fleet-client";
import { can } from "@/lib/permissions";
import { ServicesBoard } from "@/components/admin/services-board";

export default async function ServicesPage() {
  const t = await getTranslations("admin");
  const session = await auth();

  if (!can(session?.roles, "manage_platform")) {
    return <p className="text-sm text-[var(--muted-foreground)]">{t("noAccess")}</p>;
  }

  const client = await fleetClient();
  const { data } = await client.GET("/v1/admin/services");

  return (
    <ServicesBoard
      initial={data ?? null}
      canReveal={(session?.roles ?? []).includes("platform_admin")}
    />
  );
}
