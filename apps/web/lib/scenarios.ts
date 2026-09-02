/**
 * Department scenario hub config (task 6.5.6), mirroring the wave-plan table
 * in docs/split/department-scenarios/00-wave-plan.md. Live scenarios deep-
 * link into a working surface; "coming soon" scenarios show their target
 * IMPLEMENTATION_PLAN.md task as a badge and are not clickable. Keep this in
 * sync with the wave-plan table by hand if a scenario's status changes.
 */

export type ScenarioStatus = "live" | "partial" | "coming_soon";

export type Scenario = {
  slug: string;
  department: string;
  status: ScenarioStatus;
  /** Only present for "coming_soon"/"partial" — the task that ships it. */
  targetTask?: string;
  /** Only present for "live"/"partial" — where to send the user. */
  href?: string;
};

export const SCENARIOS: Scenario[] = [
  { slug: "support_copilot", department: "Customer Service", status: "live", href: "/chat?agent=support_copilot" },
  { slug: "analytics", department: "Data", status: "live", href: "/chat?agent=analytics" },
  { slug: "dev_agent", department: "IT / Engineering", status: "live", href: "/examples?agent=dev_agent" },
  { slug: "invoice_agent", department: "Finance", status: "live", href: "/automations" },
  { slug: "hr_talent", department: "HR", status: "live", href: "/examples?agent=hr_agent" },
  { slug: "listing_quality", department: "Listings Ops", status: "live", href: "/examples?agent=listing_quality" },
  { slug: "vehicle_intake", department: "Trink sat!", status: "live", href: "/examples?agent=vehicle_intake" },
  { slug: "insights_publisher", department: "Marketing", status: "live", href: "/examples?agent=insights_publisher" },
  { slug: "dealer_onboarding", department: "Corporate Sales", status: "live", href: "/examples?agent=dealer_onboarding" },
  { slug: "legal_review", department: "Legal", status: "live", href: "/examples?agent=legal_review" },
];
