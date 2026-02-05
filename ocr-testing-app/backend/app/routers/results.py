"""
Results viewing routes.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from fastapi.responses import Response
from typing import Optional, List

from app.auth.dependencies import get_current_user_id
from app.models.result import ResultResponse, ResultListResponse, DocumentResult
from app.services.firestore import FirestoreService
from app.services.storage import StorageService

router = APIRouter()


@router.get("", response_model=ResultListResponse)
async def list_results(
    test_run_id: Optional[str] = Query(None),
    batch_id: Optional[str] = Query(None),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    List results with optional filtering.
    Filter by test_run_id and/or batch_id.
    """
    firestore = FirestoreService()

    if test_run_id:
        # Get results for specific test run
        results = await firestore.get_results_by_test_run(test_run_id)

        # Filter by batch_id if provided
        if batch_id:
            results = [r for r in results if r.batch_id == batch_id]
    else:
        # Without test_run_id, we'd need to implement a more general query
        # For now, return empty if no test_run_id
        results = []

    return ResultListResponse(
        results=[ResultResponse(**r.model_dump()) for r in results],
        total=len(results)
    )


@router.get("/{test_run_id}", response_model=ResultListResponse)
async def get_results_for_test_run(
    test_run_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get all results for a specific test run."""
    firestore = FirestoreService()

    # Verify test run exists
    test_run = await firestore.get_test_run_by_id(test_run_id)
    if not test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test run not found"
        )

    results = await firestore.get_results_by_test_run(test_run_id)

    return ResultListResponse(
        results=[ResultResponse(**r.model_dump()) for r in results],
        total=len(results)
    )


@router.get("/{test_run_id}/document/{document_id}")
async def get_document_result(
    test_run_id: str,
    document_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get detailed result for a specific document."""
    firestore = FirestoreService()

    # Get result
    result = await firestore.get_result_by_document(test_run_id, document_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )

    # Get batch to find document storage path
    batch = await firestore.get_batch_by_id(result.batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )

    # Find document in batch
    document = None
    for doc in batch.documents:
        if doc.id == document_id:
            document = doc
            break

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in batch"
        )

    # Build proxy URL for the document image (avoids signed URL issues on Cloud Run)
    document_url = f"/api/results/{test_run_id}/document/{document_id}/image"

    return {
        "document_id": document_id,
        "document_url": document_url,
        "expected_field_values": document.field_values,
        "extracted_fields": [ef.model_dump() for ef in result.extracted_fields],
        "overall_accuracy": result.overall_accuracy,
        "verified_accuracy": result.verified_accuracy,
        "layout_results": result.layout_results,
        "ocr_results": result.ocr_results
    }


@router.get("/{test_run_id}/document/{document_id}/image")
async def get_document_image(
    test_run_id: str,
    document_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Proxy endpoint to serve document images directly from GCS."""
    firestore = FirestoreService()
    storage = StorageService()

    # Get result to find batch_id
    result = await firestore.get_result_by_document(test_run_id, document_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )

    # Get batch to find document storage path
    batch = await firestore.get_batch_by_id(result.batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )

    # Find document in batch
    document = None
    for doc in batch.documents:
        if doc.id == document_id:
            document = doc
            break

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in batch"
        )

    # Download image bytes from GCS and serve directly
    image_bytes = await storage.download_file(document.storage_path)
    return Response(content=image_bytes, media_type="image/png")


@router.get("/{test_run_id}/summary")
async def get_test_run_summary(
    test_run_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get summary statistics for a test run."""
    firestore = FirestoreService()

    # Get test run
    test_run = await firestore.get_test_run_by_id(test_run_id)
    if not test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test run not found"
        )

    # Get all results
    results = await firestore.get_results_by_test_run(test_run_id)

    if not results:
        return {
            "test_run_id": test_run_id,
            "total_documents": 0,
            "average_accuracy": 0.0,
            "field_accuracies": {},
            "accuracy_distribution": {}
        }

    # Calculate statistics - prefer verified_accuracy over overall_accuracy
    def best_accuracy(r):
        if r.verified_accuracy is not None:
            return r.verified_accuracy
        return r.overall_accuracy

    total_accuracy = sum(best_accuracy(r) for r in results)
    avg_accuracy = total_accuracy / len(results)

    # Per-field accuracy (only for important fields)
    field_scores = {}
    field_counts = {}

    for result in results:
        for field in result.extracted_fields:
            if not field.is_important:
                continue
            if field.field_name not in field_scores:
                field_scores[field.field_name] = 0.0
                field_counts[field.field_name] = 0

            field_scores[field.field_name] += field.match_score
            field_counts[field.field_name] += 1

    # Fallback: if no fields have is_important, use all fields (legacy data)
    if not field_scores:
        for result in results:
            for field in result.extracted_fields:
                if field.field_name not in field_scores:
                    field_scores[field.field_name] = 0.0
                    field_counts[field.field_name] = 0
                field_scores[field.field_name] += field.match_score
                field_counts[field.field_name] += 1

    field_accuracies = {
        name: field_scores[name] / field_counts[name]
        for name in field_scores
    }

    # Accuracy distribution (buckets)
    distribution = {
        "0-20%": 0,
        "20-40%": 0,
        "40-60%": 0,
        "60-80%": 0,
        "80-100%": 0
    }

    for result in results:
        acc = best_accuracy(result) * 100
        if acc < 20:
            distribution["0-20%"] += 1
        elif acc < 40:
            distribution["20-40%"] += 1
        elif acc < 60:
            distribution["40-60%"] += 1
        elif acc < 80:
            distribution["60-80%"] += 1
        else:
            distribution["80-100%"] += 1

    return {
        "test_run_id": test_run_id,
        "layout_library": test_run.layout_library,
        "ocr_library": test_run.ocr_library,
        "total_documents": len(results),
        "average_accuracy": round(avg_accuracy, 4),
        "field_accuracies": {k: round(v, 4) for k, v in field_accuracies.items()},
        "accuracy_distribution": distribution
    }
