import { getTranslations } from "next-intl/server";
import { fleetClient } from "@/lib/fleet-client";
import { ChatWindow } from "@/components/chat/chat-window";

export default async function ChatPage() {
  const t = await getTranslations("chat");
  const client = await fleetClient();

  const { data: agents } = await client.GET("/v1/agents");

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold">{t("title")}</h1>
      <ChatWindow agents={agents ?? []} />
    </div>
  );
}
