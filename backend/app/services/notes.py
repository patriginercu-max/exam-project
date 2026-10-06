"""错因与复习笔记的读写。

保存与清空都先做一次归属校验，因此对他人记录的笔记操作会得到 403。
"""

from sqlalchemy.orm import Session

from app.models import Note, Student
from app.services.records import get_record_for_student


def save_note(
    db: Session,
    student: Student,
    record_id: str,
    cause: str,
    content: str,
) -> Note:
    """新增或修改笔记；两个字段都为空字符串时即为清空。"""
    record = get_record_for_student(db, student, record_id)

    note = record.note
    if note is None:
        note = Note(record_id=record.id, student_id=student.id, cause="", content="")
        db.add(note)

    note.cause = cause
    note.content = content
    db.commit()
    db.refresh(note)
    return note


def clear_note(db: Session, student: Student, record_id: str) -> Note:
    """清空笔记；本来就为空时同样返回一条空笔记，接口保持幂等。"""
    return save_note(db, student, record_id, "", "")
