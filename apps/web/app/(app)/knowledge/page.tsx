import { getTranslations } from "next-intl/server";
import { fleetClient } from "@/lib/fleet-client";
import { KnowledgeBrowser } from "@/components/knowledge/knowledge-browser";
import { PageHeader } from "@/components/layout/page-header";

export default async function KnowledgePage() {
  const t = await getTranslations("knowledge");
  const client = await fleetClient();

  const { data: collections } = await client.GET("/v1/collections");

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={t("title")}
        intro={t("intro")}
        howToLabel={t("howToLabel")}
        howTo={t.raw("howTo") as string[]}
      />
      <KnowledgeBrowser initialCollections={collections ?? []} />
    </div>
  );
}
