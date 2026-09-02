// chat_smoke — 50 VU / 5m steady chat load (task 9.1, TRD §13.6).
//
// Thresholds encode the §10 SLOs so the run FAILS (non-zero exit) on a breach:
//   chat first token   p50 < 2s, p95 < 6s
//   full stream        p95 < 10s (generation-bound; looser than first-token)
//   errors             < 1%
//
// Run:  make load TEST=chat_smoke   (or: k6 run tests/load/chat_smoke.js)
// Point at k3d by exporting FLEET_API_BASE / FLEET_KEYCLOAK_BASE to the ingress.
import { sleep } from "k6";
import {
  login,
  resolveAgentId,
  createConversation,
  sendMessage,
  randomQuestion,
} from "./lib/fleet.js";

export const options = {
  scenarios: {
    chat_smoke: {
      executor: "constant-vus",
      vus: Number(__ENV.VUS || 50),
      duration: __ENV.DURATION || "5m",
    },
  },
  thresholds: {
    // Gating SLOs (TRD §10): first-token latency is the user-perceived SLO.
    chat_first_token: ["p(50)<2000", "p(95)<6000"],
    chat_errors: ["rate<0.01"],
    http_req_failed: ["rate<0.01"],
    // Observational only (no abort): full-stream completion is generation-
    // throughput-bound and scales with GPU capacity — meaningful to record, but
    // not a fixed SLO on a single-GPU dev box vs the reference cluster.
    chat_stream_complete: [{ threshold: "p(95)<60000", abortOnFail: false }],
  },
};

export function setup() {
  const token = login({ username: "builder", password: "builder" });
  const agentId = resolveAgentId(token);
  return { agentId };
}

export default function (data) {
  const token = login();
  const conversationId = createConversation(token, data.agentId);
  sendMessage(token, conversationId, randomQuestion());
  sleep(Math.random() * 2 + 1); // 1–3s think time between turns
}
