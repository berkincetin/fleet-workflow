"""Static slug -> n8n workflow metadata map (task 6.5.3).

Friendly TR/EN titles/descriptions live in the web app's i18n messages, not
here — this module only carries what the Fleet API needs to find and drive
each workflow in n8n: its n8n workflow name (for matching the /api/v1/workflows
list response, which is keyed by n8n's internal id, not a stable slug) and its
trigger webhook path(s).

`n8n_name` must equal the `name` field of the matching export in `workflows/`
verbatim — the lookup is an exact string compare, so a mismatch makes the
workflow invisible to the catalog (reported as `active: null`) even while it is
imported and active in n8n.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowMeta:
    slug: str
    n8n_name: str
    kind: str  # "webhook" | "cron+manual"
    run_webhook_path: str


CATALOG: dict[str, WorkflowMeta] = {
    "invoice-intake": WorkflowMeta(
        slug="invoice-intake",
        n8n_name="invoice-intake",
        kind="webhook",
        run_webhook_path="invoice-intake",
    ),
    "weekly-summary": WorkflowMeta(
        slug="weekly-summary",
        n8n_name="weekly-summary",
        kind="cron+manual",
        run_webhook_path="weekly-summary-run",
    ),
}
