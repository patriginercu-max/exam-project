"""错题筛选、详情与笔记接口。"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_student
from app.db.session import get_db
from app.models import Student
from app.schemas.record import (
    CourseOut,
    NoteOut,
    NotePayload,
    RecordListOut,
    RecordOut,
)
from app.services import notes as note_service
from app.services import records as record_service

router = APIRouter(prefix="/api", tags=["records"])


@router.get("/courses", response_model=List[CourseOut])
def list_courses(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> List[CourseOut]:
    return [
        CourseOut.model_validate(course)
        for course in record_service.list_courses(db, student)
    ]


@router.get("/knowledge-points", response_model=List[str])
def list_knowledge_points(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> List[str]:
    return record_service.list_knowledge_points(db, student)


@router.get("/records", response_model=RecordListOut)
def list_records(
    course_id: Optional[str] = Query(default=None, alias="courseId"),
    knowledge_point: Optional[str] = Query(default=None, alias="knowledgePoint"),
    keyword: Optional[str] = Query(default=None),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> RecordListOut:
    records = record_service.list_records(
        db,
        student,
        course_id=course_id,
        knowledge_point=knowledge_point,
        keyword=keyword,
    )
    return RecordListOut(
        records=[RecordOut.from_record(record) for record in records],
        total=len(records),
    )


@router.get("/records/{record_id}", response_model=RecordOut)
def get_record(
    record_id: str,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> RecordOut:
    record = record_service.get_record_for_student(db, student, record_id)
    return RecordOut.from_record(record)


@router.put("/records/{record_id}/note", response_model=NoteOut)
def save_note(
    record_id: str,
    payload: NotePayload,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> NoteOut:
    note = note_service.save_note(db, student, record_id, payload.cause, payload.content)
    return NoteOut.from_note(note)


@router.delete("/records/{record_id}/note", response_model=NoteOut)
def clear_note(
    record_id: str,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> NoteOut:
    note = note_service.clear_note(db, student, record_id)
    return NoteOut.from_note(note)
