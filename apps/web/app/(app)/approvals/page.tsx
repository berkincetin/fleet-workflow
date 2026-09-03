import { getTranslations } from "next-intl/server";
import { fleetClient } from "@/lib/fleet-client";
import { ApprovalsQueue } from "@/components/approvals/approvals-queue";
import { GlossaryList } from "@/components/layout/glossary";
import { PageHeader } from "@/components/layout/page-header";

export default async function ApprovalsPage() {
  const t = await getTranslations("approvals");
  const client = await fleetClient();

  const { data: approvals } = await client.GET("/v1/approvals", {
    params: { query: { status: "pending" } },
  });

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={t("title")}
        intro={t("intro")}
        howToLabel={t("howToLabel")}
        howTo={t.raw("howTo") as string[]}
      />
      <GlossaryList terms={["writeExternal", "riskClass", "hitl"]} />
      <ApprovalsQueue initialApprovals={approvals ?? []} />
    </div>
  );
}
