"""学生自己填写的错因与复习笔记。

每个 ``record_id`` 最多一行；空字符串表示“已清空”，与“未修改”区分开，
因此保存空串必须真的落库为 ``''``，而不是被当作缺省值跳过。
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utcnow

if TYPE_CHECKING:  # pragma: no cover
    from app.models.record import Record
    from app.models.student import Student


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[str] = mapped_column(
        ForeignKey("records.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    student_id: Mapped[str] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # 错因
    cause: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # 复习笔记
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )

    record: Mapped["Record"] = relationship(back_populates="note")
    student: Mapped["Student"] = relationship(back_populates="notes")

    @property
    def is_empty(self) -> bool:
        return not self.cause and not self.content
