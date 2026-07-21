// SSE consumption for the chat message endpoint. openapi-fetch (the typed
// client used elsewhere per CLAUDE.md's "API access only through
// packages/shared client") parses JSON responses and isn't built for reading
// a streaming body, so this one call site uses the platform fetch API
// directly against the same typed route contract instead.

export type ChatStreamEvent =
  | { type: "token"; delta: string }
  | { type: "citations"; citations: unknown[] }
  | { type: "done"; message_id: number; trace_id: string }
  | { type: "error"; detail: string };

function parseSseBlock(block: string): ChatStreamEvent | null {
  let eventName: string | null = null;
  let dataLine: string | null = null;
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) eventName = line.slice("event:".length).trim();
    else if (line.startsWith("data:")) dataLine = line.slice("data:".length).trim();
  }
  if (!eventName || dataLine == null) return null;
  const data = JSON.parse(dataLine);
  return { type: eventName, ...data } as ChatStreamEvent;
}

export async function* streamChatMessage(
  apiBaseUrl: string,
  conversationId: number,
  content: string,
  accessToken?: string,
): AsyncGenerator<ChatStreamEvent> {
  const resp = await fetch(`${apiBaseUrl}/v1/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    },
    body: JSON.stringify({ content }),
  });
  if (!resp.ok || !resp.body) {
    throw new Error(`chat stream failed: ${resp.status}`);
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let sepIndex: number;
    while ((sepIndex = buffer.indexOf("\n\n")) !== -1) {
      const block = buffer.slice(0, sepIndex);
      buffer = buffer.slice(sepIndex + 2);
      const event = parseSseBlock(block);
      if (event) yield event;
    }
  }
}
