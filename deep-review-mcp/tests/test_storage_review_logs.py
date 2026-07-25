# tests/test_storage_review_logs.py
"""FSRS ReviewLog 日志持久化测试

验证 storage.py 中新增的 review_logs.jsonl 读写功能：
  - append_review_log：追加一条复习记录
  - list_review_logs：按 question_id 查询历史复习记录
  - list_all_review_logs：查询全部复习记录（Optimizer 数据源）
  - 文件不存在/损坏行的降级处理
  - mark_reviewed 自动调用 append_review_log 持久化
"""
import json
from datetime import datetime, timezone

import pytest

from deep_review_mcp.storage import Storage
from deep_review_mcp.models import WrongQuestion, StructuredQuestion, Improvement


@pytest.fixture
def tmp_storage(tmp_path):
    """临时 Storage 实例（review_logs_file 默认指向 tmp_path/review_logs.jsonl）"""
    return Storage(base_dir=tmp_path)


@pytest.fixture
def sample_question():
    """带 improvement 的错题（用于 mark_reviewed 测试）"""
    return WrongQuestion(
        question_id="wq_log_001",
        created_at=datetime(2026, 7, 25, 10, 0, tzinfo=timezone.utc),
        raw_text="测试 ReviewLog 持久化",
        structured=StructuredQuestion(
            subject="数学", grade_level="初二",
            knowledge_points=["方程"], difficulty="中等", question_type="计算题",
        ),
        improvement=Improvement(
            plan="复习方程", similar_topics=["一元二次方程"],
            review_count=0, next_review_date=None, fsrs_state=None,
        ),
    )


# ──────────────────────────────────────────
# append_review_log
# ──────────────────────────────────────────

def test_append_review_log_creates_file_if_not_exists(tmp_storage):
    """文件不存在时，追加写入自动创建文件"""
    assert not tmp_storage.review_logs_file.exists()
    tmp_storage.append_review_log(
        question_id="wq_001",
        review_log_json='{"rating":3}',
        rating=3,
        reviewed_at="2026-07-25T10:00:00+00:00",
    )
    assert tmp_storage.review_logs_file.exists()


def test_append_review_log_writes_valid_jsonl(tmp_storage):
    """追加写入的每行应为合法 JSON，含必需字段"""
    tmp_storage.append_review_log(
        question_id="wq_001",
        review_log_json='{"rating":3,"state":1}',
        rating=3,
        reviewed_at="2026-07-25T10:00:00+00:00",
    )
    content = tmp_storage.review_logs_file.read_text(encoding="utf-8")
    lines = [l for l in content.splitlines() if l.strip()]
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["question_id"] == "wq_001"
    assert rec["rating"] == 3
    assert rec["reviewed_at"] == "2026-07-25T10:00:00+00:00"
    assert rec["review_log"] == '{"rating":3,"state":1}'


def test_append_review_log_multiple_lines(tmp_storage):
    """连续追加多条记录，每条独占一行（jsonl 格式）"""
    for i in range(3):
        tmp_storage.append_review_log(
            question_id=f"wq_{i:03d}",
            review_log_json='{"rating":3}',
            rating=3,
            reviewed_at=f"2026-07-25T10:0{i}:00+00:00",
        )
    content = tmp_storage.review_logs_file.read_text(encoding="utf-8")
    lines = [l for l in content.splitlines() if l.strip()]
    assert len(lines) == 3
    # 每行都能独立解析
    for line in lines:
        assert json.loads(line)["question_id"]


# ──────────────────────────────────────────
# list_review_logs
# ──────────────────────────────────────────

def test_list_review_logs_empty_when_file_not_exists(tmp_storage):
    """文件不存在时返回空列表，不抛异常"""
    assert tmp_storage.list_review_logs("wq_any") == []


def test_list_review_logs_filters_by_question_id(tmp_storage):
    """按 question_id 过滤复习记录"""
    # 写入 wq_001 两条、wq_002 一条
    for ts in ["2026-07-25T10:00:00+00:00", "2026-07-26T10:00:00+00:00"]:
        tmp_storage.append_review_log(
            question_id="wq_001", review_log_json='{}', rating=3, reviewed_at=ts,
        )
    tmp_storage.append_review_log(
        question_id="wq_002", review_log_json='{}', rating=4, reviewed_at="2026-07-25T11:00:00+00:00",
    )
    # 查询 wq_001
    logs = tmp_storage.list_review_logs("wq_001")
    assert len(logs) == 2
    assert all(log["question_id"] == "wq_001" for log in logs)
    # 查询 wq_002
    logs2 = tmp_storage.list_review_logs("wq_002")
    assert len(logs2) == 1
    assert logs2[0]["rating"] == 4


def test_list_review_logs_sorted_by_time_asc(tmp_storage):
    """复习记录按 reviewed_at 升序排列（旧→新）"""
    # 故意乱序写入
    tmp_storage.append_review_log(
        question_id="wq_001", review_log_json='{}', rating=3, reviewed_at="2026-07-27T10:00:00+00:00",
    )
    tmp_storage.append_review_log(
        question_id="wq_001", review_log_json='{}', rating=3, reviewed_at="2026-07-25T10:00:00+00:00",
    )
    tmp_storage.append_review_log(
        question_id="wq_001", review_log_json='{}', rating=3, reviewed_at="2026-07-26T10:00:00+00:00",
    )
    logs = tmp_storage.list_review_logs("wq_001")
    assert [log["reviewed_at"] for log in logs] == [
        "2026-07-25T10:00:00+00:00",
        "2026-07-26T10:00:00+00:00",
        "2026-07-27T10:00:00+00:00",
    ]


def test_list_review_logs_skips_corrupted_lines(tmp_storage):
    """损坏行（非法 JSON）应被跳过，不中断查询"""
    # 手工写入：1 条合法 + 1 条损坏 + 1 条合法
    with open(tmp_storage.review_logs_file, "a", encoding="utf-8") as f:
        f.write(json.dumps({"question_id": "wq_001", "rating": 3, "reviewed_at": "t1", "review_log": "{}"}) + "\n")
        f.write("{invalid json line}\n")
        f.write(json.dumps({"question_id": "wq_001", "rating": 4, "reviewed_at": "t2", "review_log": "{}"}) + "\n")
    logs = tmp_storage.list_review_logs("wq_001")
    assert len(logs) == 2  # 损坏行被跳过


# ──────────────────────────────────────────
# list_all_review_logs
# ──────────────────────────────────────────

def test_list_all_review_logs_returns_all(tmp_storage):
    """list_all_review_logs 返回全部记录（不分 question_id）"""
    for qid in ["wq_001", "wq_002", "wq_003"]:
        tmp_storage.append_review_log(
            question_id=qid, review_log_json='{}', rating=3, reviewed_at="2026-07-25T10:00:00+00:00",
        )
    all_logs = tmp_storage.list_all_review_logs()
    assert len(all_logs) == 3
    assert {log["question_id"] for log in all_logs} == {"wq_001", "wq_002", "wq_003"}


def test_list_all_review_logs_empty_when_file_not_exists(tmp_storage):
    """文件不存在时返回空列表"""
    assert tmp_storage.list_all_review_logs() == []


# ──────────────────────────────────────────
# mark_reviewed 自动持久化
# ──────────────────────────────────────────

def test_mark_reviewed_writes_review_log(tmp_storage, sample_question):
    """mark_reviewed 后，review_logs.jsonl 应有一条对应记录"""
    tmp_storage.save_wrong_question(sample_question)
    tmp_storage.mark_reviewed("wq_log_001", rating=3)

    logs = tmp_storage.list_review_logs("wq_log_001")
    assert len(logs) == 1
    assert logs[0]["rating"] == 3
    assert logs[0]["question_id"] == "wq_log_001"
    # review_log 字段应是合法 JSON 字符串（FSRS ReviewLog 的序列化）
    rl = json.loads(logs[0]["review_log"])
    assert "rating" in rl or "state" in rl  # FSRS ReviewLog 至少含这些字段


def test_mark_reviewed_multiple_times_appends_multiple_logs(
    tmp_storage, sample_question
):
    """多次 mark_reviewed 应追加多条日志，与 review_count 一致"""
    tmp_storage.save_wrong_question(sample_question)
    for _ in range(3):
        tmp_storage.mark_reviewed("wq_log_001", rating=3)

    logs = tmp_storage.list_review_logs("wq_log_001")
    assert len(logs) == 3
    # 三条记录的 reviewed_at 应递增（FSRS 内部用当前时间，每次不同）
    timestamps = [log["reviewed_at"] for log in logs]
    assert timestamps == sorted(timestamps)


def test_mark_reviewed_nonexistent_question_no_log_written(tmp_storage):
    """不存在的错题 ID：返回 None，且不应写入 review_log"""
    result = tmp_storage.mark_reviewed("wq_not_exist", rating=3)
    assert result is None
    # 文件可能未创建，或已存在但无记录
    if tmp_storage.review_logs_file.exists():
        logs = tmp_storage.list_all_review_logs()
        assert len(logs) == 0


def test_mark_reviewed_review_log_persists_fsrs_state_json(
    tmp_storage, sample_question
):
    """持久化的 review_log 字段可被 FSRS ReviewLog.from_json 反序列化

    这是未来 Optimizer 计算个性化参数的前提。
    """
    tmp_storage.save_wrong_question(sample_question)
    tmp_storage.mark_reviewed("wq_log_001", rating=3)

    logs = tmp_storage.list_review_logs("wq_log_001")
    assert len(logs) == 1

    # 验证 review_log 可被 py-fsrs 反序列化
    from fsrs import ReviewLog
    rl = ReviewLog.from_json(logs[0]["review_log"])
    # ReviewLog 应有 rating 属性（1-4）
    assert rl.rating in (1, 2, 3, 4)
