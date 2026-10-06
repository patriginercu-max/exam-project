"""作答记录查询。

所有查询都先按当前登录学生过滤；跨学生访问抛 403 而不是 404，
以免把“存在但不属于你”和“不存在”混为一谈。
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.errors import ForbiddenError, NotFoundError
from app.models import Course, Record, Student


def _escape_like(value: str) -> str:
    """转义 LIKE 通配符，关键词按字面量匹配。"""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _query_with_relations():
    return select(Record).options(
        joinedload(Record.course),
        joinedload(Record.assignment),
        joinedload(Record.note),
    )


def list_courses(db: Session, student: Student) -> List[Course]:
    """只返回当前学生有记录参与的课程。"""
    stmt = (
        select(Course)
        .join(Record, Record.course_id == Course.id)
        .where(Record.student_id == student.id)
        .distinct()
        .order_by(Course.id)
    )
    return list(db.scalars(stmt))


def list_knowledge_points(db: Session, student: Student) -> List[str]:
    stmt = select(Record.knowledge_points).where(Record.student_id == student.id)
    collected = set()
    for points in db.scalars(stmt):
        for point in points or []:
            collected.add(point)
    return sorted(collected)


def list_records(
    db: Session,
    student: Student,
    *,
    course_id: Optional[str] = None,
    knowledge_point: Optional[str] = None,
    keyword: Optional[str] = None,
) -> List[Record]:
    """先限定当前学生，再叠加各筛选条件（已填写的条件之间是 AND）。"""
    stmt = _query_with_relations().where(Record.student_id == student.id)

    if course_id:
        stmt = stmt.where(Record.course_id == course_id)
    if keyword:
        pattern = "%{}%".format(_escape_like(keyword))
        stmt = stmt.where(Record.question_text.like(pattern, escape="\\"))

    stmt = stmt.order_by(Record.id)
    records = list(db.scalars(stmt).unique())

    # knowledge_points 是 JSON 列，按元素筛选在 SQLite 上不便，
    # 且记录量很小，因此在这一层过滤。
    if knowledge_point:
        records = [
            record
            for record in records
            if knowledge_point in (record.knowledge_points or [])
        ]
    return records


def get_record_for_student(db: Session, student: Student, record_id: str) -> Record:
    record = db.scalar(_query_with_relations().where(Record.id == record_id))
    if record is None:
        raise NotFoundError("作答记录不存在")
    if record.student_id != student.id:
        raise ForbiddenError()
    return record
