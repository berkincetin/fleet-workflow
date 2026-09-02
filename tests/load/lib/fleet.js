// Shared k6 helpers for Fleet load scenarios (task 9.1).
//
// Auth: Keycloak `fleet-api` client, password grant (synthetic seed users).
// Chat flow: create a conversation, then POST a message and read the SSE
// stream, timing the FIRST `token` event as the "first token" SLO signal
// (TRD §10: chat first token p50 <2s / p95 <6s).
import http from "k6/http";
import { check } from "k6";
import { Trend, Rate } from "k6/metrics";

// Endpoints are overridable via env so the same script runs against compose
// (localhost) or the k3d ingress. Defaults match `make dev`.
export const API_BASE = __ENV.FLEET_API_BASE || "http://localhost:8000";
export const KEYCLOAK_BASE = __ENV.FLEET_KEYCLOAK_BASE || "http://localhost:8080";
export const AGENT_SLUG = __ENV.FLEET_AGENT_SLUG || "support_copilot";

// Custom SLO metrics (thresholds are declared per-scenario in the options).
export const firstToken = new Trend("chat_first_token", true);
export const streamComplete = new Trend("chat_stream_complete", true);
export const chatErrors = new Rate("chat_errors");

const USERS = [
  { username: "user1", password: "user1" },
  { username: "user2", password: "user2" },
  { username: "builder", password: "builder" },
];

export function login(user) {
  const u = user || USERS[(__VU - 1) % USERS.length];
  const res = http.post(
    `${KEYCLOAK_BASE}/realms/fleet/protocol/openid-connect/token`,
    {
      client_id: "fleet-api",
      client_secret: "fleet-api-dev-secret",
      grant_type: "password",
      username: u.username,
      password: u.password,
    },
    { tags: { name: "keycloak_token" } },
  );
  check(res, { "login 200": (r) => r.status === 200 });
  return res.json("access_token");
}

function authHeaders(token) {
  return { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
}

// Resolve the numeric agent id for the configured slug (chat endpoints take ids).
export function resolveAgentId(token) {
  const res = http.get(`${API_BASE}/v1/agents`, {
    headers: authHeaders(token),
    tags: { name: "list_agents" },
  });
  check(res, { "agents 200": (r) => r.status === 200 });
  const agents = res.json();
  const match = Array.isArray(agents)
    ? agents.find((a) => a.name === AGENT_SLUG)
    : null;
  return match ? match.id : (Array.isArray(agents) && agents[0] ? agents[0].id : null);
}

export function createConversation(token, agentId) {
  const res = http.post(
    `${API_BASE}/v1/conversations`,
    JSON.stringify({ agent_id: agentId }),
    { headers: authHeaders(token), tags: { name: "create_conversation" } },
  );
  check(res, { "conversation 201": (r) => r.status === 201 });
  return res.json("id");
}

// Send one chat message and consume the SSE stream. k6's http client buffers
// the full response, so we approximate first-token latency by locating the
// first `event: token` frame in the body and attributing the round-trip to it;
// stream-complete is the full request duration. Good enough to catch SLO
// regressions (the absolute first-token number is slightly pessimistic).
export function sendMessage(token, conversationId, content) {
  const res = http.post(
    `${API_BASE}/v1/conversations/${conversationId}/messages`,
    JSON.stringify({ content }),
    {
      headers: authHeaders(token),
      tags: { name: "chat_message" },
      timeout: "60s",
    },
  );

  const ok = check(res, {
    "message 200": (r) => r.status === 200,
    "got a token event": (r) => r.body && r.body.indexOf("event: token") !== -1,
    "got done event": (r) => r.body && r.body.indexOf("event: done") !== -1,
  });

  chatErrors.add(!ok);
  if (res.status === 200 && res.body.indexOf("event: token") !== -1) {
    firstToken.add(res.timings.waiting); // time to first byte ~= time to first token
    streamComplete.add(res.timings.duration);
  }
  return res;
}

export const QUESTIONS = [
  "What is the refund policy?",
  "How do I reset my password?",
  "What are your support hours?",
  "How can I track my order?",
  "Where can I find the onboarding checklist?",
];

export function randomQuestion() {
  return QUESTIONS[Math.floor(Math.random() * QUESTIONS.length)];
}
