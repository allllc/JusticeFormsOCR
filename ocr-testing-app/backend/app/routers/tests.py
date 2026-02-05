"""
Test execution routes.
"""
import asyncio
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks

from app.auth.dependencies import get_current_user_id
from app.models.test_run import (
    TestRunResponse,
    TestRunListResponse,
    RunTestsRequest,
    TestStatus,
)
from app.services.firestore import FirestoreService
from app.services.ocr_pipeline import OCRPipelineService
from app.processing.layout import list_layout_detectors
from app.processing.ocr import list_ocr_engines

router = APIRouter()


async def run_test_background(
    test_run_id: str,
    batch_ids: list[str],
    layout_library: str,
    ocr_library: str
):
    """Background task to run OCR pipeline on batches."""
    firestore = FirestoreService()
    pipeline = OCRPipelineService()

    try:
        # Update status to running
        await firestore.update_test_run_status(
            test_run_id,
            TestStatus.RUNNING
        )

        total_processed = 0

        for batch_id in batch_ids:
            batch = await firestore.get_batch_by_id(batch_id)
            if not batch:
                continue

            # Process batch
            await pipeline.process_batch(
                batch=batch,
                layout_library=layout_library,
                ocr_library=ocr_library,
                test_run_id=test_run_id,
                progress_callback=lambda curr, total: firestore.update_test_run_status(
                    test_run_id,
                    TestStatus.RUNNING,
                    processed_documents=total_processed + curr
                )
            )

            total_processed += len(batch.documents)

        # Update status to completed
        await firestore.update_test_run_status(
            test_run_id,
            TestStatus.COMPLETED,
            processed_documents=total_processed
        )

    except Exception as e:
        # Update status to failed
        await firestore.update_test_run_status(
            test_run_id,
            TestStatus.FAILED,
            error_message=str(e)
        )


@router.post("/run", response_model=TestRunResponse)
async def run_tests(
    request: RunTestsRequest,
    background_tasks: BackgroundTasks,
    current_user_id: str = Depends(get_current_user_id)
):
    """Start a test run on selected batches."""
    firestore = FirestoreService()

    # Check if any batch is handwritten (skip layout validation for those)
    has_handwritten = False
    has_synthetic = False
    total_documents = 0

    for batch_id in request.batch_ids:
        batch = await firestore.get_batch_by_id(batch_id)
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch not found: {batch_id}"
            )
        total_documents += len(batch.documents)
        if getattr(batch, "batch_type", "synthetic") == "handwritten":
            has_handwritten = True
        else:
            has_synthetic = True

    # Validate layout library only if there are synthetic batches
    if has_synthetic:
        available_layouts = list_layout_detectors()
        if request.layout_library not in available_layouts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid layout library. Available: {available_layouts}"
            )

    # Validate OCR library
    available_ocrs = list_ocr_engines()
    if request.ocr_library not in available_ocrs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OCR library. Available: {available_ocrs}"
        )

    if total_documents == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected batches contain no documents"
        )

    # Default layout_library for handwritten-only runs
    layout_library = request.layout_library
    if not layout_library and has_handwritten and not has_synthetic:
        layout_library = "none"

    # Look up user email
    user = await firestore.get_user_by_id(current_user_id)
    started_by_name = user.email if user else ""

    # Create test run record
    test_run = await firestore.create_test_run(
        batch_ids=request.batch_ids,
        layout_library=layout_library,
        ocr_library=request.ocr_library,
        started_by=current_user_id,
        total_documents=total_documents,
        started_by_name=started_by_name,
    )

    # Start background processing
    background_tasks.add_task(
        run_test_background,
        test_run.id,
        request.batch_ids,
        layout_library,
        request.ocr_library
    )

    return TestRunResponse(**test_run.model_dump())


@router.get("", response_model=TestRunListResponse)
async def list_test_runs(current_user_id: str = Depends(get_current_user_id)):
    """List all test runs."""
    firestore = FirestoreService()
    test_runs = await firestore.list_test_runs()

    return TestRunListResponse(
        test_runs=[TestRunResponse(**tr.model_dump()) for tr in test_runs],
        total=len(test_runs)
    )


@router.get("/{test_run_id}", response_model=TestRunResponse)
async def get_test_run(
    test_run_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get test run details by ID."""
    firestore = FirestoreService()
    test_run = await firestore.get_test_run_by_id(test_run_id)

    if not test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test run not found"
        )

    return TestRunResponse(**test_run.model_dump())


@router.get("/{test_run_id}/status")
async def get_test_run_status(
    test_run_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get test run status (for polling during processing)."""
    firestore = FirestoreService()
    test_run = await firestore.get_test_run_by_id(test_run_id)

    if not test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test run not found"
        )

    return {
        "id": test_run.id,
        "status": test_run.status.value,
        "processed_documents": test_run.processed_documents,
        "total_documents": test_run.total_documents,
        "progress_percent": (
            (test_run.processed_documents / test_run.total_documents * 100)
            if test_run.total_documents > 0 else 0
        ),
        "error_message": test_run.error_message
    }


@router.post("/{test_run_id}/cancel")
async def cancel_test_run(
    test_run_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Cancel/reset a stuck test run."""
    firestore = FirestoreService()
    test_run = await firestore.get_test_run_by_id(test_run_id)

    if not test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test run not found"
        )

    if test_run.status not in [TestStatus.RUNNING, TestStatus.PENDING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Test run is already {test_run.status.value}"
        )

    await firestore.update_test_run_status(
        test_run_id,
        TestStatus.FAILED,
        error_message="Cancelled by user"
    )

    return {"message": "Test run cancelled", "id": test_run_id}


@router.get("/options/libraries")
async def get_available_libraries(
    current_user_id: str = Depends(get_current_user_id)
):
    """Get available layout and OCR libraries."""
    return {
        "layout_libraries": list_layout_detectors(),
        "ocr_libraries": list_ocr_engines()
    }
