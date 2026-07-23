import { getTranslations } from "next-intl/server";
import { fleetClient } from "@/lib/fleet-client";
import { ExamplesGallery } from "@/components/examples/examples-gallery";

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
      <div>
        <h1 className="text-xl font-semibold">{t("title")}</h1>
        <p className="text-sm text-[var(--muted-foreground)]">{t("subtitle")}</p>
      </div>
      <ExamplesGallery
        agents={agents ?? []}
        initialExamples={examples ?? []}
        initialAgentName={agent}
      />
    </div>
  );
}
