"""Missing-document email, rendered from a fixed TR formal template (task 12.1,
dept scenario 09).

**Deliberately not model-generated.** The department scenario allows the cloud
utility lane for "non-PII orchestration text", but this particular text is an
approval-gated *external* email to a business applicant: it names the company,
the application id and the exact documents we are asking for. Generating it
would put drift between what the approver reads in the queue and what a rerun
would send, and would open the door to an invented document requirement. The
template makes the two identical by construction, so the approval item is a
faithful preview of the outbound message.

Tone is the scenario's own bar — "TR formal-tone email template correctness":
"Sayın" salutation, the plural/formal register throughout ("rica ederiz",
"iletebilirsiniz"), a "Saygılarımızla" close, and no informal second-person
forms anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass

from agents.dealer_onboarding.crosscheck import CrossCheck, missing_item_labels

SUBJECT_TEMPLATE = "Bayi Başvurunuz ({application_id}) — Eksik Belge Bildirimi"


@dataclass(frozen=True)
class MissingDocsEmail:
    to: str
    subject: str
    body: str
    missing_items: list[str]


def render_missing_docs_email(
    *, application: dict[str, object], check: CrossCheck
) -> MissingDocsEmail:
    """Render the formal TR missing-document request for this application."""
    items = missing_item_labels(check)
    if not items:
        raise ValueError("render_missing_docs_email called with nothing missing")

    application_id = str(application.get("application_id", ""))
    contact_name = str(application.get("contact_name", "") or "Yetkili")
    company_name = str(application.get("company_name", "") or "")
    to = str(application.get("contact_email", ""))

    bullet_list = "\n".join(f"- {item}" for item in items)
    body = (
        f"Sayın {contact_name},\n\n"
        f"{company_name} unvanlı firmanız adına yaptığınız bayi başvurusu "
        f"({application_id}) tarafımıza ulaşmıştır. Başvuru dosyanızın "
        f"değerlendirmeye alınabilmesi için aşağıdaki belgelere ihtiyaç "
        f"duyulmaktadır:\n\n"
        f"{bullet_list}\n\n"
        f"İlgili belgeleri bu e-postayı yanıtlayarak tarafımıza iletmenizi rica "
        f"ederiz. Belgeler tamamlandığında başvurunuz kurumsal satış ekibimizce "
        f"değerlendirilecektir.\n\n"
        f"Sorularınız için bu adres üzerinden bize ulaşabilirsiniz.\n\n"
        f"Saygılarımızla,\n"
        f"Kurumsal Satış Ekibi"
    )
    return MissingDocsEmail(
        to=to,
        subject=SUBJECT_TEMPLATE.format(application_id=application_id),
        body=body,
        missing_items=items,
    )
