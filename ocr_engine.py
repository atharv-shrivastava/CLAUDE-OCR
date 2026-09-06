"""
ocr_engine.py
Local OCR layer for PARAKH package-info extraction.

Uses PaddleOCR (runs entirely on-device, no external API calls, no
network dependency at inference time beyond the one-time model download).

Output: list of OCRToken(text, confidence, bbox) — the raw evidence
that the field-extraction layer (field_extractor.py) will parse.
"""

from dataclasses import dataclass, field
from typing import List, Tuple
import numpy as np

try:
    from paddleocr import PaddleOCR
except ImportError as e:
    raise ImportError(
        "PaddleOCR not installed. Run: pip install paddleocr paddlepaddle --break-system-packages"
    ) from e


@dataclass
class OCRToken:
    text: str
    confidence: float
    bbox: List[Tuple[float, float]]  # 4 corner points, clockwise from top-left

    @property
    def center_y(self) -> float:
        return sum(p[1] for p in self.bbox) / 4

    @property
    def center_x(self) -> float:
        return sum(p[0] for p in self.bbox) / 4


@dataclass
class OCRResult:
    tokens: List[OCRToken] = field(default_factory=list)
    full_text: str = ""  # tokens joined in reading order, for regex passes

    def sorted_reading_order(self) -> List[OCRToken]:
        """Rough top-to-bottom, left-to-right ordering.
        Groups tokens into text lines by y-proximity, then sorts each
        line left-to-right. Packaging labels are rarely single-column
        so this is an approximation, not a layout parser.
        """
        if not self.tokens:
            return []
        toks = sorted(self.tokens, key=lambda t: t.center_y)
        lines: List[List[OCRToken]] = []
        line_thresh = 15  # px tolerance for "same line"
        for tok in toks:
            placed = False
            for line in lines:
                if abs(line[0].center_y - tok.center_y) < line_thresh:
                    line.append(tok)
                    placed = True
                    break
            if not placed:
                lines.append([tok])
        ordered: List[OCRToken] = []
        for line in lines:
            ordered.extend(sorted(line, key=lambda t: t.center_x))
        return ordered


class OCREngine:
    """
    Thin wrapper around PaddleOCR. Loads once, reused across images.
    lang='en' works for English + digits; Indian packs often mix in
    Hindi/regional script — for those, swap lang or run a second pass
    with lang='hi' and merge results (see README for why we don't
    auto-detect language: it doubles inference time on every image and
    most compliance-relevant fields — MRP, FSSAI no, dates — are in
    English/numerals regardless of the rest of the label).
    """

    def __init__(self, lang: str = "en", use_gpu: bool = False):
        self._ocr = PaddleOCR(
            use_angle_cls=True,   # handles rotated/skewed pack photos
            lang=lang,
            show_log=False,
        )

    def extract(self, image_path: str) -> OCRResult:
        raw = self._ocr.ocr(image_path, cls=True)
        result = OCRResult()
        if not raw or raw[0] is None:
            return result

        lines_text = []
        for line in raw[0]:
            bbox, (text, conf) = line
            result.tokens.append(OCRToken(text=text, confidence=float(conf), bbox=bbox))
            lines_text.append(text)

        result.full_text = "\n".join(
            t.text for t in result.sorted_reading_order()
        )
        return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python ocr_engine.py <image_path>")
        sys.exit(1)

    engine = OCREngine()
    res = engine.extract(sys.argv[1])
    print("--- Raw tokens ---")
    for t in res.tokens:
        print(f"[{t.confidence:.2f}] {t.text}")
    print("\n--- Reading order text ---")
    print(res.full_text)
