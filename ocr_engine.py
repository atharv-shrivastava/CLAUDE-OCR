"""
ocr_engine.py
Local OCR layer for PARAKH package-info extraction.

Uses PaddleOCR 3.x predict() API and converts its output into the
OCRToken format used by the field-extraction layer.
"""

from dataclasses import dataclass, field
from typing import List, Tuple

try:
    from paddleocr import PaddleOCR
except ImportError as e:
    raise ImportError(
        "PaddleOCR not installed. Run: pip install paddleocr paddlepaddle"
    ) from e


@dataclass
class OCRToken:
    text: str
    confidence: float
    bbox: List[Tuple[float, float]]

    @property
    def center_y(self) -> float:
        if not self.bbox:
            return 0.0
        return sum(p[1] for p in self.bbox) / len(self.bbox)

    @property
    def center_x(self) -> float:
        if not self.bbox:
            return 0.0
        return sum(p[0] for p in self.bbox) / len(self.bbox)


@dataclass
class OCRResult:
    tokens: List[OCRToken] = field(default_factory=list)
    full_text: str = ""

    def sorted_reading_order(self) -> List[OCRToken]:
        if not self.tokens:
            return []

        toks = sorted(self.tokens, key=lambda t: t.center_y)
        lines: List[List[OCRToken]] = []
        line_thresh = 15

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
    """Thin wrapper around PaddleOCR's current predict() API."""

    def __init__(self, lang: str = "en", use_gpu: bool = False):
        # PaddleOCR 3.x uses the unified predict() interface.
        # Do not pass the old show_log or cls arguments.
        #
        # PaddlePaddle 3.3.x + PaddleOCR 3.7.x can crash on Windows/CPU
        # inside the oneDNN/PIR path with:
        # ConvertPirAttribute2RuntimeAttribute not support
        # [pir::ArrayAttribute<pir::DoubleAttribute>]
        # Disable oneDNN so CPU inference uses the standard Paddle kernels.
        self._ocr = PaddleOCR(
            lang=lang,
            enable_mkldnn=False,
        )

    @staticmethod
    def _to_list(value):
        """Convert numpy arrays / Paddle tensors / tuples to Python lists."""
        if value is None:
            return None
        if hasattr(value, "tolist"):
            return value.tolist()
        return value

    @staticmethod
    def _extract_result_dict(res):
        """Get the result dictionary from PaddleOCR 3.x OCRResult."""
        data = res

        if hasattr(res, "json"):
            data = res.json
            if callable(data):
                data = data()

        if isinstance(data, str):
            import json
            data = json.loads(data)

        if isinstance(data, dict) and "res" in data:
            data = data["res"]

        return data if isinstance(data, dict) else {}

    def extract(self, image_path: str) -> OCRResult:
        result = OCRResult()

        # PaddleOCR 3.x: predict() replaces the old ocr(..., cls=True) API.
        raw = self._ocr.predict(image_path)

        if raw is None:
            return result

        for res in raw:
            data = self._extract_result_dict(res)

            texts = self._to_list(data.get("rec_texts")) or []
            scores = self._to_list(data.get("rec_scores")) or []
            boxes = self._to_list(data.get("rec_polys"))
            if boxes is None:
                boxes = self._to_list(data.get("dt_polys"))
            if boxes is None:
                boxes = self._to_list(data.get("rec_boxes")) or []

            for i, text in enumerate(texts):
                text = str(text).strip()
                if not text:
                    continue

                confidence = float(scores[i]) if i < len(scores) else 0.0
                bbox = boxes[i] if i < len(boxes) else []
                bbox = self._to_list(bbox) or []

                if (
                    len(bbox) == 4
                    and bbox
                    and isinstance(bbox[0], (int, float))
                ):
                    x1, y1, x2, y2 = bbox
                    bbox = [
                        (float(x1), float(y1)),
                        (float(x2), float(y1)),
                        (float(x2), float(y2)),
                        (float(x1), float(y2)),
                    ]
                else:
                    bbox = [
                        (float(point[0]), float(point[1]))
                        for point in bbox
                        if isinstance(point, (list, tuple)) and len(point) >= 2
                    ]

                if len(bbox) < 4:
                    continue

                result.tokens.append(
                    OCRToken(
                        text=text,
                        confidence=confidence,
                        bbox=bbox[:4],
                    )
                )

        result.full_text = "\n".join(
            token.text for token in result.sorted_reading_order()
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
    for token in res.tokens:
        print(f"[{token.confidence:.2f}] {token.text}")

    print("\n--- Reading order text ---")
    print(res.full_text)
