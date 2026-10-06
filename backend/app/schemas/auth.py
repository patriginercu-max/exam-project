"""登录相关的请求/响应体。"""

from app.schemas.base import CamelModel


class LoginRequest(CamelModel):
    login: str
    password: str


class StudentOut(CamelModel):
    id: str
    name: str
    login: str
    role: str


class LoginResponse(CamelModel):
    student: StudentOut
