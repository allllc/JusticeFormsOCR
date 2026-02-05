"""
Surya OCR engine implementation.
"""
from typing import List
from PIL import Image

from .base import OCREngineBase, OCRResult, TextLine
from ..layout.base import Region


class SuryaOCREngine(OCREngineBase):
    """OCR engine using Surya."""

    _foundation_predictor = None
    _recognition_predictor = None

    @property
    def name(self) -> str:
        return "surya"

    def _load_model(self):
        """Lazy load the model."""
        if SuryaOCREngine._recognition_predictor is None:
            from surya.recognition import RecognitionPredictor, FoundationPredictor

            SuryaOCREngine._foundation_predictor = FoundationPredictor()
            SuryaOCREngine._recognition_predictor = RecognitionPredictor(
                SuryaOCREngine._foundation_predictor
            )
        return SuryaOCREngine._recognition_predictor

    def extract_text(
        self,
        image: Image.Image,
        regions: List[Region]
    ) -> List[OCRResult]:
        """Extract text from all regions."""
        results = []
        for region in regions:
            result = self.extract_from_region(image, region)
            results.append(result)
        return results

    def _process_cropped_image(
        self,
        image: Image.Image,
        region_id: int
    ) -> OCRResult:
        """Process a cropped image with Surya OCR."""
        predictor = self._load_model()

        # Get image dimensions for full region bbox
        width, height = image.size
        full_region_bbox = [[0, 0, width, height]]

        # Run OCR
        results = predictor([image], bboxes=[full_region_bbox])

        lines = []
        full_text_parts = []

        if results and len(results) > 0:
            page_result = results[0]

            for text_line in page_result.text_lines:
                text = text_line.text
                confidence = getattr(text_line, 'confidence', 0.5)
                bbox = getattr(text_line, 'bbox', [0, 0, width, height])

                lines.append(TextLine(
                    text=text,
                    confidence=round(float(confidence), 4),
                    bbox_in_region={
                        "x1": int(bbox[0]),
                        "y1": int(bbox[1]),
                        "x2": int(bbox[2]),
                        "y2": int(bbox[3])
                    }
                ))
                full_text_parts.append(text)

        full_text = " ".join(full_text_parts)

        return OCRResult(
            region_id=region_id,
            full_text=full_text,
            lines=lines
        )
