import { getTranslations } from "next-intl/server";
import { fleetClient } from "@/lib/fleet-client";
import { KnowledgeBrowser } from "@/components/knowledge/knowledge-browser";

export default async function KnowledgePage() {
  const t = await getTranslations("knowledge");
  const client = await fleetClient();

  const { data: collections } = await client.GET("/v1/collections");

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold">{t("title")}</h1>
      <KnowledgeBrowser initialCollections={collections ?? []} />
    </div>
  );
}
