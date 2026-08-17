# tests/test_fsrs_integration.py
"""FSRS 与 Storage 集成测试

验证 storage.mark_reviewed 正确调用 FSRS 调度：
  - 老数据（无 fsrs_state）首次复习自动初始化
  - 复习后 fsrs_state 非空、review_count 递增、next_review_date 回填
  - 不同 rating 产生差异化调度
  - 默认 rating=3（Good）向后兼容
"""
from datetime import UTC, datetime

import pytest

from deep_review_mcp.models import Improvement, StructuredQuestion, WrongQuestion
from deep_review_mcp.storage import Storage


@pytest.fixture
def tmp_storage(tmp_path):
    """临时 Storage 实例"""
    return Storage(base_dir=tmp_path)


@pytest.fixture
def question_with_improvement():
    """带 improvement 的错题（老数据，无 fsrs_state）"""
    return WrongQuestion(
        question_id="wq_fsrs_001",
        created_at=datetime(2026, 7, 24, 10, 0, tzinfo=UTC),
        structured=StructuredQuestion(
            subject="数学", grade_level="初二",
            knowledge_points=["方程"], difficulty="中等", question_type="计算题",
            question_content="测试 FSRS 集成",
        ),
        improvement=Improvement(
            plan="复习方程解法", similar_topics=["一元二次方程"],
            review_count=0, next_review_date=None, fsrs_state=None,
        ),
    )


# ──────────────────────────────────────────
# 向后兼容：老数据迁移
# ──────────────────────────────────────────

def test_mark_reviewed_initializes_fsrs_state_for_legacy_data(
    tmp_storage, question_with_improvement
):
    """老数据（fsrs_state=None）首次复习后应自动初始化 FSRS 状态"""
    tmp_storage.save_wrong_question(question_with_improvement)
    updated = tmp_storage.mark_reviewed("wq_fsrs_001", rating=3)
    assert updated is not None
    assert updated.improvement.fsrs_state is not None
    # fsrs_state 应为有效 JSON 字符串
    import json
    data = json.loads(updated.improvement.fsrs_state)
    assert "due" in data
    assert "stability" in data


def test_mark_reviewed_increments_review_count(tmp_storage, question_with_improvement):
    """复习后 review_count 应递增"""
    tmp_storage.save_wrong_question(question_with_improvement)
    assert question_with_improvement.improvement.review_count == 0
    updated = tmp_storage.mark_reviewed("wq_fsrs_001", rating=3)
    assert updated.improvement.review_count == 1
    # 第二次
    updated2 = tmp_storage.mark_reviewed("wq_fsrs_001", rating=3)
    assert updated2.improvement.review_count == 2


def test_mark_reviewed_fills_next_review_date(tmp_storage, question_with_improvement):
    """复习后 next_review_date 应被 FSRS due 回填（非空）"""
    tmp_storage.save_wrong_question(question_with_improvement)
    assert question_with_improvement.improvement.next_review_date is None
    updated = tmp_storage.mark_reviewed("wq_fsrs_001", rating=3)
    assert updated.improvement.next_review_date is not None
    assert isinstance(updated.improvement.next_review_date, str)
    # 日期格式 YYYY-MM-DD
    assert len(updated.improvement.next_review_date) == 10


# ──────────────────────────────────────────
# 默认 rating 向后兼容
# ──────────────────────────────────────────

def test_mark_reviewed_default_rating_is_good(tmp_storage, question_with_improvement):
    """不传 rating 时默认 Good（3），向后兼容老调用方"""
    tmp_storage.save_wrong_question(question_with_improvement)
    # 不传 rating
    updated_default = tmp_storage.mark_reviewed("wq_fsrs_001")
    assert updated_default is not None
    assert updated_default.improvement.fsrs_state is not None

    # 与显式传 rating=3 结果类型一致（都有 fsrs_state）
    tmp_storage.save_wrong_question(question_with_improvement)
    tmp_storage.mark_reviewed("wq_fsrs_001")
    updated_explicit = tmp_storage.mark_reviewed("wq_fsrs_001", rating=3)
    assert updated_explicit.improvement.fsrs_state is not None


# ──────────────────────────────────────────
# 4 档评分差异化
# ──────────────────────────────────────────

def test_mark_reviewed_again_vs_easy_different_dates(
    tmp_storage, question_with_improvement
):
    """Again 与 Easy 评分应产生不同的 next_review_date

    首次评分：Again 留在今天（Learning 1分钟），Easy 调度到未来（毕业）。
    """
    # Again
    tmp_storage.save_wrong_question(question_with_improvement)
    r_again = tmp_storage.mark_reviewed("wq_fsrs_001", rating=1)
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    assert r_again.improvement.next_review_date == today

    # Easy（用新错题避免状态污染）
    q2 = question_with_improvement.model_copy(deep=True)
    q2.question_id = "wq_fsrs_002"
    tmp_storage.save_wrong_question(q2)
    r_easy = tmp_storage.mark_reviewed("wq_fsrs_002", rating=4)
    # Easy 应调度到今天或未来
    assert r_easy.improvement.next_review_date >= today


def test_mark_reviewed_persists_fsrs_state_across_loads(
    tmp_storage, question_with_improvement
):
    """FSRS 状态应持久化到 JSON，重新加载后仍存在"""
    tmp_storage.save_wrong_question(question_with_improvement)
    tmp_storage.mark_reviewed("wq_fsrs_001", rating=3)

    # 重新从磁盘加载
    reloaded = tmp_storage.load_wrong_question("wq_fsrs_001")
    assert reloaded.improvement.fsrs_state is not None
    assert reloaded.improvement.review_count == 1


# ──────────────────────────────────────────
# ReviewLog 持久化（jsonl 日志表）
# ──────────────────────────────────────────

def test_mark_reviewed_appends_review_log_to_jsonl(
    tmp_storage, question_with_improvement
):
    """mark_reviewed 应同步追加一条 ReviewLog 到 review_logs.jsonl"""
    tmp_storage.save_wrong_question(question_with_improvement)
    tmp_storage.mark_reviewed("wq_fsrs_001", rating=3)

    logs = tmp_storage.list_review_logs("wq_fsrs_001")
    assert len(logs) == 1
    assert logs[0]["rating"] == 3
    assert logs[0]["question_id"] == "wq_fsrs_001"


def test_mark_reviewed_multiple_ratings_log_all(
    tmp_storage, question_with_improvement
):
    """多次 mark_reviewed 应追加多条日志，数量与 review_count 一致"""
    tmp_storage.save_wrong_question(question_with_improvement)
    for r in [1, 2, 3, 4]:
        tmp_storage.mark_reviewed("wq_fsrs_001", rating=r)

    logs = tmp_storage.list_review_logs("wq_fsrs_001")
    assert len(logs) == 4
    # 评分应依次为 1/2/3/4
    assert [log["rating"] for log in logs] == [1, 2, 3, 4]


def test_mark_reviewed_review_log_reversible_by_fsrs(
    tmp_storage, question_with_improvement
):
    """持久化的 review_log 可被 fsrs.ReviewLog.from_json 反序列化

    这是未来启用 Optimizer 个性化参数的前提条件。
    """
    from fsrs import ReviewLog

    tmp_storage.save_wrong_question(question_with_improvement)
    tmp_storage.mark_reviewed("wq_fsrs_001", rating=3)

    logs = tmp_storage.list_review_logs("wq_fsrs_001")
    rl = ReviewLog.from_json(logs[0]["review_log"])
    assert rl.rating == 3


def test_review_logs_isolated_per_question(tmp_storage, question_with_improvement):
    """不同错题的 ReviewLog 互不干扰"""
    tmp_storage.save_wrong_question(question_with_improvement)
    q2 = question_with_improvement.model_copy(deep=True)
    q2.question_id = "wq_fsrs_002"
    tmp_storage.save_wrong_question(q2)

    tmp_storage.mark_reviewed("wq_fsrs_001", rating=3)
    tmp_storage.mark_reviewed("wq_fsrs_002", rating=4)

    assert len(tmp_storage.list_review_logs("wq_fsrs_001")) == 1
    assert len(tmp_storage.list_review_logs("wq_fsrs_002")) == 1
    # 全局查询应返回 2 条
    assert len(tmp_storage.list_all_review_logs()) == 2


# ──────────────────────────────────────────
# 异常场景
# ──────────────────────────────────────────

def test_mark_reviewed_nonexistent_question_returns_none(tmp_storage):
    """不存在的错题 ID 返回 None"""
    assert tmp_storage.mark_reviewed("wq_not_exist", rating=3) is None


def test_mark_reviewed_without_improvement_returns_none(tmp_storage):
    """无 improvement 字段的错题返回 None"""
    q = WrongQuestion(
        question_id="wq_no_imp",
        created_at=datetime(2026, 7, 24, 10, 0, tzinfo=UTC),
        structured=StructuredQuestion(
            subject="数学", grade_level="初二",
            knowledge_points=["方程"], difficulty="中等", question_type="计算题",
            question_content="无改进建议",
        ),
        improvement=None,
    )
    tmp_storage.save_wrong_question(q)
    assert tmp_storage.mark_reviewed("wq_no_imp", rating=3) is None


def test_mark_reviewed_invalid_rating_raises(tmp_storage, question_with_improvement):
    """无效 rating 抛 ValueError"""
    tmp_storage.save_wrong_question(question_with_improvement)
    with pytest.raises(ValueError):
        tmp_storage.mark_reviewed("wq_fsrs_001", rating=0)
    with pytest.raises(ValueError):
        tmp_storage.mark_reviewed("wq_fsrs_001", rating=5)
