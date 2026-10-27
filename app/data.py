"""Data layer of the demo: reads the fictional test set and the caches, and runs the engine.

No API calls, no OCR and no uploads. Everything comes from files already in the
repository:
- data/applicants.csv, data/documents.csv, data/ground_truth.csv, data/photos.csv;
- cache/extraction_v4/<model>/ (LLM extraction of each document);
- cache/photos_v2/extraction_v4/<model>/ (LLM extraction of the phone photos);
- cache/ocr/confidence.csv and confidence_v2.csv (OCR word counts).
It deliberately does not import core/ocr.py (which needs pytesseract) nor the
evaluation scripts (which need the Gemini SDK). The decision always comes from
core/engine.py, the same function the eval uses; only the income multiplier
is changed, on a copy of the configuration.
"""

import csv
import json
import sys
from dataclasses import dataclass, field, replace
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import config as engine_config  # noqa: E402
from core.engine import decidir  # noqa: E402
from core.inputs import documento_da_extracao  # noqa: E402
from core.models import Cliente  # noqa: E402

DATA = ROOT / "data"
IMAGES = DATA / "images"
PHOTOS = IMAGES / "v2"
PROMPT = "extraction_v4"
MODEL = "gemini-3.5-flash-lite"
EXTRACTIONS = ROOT / "cache" / PROMPT / MODEL
PHOTO_EXTRACTIONS = ROOT / "cache" / "photos_v2" / PROMPT / MODEL

# Demo-only case: A01 (the happy path) with its July pay stub sent as a photo of the screen.
PHOTO_CASE = "A01-PHOTO"
PHOTO_CASE_BASE = "A01"
PHOTO_CASE_SOURCE = "A01_2026-07.png"
PHOTO_CASE_PHOTO = "A01_2026-07_happy-path.jpeg"

TOUR = ["A17", "N10", "N09", "N14", "N12", PHOTO_CASE, "N17"]
DEFAULT_CASE = "A17"


def _read(path, encoding="utf-8"):
    with open(path, newline="", encoding=encoding) as f:
        return list(csv.DictReader(f))


def _words(path):
    return {row["file"]: int(row["words"]) for row in _read(path)}


@dataclass
class CaseDocument:
    file: str
    image: Path
    extraction: dict
    document: object  # core.models.Documento
    is_photo: bool = False


@dataclass
class Case:
    case_id: str
    applicant: Cliente
    documents: list
    scenario: str
    expected_decision: str
    expected_reason: str
    is_demo_build: bool = False
    original_documents: list = field(default_factory=list)  # A01-PHOTO only: the PDF version


def _applicant(row):
    return Cliente(row["applicant_id"], row["name"], row["cpf"], Decimal(row["installment_amount"]),
                   date.fromisoformat(row["analysis_date"]))


def _extraction(folder, file):
    return json.loads((folder / f"{file}.json").read_text(encoding="utf-8"))["extraction"]


def load_cases():
    """{case_id: Case} for the 34 applicants plus the demo-only screen photo case."""
    applicants = {row["applicant_id"]: _applicant(row) for row in _read(DATA / "applicants.csv")}
    truth = {row["applicant_id"]: row for row in _read(DATA / "ground_truth.csv", encoding="utf-8-sig")}
    words = _words(ROOT / "cache" / "ocr" / "confidence.csv")
    photo_words = _words(ROOT / "cache" / "ocr" / "confidence_v2.csv")

    per_applicant = {}
    for row in _read(DATA / "documents.csv"):
        if row["applicant_id"] not in applicants:
            continue  # example documents that belong to no applicant
        extraction = _extraction(EXTRACTIONS, row["file"])
        per_applicant.setdefault(row["applicant_id"], []).append(CaseDocument(
            row["file"], IMAGES / row["file"], extraction,
            documento_da_extracao(row["file"], extraction, words.get(row["file"]))))

    cases = {}
    for cid, applicant in applicants.items():
        t = truth[cid]
        cases[cid] = Case(cid, applicant, per_applicant.get(cid, []), t["scenario"], t["expected_decision"],
                          t["expected_reason"])

    base = cases[PHOTO_CASE_BASE]
    photo_extraction = _extraction(PHOTO_EXTRACTIONS, PHOTO_CASE_PHOTO)
    photo = CaseDocument(PHOTO_CASE_PHOTO, PHOTOS / PHOTO_CASE_PHOTO, photo_extraction,
                         documento_da_extracao(PHOTO_CASE_PHOTO, photo_extraction, photo_words.get(PHOTO_CASE_PHOTO)),
                         is_photo=True)
    documents = [photo if d.file == PHOTO_CASE_SOURCE else d for d in base.documents]
    cases[PHOTO_CASE] = Case(PHOTO_CASE, base.applicant, documents, base.scenario, "reject", "screen_capture",
                             is_demo_build=True, original_documents=base.documents)
    return cases


def decide(applicant, documents, multiplier):
    """Runs core/engine.py with the default configuration and the chosen income multiplier."""
    # The widget gives a float (e.g. 2.9000000000000004); the engine compares in exact decimals.
    cfg = replace(engine_config.carregar(), income_multiplier=Decimal(str(round(multiplier, 2))))
    return decidir(applicant, [d.document for d in documents], cfg, prior_legibility_failures=0)


def default_multiplier():
    return float(engine_config.carregar().income_multiplier)


RESULTS = ROOT / "evaluation" / "results"


def result_reports():
    """{group: [paths]} of the markdown reports in evaluation/results/."""
    groups = {"applicants": [], "documents": [], "photos": [], "gates": []}
    for path in sorted(RESULTS.glob("*.md")):
        for prefix in groups:
            if path.name.startswith(prefix):
                groups[prefix].append(path)
    return {k: v for k, v in groups.items() if v}
