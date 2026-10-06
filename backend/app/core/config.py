"""应用配置。

所有配置项都有可用默认值，因此本地不写任何环境文件也能直接跑；
Docker 通过环境变量覆盖数据库与数据集路径。
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

# .../backend
BACKEND_DIR = Path(__file__).resolve().parents[2]
# 仓库根目录，同时是随包提供的数据包所在位置
PROJECT_ROOT = BACKEND_DIR.parent

DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:8080,http://127.0.0.1:8080"
)

# 数据集查找顺序：仓库内的原始包 -> 后端目录 -> 容器挂载点
_DATASET_CANDIDATES = (
    PROJECT_ROOT / "wrong-answers-20" / "dataset.json",
    BACKEND_DIR / "dataset.json",
    Path("/data/dataset.json"),
)


def _env(name: str) -> Optional[str]:
    raw = os.environ.get(name)
    if raw is None:
        return None
    raw = raw.strip()
    return raw or None


def _env_int(name: str, default: int) -> int:
    raw = _env(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        raise ValueError("{} must be an integer, got {!r}".format(name, raw))


def _env_bool(name: str, default: bool) -> bool:
    raw = _env(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    database_url: str
    dataset_path: Path
    session_ttl_hours: int
    cors_origins: Tuple[str, ...]
    cookie_name: str
    cookie_secure: bool


def _default_database_url() -> str:
    return "sqlite:///" + (BACKEND_DIR / "data" / "app.db").as_posix()


def _default_dataset_path() -> Path:
    for candidate in _DATASET_CANDIDATES:
        if candidate.is_file():
            return candidate
    return _DATASET_CANDIDATES[0]


def load_settings() -> Settings:
    dataset_env = _env("DATASET_PATH")
    raw_origins = _env("CORS_ORIGINS") or DEFAULT_CORS_ORIGINS
    origins = tuple(part.strip() for part in raw_origins.split(",") if part.strip())

    return Settings(
        database_url=_env("DATABASE_URL") or _default_database_url(),
        dataset_path=Path(dataset_env) if dataset_env else _default_dataset_path(),
        session_ttl_hours=_env_int("SESSION_TTL_HOURS", 48),
        cors_origins=origins,
        cookie_name=_env("SESSION_COOKIE_NAME") or "wa_session",
        cookie_secure=_env_bool("SESSION_COOKIE_SECURE", False),
    )


settings = load_settings()
