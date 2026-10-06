"""FastAPI 应用入口。"""

from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.routes import auth as auth_routes
from app.api.routes import records as record_routes
from app.core.config import settings
from app.core.errors import ApiError
from app.db.session import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="错题整理与个人笔记", version=__version__, lifespan=lifespan)

    # 带凭据的跨域必须显式列出源，不能用通配符
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ApiError)
    async def _api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": exc.code},
        )

    @app.get("/api/health")
    def health() -> Dict[str, str]:
        return {"status": "ok", "version": __version__}

    app.include_router(auth_routes.router)
    app.include_router(record_routes.router)
    return app


app = create_app()
