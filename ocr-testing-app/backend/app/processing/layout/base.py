"""
Base class for layout detectors.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
from PIL import Image


@dataclass
class Region:
    """A detected region in the document."""
    id: int
    type: str
    confidence: float
    bbox: Dict[str, int]  # {"x1": int, "y1": int, "x2": int, "y2": int}


class LayoutDetectorBase(ABC):
    """
    Abstract base class for layout detectors.

    To add a new layout detector:
    1. Create a new file in this directory
    2. Create a class that inherits from LayoutDetectorBase
    3. Implement the `name` property and `detect` method
    4. Register it in __init__.py
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the layout detector."""
        pass

    @abstractmethod
    def detect(self, image: Image.Image) -> List[Region]:
        """
        Detect layout regions in an image.

        Args:
            image: PIL Image object

        Returns:
            List of Region objects
        """
        pass

    def to_dict(self, regions: List[Region]) -> Dict[str, Any]:
        """Convert regions to dictionary format."""
        return {
            "library": self.name,
            "num_regions": len(regions),
            "regions": [
                {
                    "id": r.id,
                    "type": r.type,
                    "confidence": r.confidence,
                    "bbox": r.bbox,
                }
                for r in regions
            ]
        }
