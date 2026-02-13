from pydantic import BaseModel, RootModel
from typing import Dict, Optional
from datetime import datetime


class StudentSchema(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None


class TestSchema(BaseModel):
    name: str
    max_marks: int
    negative_marking: Dict[str, int]
    answer_key: Optional[Dict[str, str]] = None


class AttemptEvent(BaseModel):
    source_event_id: str
    student: StudentSchema
    test: TestSchema
    started_at: str
    submitted_at: Optional[str]
    answers: Dict[str, str]


class AttemptBatch(RootModel[list[AttemptEvent]]):
    pass


class FlagRequest(BaseModel):
    reason: str