"""
DocTR layout detector implementation.
"""
from typing import List
from PIL import Image
import numpy as np

from .base import LayoutDetectorBase, Region


class DocTRLayoutDetector(LayoutDetectorBase):
    """Layout detector using DocTR."""

    _model = None

    @property
    def name(self) -> str:
        return "doctr"

    def _load_model(self):
        """Lazy load the model."""
        if DocTRLayoutDetector._model is None:
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context

            from doctr.models import detection_predictor

            DocTRLayoutDetector._model = detection_predictor(
                arch='db_resnet50',
                pretrained=True
            )
        return DocTRLayoutDetector._model

    def detect(self, image: Image.Image) -> List[Region]:
        """Detect layout regions using DocTR."""
        model = self._load_model()

        # Convert to numpy array
        image_array = np.array(image)

        # Run detection
        result = model([image_array])

        regions = []
        img_height, img_width = image_array.shape[:2]

        # DocTR returns a list of dicts, one per page
        # Each dict has "words" key with numpy array of shape (N, 5)
        # where each row is [xmin, ymin, xmax, ymax, confidence] (normalized 0-1)
        if result and len(result) > 0:
            page_result = result[0]

            if 'words' in page_result:
                words = page_result['words']
            else:
                words = page_result

            for i, det in enumerate(words):
                xmin, ymin, xmax, ymax, confidence = det
                x1 = int(float(xmin) * img_width)
                y1 = int(float(ymin) * img_height)
                x2 = int(float(xmax) * img_width)
                y2 = int(float(ymax) * img_height)

                regions.append(Region(
                    id=i + 1,
                    type="text",
                    confidence=float(confidence),
                    bbox={"x1": x1, "y1": y1, "x2": x2, "y2": y2}
                ))

        # Sort by y-coordinate (top to bottom), then x-coordinate (left to right)
        regions.sort(key=lambda r: (r.bbox["y1"], r.bbox["x1"]))

        # Re-assign IDs after sorting
        for i, region in enumerate(regions):
            region.id = i + 1

        return regions
