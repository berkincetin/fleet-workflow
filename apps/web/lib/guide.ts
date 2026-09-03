/**
 * The in-app guide's walkthroughs (task 13.7).
 *
 * Fleet's screens each explain themselves — `PageHeader` says what a screen is
 * for, `EmptyState` says what to do first — but nothing explained how the
 * screens fit *together*: that a question in Chat, a document in Knowledge, an
 * automation in the builder and an entry in Approvals are four points on one
 * path. That is what this page is for, and why it is a guide rather than more
 * per-screen help text.
 *
 * Each walkthrough is a short numbered path with a link into the screen it
 * starts at, so reading it and doing it are the same click. Copy lives in i18n
 * under `guide.walkthroughs.<id>`; `steps` is the number of `s<n>` keys.
 */

import type { Section } from "@/lib/nav";

export interface Walkthrough {
  /** Key under `guide.walkthroughs`. */
  id: string;
  /** Where the walkthrough starts — the button links here. */
  href: string;
  /** Colour family, matching the section the walkthrough lives in. */
  section: Section;
  /** Number of `guide.walkthroughs.<id>.s<n>` step keys. */
  steps: number;
  /** Roughly how long it takes, in minutes — sets expectations before starting. */
  minutes: number;
}

export const WALKTHROUGHS: Walkthrough[] = [
  {
    // First on purpose: it is the only one that needs nothing set up and no
    // elevated role, and it ends with a cited answer — the clearest single
    // demonstration that the platform is wired end to end.
    id: "askAgent",
    href: "/chat?agent=support_copilot",
    section: "work",
    steps: 4,
    minutes: 2,
  },
  {
    id: "addKnowledge",
    href: "/knowledge",
    section: "knowledge",
    steps: 4,
    minutes: 5,
  },
  {
    id: "buildAutomation",
    href: "/automations/new?template=weeklySalesDigest",
    section: "automation",
    steps: 5,
    minutes: 5,
  },
  {
    // The one that teaches the governance model rather than a feature: the
    // reader watches a write be *refused* and queued, which is the behaviour
    // most likely to look like a bug if met without warning.
    id: "approvalFlow",
    href: "/automations/new?template=monthlyReport",
    section: "automation",
    steps: 5,
    minutes: 5,
  },
];
