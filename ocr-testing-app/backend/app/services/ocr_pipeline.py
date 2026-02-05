"""
OCR Pipeline service.
Orchestrates layout detection and OCR extraction.
"""
import io
from typing import List, Dict, Any, Optional
from PIL import Image
from difflib import SequenceMatcher

from app.models.batch import BatchInDB, SyntheticDocument
from app.models.result import ExtractedField
from app.services.storage import StorageService
from app.services.firestore import FirestoreService
from app.processing.layout import get_layout_detector, list_layout_detectors
from app.processing.ocr import get_ocr_engine, list_ocr_engines


class OCRPipelineService:
    """Service for running the OCR pipeline on documents."""

    def __init__(self):
        self.storage = StorageService()
        self.firestore = FirestoreService()

    async def process_document(
        self,
        document: SyntheticDocument,
        layout_library: str,
        ocr_library: str,
    ) -> Dict[str, Any]:
        """
        Process a single document through the pipeline.

        Args:
            document: The synthetic document to process
            layout_library: Name of layout detector to use
            ocr_library: Name of OCR engine to use

        Returns:
            Dictionary with layout_results, ocr_results, extracted_fields, accuracy
        """
        # Download document image
        image_bytes = await self.storage.download_file(document.storage_path)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Get layout detector and OCR engine
        layout_detector = get_layout_detector(layout_library)
        ocr_engine = get_ocr_engine(ocr_library)

        # Run layout detection
        regions = layout_detector.detect(image)
        layout_results = layout_detector.to_dict(regions)

        # Run OCR on detected regions
        ocr_results_list = ocr_engine.extract_text(image, regions)
        ocr_results = ocr_engine.to_dict(ocr_results_list)

        # Extract and match fields
        extracted_fields = self._match_fields(
            document.field_values,
            ocr_results_list
        )

        # Calculate overall accuracy
        overall_accuracy = self._calculate_accuracy(extracted_fields)

        return {
            "layout_results": layout_results,
            "ocr_results": ocr_results,
            "extracted_fields": extracted_fields,
            "overall_accuracy": overall_accuracy
        }

    def _match_fields(
        self,
        expected_values: Dict[str, str],
        ocr_results: List
    ) -> List[ExtractedField]:
        """
        Match OCR results to expected field values.

        Uses fuzzy string matching to find the best match for each expected field.
        """
        extracted_fields = []

        # Combine all OCR text
        all_text = " ".join([r.full_text for r in ocr_results])

        for field_name, expected_value in expected_values.items():
            # Find the best match in OCR text
            best_match = ""
            best_score = 0.0
            best_confidence = 0.0

            # Search in each OCR result
            for ocr_result in ocr_results:
                for line in ocr_result.lines:
                    # Calculate similarity
                    score = SequenceMatcher(
                        None,
                        expected_value.lower(),
                        line.text.lower()
                    ).ratio()

                    if score > best_score:
                        best_score = score
                        best_match = line.text
                        best_confidence = line.confidence

                # Also check full text
                score = SequenceMatcher(
                    None,
                    expected_value.lower(),
                    ocr_result.full_text.lower()
                ).ratio()

                if score > best_score:
                    best_score = score
                    best_match = ocr_result.full_text
                    best_confidence = sum(
                        [l.confidence for l in ocr_result.lines]
                    ) / max(len(ocr_result.lines), 1)

            extracted_fields.append(ExtractedField(
                field_name=field_name,
                expected_value=expected_value,
                extracted_value=best_match,
                confidence=best_confidence,
                match_score=best_score,
                is_important=True,
            ))

        return extracted_fields

    def _calculate_accuracy(self, extracted_fields: List[ExtractedField]) -> float:
        """Calculate overall accuracy from important extracted fields."""
        if not extracted_fields:
            return 0.0

        important = [f for f in extracted_fields if f.is_important]
        if not important:
            important = extracted_fields  # fallback for legacy data
        total_score = sum(f.match_score for f in important)
        return total_score / len(important)

    async def process_document_full_text(
        self,
        document: SyntheticDocument,
        ocr_library: str,
    ) -> Dict[str, Any]:
        """
        Process a document with full-text OCR (no layout detection).
        Used for handwritten forms where we don't have field coordinates.

        Args:
            document: The document to process
            ocr_library: Name of OCR engine to use

        Returns:
            Dictionary with ocr_results (including full_text and regions)
        """
        # Download document image
        image_bytes = await self.storage.download_file(document.storage_path)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Get OCR engine
        ocr_engine = get_ocr_engine(ocr_library)

        # Run OCR on the full image as a single region
        # Create a single region covering the entire image
        from app.processing.layout.base import Region
        full_region = Region(
            id=0,
            type="full_page",
            confidence=1.0,
            bbox={"x1": 0, "y1": 0, "x2": image.width, "y2": image.height},
        )

        ocr_results_list = ocr_engine.extract_text(image, [full_region])
        ocr_results = ocr_engine.to_dict(ocr_results_list)

        # Combine all text
        full_text = " ".join([r.full_text for r in ocr_results_list])
        ocr_results["full_text"] = full_text

        # Collect individual text regions
        regions = []
        for r in ocr_results_list:
            for line in r.lines:
                regions.append({
                    "text": line.text,
                    "confidence": line.confidence,
                })
        ocr_results["text_regions"] = regions

        return {
            "layout_results": {"regions": [], "method": "none (full-text OCR)"},
            "ocr_results": ocr_results,
            "extracted_fields": [],
            "overall_accuracy": 0.0,
        }

    async def process_batch(
        self,
        batch: BatchInDB,
        layout_library: str,
        ocr_library: str,
        test_run_id: str,
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Process all documents in a batch.

        Args:
            batch: The batch to process
            layout_library: Name of layout detector to use
            ocr_library: Name of OCR engine to use
            test_run_id: ID of the test run
            progress_callback: Optional callback for progress updates

        Returns:
            List of results for each document
        """
        results = []
        is_handwritten = getattr(batch, "batch_type", "synthetic") == "handwritten"

        for i, document in enumerate(batch.documents):
            # Process document based on batch type
            if is_handwritten:
                doc_results = await self.process_document_full_text(
                    document=document,
                    ocr_library=ocr_library,
                )
            else:
                doc_results = await self.process_document(
                    document=document,
                    layout_library=layout_library,
                    ocr_library=ocr_library
                )

            # Store result in Firestore
            await self.firestore.create_result(
                test_run_id=test_run_id,
                document_id=document.id,
                batch_id=batch.id,
                layout_results=doc_results["layout_results"],
                ocr_results=doc_results["ocr_results"],
                extracted_fields=doc_results["extracted_fields"],
                overall_accuracy=doc_results["overall_accuracy"]
            )

            results.append({
                "document_id": document.id,
                **doc_results
            })

            # Call progress callback if provided
            if progress_callback:
                await progress_callback(i + 1, len(batch.documents))

        return results
