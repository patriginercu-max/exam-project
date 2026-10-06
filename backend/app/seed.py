"""数据初始化导入脚本。

用法::

    python -m app.seed                    # 按 DATASET_PATH（默认自动探测）导入
    python -m app.seed --dataset <path>   # 指定数据包
    python -m app.seed --check-sums       # 只做 SHA-256 完整性校验

脚本按主键 upsert，可重复执行：第二次运行不会产生重复数据，
并且完全不触碰 ``notes`` 表，因此已保存的错因与笔记不会被初始化覆盖。
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal, init_db
from app.models import Assignment, Course, Note, Record, Student
from app.security import hash_password, verify_password

SUPPORTED_SCHEMA_VERSION = "1.0"

REQUIRED_TOP_LEVEL = ("schemaVersion", "students", "courses", "assignments", "records")

REQUIRED_RECORD_FIELDS = (
    "id",
    "studentId",
    "courseId",
    "assignmentId",
    "questionId",
    "questionType",
    "questionText",
    "questionFormat",
    "originalAnswer",
    "answerFormat",
    "score",
    "maxScore",
    "feedback",
    "gradingSource",
    "knowledgePoints",
    "initialNote",
)

ENTITY_MODELS = (
    ("students", Student),
    ("courses", Course),
    ("assignments", Assignment),
    ("records", Record),
    ("notes", Note),
)


class DatasetError(RuntimeError):
    """数据包缺失、结构不符或引用不一致。"""


def _require_unique(items: List[Dict[str, Any]], collection: str) -> None:
    seen = set()
    for item in items:
        identifier = item.get("id")
        if not identifier:
            raise DatasetError("{} 中存在缺少 id 的条目".format(collection))
        if identifier in seen:
            raise DatasetError("{} 中 id 重复: {}".format(collection, identifier))
        seen.add(identifier)


def validate_dataset(dataset: Any) -> None:
    if not isinstance(dataset, dict):
        raise DatasetError("数据集顶层必须是 JSON 对象")

    missing = [key for key in REQUIRED_TOP_LEVEL if key not in dataset]
    if missing:
        raise DatasetError("数据集缺少顶层字段: {}".format(", ".join(missing)))

    version = dataset.get("schemaVersion")
    if version != SUPPORTED_SCHEMA_VERSION:
        raise DatasetError(
            "不支持的 schemaVersion: {!r}（期望 {!r}）".format(version, SUPPORTED_SCHEMA_VERSION)
        )

    for collection in ("students", "courses", "assignments", "records"):
        if not isinstance(dataset[collection], list):
            raise DatasetError("{} 必须是数组".format(collection))
        _require_unique(dataset[collection], collection)

    for record in dataset["records"]:
        missing = [field for field in REQUIRED_RECORD_FIELDS if field not in record]
        if missing:
            raise DatasetError(
                "记录 {} 缺少字段: {}".format(record.get("id", "<无 id>"), ", ".join(missing))
            )
        if not isinstance(record["knowledgePoints"], list):
            raise DatasetError(
                "记录 {} 的 knowledgePoints 必须是数组".format(record["id"])
            )

    _validate_references(dataset)


def _validate_references(dataset: Dict[str, Any]) -> None:
    known = {
        "studentId": {item["id"] for item in dataset["students"]},
        "courseId": {item["id"] for item in dataset["courses"]},
        "assignmentId": {item["id"] for item in dataset["assignments"]},
    }
    for assignment in dataset["assignments"]:
        if assignment["courseId"] not in known["courseId"]:
            raise DatasetError(
                "作业 {} 指向不存在的课程: {}".format(assignment["id"], assignment["courseId"])
            )
    for record in dataset["records"]:
        for field, identifiers in known.items():
            if record[field] not in identifiers:
                raise DatasetError(
                    "记录 {} 的 {} 指向不存在的实体: {}".format(
                        record["id"], field, record[field]
                    )
                )


def load_dataset(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise DatasetError("数据集不存在: {}".format(path))
    try:
        dataset = json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise DatasetError("数据集不是 UTF-8 文本: {}".format(exc))
    except json.JSONDecodeError as exc:
        raise DatasetError("数据集不是合法 JSON: {}".format(exc))
    validate_dataset(dataset)
    return dataset


def verify_checksums(dataset_path: Path) -> List[Tuple[str, bool]]:
    """按同目录的 SHA256SUMS 校验数据包文件。没有该文件时返回空列表。"""
    sums_file = dataset_path.parent / "SHA256SUMS"
    if not sums_file.is_file():
        return []

    results: List[Tuple[str, bool]] = []
    for line in sums_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, _, name = line.partition("  ")
        name = name.strip()
        target = dataset_path.parent / name
        if not name or not target.is_file():
            results.append((name or "<空文件名>", False))
            continue
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        results.append((name, actual == digest.strip().lower()))
    return results


def _import_student(db: Session, item: Dict[str, Any], fallback_password: Optional[str]) -> bool:
    password = item.get("testPassword") or fallback_password
    if not password:
        raise DatasetError(
            "学生 {} 没有 testPassword，且未提供默认密码".format(item["id"])
        )

    conflict = db.scalar(select(Student).where(Student.login == item["login"]))
    if conflict is not None and conflict.id != item["id"]:
        raise DatasetError(
            "登录名 {} 已被 {} 占用，无法分配给 {}".format(
                item["login"], conflict.id, item["id"]
            )
        )

    created = False
    student = db.get(Student, item["id"])
    if student is None:
        student = Student(id=item["id"])
        db.add(student)
        created = True

    student.name = item["name"]
    student.login = item["login"]
    student.role = item.get("role") or "STUDENT"

    # 同一密码仍可登录时不重算哈希，保证重复导入是真正的无操作
    if created or not verify_password(password, student.password_hash or ""):
        student.password_hash = hash_password(password)
    return created


def _import_course(db: Session, item: Dict[str, Any]) -> bool:
    created = False
    course = db.get(Course, item["id"])
    if course is None:
        course = Course(id=item["id"])
        db.add(course)
        created = True
    course.name = item["name"]
    return created


def _import_assignment(db: Session, item: Dict[str, Any]) -> bool:
    created = False
    assignment = db.get(Assignment, item["id"])
    if assignment is None:
        assignment = Assignment(id=item["id"])
        db.add(assignment)
        created = True
    assignment.course_id = item["courseId"]
    assignment.title = item["title"]
    return created


def _import_record(db: Session, item: Dict[str, Any]) -> bool:
    created = False
    record = db.get(Record, item["id"])
    if record is None:
        record = Record(id=item["id"])
        db.add(record)
        created = True

    record.student_id = item["studentId"]
    record.course_id = item["courseId"]
    record.assignment_id = item["assignmentId"]
    record.question_id = item["questionId"]
    record.question_type = item["questionType"]
    record.question_text = item["questionText"]
    record.question_format = item["questionFormat"]
    record.original_answer = item["originalAnswer"]
    record.answer_format = item["answerFormat"]
    record.score = float(item["score"])
    record.max_score = float(item["maxScore"])
    record.feedback = item["feedback"]
    record.grading_source = item["gradingSource"]
    record.knowledge_points = list(item["knowledgePoints"])
    record.initial_note = item["initialNote"]
    return created


def seed_database(
    db: Session,
    dataset: Dict[str, Any],
    *,
    default_password: Optional[str] = None,
) -> Dict[str, Dict[str, int]]:
    """导入全部实体，返回每个实体的 created/updated 统计。"""
    created_flags: Dict[str, List[bool]] = {
        "students": [_import_student(db, item, default_password) for item in dataset["students"]],
        "courses": [_import_course(db, item) for item in dataset["courses"]],
        "assignments": [_import_assignment(db, item) for item in dataset["assignments"]],
        "records": [_import_record(db, item) for item in dataset["records"]],
    }

    summary: Dict[str, Dict[str, int]] = {}
    for collection, flags in created_flags.items():
        created = sum(1 for flag in flags if flag)
        summary[collection] = {
            "created": created,
            "updated": len(flags) - created,
            "expected": len(dataset[collection]),
        }
    return summary


def load_counts(db: Session) -> Dict[str, int]:
    return {
        collection: db.scalar(select(func.count()).select_from(model))
        for collection, model in ENTITY_MODELS
    }


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="把数据包导入本地数据库（可重复执行，不会覆盖已有笔记）"
    )
    parser.add_argument("--dataset", type=Path, default=None, help="dataset.json 路径")
    parser.add_argument(
        "--password",
        default=None,
        help="学生账号的兜底密码；默认使用数据包里每个账号的 testPassword",
    )
    parser.add_argument("--check-sums", action="store_true", help="只校验 SHA256SUMS 后退出")
    parser.add_argument("--skip-checksums", action="store_true", help="跳过 SHA256SUMS 校验")
    parser.add_argument("--quiet", action="store_true", help="不打印 JSON 摘要")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)
    dataset_path: Path = args.dataset or settings.dataset_path

    try:
        if not args.skip_checksums or args.check_sums:
            results = verify_checksums(dataset_path)
            failed = [name for name, ok in results if not ok]
            if failed:
                raise DatasetError("数据包校验失败: {}".format(", ".join(failed)))
            if results and not args.quiet:
                print("[checksum] 已校验 {} 个文件，全部匹配".format(len(results)))
            if args.check_sums:
                return 0

        dataset = load_dataset(dataset_path)
        init_db()
        with SessionLocal() as db:
            summary = seed_database(db, dataset, default_password=args.password)
            db.commit()
            counts = load_counts(db)
    except DatasetError as exc:
        print("[error] {}".format(exc), file=sys.stderr)
        return 2

    if not args.quiet:
        print(
            json.dumps(
                {
                    "dataset": str(dataset_path),
                    "database": settings.database_url,
                    "summary": summary,
                    "counts": counts,
                },
                ensure_ascii=False,
                indent=2,
            )
        )

    mismatched = [
        collection
        for collection, stats in summary.items()
        if counts.get(collection) < stats["expected"]
    ]
    if mismatched:
        print(
            "[error] 导入后数量少于数据包: {}".format(", ".join(mismatched)),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
