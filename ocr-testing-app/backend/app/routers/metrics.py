"""
Metrics and analytics routes.
"""
import io
import csv
from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List

from app.auth.dependencies import get_current_user_id
from app.services.firestore import FirestoreService

router = APIRouter()


@router.get("/aggregate")
async def get_aggregate_metrics(
    current_user_id: str = Depends(get_current_user_id)
):
    """Get aggregate metrics across all test runs."""
    firestore = FirestoreService()

    # Get all test runs
    test_runs = await firestore.list_test_runs()

    if not test_runs:
        return {
            "total_test_runs": 0,
            "total_documents_processed": 0,
            "average_accuracy": 0.0,
            "by_layout_library": {},
            "by_ocr_library": {}
        }

    # Collect all results
    all_results = []
    layout_results = {}
    ocr_results = {}

    for test_run in test_runs:
        if test_run.status.value != "completed":
            continue

        results = await firestore.get_results_by_test_run(test_run.id)
        all_results.extend(results)

        # Aggregate by layout library
        if test_run.layout_library not in layout_results:
            layout_results[test_run.layout_library] = {
                "count": 0,
                "total_accuracy": 0.0
            }
        layout_results[test_run.layout_library]["count"] += len(results)
        layout_results[test_run.layout_library]["total_accuracy"] += sum(
            [r.overall_accuracy for r in results]
        )

        # Aggregate by OCR library
        if test_run.ocr_library not in ocr_results:
            ocr_results[test_run.ocr_library] = {
                "count": 0,
                "total_accuracy": 0.0
            }
        ocr_results[test_run.ocr_library]["count"] += len(results)
        ocr_results[test_run.ocr_library]["total_accuracy"] += sum(
            [r.overall_accuracy for r in results]
        )

    # Calculate averages
    total_accuracy = sum([r.overall_accuracy for r in all_results])
    avg_accuracy = total_accuracy / len(all_results) if all_results else 0.0

    by_layout = {
        lib: round(data["total_accuracy"] / data["count"], 4)
        for lib, data in layout_results.items()
        if data["count"] > 0
    }

    by_ocr = {
        lib: round(data["total_accuracy"] / data["count"], 4)
        for lib, data in ocr_results.items()
        if data["count"] > 0
    }

    return {
        "total_test_runs": len([tr for tr in test_runs if tr.status.value == "completed"]),
        "total_documents_processed": len(all_results),
        "average_accuracy": round(avg_accuracy, 4),
        "by_layout_library": by_layout,
        "by_ocr_library": by_ocr
    }


@router.get("/by-field")
async def get_field_metrics(
    current_user_id: str = Depends(get_current_user_id)
):
    """Get per-field accuracy breakdown across all test runs."""
    firestore = FirestoreService()

    # Get all completed test runs
    test_runs = await firestore.list_test_runs()

    field_scores = {}
    field_counts = {}

    for test_run in test_runs:
        if test_run.status.value != "completed":
            continue

        results = await firestore.get_results_by_test_run(test_run.id)

        for result in results:
            for field in result.extracted_fields:
                if field.field_name not in field_scores:
                    field_scores[field.field_name] = 0.0
                    field_counts[field.field_name] = 0

                field_scores[field.field_name] += field.match_score
                field_counts[field.field_name] += 1

    # Calculate averages
    field_accuracies = {}
    for name in field_scores:
        if field_counts[name] > 0:
            field_accuracies[name] = {
                "average_accuracy": round(
                    field_scores[name] / field_counts[name], 4
                ),
                "sample_count": field_counts[name]
            }

    # Sort by accuracy (worst first for easy identification of problem fields)
    sorted_fields = dict(sorted(
        field_accuracies.items(),
        key=lambda x: x[1]["average_accuracy"]
    ))

    return {
        "fields": sorted_fields,
        "total_fields": len(sorted_fields)
    }


@router.get("/comparison")
async def get_comparison_metrics(
    test_run_ids: List[str] = Query(...),
    current_user_id: str = Depends(get_current_user_id)
):
    """Compare metrics across specific test runs."""
    firestore = FirestoreService()

    comparisons = []

    for test_run_id in test_run_ids:
        test_run = await firestore.get_test_run_by_id(test_run_id)
        if not test_run:
            continue

        results = await firestore.get_results_by_test_run(test_run_id)

        if not results:
            continue

        # Calculate metrics
        avg_accuracy = sum([r.overall_accuracy for r in results]) / len(results)

        # Per-field accuracy
        field_scores = {}
        field_counts = {}

        for result in results:
            for field in result.extracted_fields:
                if field.field_name not in field_scores:
                    field_scores[field.field_name] = 0.0
                    field_counts[field.field_name] = 0

                field_scores[field.field_name] += field.match_score
                field_counts[field.field_name] += 1

        field_accuracies = {
            name: round(field_scores[name] / field_counts[name], 4)
            for name in field_scores
            if field_counts[name] > 0
        }

        comparisons.append({
            "test_run_id": test_run_id,
            "layout_library": test_run.layout_library,
            "ocr_library": test_run.ocr_library,
            "document_count": len(results),
            "average_accuracy": round(avg_accuracy, 4),
            "field_accuracies": field_accuracies,
            "started_at": test_run.started_at.isoformat()
        })

    return {"comparisons": comparisons}


@router.get("/export")
async def export_metrics(
    format: str = Query("csv", regex="^(csv|json)$"),
    test_run_id: Optional[str] = Query(None),
    current_user_id: str = Depends(get_current_user_id)
):
    """Export metrics data as CSV or JSON."""
    firestore = FirestoreService()

    if test_run_id:
        test_runs = [await firestore.get_test_run_by_id(test_run_id)]
        test_runs = [tr for tr in test_runs if tr is not None]
    else:
        test_runs = await firestore.list_test_runs()
        test_runs = [tr for tr in test_runs if tr.status.value == "completed"]

    # Collect data for export
    export_data = []

    for test_run in test_runs:
        results = await firestore.get_results_by_test_run(test_run.id)

        for result in results:
            for field in result.extracted_fields:
                export_data.append({
                    "test_run_id": test_run.id,
                    "layout_library": test_run.layout_library,
                    "ocr_library": test_run.ocr_library,
                    "document_id": result.document_id,
                    "field_name": field.field_name,
                    "expected_value": field.expected_value,
                    "extracted_value": field.extracted_value,
                    "confidence": field.confidence,
                    "match_score": field.match_score,
                    "overall_accuracy": result.overall_accuracy
                })

    if format == "json":
        return {"data": export_data}

    # CSV export
    if not export_data:
        return StreamingResponse(
            io.StringIO("No data"),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=metrics.csv"}
        )

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
    writer.writeheader()
    writer.writerows(export_data)

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=metrics.csv"}
    )
