"""
pipeline.py
Full local pipeline: image -> OCR -> structured fields -> plain-English
explanation of what each field means (for a non-technical PARAKH end user).

No external API calls anywhere in this file. Everything runs on-device.
"""

import json
import sys
from typing import Dict, Any

from ocr_engine import OCREngine
from field_extractor import extract_all_fields


FIELD_EXPLANATIONS = {
    "fssai_number": (
        "This is the food business's license number issued by FSSAI "
        "(Food Safety and Standards Authority of India). Every packaged "
        "food sold in India is legally required to print this 14-digit "
        "number. You can look it up on the FSSAI portal to verify who's "
        "actually licensed to sell this product."
    ),
    "mrp": (
        "Maximum Retail Price — the highest price the seller is legally "
        "allowed to charge you for this item, inclusive of all taxes. "
        "Selling above this is a violation."
    ),
    "net_quantity": (
        "The actual amount of product inside the pack (by weight or "
        "volume), not counting the packaging itself."
    ),
    "mfg_date": (
        "The date the product was manufactured or packed. Used together "
        "with the expiry/best-before info to judge freshness."
    ),
    "expiry_date": (
        "Either a fixed 'use by' date, or a shelf-life duration counted "
        "from the manufacturing date (e.g. '6 months from mfg'). If it's "
        "a duration, you need the mfg_date too to know the actual cutoff."
    ),
    "batch_number": (
        "An internal production-batch code. Mainly useful for recalls — "
        "if a batch is found unsafe, this number identifies which units "
        "are affected."
    ),
    "consumer_care_phone": (
        "Phone number to contact if there's a complaint or safety issue "
        "with the product."
    ),
    "consumer_care_email": (
        "Email address for the same purpose as consumer care phone."
    ),
    "country_of_origin": (
        "Where the product was actually made — required disclosure, "
        "especially relevant for imported goods."
    ),
    "barcode_candidate": (
        "A 12-13 digit number that looks like a barcode (EAN-13/UPC-A). "
        "Flagged as a candidate only — OCR reads printed digits, it "
        "doesn't scan the actual barcode, so this should be cross-checked "
        "against a real barcode scan if accuracy matters."
    ),
    "manufacturer_block": (
        "Name and address of whoever manufactured, packed, or imported "
        "the product — legally required so the responsible party is "
        "traceable."
    ),
}


def run_pipeline(image_path: str, lang: str = "en") -> Dict[str, Any]:
    engine = OCREngine(lang=lang)
    ocr_result = engine.extract(image_path)
    fields = extract_all_fields(ocr_result.full_text)

    # attach plain-English meaning to each field that had a real match
    for name, data in fields.items():
        if data["value"] is not None:
            data["meaning"] = FIELD_EXPLANATIONS.get(name, "")

    return {
        "ocr_raw_text": ocr_result.full_text,
        "fields": fields,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python pipeline.py <image_path>")
        sys.exit(1)
    result = run_pipeline(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))
