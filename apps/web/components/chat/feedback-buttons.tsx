"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { browserFleetClient } from "@/lib/fleet-client-browser";

type FeedbackState = "idle" | "sent";

export function FeedbackButtons({ messageId }: { messageId: number }) {
  const { data: session } = useSession();
  const [state, setState] = useState<FeedbackState>("idle");
  const [picked, setPicked] = useState<1 | -1 | null>(null);

  async function send(score: 1 | -1) {
    if (state === "sent") return;
    setPicked(score);
    const client = browserFleetClient(session?.accessToken);
    await client.POST("/v1/messages/{message_id}/feedback", {
      params: { path: { message_id: messageId } },
      body: { score },
    });
    setState("sent");
  }

  return (
    <div className="mt-1 flex items-center gap-2">
      <button
        aria-label="thumbs up"
        onClick={() => send(1)}
        disabled={state === "sent"}
        className={`text-sm ${picked === 1 ? "opacity-100" : "opacity-50"} hover:opacity-100 disabled:cursor-default`}
      >
        👍
      </button>
      <button
        aria-label="thumbs down"
        onClick={() => send(-1)}
        disabled={state === "sent"}
        className={`text-sm ${picked === -1 ? "opacity-100" : "opacity-50"} hover:opacity-100 disabled:cursor-default`}
      >
        👎
      </button>
    </div>
  );
}
