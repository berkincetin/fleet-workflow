"""Task 8.1: local-lane quality rehearsal.

Renders synthetic TR CV "scans" (never real CVs — KVKK/CLAUDE.md), runs them
through the real local-only pipeline (tesseract tur+eng OCR -> local Qwen
structured extraction, both forced local by `sensitivity="pii"` the same way
production's hr-cvs collection will be, task 8.2), and reports two numbers per
fixture: OCR word-accuracy (tesseract text vs. the ground-truth line, tolerant
of realistic OCR noise the same way `evals/runner.py`'s `_vendor_reasonably_matches`
is) and field-extraction accuracy (does `extract_cv_profile` recover each
ground-truth field correctly from the OCR'd, possibly-noisy text).

Invoice OCR/extraction accuracy is not duplicated here — `make eval
AGENT=invoice_agent` already measures the identical local-only pipeline
end-to-end (12 synthetic invoice cases, task 6.3) now that task 8.2's OCR fix
makes it genuinely local; this script's findings report cites that run's pass
rate as the invoice-document-type number.

Usage: `uv run python evals/local_lane_rehearsal.py` (needs the real gateway
client -> local Qwen via the compose stack + Ollama; local Tesseract on PATH).
Writes docs/reports/sprint-8-local-lane-rehearsal.md.
"""

from __future__ import annotations

import asyncio
import difflib
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from synthetic_images import render_document_image_base64

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class CvFixture:
    id: str
    lines: list[str]
    expect_full_name: str
    expect_email: str
    expect_phone: str
    expect_education_contains: str
    expect_experience_contains: str
    expect_skill: str


_FIXTURES: list[CvFixture] = [
    CvFixture(
        id="cv-01",
        lines=[
            "Ayse Yilmaz",
            "E-posta: ayse.yilmaz@example.com",
            "Telefon: +90 555 111 2233",
            "Egitim: BSc Bilgisayar Muhendisligi, ODTU, 2019",
            "Deneyim: Yazilim Muhendisi, Acme A.S., 2019-2022",
            "Yetenekler: Python, SQL, Docker",
        ],
        expect_full_name="Ayse Yilmaz",
        expect_email="ayse.yilmaz@example.com",
        expect_phone="+90 555 111 2233",
        expect_education_contains="ODTU",
        expect_experience_contains="Acme",
        expect_skill="Python",
    ),
    CvFixture(
        id="cv-02",
        lines=[
            "Mehmet Demir",
            "E-posta: mehmet.demir@example.com",
            "Telefon: +90 532 444 5566",
            "Egitim: MSc Elektrik Muhendisligi, Bogazici Universitesi, 2017",
            "Deneyim: Kidemli Muhendis, Trink Otomotiv, 2018-2023",
            "Yetenekler: Java, Kubernetes, CI/CD",
        ],
        expect_full_name="Mehmet Demir",
        expect_email="mehmet.demir@example.com",
        expect_phone="+90 532 444 5566",
        expect_education_contains="Bogazici",
        expect_experience_contains="Trink",
        expect_skill="Java",
    ),
    CvFixture(
        id="cv-03",
        lines=[
            "Zeynep Kaya",
            "E-posta: zeynep.kaya@example.com",
            "Telefon: +90 505 777 8899",
            "Egitim: BSc Endustri Muhendisligi, ITU, 2020",
            "Deneyim: Veri Analisti, Fleet Lojistik, 2020-2024",
            "Yetenekler: SQL, Tableau, Excel",
        ],
        expect_full_name="Zeynep Kaya",
        expect_email="zeynep.kaya@example.com",
        expect_phone="+90 505 777 8899",
        expect_education_contains="ITU",
        expect_experience_contains="Fleet Lojistik",
        expect_skill="Tableau",
    ),
    CvFixture(
        id="cv-04",
        lines=[
            "Can Ozturk",
            "E-posta: can.ozturk@example.com",
            "Telefon: +90 542 222 3344",
            "Egitim: BSc Makine Muhendisligi, Yildiz Teknik Universitesi, 2018",
            "Deneyim: Proje Muhendisi, Anadolu Sanayi, 2019-2023",
            "Yetenekler: SolidWorks, AutoCAD, MS Project",
        ],
        expect_full_name="Can Ozturk",
        expect_email="can.ozturk@example.com",
        expect_phone="+90 542 222 3344",
        expect_education_contains="Yildiz",
        expect_experience_contains="Anadolu",
        expect_skill="AutoCAD",
    ),
    CvFixture(
        id="cv-05",
        lines=[
            "Elif Sahin",
            "E-posta: elif.sahin@example.com",
            "Telefon: +90 555 999 1122",
            "Egitim: BSc Isletme, Marmara Universitesi, 2021",
            "Deneyim: Insan Kaynaklari Uzmani, Fleet Holding, 2021-2024",
            "Yetenekler: Ise Alim, Bordro, SAP",
        ],
        expect_full_name="Elif Sahin",
        expect_email="elif.sahin@example.com",
        expect_phone="+90 555 999 1122",
        expect_education_contains="Marmara",
        expect_experience_contains="Fleet Holding",
        expect_skill="SAP",
    ),
    CvFixture(
        id="cv-06",
        lines=[
            "Burak Aydin",
            "E-posta: burak.aydin@example.com",
            "Telefon: +90 533 666 7788",
            "Egitim: BSc Matematik, Hacettepe Universitesi, 2016",
            "Deneyim: Veri Bilimci, Trink Analitik, 2019-2024",
            "Yetenekler: Python, Makine Ogrenmesi, Pandas",
        ],
        expect_full_name="Burak Aydin",
        expect_email="burak.aydin@example.com",
        expect_phone="+90 533 666 7788",
        expect_education_contains="Hacettepe",
        expect_experience_contains="Trink Analitik",
        expect_skill="Pandas",
    ),
    CvFixture(
        id="cv-07",
        lines=[
            "Selin Arslan",
            "E-posta: selin.arslan@example.com",
            "Telefon: +90 505 333 4455",
            "Egitim: BSc Grafik Tasarim, Marmara Universitesi, 2019",
            "Deneyim: UI/UX Tasarimci, Fleet Dijital, 2020-2024",
            "Yetenekler: Figma, Adobe XD, Sketch",
        ],
        expect_full_name="Selin Arslan",
        expect_email="selin.arslan@example.com",
        expect_phone="+90 505 333 4455",
        expect_education_contains="Marmara",
        expect_experience_contains="Fleet Dijital",
        expect_skill="Figma",
    ),
    CvFixture(
        id="cv-08",
        lines=[
            "Emre Celik",
            "E-posta: emre.celik@example.com",
            "Telefon: +90 542 888 9900",
            "Egitim: BSc Bilgisayar Muhendisligi, Ege Universitesi, 2015",
            "Deneyim: DevOps Muhendisi, Trink Bulut, 2017-2024",
            "Yetenekler: Terraform, AWS, Linux",
        ],
        expect_full_name="Emre Celik",
        expect_email="emre.celik@example.com",
        expect_phone="+90 542 888 9900",
        expect_education_contains="Ege",
        expect_experience_contains="Trink Bulut",
        expect_skill="Terraform",
    ),
]


@dataclass
class CvRehearsalResult:
    id: str
    ocr_source: str
    ocr_word_accuracy: float
    field_hits: int
    field_total: int
    field_reasons: list[str] = field(default_factory=list)


def _fold_ascii(text: str) -> str:
    lowered = text.lower()
    stripped = "".join(
        c for c in unicodedata.normalize("NFD", lowered) if unicodedata.category(c) != "Mn"
    )
    return stripped.translate(str.maketrans("ıİşŞçÇğĞöÖüÜ", "iIsScCgGoOuU"))


def _ocr_word_accuracy(expected_lines: list[str], ocr_text: str) -> float:
    """Word-level accuracy: fraction of ground-truth words found (ASCII-folded,
    tolerant of case/diacritic OCR noise) somewhere in the OCR'd text."""
    expected_words = _fold_ascii(" ".join(expected_lines)).split()
    ocr_words = set(_fold_ascii(ocr_text).split())
    if not expected_words:
        return 1.0
    hits = sum(1 for w in expected_words if w in ocr_words)
    return hits / len(expected_words)


def _field_hit(expected: str, actual: str) -> bool:
    e, a = _fold_ascii(expected), _fold_ascii(actual)
    return e in a or difflib.SequenceMatcher(None, e, a).ratio() >= 0.85


async def _run_cv_fixture(fixture: CvFixture, *, llm_client: object) -> CvRehearsalResult:
    import base64

    from agents.hr_agent.extractor import ExtractionParseError, extract_cv_profile
    from fleet_rag.ingest.ocr import tesseract_ocr

    image_b64 = render_document_image_base64(fixture.lines)
    image_bytes = base64.b64decode(image_b64)
    ocr_text = tesseract_ocr(image_bytes)
    word_accuracy = _ocr_word_accuracy(fixture.lines, ocr_text)

    reasons: list[str] = []
    hits = 0
    total = 6
    try:
        profile = await extract_cv_profile(ocr_text=ocr_text, llm_client=llm_client)  # type: ignore[arg-type]
    except ExtractionParseError as exc:
        return CvRehearsalResult(
            id=fixture.id, ocr_source="tesseract", ocr_word_accuracy=word_accuracy,
            field_hits=0, field_total=total, field_reasons=[f"extraction failed: {exc}"],
        )

    checks = [
        ("full_name", fixture.expect_full_name, profile.full_name),
        ("email", fixture.expect_email, profile.email),
        ("phone", fixture.expect_phone, profile.phone),
        ("education", fixture.expect_education_contains, " ".join(profile.education)),
        ("experience", fixture.expect_experience_contains, " ".join(profile.experience)),
        ("skills", fixture.expect_skill, " ".join(profile.skills)),
    ]
    for name, expected, actual in checks:
        if _field_hit(expected, actual):
            hits += 1
        else:
            reasons.append(f"{name}: expected ~{expected!r}, got {actual!r}")

    return CvRehearsalResult(
        id=fixture.id, ocr_source="tesseract", ocr_word_accuracy=word_accuracy,
        field_hits=hits, field_total=total, field_reasons=reasons,
    )


async def run_cv_rehearsal(*, limit: int | None = None) -> list[CvRehearsalResult]:
    from core.llm.factory import build_client

    llm_client = await build_client()
    results = []
    fixtures = _FIXTURES[:limit] if limit else _FIXTURES
    for fixture in fixtures:
        try:
            result = await _run_cv_fixture(fixture, llm_client=llm_client)
        except Exception as exc:  # noqa: BLE001 — CPU-only local-lane latency/instability
            # is exactly what this rehearsal exists to characterize (task 8.1's own AC
            # asks for a findings report, not a crash); one flaky case must not lose
            # every other result already gathered in this run.
            result = CvRehearsalResult(
                id=fixture.id, ocr_source="none", ocr_word_accuracy=0.0,
                field_hits=0, field_total=6, field_reasons=[f"gateway error: {exc}"],
            )
        results.append(result)
        print(
            f"[{result.id}] OCR word-accuracy={result.ocr_word_accuracy:.0%} "
            f"fields={result.field_hits}/{result.field_total} "
            f"{'OK' if result.field_hits == result.field_total else result.field_reasons}",
            flush=True,
        )
    return results


def main() -> None:
    import os

    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    limit_env = os.environ.get("REHEARSAL_LIMIT")
    limit = int(limit_env) if limit_env else None
    results = asyncio.run(run_cv_rehearsal(limit=limit))

    n = len(results)
    avg_ocr = sum(r.ocr_word_accuracy for r in results) / n
    avg_field = sum(r.field_hits / r.field_total for r in results) / n
    print(f"\nCV OCR word-accuracy (avg over {n}): {avg_ocr:.1%}")
    print(f"CV field-extraction accuracy (avg over {n}): {avg_field:.1%}")


if __name__ == "__main__":
    main()
