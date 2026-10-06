"""登录、登出与当前身份。"""

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_student
from app.core.config import settings
from app.core.errors import UnauthorizedError
from app.db.session import get_db
from app.models import Student
from app.schemas.auth import LoginRequest, LoginResponse, StudentOut
from app.services import auth as auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> LoginResponse:
    student = auth_service.authenticate(db, payload.login, payload.password)
    if student is None:
        # 不区分“账号不存在”和“密码错误”，避免账号枚举
        raise UnauthorizedError("登录名或密码不正确")

    session = auth_service.create_session(db, student)
    _set_session_cookie(response, session.id)
    return LoginResponse(student=StudentOut.model_validate(student))


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> None:
    auth_service.revoke_session(db, request.cookies.get(settings.cookie_name))
    response.delete_cookie(settings.cookie_name, path="/")


@router.get("/me", response_model=LoginResponse)
def me(student: Student = Depends(get_current_student)) -> LoginResponse:
    return LoginResponse(student=StudentOut.model_validate(student))
