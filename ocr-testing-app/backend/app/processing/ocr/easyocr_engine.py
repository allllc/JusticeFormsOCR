"""
EasyOCR engine implementation.
"""
from typing import List
from PIL import Image
import numpy as np

from .base import OCREngineBase, OCRResult, TextLine
from ..layout.base import Region


class EasyOCREngine(OCREngineBase):
    """OCR engine using EasyOCR."""

    _reader = None

    @property
    def name(self) -> str:
        return "easyocr"

    def _load_model(self):
        """Lazy load the model."""
        if EasyOCREngine._reader is None:
            import easyocr

            EasyOCREngine._reader = easyocr.Reader(
                ['en'],
                gpu=False,
                verbose=False
            )
        return EasyOCREngine._reader

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
        """Process a cropped image with EasyOCR."""
        reader = self._load_model()

        # Convert to numpy array
        image_array = np.array(image)

        # Run OCR
        ocr_result = reader.readtext(image_array)

        lines = []
        full_text_parts = []

        for detection in ocr_result:
            bbox_points, text, confidence = detection

            # bbox_points is [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
            x_coords = [p[0] for p in bbox_points]
            y_coords = [p[1] for p in bbox_points]

            lines.append(TextLine(
                text=text,
                confidence=round(float(confidence), 4),
                bbox_in_region={
                    "x1": int(min(x_coords)),
                    "y1": int(min(y_coords)),
                    "x2": int(max(x_coords)),
                    "y2": int(max(y_coords))
                }
            ))
            full_text_parts.append(text)

        full_text = " ".join(full_text_parts)

        return OCRResult(
            region_id=region_id,
            full_text=full_text,
            lines=lines
        )
