"""WA-01：重复初始化不产生重复数据。"""

from pathlib import Path

from app.seed import load_dataset, load_counts, seed_database

from tests.conftest import DATASET_PATH, SessionLocal

EXPECTED_COUNTS = {
    "students": 13,
    "courses": 6,
    "assignments": 7,
    "records": 20,
}


def test_seed_is_idempotent():
    assert Path(DATASET_PATH).is_file(), "测试依赖仓库内的原始数据包"

    dataset = load_dataset(DATASET_PATH)

    with SessionLocal() as db:
        before = load_counts(db)
        summary = seed_database(db, dataset)
        db.commit()
        after = load_counts(db)

    assert {key: before[key] for key in EXPECTED_COUNTS} == EXPECTED_COUNTS
    assert {key: after[key] for key in EXPECTED_COUNTS} == EXPECTED_COUNTS
    assert after == before, "重复导入不得新增或删除实体"
    assert all(stats["created"] == 0 for stats in summary.values())
