"""
Base class for OCR engines.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
from PIL import Image

from ..layout.base import Region


@dataclass
class TextLine:
    """A detected text line within a region."""
    text: str
    confidence: float
    bbox_in_region: Dict[str, int]


@dataclass
class OCRResult:
    """OCR result for a single region."""
    region_id: int
    full_text: str
    lines: List[TextLine]


class OCREngineBase(ABC):
    """
    Abstract base class for OCR engines.

    To add a new OCR engine:
    1. Create a new file in this directory
    2. Create a class that inherits from OCREngineBase
    3. Implement the `name` property and `extract_text` method
    4. Register it in __init__.py
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the OCR engine."""
        pass

    @abstractmethod
    def extract_text(
        self,
        image: Image.Image,
        regions: List[Region]
    ) -> List[OCRResult]:
        """
        Extract text from regions in an image.

        Args:
            image: PIL Image object
            regions: List of Region objects from layout detection

        Returns:
            List of OCRResult objects
        """
        pass

    def extract_from_region(
        self,
        image: Image.Image,
        region: Region
    ) -> OCRResult:
        """
        Extract text from a single region.

        Args:
            image: PIL Image object
            region: Region object

        Returns:
            OCRResult object
        """
        bbox = region.bbox
        cropped = image.crop((
            bbox["x1"],
            bbox["y1"],
            bbox["x2"],
            bbox["y2"]
        ))
        return self._process_cropped_image(cropped, region.id)

    @abstractmethod
    def _process_cropped_image(
        self,
        image: Image.Image,
        region_id: int
    ) -> OCRResult:
        """
        Process a cropped image and extract text.

        Args:
            image: Cropped PIL Image
            region_id: ID of the region

        Returns:
            OCRResult object
        """
        pass

    def to_dict(self, results: List[OCRResult]) -> Dict[str, Any]:
        """Convert OCR results to dictionary format."""
        return {
            "library": self.name,
            "num_regions": len(results),
            "regions": [
                {
                    "region_id": r.region_id,
                    "full_text": r.full_text,
                    "lines": [
                        {
                            "text": line.text,
                            "confidence": line.confidence,
                            "bbox_in_region": line.bbox_in_region,
                        }
                        for line in r.lines
                    ]
                }
                for r in results
            ]
        }
