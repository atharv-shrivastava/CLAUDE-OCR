# PARAKH OCR/Field-Extraction Module

Standalone, local, no-external-API module for extracting structured info
from Indian packaged-food labels. Built to be manually wired into PARAKH
later — no auth, no db, no dashboard here on purpose.

## What's actually in here

- `src/ocr_engine.py` — PaddleOCR wrapper. Runs fully on-device.
  No network calls at inference time (PaddleOCR downloads its model
  weights once on first run, then it's offline).
- `src/field_extractor.py` — turns raw OCR text into structured fields
  (FSSAI number, MRP, net qty, dates, batch no, consumer care, country
  of origin, barcode candidate, manufacturer block). Pure regex/rules,
  matches your `{value, raw, confidence, evidence}` schema exactly.
- `src/pipeline.py` — wires the two together, attaches a plain-English
  "what does this field mean" explanation for each successfully
  extracted field.

## Setup

```bash
pip install paddleocr paddlepaddle --break-system-packages
python3 src/pipeline.py path/to/pack_photo.jpg
```

Output is JSON: raw OCR text + all fields with value/raw/confidence/evidence/meaning.

## Honest limitations — read before you trust this in prod

1. **This is regex, not comprehension.** Fields with a legally fixed
   format (FSSAI 14-digit, MRP with currency symbol, dd/mm/yyyy dates)
   get high confidence and will be reliable. Fields with no fixed
   format (manufacturer name/address) are proximity heuristics —
   confidence capped at 0.5 deliberately, because that's genuinely how
   confident you should be in a keyword-window grab.

2. **Tested against 2 synthetic label texts, not real photographed
   packs.** I fixed 3 real bugs during that testing (keyword collision
   between "MFD BY <company>" and "MFG <date>"; separator-less
   MM YYYY dates; "Lot No" false-positive matching before real batch
   number). That means the regex is more robust than a first draft,
   but it has NOT been run against actual OCR output from a real,
   skewed, low-res pack photo — real OCR noise (missing chars, merged
   words, wrong character substitutions like O/0 or l/1) will surface
   more edge cases. Budget time to test against ~20-30 real pack
   photos before treating this as production-ready.

3. **No language auto-detection.** Defaults to `lang='en'`. Indian
   packs often mix Hindi/regional scripts — if you need those fields
   too, run a second OCR pass with `lang='hi'` (or relevant script) and
   merge token lists. Auto-detecting per-image doubles inference cost
   on every image, so I left it manual rather than silently slow
   everything down.

4. **Barcode field is OCR digits, not a barcode scan.** A 12-13 digit
   number near the right length is flagged as a "candidate" — it is
   NOT verified against actual EAN-13 checksum logic. Add that check
   before trusting it (it's a 1-line addition, just didn't want to
   claim more confidence than the current code earns).

5. **No compliance judgment** — by design, per your PARAKH spec. This
   module extracts facts; whether e.g. a missing FSSAI number is a
   violation is your separate rules engine's job.

## Integration into PARAKH

This has zero dependency on your Node/Express/Prisma stack — it's a
standalone Python callable. Two ways to wire it in:
- Simplest: expose `pipeline.run_pipeline()` behind a minimal local
  Flask/FastAPI endpoint your Node backend calls (same shape as your
  existing PaddleOCR-on-Render setup, just add this extraction layer
  in the same service instead of shipping raw OCR text to GLiNER2).
- Since this replaces what GLiNER2 was doing (semantic field mapping)
  with local rules, you could actually drop GLiNER2 from your Render
  deployment for these specific fields — no more 1.5GB model, no more
  OOM crashes on the free tier. Note: you told me earlier you don't
  want to remove GLiNER2 from the architecture, so I'm not doing that
  for you — just flagging that this module makes that RAM problem
  solvable if you ever reconsider.
