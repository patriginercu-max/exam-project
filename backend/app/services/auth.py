"""登录会话服务。身份只由服务端会话决定。"""

from datetime import timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import utcnow
from app.models import AuthSession, Student
from app.security import new_session_token, verify_password

# 存活会话的 last_seen_at 最长延后多久才回写，避免每个请求都写库
_TOUCH_INTERVAL = timedelta(minutes=5)


def authenticate(db: Session, login: str, password: str) -> Optional[Student]:
    student = db.scalar(select(Student).where(Student.login == login))
    if student is None or not verify_password(password, student.password_hash):
        return None
    return student


def create_session(db: Session, student: Student) -> AuthSession:
    session = AuthSession(
        id=new_session_token(),
        student_id=student.id,
        expires_at=utcnow() + timedelta(hours=settings.session_ttl_hours),
    )
    db.add(session)
    db.commit()
    return session


def resolve_student(db: Session, token: Optional[str]) -> Optional[Student]:
    """把不透明令牌换成学生；过期会话顺带清理。"""
    if not token:
        return None

    session = db.get(AuthSession, token)
    if session is None:
        return None

    now = utcnow()
    if session.expires_at <= now:
        db.delete(session)
        db.commit()
        return None

    student = db.get(Student, session.student_id)
    if student is None:
        db.delete(session)
        db.commit()
        return None

    if now - session.last_seen_at > _TOUCH_INTERVAL:
        session.last_seen_at = now
        db.commit()

    return student


def revoke_session(db: Session, token: Optional[str]) -> None:
    if not token:
        return
    session = db.get(AuthSession, token)
    if session is not None:
        db.delete(session)
        db.commit()
