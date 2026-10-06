"""FastAPI 依赖。"""

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import UnauthorizedError
from app.db.session import get_db
from app.models import Student
from app.services import auth as auth_service


def get_current_student(
    request: Request,
    db: Session = Depends(get_db),
) -> Student:
    """从会话 cookie 解析当前学生。

    客户端提交的任何 studentId 都不参与判定，权限只来自服务端会话。
    """
    student = auth_service.resolve_student(db, request.cookies.get(settings.cookie_name))
    if student is None:
        raise UnauthorizedError()
    return student
