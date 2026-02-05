"""
Test run data models.
"""
from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel


class TestStatus(str, Enum):
    """Test run status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TestRunBase(BaseModel):
    """Base test run model."""
    batch_ids: List[str]
    layout_library: str = ""
    ocr_library: str


class TestRunCreate(TestRunBase):
    """Model for creating a new test run."""
    pass


class TestRunInDB(TestRunBase):
    """Test run model as stored in database."""
    id: str
    started_by: str
    started_by_name: str = ""
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: TestStatus = TestStatus.PENDING
    error_message: Optional[str] = None
    total_documents: int = 0
    processed_documents: int = 0


class TestRunResponse(TestRunInDB):
    """Test run model for API responses."""
    pass


class TestRunListResponse(BaseModel):
    """Response for listing test runs."""
    test_runs: List[TestRunResponse]
    total: int


class RunTestsRequest(BaseModel):
    """Request to run tests on batches."""
    batch_ids: List[str]
    layout_library: str = ""
    ocr_library: str
