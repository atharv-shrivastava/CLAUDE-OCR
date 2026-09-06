"""
field_extractor.py
Turns raw OCR text into structured, PARAKH-schema fields.

Every field is emitted as:
    {
      "value": <cleaned/normalized value or None>,
      "raw": <exact OCR substring that produced it>,
      "confidence": <0-1 float>,
      "evidence": <short string explaining why we picked it>
    }

Design stance (read this before tuning regexes):
- This is 100% local pattern-matching. No calls to any LLM/NLP API.
- Fields with strong, legally-mandated formats (FSSAI 14-digit number,
  MRP with ₹/Rs, dd/mm/yyyy dates) get high-confidence regex matches.
- Fields with no fixed format (manufacturer name, brand) get lower-
  confidence heuristics (proximity to keywords, position on label).
  Don't expect these to hit 95% — that needs a trained NER model, not
  regex. Confidence scores reflect that honestly instead of pretending.
- Never invent a value. If nothing matches, value=None and confidence=0.
"""

import re
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any


@dataclass
class ExtractedField:
    value: Optional[str]
    raw: Optional[str]
    confidence: float
    evidence: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Regex library — Indian packaged-food-label specific
# ---------------------------------------------------------------------------

FSSAI_RE = re.compile(r"\b(\d{14})\b")
FSSAI_CONTEXT_RE = re.compile(r"FSSAI[^\d]{0,20}(\d{14})", re.IGNORECASE)

MRP_RE = re.compile(
    r"(?:MRP|M\.R\.P\.?|Maximum\s+Retail\s+Price)\s*[:\-]?\s*"
    r"(?:Rs\.?|₹|INR)?\s*([0-9]+(?:[.,][0-9]{1,2})?)",
    re.IGNORECASE,
)

NET_QTY_RE = re.compile(
    r"(?:Net\s*(?:Qty|Quantity|Wt|Weight)\.?)\s*[:\-]?\s*"
    r"([0-9]+(?:\.[0-9]+)?)\s*(g|gm|gms|kg|ml|l|litre|liter)\b",
    re.IGNORECASE,
)

DATE_RE = re.compile(
    r"\b(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4})\b"
)
# MM/YYYY, MM-YYYY, or MM YYYY (space) — OCR frequently drops the
# separator entirely, so a bare space between month and year counts too.
NUMERIC_MONTH_YEAR_RE = re.compile(
    r"\b(0[1-9]|1[0-2])[\/\-\s](\d{4})\b"
)
MONTH_YEAR_RE = re.compile(
    r"\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*[\s\-\/]?(\d{4}|\d{2})\b",
    re.IGNORECASE,
)

BATCH_RE = re.compile(
    r"(?:Batch\s*(?:No\.?|Number)?|B\.?No\.?)\s*[:\-]?\s*([A-Za-z0-9\-\/]{2,20})",
    re.IGNORECASE,
)
# "Lot No" is separate and lower-priority: on Indian food packs "lot no"
# almost never means batch — it more often shows up in unrelated address/
# plot references ("Plot No 47"). Only used as a fallback, never first.
LOT_RE = re.compile(
    r"\bLot\s*No\.?\s*[:\-]?\s*([A-Za-z0-9\-\/]{2,20})", re.IGNORECASE
)

CONSUMER_CARE_PHONE_RE = re.compile(
    r"(?:Consumer\s*Care|Customer\s*Care|Toll\s*Free|Helpline)(?:\s*(?:No\.?|Number)?)?[^\d]{0,20}"
    r"((?:\+?91[\-\s]?)?[6-9]\d{9}|1[\-\s]?800[\-\s]?\d{1,4}[\-\s]?\d{1,4}[\-\s]?\d{0,4})",
    re.IGNORECASE,
)
CONSUMER_CARE_EMAIL_RE = re.compile(
    r"[\w\.\-]+@[\w\-]+\.\w{2,}"
)

COUNTRY_OF_ORIGIN_RE = re.compile(
    r"Country\s*of\s*Origin\s*[:\-]?\s*([A-Za-z ]{3,30})", re.IGNORECASE
)

BARCODE_RE = re.compile(r"\b(\d{12,13})\b")  # EAN-13 / UPC-A candidate

MFG_KEYWORDS = ["manufactured by", "mfd by", "manufactured and marketed by",
                "packed by", "marketed by", "imported by"]

# addresses are messy; we treat the text following an mfg keyword up to
# the next newline/keyword as an address candidate
ADDRESS_STOP_KEYWORDS = ["fssai", "net", "mrp", "batch", "best before",
                         "consumer", "customer care", "exp", "mfg date"]


def _find_first(pattern: re.Pattern, text: str) -> Optional[re.Match]:
    return pattern.search(text)


def extract_fssai(text: str) -> ExtractedField:
    m = FSSAI_CONTEXT_RE.search(text)
    if m:
        return ExtractedField(m.group(1), m.group(0), 0.95, "matched 'FSSAI' keyword + 14-digit number")
    m = FSSAI_RE.search(text)
    if m:
        return ExtractedField(m.group(1), m.group(0), 0.55, "14-digit number found without FSSAI keyword nearby — unverified")
    return ExtractedField(None, None, 0.0, "no 14-digit FSSAI-format number found")


def extract_mrp(text: str) -> ExtractedField:
    m = MRP_RE.search(text)
    if m:
        return ExtractedField(m.group(1), m.group(0), 0.9, "matched MRP keyword + currency + number")
    return ExtractedField(None, None, 0.0, "no MRP pattern found")


def extract_net_quantity(text: str) -> ExtractedField:
    m = NET_QTY_RE.search(text)
    if m:
        val = f"{m.group(1)} {m.group(2)}"
        return ExtractedField(val, m.group(0), 0.9, "matched Net Qty/Weight keyword + number + unit")
    return ExtractedField(None, None, 0.0, "no net quantity pattern found")


def extract_dates(text: str) -> Dict[str, ExtractedField]:
    """Returns dict with 'mfg_date' and 'expiry_date' best-guesses.
    We can't reliably tell which numeric date is mfg vs expiry from
    regex alone unless a keyword (MFG/EXP/Best Before) sits next to it —
    so we search in keyword-anchored windows first, numeric-only as fallback.
    """
    results = {}

    # Anchor strictly to a date-labeled MFG/MFD, not "manufactured by <company>".
    # "MFD BY"/"MFG BY" followed by letters is a manufacturer credit, not a
    # date field — exclude that shape explicitly so it doesn't win the search
    # just because it appears earlier in the text.
    mfg_window = None
    for m in re.finditer(r"(?:MFG|MFD|Manufactur(?:ed|ing))\s*(?:DATE)?[^\n]{0,25}", text, re.IGNORECASE):
        snippet = m.group(0)
        if re.search(r"\b(?:by)\b\s*[A-Za-z]", snippet, re.IGNORECASE) and not re.search(r"\d", snippet):
            continue  # "mfd by <company name>" with no digits yet — not the date field
        mfg_window = m
        break
    exp_window = re.search(r"(?:EXP|Expiry|Best\s*Before|Use\s*By)[^\n]{0,25}", text, re.IGNORECASE)

    def date_in(window_match, label):
        if not window_match:
            return ExtractedField(None, None, 0.0, f"no '{label}' keyword found")
        window_text = window_match.group(0)
        d = (DATE_RE.search(window_text)
             or NUMERIC_MONTH_YEAR_RE.search(window_text)
             or MONTH_YEAR_RE.search(window_text))
        if d:
            return ExtractedField(d.group(0), window_match.group(0), 0.85, f"matched '{label}' keyword with adjacent date")
        return ExtractedField(None, None, 0.2, f"'{label}' keyword found but no date pattern adjacent")

    results["mfg_date"] = date_in(mfg_window, "MFG/Manufacturing Date")

    exp_field = date_in(exp_window, "EXP/Best Before")
    if exp_field.value is None and exp_window:
        # common Indian-label pattern: "Best Before 9 months from MFG/packaging"
        # instead of a fixed date — real info, just not a calendar date
        relative = re.search(r"(\d{1,3})\s*(day|month|year)s?\s*from", exp_window.group(0), re.IGNORECASE)
        if relative:
            exp_field = ExtractedField(
                f"{relative.group(1)} {relative.group(2)}(s) from mfg/packaging date",
                exp_window.group(0),
                0.8,
                "matched relative shelf-life pattern (no fixed expiry date printed — must be computed from mfg_date)",
            )
    results["expiry_date"] = exp_field
    return results


def extract_batch_number(text: str) -> ExtractedField:
    m = BATCH_RE.search(text)
    if m:
        return ExtractedField(m.group(1), m.group(0), 0.85, "matched Batch No. keyword")
    m = LOT_RE.search(text)
    if m:
        return ExtractedField(m.group(1), m.group(0), 0.5, "matched 'Lot No' keyword (lower confidence — 'lot no' on food packs is sometimes a false positive from address/plot references)")
    return ExtractedField(None, None, 0.0, "no batch number pattern found")


def extract_consumer_care(text: str) -> Dict[str, ExtractedField]:
    results = {}
    m = CONSUMER_CARE_PHONE_RE.search(text)
    if m:
        results["phone"] = ExtractedField(m.group(1).strip(), m.group(0).strip(), 0.85, "matched Consumer Care keyword + phone pattern")
    else:
        results["phone"] = ExtractedField(None, None, 0.0, "no consumer care phone pattern found")

    m = CONSUMER_CARE_EMAIL_RE.search(text)
    if m:
        results["email"] = ExtractedField(m.group(0), m.group(0), 0.8, "matched email pattern (not keyword-anchored, so could be unrelated email on pack)")
    else:
        results["email"] = ExtractedField(None, None, 0.0, "no email pattern found")
    return results


def extract_country_of_origin(text: str) -> ExtractedField:
    m = COUNTRY_OF_ORIGIN_RE.search(text)
    if m:
        return ExtractedField(m.group(1).strip(), m.group(0), 0.9, "matched 'Country of Origin' keyword")
    if re.search(r"\bMade\s+in\s+India\b", text, re.IGNORECASE):
        return ExtractedField("India", "Made in India", 0.85, "matched 'Made in India' phrase")
    return ExtractedField(None, None, 0.0, "no country-of-origin pattern found")


def extract_barcode(text: str) -> ExtractedField:
    m = BARCODE_RE.search(text)
    if m:
        return ExtractedField(m.group(1), m.group(0), 0.6, "12-13 digit number matching EAN-13/UPC-A length — needs visual barcode confirmation, not just OCR digits")
    return ExtractedField(None, None, 0.0, "no barcode-length number found")


def extract_manufacturer_block(text: str) -> ExtractedField:
    """Weakest-confidence extraction by design: manufacturer name/address
    has no fixed format. We grab the text after a keyword like
    'Manufactured by' up to the next known-field keyword or line break.
    This is a heuristic, not semantic understanding — flag it as such.
    """
    lower = text.lower()
    for kw in MFG_KEYWORDS:
        idx = lower.find(kw)
        if idx == -1:
            continue
        start = idx + len(kw)
        snippet = text[start:start + 200]
        # cut at the first stop keyword
        cut = len(snippet)
        for stop in ADDRESS_STOP_KEYWORDS:
            pos = snippet.lower().find(stop)
            if pos != -1:
                cut = min(cut, pos)
        candidate = snippet[:cut].strip(" :\n-")
        if candidate:
            return ExtractedField(candidate, text[idx:start + cut], 0.5,
                                   f"text following '{kw}' keyword, truncated at next field keyword — address parsing is approximate")
    return ExtractedField(None, None, 0.0, "no manufacturer/packer keyword found")


def extract_all_fields(full_text: str) -> Dict[str, Any]:
    """Main entry point. Takes OCR full_text, returns PARAKH-schema dict."""
    dates = extract_dates(full_text)
    care = extract_consumer_care(full_text)

    fields = {
        "fssai_number": extract_fssai(full_text),
        "mrp": extract_mrp(full_text),
        "net_quantity": extract_net_quantity(full_text),
        "mfg_date": dates["mfg_date"],
        "expiry_date": dates["expiry_date"],
        "batch_number": extract_batch_number(full_text),
        "consumer_care_phone": care["phone"],
        "consumer_care_email": care["email"],
        "country_of_origin": extract_country_of_origin(full_text),
        "barcode_candidate": extract_barcode(full_text),
        "manufacturer_block": extract_manufacturer_block(full_text),
    }
    return {k: v.to_dict() for k, v in fields.items()}


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) != 2:
        print("Usage: python field_extractor.py <text_file_or_'-' for stdin>")
        sys.exit(1)
    text = sys.stdin.read() if sys.argv[1] == "-" else open(sys.argv[1]).read()
    print(json.dumps(extract_all_fields(text), indent=2))
