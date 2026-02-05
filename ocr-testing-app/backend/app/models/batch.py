"""
Batch (synthetic data) data models.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class SyntheticDocument(BaseModel):
    """A single synthetic document in a batch."""
    id: str
    storage_path: str
    field_values: Dict[str, str]
    is_skewed: bool = False


class BatchBase(BaseModel):
    """Base batch model."""
    form_id: str


class BatchCreate(BaseModel):
    """Model for creating a new batch."""
    form_id: str
    count: int
    field_value_options: Optional[Dict[str, List[str]]] = None


class BatchInDB(BatchBase):
    """Batch model as stored in database."""
    id: str
    batch_number: str
    batch_type: str = "synthetic"
    form_id: str
    form_name: str
    created_by: str
    created_by_name: str = ""
    created_at: datetime
    count: int
    skew_preset: Optional[str] = None
    documents: List[SyntheticDocument] = []


class BatchResponse(BatchInDB):
    """Batch model for API responses."""
    pass


class BatchListResponse(BaseModel):
    """Response for listing batches."""
    batches: List[BatchResponse]
    total: int


class GenerateBatchRequest(BaseModel):
    """Request to generate a synthetic batch."""
    form_id: str
    count: int = 10
    field_value_options: Optional[Dict[str, List[str]]] = None
    skew_preset: Optional[str] = None
