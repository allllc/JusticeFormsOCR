"""
PaddleOCR engine implementation.

Note: PaddleOCR 3.x on Python 3.13 requires setting HUB_DATASET_ENDPOINT
environment variable before importing. This is handled in this module.
"""
import os
from typing import List
from PIL import Image
import numpy as np

from .base import OCREngineBase, OCRResult, TextLine
from ..layout.base import Region


class PaddleOCREngine(OCREngineBase):
    """OCR engine using PaddleOCR (3.x API)."""

    _ocr = None

    @property
    def name(self) -> str:
        return "paddleocr"

    def _load_model(self):
        """Lazy load the model with Python 3.13 workaround."""
        if PaddleOCREngine._ocr is None:
            # Apply workaround for Python 3.13 modelscope bug
            # Must be set BEFORE importing paddleocr
            os.environ.setdefault(
                'HUB_DATASET_ENDPOINT',
                'https://modelscope.cn/api/v1/datasets'
            )

            import logging
            logging.getLogger('ppocr').setLevel(logging.WARNING)

            # Disable MKLDNN/oneDNN to avoid ConvertPirAttribute2RuntimeAttribute errors
            os.environ['FLAGS_use_mkldnn'] = '0'

            import paddle
            paddle.set_device('cpu')

            from paddleocr import PaddleOCR

            # PaddleOCR 3.x API: use_angle_cls replaced by granular params
            PaddleOCREngine._ocr = PaddleOCR(
                lang='en',
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=True,
                device='cpu',
                enable_mkldnn=False,
            )
        return PaddleOCREngine._ocr

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
        """Process a cropped image with PaddleOCR 3.x."""
        ocr = self._load_model()

        # Convert to numpy array
        image_array = np.array(image)

        # PaddleOCR 3.x uses predict() instead of ocr()
        results = ocr.predict(image_array)

        lines = []
        full_text_parts = []

        # PaddleOCR 3.x returns Result objects with:
        #   rec_texts: list of strings
        #   rec_scores: list of floats
        #   rec_boxes: ndarray of [x_min, y_min, x_max, y_max]
        for res in results:
            texts = getattr(res, 'rec_texts', []) or []
            scores = getattr(res, 'rec_scores', []) or []
            boxes = getattr(res, 'rec_boxes', None)

            for i, text in enumerate(texts):
                if not text:
                    continue

                confidence = float(scores[i]) if i < len(scores) else 0.0

                bbox = {}
                if boxes is not None and i < len(boxes):
                    box = boxes[i]
                    bbox = {
                        "x1": int(box[0]),
                        "y1": int(box[1]),
                        "x2": int(box[2]),
                        "y2": int(box[3]),
                    }
                else:
                    bbox = {"x1": 0, "y1": 0, "x2": 0, "y2": 0}

                lines.append(TextLine(
                    text=text,
                    confidence=round(confidence, 4),
                    bbox_in_region=bbox,
                ))
                full_text_parts.append(text)

        full_text = " ".join(full_text_parts)

        return OCRResult(
            region_id=region_id,
            full_text=full_text,
            lines=lines,
        )
