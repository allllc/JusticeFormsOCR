"""
GOT-OCR2.0 engine implementation.

Uses stepfun-ai/GOT-OCR-2.0-hf - a unified end-to-end OCR model (580M params).
Handles plain text, formatted text, tables, formulas, etc.
Uses the HuggingFace transformers integration.
"""
from typing import List
from PIL import Image
import numpy as np

from .base import OCREngineBase, OCRResult, TextLine
from ..layout.base import Region


class GotOCREngine(OCREngineBase):
    """OCR engine using GOT-OCR2.0 (General OCR Theory)."""

    _processor = None
    _model = None

    @property
    def name(self) -> str:
        return "got_ocr"

    def _load_model(self):
        """Lazy load GOT-OCR2.0 model and processor."""
        if GotOCREngine._processor is None:
            import torch
            from transformers import AutoProcessor, AutoModelForImageTextToText

            model_name = "stepfun-ai/GOT-OCR-2.0-hf"

            GotOCREngine._processor = AutoProcessor.from_pretrained(
                model_name,
                use_fast=True,
            )
            GotOCREngine._model = AutoModelForImageTextToText.from_pretrained(
                model_name,
                device_map="cpu",
                torch_dtype=torch.float32,
            )
            GotOCREngine._model.eval()

        return GotOCREngine._processor, GotOCREngine._model

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
        """Process a cropped image with GOT-OCR2.0."""
        import torch

        processor, model = self._load_model()

        # Ensure RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Process image through GOT-OCR2.0
        inputs = processor(
            image,
            return_tensors="pt",
        ).to("cpu")

        with torch.no_grad():
            generate_ids = model.generate(
                **inputs,
                do_sample=False,
                tokenizer=processor.tokenizer,
                stop_strings="<|im_end|>",
                max_new_tokens=4096,
            )

        # Decode the generated text
        full_text = processor.decode(
            generate_ids[0, inputs["input_ids"].shape[1]:],
            skip_special_tokens=True
        ).strip()

        # GOT-OCR2.0 returns full text; split into lines
        lines = []
        if full_text:
            text_lines = full_text.split('\n')
            for i, line_text in enumerate(text_lines):
                line_text = line_text.strip()
                if not line_text:
                    continue

                lines.append(TextLine(
                    text=line_text,
                    confidence=0.95,  # GOT-OCR doesn't expose confidence scores
                    bbox_in_region={
                        "x1": 0,
                        "y1": 0,
                        "x2": image.width,
                        "y2": image.height,
                    }
                ))

        return OCRResult(
            region_id=region_id,
            full_text=full_text,
            lines=lines,
        )
