"""作答记录与笔记的响应体。"""

from datetime import datetime
from typing import List, Optional

from pydantic import Field

from app.schemas.base import CamelModel

# 笔记正文上限，防止把超大文本塞进 SQLite
MAX_NOTE_LENGTH = 20_000


class NotePayload(CamelModel):
    """保存笔记。

    ``cause`` 与 ``content`` 都是必填：空字符串表示“清空”，
    缺失字段不会被当成“保持不变”，避免清空操作被静默忽略。
    """

    cause: str = Field(max_length=MAX_NOTE_LENGTH)
    content: str = Field(max_length=MAX_NOTE_LENGTH)


class NoteOut(CamelModel):
    cause: str = ""
    content: str = ""
    # 从未保存过时为 None，便于前端区分“空笔记”和“没写过”
    updated_at: Optional[datetime] = None

    @classmethod
    def from_note(cls, note: object) -> "NoteOut":
        if note is None:
            return cls()
        return cls(
            cause=note.cause or "",
            content=note.content or "",
            updated_at=note.updated_at,
        )


class CourseOut(CamelModel):
    id: str
    name: str


class RecordOut(CamelModel):
    id: str
    course_id: str
    course_name: Optional[str] = None
    assignment_id: str
    assignment_title: Optional[str] = None
    question_id: str
    question_type: str

    question_text: str
    question_format: str

    original_answer: str
    answer_format: str

    score: float
    max_score: float
    # None 表示来源未公开评语，前端显示“暂无评语”，不生成内容
    feedback: Optional[str] = None
    grading_source: str
    # 空数组表示来源未标注知识点，前端显示“未标注”
    knowledge_points: List[str] = []

    note: NoteOut = NoteOut()

    @classmethod
    def from_record(cls, record: object) -> "RecordOut":
        return cls(
            id=record.id,
            course_id=record.course_id,
            course_name=record.course.name if record.course else None,
            assignment_id=record.assignment_id,
            assignment_title=record.assignment.title if record.assignment else None,
            question_id=record.question_id,
            question_type=record.question_type,
            question_text=record.question_text,
            question_format=record.question_format,
            original_answer=record.original_answer,
            answer_format=record.answer_format,
            score=record.score,
            max_score=record.max_score,
            feedback=record.feedback,
            grading_source=record.grading_source,
            knowledge_points=list(record.knowledge_points or []),
            note=NoteOut.from_note(record.note),
        )


class RecordListOut(CamelModel):
    records: List[RecordOut]
    total: int
