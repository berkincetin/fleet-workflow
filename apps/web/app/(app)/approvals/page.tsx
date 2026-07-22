import { getTranslations } from "next-intl/server";
import { fleetClient } from "@/lib/fleet-client";
import { ApprovalsQueue } from "@/components/approvals/approvals-queue";

export default async function ApprovalsPage() {
  const t = await getTranslations("approvals");
  const client = await fleetClient();

  const { data: approvals } = await client.GET("/v1/approvals", {
    params: { query: { status: "pending" } },
  });

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold">{t("title")}</h1>
      <ApprovalsQueue initialApprovals={approvals ?? []} />
    </div>
  );
}
