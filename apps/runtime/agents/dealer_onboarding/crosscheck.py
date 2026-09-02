"""Deterministic dossier cross-check (task 12.1, dept scenario 09).

Two checks, both pure functions with no model in the loop — the department
scenario's "validate fields, cross-check application" step decides whether a
dealer gets an email, a manual review, or a hand-off to a sales rep, and that
decision must be reproducible and auditable, not a model judgement.

1. **Missing documents.** Which of the required document kinds the applicant did
   not supply, plus any required identity field the supplied documents did not
   yield. This drives the missing-document email.
2. **Name mismatch.** The company name on the authorization certificate vs the
   one on the CRM application. Comparison is on a folded form (case, Turkish
   diacritics, punctuation and the legal-form suffixes A.Ş./LTD.ŞTİ. etc. are
   normalized away) so "Anadolu Otomotiv Ticaret A.Ş." and "ANADOLU OTOMOTIV
   TICARET AS" are the same company, while a genuinely different trade name is
   flagged. A mismatch is a fraud/typo signal: it goes to a human, and the agent
   sends the applicant nothing.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# The dossier a dealer application must contain before it can reach a sales rep.
REQUIRED_DOCUMENTS = ("authorization_certificate", "tax_registration")

# Human-facing TR labels for the missing-document email (dept scenario 09's
# "right missing items listed").
DOCUMENT_LABELS_TR = {
    "authorization_certificate": "Yetki Belgesi",
    "tax_registration": "Vergi Levhası",
}
FIELD_LABELS_TR = {
    "company_name": "Belge üzerindeki ticari unvan",
    "tax_no": "Vergi Kimlik Numarası",
}

_LEGAL_FORM_TOKENS = {
    "as", "a s", "anonim", "sirketi", "sirket", "ltd", "limited", "sti",
    "ticaret", "tic", "sanayi", "san", "ve", "co", "inc",
}

_TR_FOLD = str.maketrans({"ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
                          "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c"})


def normalize_company_name(name: str) -> str:
    """Fold a Turkish trade name to a comparable core (legal form removed).

    Abbreviation dots are deleted rather than turned into separators, so
    "A.Ş." folds to the single token "as" (a known legal form) instead of the
    two stray letters "a" and "s". Remaining single-character tokens are
    dropped as OCR debris — a trade name is never distinguished by one letter,
    and letting one through would flag an otherwise-matching dossier for fraud
    review.
    """
    folded = name.translate(_TR_FOLD).lower()
    folded = unicodedata.normalize("NFKD", folded)
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    folded = folded.replace(".", "")
    folded = re.sub(r"[^a-z0-9\s]", " ", folded)
    tokens = [
        t for t in folded.split() if len(t) > 1 and t not in _LEGAL_FORM_TOKENS
    ]
    return " ".join(tokens)


@dataclass(frozen=True)
class CrossCheck:
    missing_documents: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    name_mismatch: bool = False
    certificate_name: str | None = None
    application_name: str | None = None

    @property
    def complete(self) -> bool:
        return not self.missing_documents and not self.missing_fields

    @property
    def clean(self) -> bool:
        """A dossier that can be handed to a sales rep untouched."""
        return self.complete and not self.name_mismatch


def cross_check(
    *,
    application: dict[str, object],
    provided_documents: list[str],
    certificate_name: str | None,
    missing_fields: list[str],
) -> CrossCheck:
    """Compare the extracted dossier against the CRM application.

    `missing_fields` comes from the extractor (fields the documents did not
    yield); it is folded into the same result so the email lists documents and
    unreadable fields together — the applicant has to act on both the same way.
    """
    provided = set(provided_documents)
    missing_documents = [d for d in REQUIRED_DOCUMENTS if d not in provided]

    application_name = application.get("company_name")
    application_name = str(application_name) if application_name is not None else None

    # A mismatch is only meaningful when both names are actually known — a
    # missing certificate name is a *missing field*, not a mismatch, and must
    # not be reported as one (it would send a clean applicant to fraud review).
    name_mismatch = False
    if certificate_name and application_name:
        name_mismatch = normalize_company_name(certificate_name) != normalize_company_name(
            application_name
        )

    return CrossCheck(
        missing_documents=missing_documents,
        missing_fields=list(missing_fields),
        name_mismatch=name_mismatch,
        certificate_name=certificate_name,
        application_name=application_name,
    )


def missing_item_labels(check: CrossCheck) -> list[str]:
    """TR labels for everything the applicant still has to send."""
    labels = [DOCUMENT_LABELS_TR[d] for d in check.missing_documents]
    labels += [
        FIELD_LABELS_TR[f] for f in check.missing_fields if f in FIELD_LABELS_TR
    ]
    return labels
