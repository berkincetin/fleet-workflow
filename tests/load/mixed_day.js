// mixed_day — a representative production day: interactive chat + background
// automation runs, together (task 9.1, TRD §13.6 "chat+automations").
//
// Two concurrent scenarios share the cluster so we measure chat SLOs *under*
// automation contention, not in isolation:
//   - chat:        ramp 0→80 VU interactive users (think-time between turns)
//   - automations: a steady arrival of "automation" chat runs (no think time,
//                   back-to-back) standing in for n8n-triggered agent calls,
//                   sized toward the §10 target of ~200 automation runs/hour.
//
// SLO thresholds (must hold under the mixed load):
//   chat first token p50 < 2s / p95 < 6s ; errors < 2% (looser than smoke:
//   this scenario deliberately pushes contention).
//
// Run:  make load TEST=mixed_day
import { sleep } from "k6";
import {
  login,
  resolveAgentId,
  createConversation,
  sendMessage,
  randomQuestion,
} from "./lib/fleet.js";

const CHAT_PEAK = Number(__ENV.CHAT_PEAK || 80);

export const options = {
  scenarios: {
    chat: {
      executor: "ramping-vus",
      exec: "chat",
      startVUs: 0,
      // Peak chat concurrency is env-tunable: default 80 targets the §10
      // reference cluster; scale down (CHAT_PEAK) for a single-GPU dev box.
      stages: [
        { duration: "1m", target: Math.ceil(CHAT_PEAK / 2) },
        { duration: "3m", target: CHAT_PEAK },
        { duration: "1m", target: 0 },
      ],
    },
    automations: {
      executor: "constant-arrival-rate",
      exec: "automation",
      // ~4 runs/sec ≈ well above 200/hour, to prove headroom under §10 sizing.
      // rate must be an integer; slow it on a dev box via AUTOMATION_PER (the
      // time unit), e.g. AUTOMATION_RATE=1 AUTOMATION_PER=3s → 1 run / 3s.
      rate: Number(__ENV.AUTOMATION_RATE || 4),
      timeUnit: __ENV.AUTOMATION_PER || "1s",
      duration: "5m",
      preAllocatedVUs: 20,
      maxVUs: 50,
    },
  },
  thresholds: {
    chat_first_token: ["p(50)<2000", "p(95)<6000"],
    chat_errors: ["rate<0.02"],
    http_req_failed: ["rate<0.02"],
  },
};

export function setup() {
  const token = login({ username: "builder", password: "builder" });
  return { agentId: resolveAgentId(token) };
}

// Interactive user: create a conversation, ask, think, repeat.
export function chat(data) {
  const token = login();
  const conversationId = createConversation(token, data.agentId);
  sendMessage(token, conversationId, randomQuestion());
  sleep(Math.random() * 3 + 2); // 2–5s think time
}

// Automation run: back-to-back, no think time — simulates an n8n workflow
// firing an agent call on a schedule/webhook.
export function automation(data) {
  const token = login({ username: "user1", password: "user1" });
  const conversationId = createConversation(token, data.agentId);
  sendMessage(token, conversationId, "Summarize this week's support tickets.");
}
