"""
Surya layout detector implementation.
"""
from typing import List
from PIL import Image

from .base import LayoutDetectorBase, Region


class SuryaLayoutDetector(LayoutDetectorBase):
    """Layout detector using Surya."""

    _predictor = None

    @property
    def name(self) -> str:
        return "surya"

    def _load_model(self):
        """Lazy load the model."""
        if SuryaLayoutDetector._predictor is None:
            from surya.detection import DetectionPredictor

            SuryaLayoutDetector._predictor = DetectionPredictor()
        return SuryaLayoutDetector._predictor

    def detect(self, image: Image.Image) -> List[Region]:
        """Detect layout regions using Surya."""
        predictor = self._load_model()

        # Run detection
        results = predictor([image])

        regions = []

        if results and len(results) > 0:
            page_result = results[0]

            # Surya returns bboxes with labels
            for i, bbox_obj in enumerate(page_result.bboxes):
                bbox = bbox_obj.bbox  # [x1, y1, x2, y2]
                confidence = getattr(bbox_obj, 'confidence', 0.5)
                label = getattr(bbox_obj, 'label', 'text')

                regions.append(Region(
                    id=i + 1,
                    type=label,
                    confidence=float(confidence),
                    bbox={
                        "x1": int(bbox[0]),
                        "y1": int(bbox[1]),
                        "x2": int(bbox[2]),
                        "y2": int(bbox[3])
                    }
                ))

        # Sort by y-coordinate then x-coordinate
        regions.sort(key=lambda r: (r.bbox["y1"], r.bbox["x1"]))

        # Re-assign IDs after sorting
        for i, region in enumerate(regions):
            region.id = i + 1

        return regions
