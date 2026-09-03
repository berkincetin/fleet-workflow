/**
 * Ready-made automation recipes the builder can be seeded from (task 13.7).
 *
 * A blank builder is the wrong first experience: the reader has to invent a
 * cron expression, guess which tables `pg.query` may read and which channels
 * `slack.post` may reach, all before seeing anything work. A template arrives
 * pre-filled with values that are *actually accepted* by the API, so the first
 * run succeeds and the form becomes an example to edit rather than a blank to
 * fill.
 *
 * Every template below is therefore constrained by the real server-side
 * allowlists, not by what reads nicely:
 *   - `pg.query` may only touch `fixture_sales` / `fixture_orders`
 *     (`_ALLOWLISTED_TABLES` in routers/service.py).
 *   - `slack.post` may only reach `#dev-agent` / `#weekly-summary`
 *     (`_ALLOWLISTED_CHANNELS`, same module).
 *   - `email.send` may only address `fleet.local` / `example.com`
 *     (`_ALLOWED_EMAIL_DOMAINS`) — and always queues an approval rather than
 *     sending, which is the point of the template that uses it.
 * If any of those allowlists change, these templates must change with them;
 * `tests/unit/test_recipe_templates.py` asserts they stay inside the lists.
 *
 * `name` is a slug the API validates against `_RECIPE_NAME_RE`; the reader is
 * free to rename before saving. Titles and descriptions are i18n keys under
 * `builder.templates.<id>`, not literals — the copy is translated, the recipe
 * body is not.
 */

import type { ActionName, Operator } from "@/lib/recipe-actions";

export interface TemplateAction {
  type: "action";
  id: string;
  action: ActionName;
  params: Record<string, string>;
}

export interface TemplateCondition {
  type: "condition";
  id: string;
  left: string;
  operator: Operator;
  right: string;
  then_steps: TemplateAction[];
  else_steps: TemplateAction[];
}

export type TemplateStep = TemplateAction | TemplateCondition;

export interface RecipeTemplate {
  /** Key under the `builder.templates` i18n namespace, and the URL's ?template=. */
  id: string;
  /** Suggested recipe slug — pre-filled, editable before save. */
  name: string;
  trigger: { type: "manual" } | { type: "schedule"; cron: string };
  steps: TemplateStep[];
  /** Drives the "needs approval" note on the template card. */
  needsApproval: boolean;
}

export const RECIPE_TEMPLATES: RecipeTemplate[] = [
  {
    // The simplest useful thing: one read, one message, on a cron. Deliberately
    // first — it is the shortest path from "I clicked a template" to "n8n ran
    // something and I can see it".
    id: "weeklySalesDigest",
    name: "haftalik-satis-ozeti",
    trigger: { type: "schedule", cron: "0 9 * * 1" },
    steps: [
      {
        type: "action",
        id: "sales",
        action: "pg.query",
        params: {
          sql:
            "SELECT region, COUNT(*) AS orders, ROUND(SUM(amount_usd)) AS total_usd " +
            "FROM fixture_sales WHERE sold_on >= CURRENT_DATE - 7 " +
            "GROUP BY region ORDER BY total_usd DESC",
        },
      },
      {
        type: "action",
        id: "post",
        action: "slack.post",
        params: {
          channel: "#weekly-summary",
          text: "Haftalık satış özeti: {{steps.sales.row_count}} bölge raporlandı.",
        },
      },
    ],
    needsApproval: false,
  },
  {
    // Shows the one thing the builder can express beyond a straight line: a
    // condition. Also the template that teaches "nothing is posted when there
    // is nothing to say", which is the habit that keeps automations tolerable.
    id: "refundWatch",
    name: "iade-takibi",
    trigger: { type: "schedule", cron: "0 9 * * *" },
    steps: [
      {
        type: "action",
        id: "refunds",
        action: "pg.query",
        params: {
          sql: "SELECT id, sale_id, quantity FROM fixture_orders WHERE refunded = true LIMIT 50",
        },
      },
      {
        type: "condition",
        id: "any_refunds",
        left: "{{steps.refunds.row_count}}",
        operator: "gt",
        right: "0",
        then_steps: [
          {
            type: "action",
            id: "alert",
            action: "slack.post",
            params: {
              channel: "#dev-agent",
              text: "Bugün {{steps.refunds.row_count}} iade kaydı var, kontrol edilmeli.",
            },
          },
        ],
        else_steps: [],
      },
    ],
    needsApproval: false,
  },
  {
    // The agent-in-an-automation shape: a scheduled question put to a real
    // agent, its answer left as an audit trail rather than messaged out.
    // `http.notify` is the deliberately outward-effect-free action.
    id: "agentBriefing",
    name: "gunluk-analiz-brifingi",
    trigger: { type: "schedule", cron: "0 9 * * *" },
    steps: [
      {
        type: "action",
        id: "ask",
        action: "agent.run",
        params: {
          agent: "analytics",
          question: "Son 7 günde hangi bölgede satış düştü? Tek paragrafta özetle.",
        },
      },
      {
        type: "action",
        id: "record",
        action: "http.notify",
        params: {
          title: "Günlük analiz brifingi",
          message: "{{steps.ask.text}}",
        },
      },
    ],
    needsApproval: false,
  },
  {
    // Exists to make the approval gate visible. Running it produces an
    // approval-queue entry and *no* email — which is the lesson, so the
    // template card says so before the reader clicks.
    id: "monthlyReport",
    name: "aylik-rapor-maili",
    trigger: { type: "schedule", cron: "0 9 1 * *" },
    steps: [
      {
        type: "action",
        id: "totals",
        action: "pg.query",
        params: {
          sql:
            "SELECT region, ROUND(SUM(amount_usd)) AS total_usd FROM fixture_sales " +
            "GROUP BY region ORDER BY total_usd DESC",
        },
      },
      {
        type: "action",
        id: "mail",
        action: "email.send",
        params: {
          to: "yonetim@example.com",
          subject: "Aylık satış raporu",
          body: "Aylık satış özeti hazır. {{steps.totals.row_count}} bölge raporlandı.",
        },
      },
    ],
    needsApproval: true,
  },
];

export function templateById(id: string | undefined): RecipeTemplate | undefined {
  return id ? RECIPE_TEMPLATES.find((t) => t.id === id) : undefined;
}
