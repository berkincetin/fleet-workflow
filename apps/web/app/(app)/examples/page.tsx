import { getTranslations } from "next-intl/server";
import { fleetClient } from "@/lib/fleet-client";
import { ExamplesGallery } from "@/components/examples/examples-gallery";
import { PageHeader } from "@/components/layout/page-header";

export default async function ExamplesPage({
  searchParams,
}: {
  searchParams: Promise<{ agent?: string }>;
}) {
  const t = await getTranslations("examples");
  const client = await fleetClient();
  const { agent } = await searchParams;

  const { data: agents } = await client.GET("/v1/agents");
  const { data: examples } = await client.GET("/v1/examples");

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={t("title")}
        intro={t("intro")}
        howToLabel={t("howToLabel")}
        howTo={t.raw("howTo") as string[]}
      />
      <ExamplesGallery
        agents={agents ?? []}
        initialExamples={examples ?? []}
        initialAgentName={agent}
      />
    </div>
  );
}
