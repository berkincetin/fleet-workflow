import { getTranslations } from "next-intl/server";
import { fleetClient } from "@/lib/fleet-client";
import { ChatWindow } from "@/components/chat/chat-window";
import { PageHeader } from "@/components/layout/page-header";

export default async function ChatPage({
  searchParams,
}: {
  searchParams: Promise<{ agent?: string; prefill?: string }>;
}) {
  const t = await getTranslations("chat");
  const client = await fleetClient();
  const { agent, prefill } = await searchParams;

  const { data: agents } = await client.GET("/v1/agents");

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={t("title")}
        intro={t("intro")}
        howToLabel={t("howToLabel")}
        howTo={t.raw("howTo") as string[]}
      />
      <ChatWindow agents={agents ?? []} initialAgentName={agent} initialPrefill={prefill} />
    </div>
  );
}
