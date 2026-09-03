/**
 * Suggested opening questions per agent (task 13.7).
 *
 * An empty chat with a free-text box is the least helpful screen in the app:
 * the reader has to guess both what this particular agent knows and how to
 * phrase it. These are the questions each agent can actually answer from what
 * `make seed` loads — support_copilot over the seeded help-centre collections,
 * analytics over the `fixture_sales`/`fixture_orders` views — so clicking one
 * produces a real, cited answer rather than a shrug.
 *
 * Keyed by agent *name*, matching `agents.name`. An agent with no entry simply
 * shows no starters, so adding an agent never breaks this screen; the generic
 * fallback is deliberately not used, since a wrong suggestion is worse than
 * none.
 *
 * The strings themselves live in i18n under `chat.starters.<agent>.<n>` — the
 * questions are user-facing copy and are translated; only the keys are here.
 */

export interface AgentStarters {
  agent: string;
  /** Number of `chat.starters.<agent>.q<n>` keys defined for this agent. */
  count: number;
}

export const CHAT_STARTERS: AgentStarters[] = [
  { agent: "support_copilot", count: 3 },
  { agent: "analytics", count: 3 },
];

export function startersFor(agentName: string | undefined): AgentStarters | undefined {
  return agentName ? CHAT_STARTERS.find((s) => s.agent === agentName) : undefined;
}
