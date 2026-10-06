"""测试夹具。

环境变量必须在导入 ``app`` 之前设置：``app.core.config`` 在导入时读取配置。
"""

import os
import shutil
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "wrong-answers-20" / "dataset.json"

_TMP_DIR = Path(tempfile.mkdtemp(prefix="wa-tests-"))
os.environ["DATABASE_URL"] = "sqlite:///" + (_TMP_DIR / "test.db").as_posix()
os.environ["DATASET_PATH"] = str(DATASET_PATH)
os.environ["SESSION_TTL_HOURS"] = "1"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db.session import SessionLocal, init_db  # noqa: E402
from app.main import create_app  # noqa: E402
from app.seed import load_dataset, seed_database  # noqa: E402

DEFAULT_PASSWORD = "ExamOnly_2026!"


def run_seed() -> None:
    dataset = load_dataset(DATASET_PATH)
    with SessionLocal() as db:
        seed_database(db, dataset)
        db.commit()


@pytest.fixture(scope="session", autouse=True)
def _cleanup_temp_dir():
    yield
    shutil.rmtree(_TMP_DIR, ignore_errors=True)


@pytest.fixture(scope="session")
def client() -> TestClient:
    init_db()
    run_seed()
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture()
def student_client(client: TestClient) -> TestClient:
    """每个用例都从无 cookie 状态开始，避免会话串场。"""
    client.cookies.clear()
    yield client
    client.cookies.clear()


@pytest.fixture()
def login_as(student_client: TestClient):
    def _login(login: str, password: str = DEFAULT_PASSWORD):
        response = student_client.post(
            "/api/auth/login", json={"login": login, "password": password}
        )
        assert response.status_code == 200, response.text
        return response

    return _login


@pytest.fixture()
def reseed():
    """模拟“重建容器后再次执行初始化”。"""
    return run_seed
