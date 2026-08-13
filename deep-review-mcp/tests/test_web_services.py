# tests/test_web_services.py
"""测试 Web 服务层 — 编排 storage/statistics/review"""
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from deep_review_mcp.models import (
    Analysis,
    Classification,
    Improvement,
    StructuredQuestion,
    WrongQuestion,
)
from deep_review_mcp.storage import Storage
from deep_review_mcp.web import services


@pytest.fixture
def temp_storage(tmp_path, monkeypatch):
    """创建临时 storage 并注入 services 模块"""
    storage = Storage(base_dir=tmp_path)
    monkeypatch.setattr(services, "_get_storage", lambda: storage)
    return storage


def _make_question(qid, subject="数学", error_type="知识漏洞",
                   days_ago=0, review_count=0, next_review=None):
    """构造完整测试错题"""
    created = datetime.now(timezone.utc) - timedelta(days=days_ago)
    wq = WrongQuestion(
        question_id=qid,
        created_at=created,
        structured=StructuredQuestion(
            subject=subject,
            grade_level="高中",
            knowledge_points=["函数基础", "二次函数"],
            difficulty="中等",
            question_type="选择题",
            question_content=f"测试题目 {qid}",
        ),
        classification=Classification(
            error_type=error_type,
            error_category="概念不清",
        ),
        analysis=Analysis(
            root_cause="测试根因",
            cause_category=error_type,
            diagnosis_detail="测试诊断",
        ),
        improvement=Improvement(
            plan="测试改进",
            similar_topics=["相似题1"],
            review_count=review_count,
            next_review_date=next_review or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        ),
    )
    return wq


# ──────────────────────────────────────────
# Dashboard summary 测试
# ──────────────────────────────────────────

def test_dashboard_summary_empty(temp_storage):
    """无数据时应返回零值"""
    summary = services.get_dashboard_summary()
    assert summary["total"] == 0
    assert summary["today_pending"] == 0
    assert summary["week_new"] == 0
    assert summary["week_reviewed"] == 0
    assert summary["subject_distribution"] == []
    assert summary["error_type_distribution"] == []
    # trends 始终填充30天，无数据时全为0
    assert len(summary["trends"]) == 30
    assert all(v == 0 for v in summary["trends"].values())


def test_dashboard_summary_with_data(temp_storage):
    """有数据时应正确统计"""
    temp_storage.save_wrong_question(_make_question("wq_001", days_ago=1))
    temp_storage.save_wrong_question(_make_question("wq_002", subject="物理", days_ago=2))

    summary = services.get_dashboard_summary()
    assert summary["total"] == 2
    assert summary["week_new"] == 2
    # subject distribution 应含两个学科
    subjects = {item["name"] for item in summary["subject_distribution"]}
    assert "数学" in subjects
    assert "物理" in subjects


# ──────────────────────────────────────────
# Multi-dim stats 测试
# ──────────────────────────────────────────

def test_multi_dim_stats(temp_storage):
    """多维统计应返回热力图、难度分布、雷达数据"""
    temp_storage.save_wrong_question(_make_question("wq_001"))
    temp_storage.save_wrong_question(_make_question("wq_002", subject="物理"))

    stats = services.get_multi_dim_stats()
    assert "knowledge_heatmap" in stats
    assert "difficulty_distribution" in stats
    assert "error_type_radar" in stats
    assert "trend_data" in stats


# ──────────────────────────────────────────
# Upcoming reviews 测试
# ──────────────────────────────────────────

def test_get_upcoming_reviews(temp_storage):
    """待复习列表应返回到期的错题"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    temp_storage.save_wrong_question(
        _make_question("wq_001", next_review=today)
    )
    future = (datetime.now(timezone.utc) + timedelta(days=10)).strftime("%Y-%m-%d")
    temp_storage.save_wrong_question(
        _make_question("wq_002", next_review=future)
    )

    upcoming = services.get_upcoming_reviews()
    assert len(upcoming) == 1
    assert upcoming[0]["question_id"] == "wq_001"


# ──────────────────────────────────────────
# Mark reviewed 测试
# ──────────────────────────────────────────

def test_mark_question_reviewed(temp_storage):
    """标记复习后 review_count 应递增"""
    temp_storage.save_wrong_question(_make_question("wq_001", review_count=0))
    result = services.mark_question_reviewed("wq_001")
    assert result is not None
    assert result["review_count"] == 1


def test_mark_question_reviewed_not_found(temp_storage):
    """标记不存在的错题应返回 None"""
    result = services.mark_question_reviewed("nonexistent")
    assert result is None


# ──────────────────────────────────────────
# Update question 测试
# ──────────────────────────────────────────

def test_update_question(temp_storage):
    """编辑保存后字段应更新"""
    temp_storage.save_wrong_question(_make_question("wq_001"))
    updated = services.update_question("wq_001", {"question_content": "修改后的题目"})
    assert updated is not None
    assert updated.structured.question_content == "修改后的题目"


def test_update_question_not_found(temp_storage):
    """更新不存在的错题应返回 None"""
    result = services.update_question("nonexistent", {"question_content": "x"})
    assert result is None


def test_update_question_with_null_structured(temp_storage):
    """编辑 structured=null 的错题时应自动填充默认值并保存成功"""
    # 创建一个 structured=null 的错题
    from deep_review_mcp.models import WrongQuestion as WQ
    wq = WQ(
        question_id="wq_null_test",
        created_at=datetime.now(timezone.utc),
        structured=None,
        classification=None,
    )
    temp_storage.save_wrong_question(wq)

    # 编辑学科和难度（structured 为 null 的情况）
    result = services.update_question("wq_null_test", {
        "subject": "物理",
        "difficulty": "困难",
        "error_type": "方法错误",
    })
    assert result is not None
    assert result.structured is not None
    assert result.structured.subject == "物理"
    assert result.structured.difficulty == "困难"
    # 默认值应被填充
    assert result.structured.grade_level == "高中"
    assert result.structured.question_type == "其他"
    # classification 也应有默认值
    assert result.classification is not None
    assert result.classification.error_type == "方法错误"
    assert result.classification.error_category == "待分类"


# ──────────────────────────────────────────
# Filtered questions 测试
# ──────────────────────────────────────────

def test_get_filtered_questions(temp_storage):
    """筛选查询应正确过滤"""
    temp_storage.save_wrong_question(_make_question("wq_001", subject="数学"))
    temp_storage.save_wrong_question(_make_question("wq_002", subject="物理"))

    result = services.get_filtered_questions({"subject": "数学"})
    assert result["total_count"] == 1
    assert result["questions"][0]["structured"]["subject"] == "数学"
