"""数据模型。

导入本包即注册全部映射，``init_db()`` 与元数据都依赖这一点。
"""

from app.models.assignment import Assignment
from app.models.auth_session import AuthSession
from app.models.course import Course
from app.models.note import Note
from app.models.record import Record
from app.models.student import Student

__all__ = [
    "Assignment",
    "AuthSession",
    "Course",
    "Note",
    "Record",
    "Student",
]
