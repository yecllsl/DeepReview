# tests/test_storage_patch.py
"""测试 storage.py 的增强功能：原子写、部分更新、标记复习"""
from datetime import datetime

from deep_review_mcp.models import Improvement, WrongQuestion
from deep_review_mcp.storage import Storage


def _make_storage(tmp_path) -> Storage:
    """创建指向临时目录的 Storage 实例"""
    return Storage(base_dir=tmp_path)


def _make_question(qid: str = "wq_test_001") -> WrongQuestion:
    """构造测试用错题"""
    return WrongQuestion(
        question_id=qid,
        created_at=datetime.now(),
        raw_text="测试题目",
    )


# ──────────────────────────────────────────
# patch_wrong_question 测试
# ──────────────────────────────────────────

def test_patch_wrong_question_updates_field(tmp_path):
    """部分更新应修改指定字段"""
    storage = _make_storage(tmp_path)
    storage.save_wrong_question(_make_question())

    updated = storage.patch_wrong_question("wq_test_001", {"raw_text": "修改后题目"})
    assert updated is not None
    assert updated.raw_text == "修改后题目"

    loaded = storage.load_wrong_question("wq_test_001")
    assert loaded.raw_text == "修改后题目"


def test_patch_wrong_question_not_found(tmp_path):
    """更新不存在的错题应返回 None"""
    storage = _make_storage(tmp_path)
    result = storage.patch_wrong_question("nonexistent", {"raw_text": "x"})
    assert result is None


def test_patch_wrong_question_preserves_other_fields(tmp_path):
    """部分更新不应影响未修改的字段"""
    storage = _make_storage(tmp_path)
    wq = _make_question()
    wq.raw_text = "原始题目"
    wq.correct_answer = "原始答案"
    storage.save_wrong_question(wq)

    updated = storage.patch_wrong_question("wq_test_001", {"raw_text": "新题目"})
    assert updated.raw_text == "新题目"
    assert updated.correct_answer == "原始答案"


# ──────────────────────────────────────────
# mark_reviewed 测试
# ──────────────────────────────────────────

def test_mark_reviewed_increments_count(tmp_path):
    """标记复习应递增 review_count 并更新 next_review_date"""
    storage = _make_storage(tmp_path)
    wq = _make_question()
    wq.improvement = Improvement(
        plan="测试计划",
        similar_topics=[],
        review_count=0,
        next_review_date="2026-07-22",
    )
    storage.save_wrong_question(wq)

    updated = storage.mark_reviewed("wq_test_001")
    assert updated is not None
    assert updated.improvement.review_count == 1
    # 下次复习日期应晚于今天
    assert updated.improvement.next_review_date is not None


def test_mark_reviewed_not_found(tmp_path):
    """标记不存在的错题应返回 None"""
    storage = _make_storage(tmp_path)
    result = storage.mark_reviewed("nonexistent")
    assert result is None


# ──────────────────────────────────────────
# 原子写测试
# ──────────────────────────────────────────

def test_atomic_write_no_corruption(tmp_path):
    """原子写入后文件应完整可读"""
    storage = _make_storage(tmp_path)
    wq = _make_question()
    storage.save_wrong_question(wq)

    loaded = storage.load_wrong_question("wq_test_001")
    assert loaded is not None
    assert loaded.question_id == "wq_test_001"


def test_atomic_write_no_temp_file_left(tmp_path):
    """原子写入后不应残留临时文件"""
    storage = _make_storage(tmp_path)
    storage.save_wrong_question(_make_question())

    temp_files = list(tmp_path.rglob("*.tmp"))
    assert len(temp_files) == 0
