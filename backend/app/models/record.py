"""历史失分作答记录。"""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, CheckConstraint, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:  # pragma: no cover
    from app.models.assignment import Assignment
    from app.models.course import Course
    from app.models.note import Note
    from app.models.student import Student


class Record(Base):
    """一条作答记录。

    ``student_id`` 唯一决定谁可以访问这条记录；
    原始作答（``original_answer``）与公开评语（``feedback``）是只读来源数据，
    学生的错因与笔记存放在 ``notes`` 表，互不覆盖。
    """

    __tablename__ = "records"
    __table_args__ = (
        CheckConstraint("score >= 0", name="score_non_negative"),
        CheckConstraint("max_score > 0", name="max_score_positive"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    student_id: Mapped[str] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assignment_id: Mapped[str] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    question_type: Mapped[str] = mapped_column(String(32), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_format: Mapped[str] = mapped_column(
        String(32), nullable=False, default="markdown_latex"
    )

    original_answer: Mapped[str] = mapped_column(Text, nullable=False)
    answer_format: Mapped[str] = mapped_column(String(32), nullable=False)

    score: Mapped[float] = mapped_column(Float, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, nullable=False)

    # None 表示来源未公开评语，界面显示“暂无评语”，不生成内容
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    grading_source: Mapped[str] = mapped_column(String(16), nullable=False)

    # 空数组表示来源未标注知识点，界面显示“未标注”
    knowledge_points: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)

    initial_note: Mapped[str] = mapped_column(Text, nullable=False, default="")

    student: Mapped["Student"] = relationship(back_populates="records")
    course: Mapped["Course"] = relationship(back_populates="records")
    assignment: Mapped["Assignment"] = relationship(back_populates="records")
    note: Mapped[Optional["Note"]] = relationship(
        back_populates="record",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return "<Record {} student={}>".format(self.id, self.student_id)
