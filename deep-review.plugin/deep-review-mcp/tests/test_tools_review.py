# tests/test_tools_review.py
from datetime import UTC, datetime, timedelta

import pytest

from deep_review_mcp.models import Improvement, StructuredQuestion, WrongQuestion
from deep_review_mcp.storage import Storage
from deep_review_mcp.tools.review import _get_overdue_questions, recommend_review


@pytest.fixture
def storage_with_overdue(tmp_path):
    s = Storage(base_dir=tmp_path)
    for i, (offset, cnt) in enumerate([(0, 0), (5, 1), (10, 2)]):
        nr = (datetime.now(UTC) - timedelta(days=offset)).strftime("%Y-%m-%d")
        s.save_wrong_question(WrongQuestion(
            question_id=f"wq_{i}", created_at=datetime(2026, 6, 10+i, 10, 30, tzinfo=UTC),
            structured=StructuredQuestion(subject="数学", grade_level="初二",
                knowledge_points=["方程"], difficulty="基础", question_type="计算题",
                question_content=f"题目{i}"),
            improvement=Improvement(plan="复习", similar_topics=["a","b","c"],
                review_count=cnt, next_review_date=nr),
        ))
    return s


def test_overdue(storage_with_overdue):
    assert len(_get_overdue_questions(storage_with_overdue)) >= 1


def test_recommend(storage_with_overdue, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.review.get_storage", lambda: storage_with_overdue)
    r = recommend_review()
    assert "priority_topics" in r and "schedule" in r and len(r["schedule"]) > 0
