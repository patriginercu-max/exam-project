"""按 expected-filters.json 与 test-cases.csv 验收筛选、隔离与笔记。"""

import json

import pytest

from tests.conftest import PROJECT_ROOT, student_client  # noqa: F401  (夹具导入)

FILTER_DOC = json.loads(
    (PROJECT_ROOT / "03-wrong-answer-supplement" / "expected-filters.json").read_text(
        encoding="utf-8"
    )
)
FILTER_CASES = FILTER_DOC["cases"]


def _ids(response):
    return [item["id"] for item in response.json()["records"]]


@pytest.mark.parametrize("case", FILTER_CASES, ids=[case["caseId"] for case in FILTER_CASES])
def test_filter_cases(student_client, login_as, case):
    """WA-02：逐项登录并筛选，结果 ID 集合与预期完全一致。"""
    login_as(case["login"])
    response = student_client.get("/api/records", params=case.get("filters") or {})
    assert response.status_code == 200, response.text
    assert _ids(response) == case["expectedRecordIds"]


def test_unauthenticated_requests_are_rejected(student_client):
    assert student_client.get("/api/records").status_code == 401
    assert student_client.get("/api/records/wrong_001").status_code == 401
    assert student_client.get("/api/courses").status_code == 401


def test_wrong_password_is_rejected(student_client):
    response = student_client.post(
        "/api/auth/login", json={"login": "student_001", "password": "not-the-password"}
    )
    assert response.status_code == 401


def test_client_supplied_student_id_is_ignored(student_client, login_as):
    """权限由服务端会话决定，查询参数里的 studentId 不起作用。"""
    login_as("student_002")
    response = student_client.get("/api/records", params={"studentId": "student_001"})
    assert response.status_code == 200
    assert _ids(response) == ["wrong_006"]


def test_cross_student_access_is_forbidden(student_client, login_as):
    """WA-05：越权读、改、清空都必须被服务端拒绝，且不产生修改。"""
    login_as("student_002")

    assert student_client.get("/api/records/wrong_001").status_code == 403
    assert (
        student_client.put(
            "/api/records/wrong_001/note", json={"cause": "越权", "content": "越权"}
        ).status_code
        == 403
    )
    assert student_client.delete("/api/records/wrong_001/note").status_code == 403

    login_as("student_001")
    note = student_client.get("/api/records/wrong_001").json()["note"]
    assert note["cause"] != "越权"
    assert note["content"] != "越权"


def test_unknown_record_is_not_found(student_client, login_as):
    login_as("student_001")
    assert student_client.get("/api/records/wrong_999").status_code == 404


def test_logout_revokes_session(student_client, login_as):
    login_as("student_001")
    assert student_client.get("/api/auth/me").status_code == 200

    assert student_client.post("/api/auth/logout").status_code == 204
    assert student_client.get("/api/auth/me").status_code == 401


def test_note_survives_reseed_and_clears_for_good(student_client, login_as, reseed):
    """WA-03 / WA-04 / WA-12：保存、跨初始化持久化、清空后不回滚。"""
    login_as("student_001")

    before = student_client.get("/api/records/wrong_001").json()
    original_answer = before["originalAnswer"]
    feedback = before["feedback"]

    saved = student_client.put(
        "/api/records/wrong_001/note",
        json={"cause": "符号判断失误", "content": "复习行列式定义，重点看逆序数"},
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["cause"] == "符号判断失误"

    reseed()

    after_reseed = student_client.get("/api/records/wrong_001").json()
    assert after_reseed["note"]["cause"] == "符号判断失误"
    assert after_reseed["note"]["content"] == "复习行列式定义，重点看逆序数"
    # 历史评语与原始作答不得被笔记覆盖
    assert after_reseed["originalAnswer"] == original_answer
    assert after_reseed["feedback"] == feedback

    cleared = student_client.delete("/api/records/wrong_001/note")
    assert cleared.status_code == 200
    assert cleared.json()["cause"] == ""
    assert cleared.json()["content"] == ""

    reseed()

    after_clear = student_client.get("/api/records/wrong_001").json()
    assert after_clear["note"]["cause"] == ""
    assert after_clear["note"]["content"] == ""


def test_saving_empty_strings_clears_note(student_client, login_as):
    """WA-04：空字符串保存表示清空，不能被当作“不修改”。"""
    login_as("student_003")

    student_client.put(
        "/api/records/wrong_007/note", json={"cause": "写错了", "content": "看课本"}
    )
    response = student_client.put(
        "/api/records/wrong_007/note", json={"cause": "", "content": ""}
    )
    assert response.status_code == 200
    assert response.json()["cause"] == ""
    assert response.json()["content"] == ""

    detail = student_client.get("/api/records/wrong_007").json()
    assert detail["note"]["cause"] == ""
    assert detail["note"]["content"] == ""


def test_partial_note_payload_is_rejected(student_client, login_as):
    """缺字段不能被静默解释成清空，直接拒绝。"""
    login_as("student_004")
    response = student_client.put(
        "/api/records/wrong_008/note", json={"cause": "只有错因"}
    )
    assert response.status_code == 422


def test_missing_feedback_and_untagged_points(student_client, login_as):
    """WA-06 / WA-07：空值按“暂无评语”“未标注”返回，不捏造内容。"""
    login_as("student_005")
    record = student_client.get("/api/records/wrong_010").json()
    assert record["feedback"] is None
    assert record["knowledgePoints"]

    login_as("student_001")
    record = student_client.get("/api/records/wrong_001").json()
    assert record["knowledgePoints"] == []
    assert record["feedback"]


def test_list_payload_keeps_source_fields(student_client, login_as):
    """列表与详情都保留原始作答与格式提示，供前端安全渲染。"""
    login_as("student_001")
    records = student_client.get("/api/records").json()["records"]
    assert len(records) == 5

    record = records[0]
    assert record["answerFormat"] == "html"
    assert record["questionFormat"] == "markdown_latex"
    assert "<sub>" in record["originalAnswer"]
    assert record["score"] == 8.36
    assert record["maxScore"] == 10
