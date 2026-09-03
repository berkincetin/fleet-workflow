"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useSession } from "next-auth/react";
import type { components } from "@fleet/shared";
import { browserFleetClient } from "@/lib/fleet-client-browser";
import { streamChatMessage } from "@/lib/chat-stream";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FeedbackButtons } from "@/components/chat/feedback-buttons";
import { Bot, Sparkles } from "lucide-react";
import { EmptyState } from "@/components/layout/empty-state";
import { startersFor } from "@/lib/chat-starters";

type AgentSummary = components["schemas"]["AgentSummaryOut"];

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  citations?: unknown[];
  messageId?: number;
  streaming?: boolean;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_FLEET_API_BASE_URL ?? "http://localhost:8000";

export function ChatWindow({
  agents,
  initialAgentName,
  initialPrefill,
}: {
  agents: AgentSummary[];
  /** Preselects an agent by name (task 6.5.8's Examples "try it" deep link). */
  initialAgentName?: string;
  /** Prefills the composer so a try-it example is one click from sending. */
  initialPrefill?: string;
}) {
  const t = useTranslations("chat");
  const { data: session } = useSession();
  const preselected = initialAgentName
    ? agents.find((a) => a.name === initialAgentName)
    : undefined;
  const [agentId, setAgentId] = useState<number | null>(preselected?.id ?? agents[0]?.id ?? null);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState(initialPrefill ?? "");
  const [busy, setBusy] = useState(false);

  // Keyed off the *selected* agent, not the deep-linked one, so switching the
  // dropdown swaps the suggestions too.
  const selectedAgent = agents.find((a) => a.id === agentId);
  const starters = startersFor(selectedAgent?.name);

  async function ensureConversation(): Promise<number> {
    if (conversationId != null) return conversationId;
    if (agentId == null) throw new Error("no agent selected");
    const client = browserFleetClient(session?.accessToken);
    const { data, error } = await client.POST("/v1/conversations", {
      body: { agent_id: agentId },
    });
    if (error || !data) throw new Error("failed to create conversation");
    setConversationId(data.id);
    return data.id;
  }

  async function handleSend() {
    const content = input.trim();
    if (!content || busy) return;
    setBusy(true);
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content }]);
    setMessages((prev) => [...prev, { role: "assistant", content: "", streaming: true }]);

    try {
      const convId = await ensureConversation();
      for await (const event of streamChatMessage(
        API_BASE_URL,
        convId,
        content,
        session?.accessToken,
      )) {
        if (event.type === "token") {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            next[next.length - 1] = { ...last, content: last.content + event.delta };
            return next;
          });
        } else if (event.type === "citations") {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            next[next.length - 1] = { ...last, citations: event.citations };
            return next;
          });
        } else if (event.type === "done") {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            next[next.length - 1] = {
              ...last,
              messageId: event.message_id,
              streaming: false,
            };
            return next;
          });
        } else if (event.type === "error") {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            next[next.length - 1] = {
              ...last,
              content: last.content || `⚠ ${event.detail}`,
              streaming: false,
            };
            return next;
          });
        }
      }
    } finally {
      setBusy(false);
    }
  }

  if (agents.length === 0) {
    return <EmptyState icon={Bot} title={t("emptyTitle")} description={t("emptyDesc")} />;
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <label htmlFor="chat-agent" className="text-sm text-[var(--muted-foreground)]">
          {t("agent")}
        </label>
        <select
          id="chat-agent"
          className="h-9 rounded-[var(--radius-md)] border border-[var(--border-strong)] bg-[var(--surface)] px-2 text-sm"
          value={agentId ?? ""}
          disabled={conversationId != null}
          onChange={(e) => setAgentId(Number(e.target.value))}
        >
          {agents.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
            </option>
          ))}
        </select>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("title")}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {/* Starters replace the blank thread, not the composer: they are
              suggestions for the *first* message only, and disappear once the
              conversation has one, so they never compete with what was said. */}
          {messages.length === 0 && starters && (
            <div className="flex flex-col gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--section-bg)] p-3">
              <p className="flex items-center gap-1.5 text-xs font-medium text-[var(--section-fg)]">
                <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
                {t("startersHeading")}
              </p>
              <div className="flex flex-wrap gap-2">
                {Array.from({ length: starters.count }, (_, i) => {
                  const question = t(`starters.${starters.agent}.q${i + 1}`);
                  return (
                    <button
                      key={i}
                      type="button"
                      disabled={busy}
                      onClick={() => setInput(question)}
                      className="rounded-full border border-[var(--border-strong)] bg-[var(--surface)] px-3 py-1.5 text-left text-xs transition-colors hover:border-[var(--section)] hover:text-[var(--section-fg)] disabled:opacity-50"
                    >
                      {question}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          <div className="flex flex-col gap-3">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`rounded-md px-3 py-2 text-sm ${
                  m.role === "user"
                    ? "self-end bg-[var(--muted)]"
                    : "self-start border border-[var(--border)]"
                }`}
              >
                <p className="whitespace-pre-wrap">
                  {m.content}
                  {m.streaming && <span className="animate-pulse">▍</span>}
                </p>
                {m.role === "assistant" && m.citations && m.citations.length > 0 && (
                  <p className="mt-1 text-xs text-[var(--muted-foreground)]">
                    {t("citationsCount", { count: m.citations.length })}
                  </p>
                )}
                {m.role === "assistant" && m.messageId != null && (
                  <FeedbackButtons messageId={m.messageId} />
                )}
              </div>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <input
              className="flex-1 rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
              placeholder={t("placeholder")}
              value={input}
              disabled={busy}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
            />
            <Button size="sm" onClick={handleSend} disabled={busy || !input.trim()}>
              {t("send")}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
