"""声明式基类与统一的约束命名规则。"""

from datetime import datetime, timezone

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


def utcnow() -> datetime:
    """当前 UTC 时间（朴素值）。

    SQLite 不保存时区，混用 aware/naive 比较会抛 TypeError，
    因此全库统一使用朴素 UTC。
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
