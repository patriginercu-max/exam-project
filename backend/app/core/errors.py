"""领域异常。

服务层只抛这些异常，由 ``register_error_handlers`` 统一转换成 JSON 响应，
服务层因此不依赖 FastAPI 的 HTTPException。
"""

from typing import Optional


def _default_code(status_code: int) -> str:
    return {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        422: "invalid_payload",
    }.get(status_code, "error")


class ApiError(Exception):
    def __init__(self, status_code: int, detail: str, code: Optional[str] = None) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.code = code or _default_code(status_code)


class UnauthorizedError(ApiError):
    def __init__(self, detail: str = "未登录或会话已过期") -> None:
        super().__init__(401, detail)


class ForbiddenError(ApiError):
    """横向越权：资源存在但不属于当前登录学生。"""

    def __init__(self, detail: str = "无权访问他人的作答记录") -> None:
        super().__init__(403, detail)


class NotFoundError(ApiError):
    def __init__(self, detail: str = "资源不存在") -> None:
        super().__init__(404, detail)
