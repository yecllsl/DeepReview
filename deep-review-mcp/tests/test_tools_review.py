# tests/test_tools_review.py
import pytest
from datetime import datetime, timezone, timedelta
from deep_review_mcp.tools.review import recommend_review, _calculate_next_review_date, _get_overdue_questions
from deep_review_mcp.storage import Storage
from deep_review_mcp.models import WrongQuestion, StructuredQuestion, Improvement


@pytest.fixture
def storage_with_overdue(tmp_path):
    s = Storage(base_dir=tmp_path)
    for i, (offset, cnt) in enumerate([(0, 0), (5, 1), (10, 2)]):
        nr = (datetime.now(timezone.utc) - timedelta(days=offset)).strftime("%Y-%m-%d")
        s.save_wrong_question(WrongQuestion(
            question_id=f"wq_{i}", created_at=datetime(2026, 6, 10+i, 10, 30, tzinfo=timezone.utc),
            raw_text=f"题目{i}",
            structured=StructuredQuestion(subject="数学", grade_level="初二",
                knowledge_points=["方程"], difficulty="基础", question_type="计算题"),
            improvement=Improvement(plan="复习", similar_topics=["a","b","c"],
                review_count=cnt, next_review_date=nr),
        ))
    return s


def test_intervals():
    assert _calculate_next_review_date(0) == 1
    assert _calculate_next_review_date(1) == 3
    assert _calculate_next_review_date(2) == 7
    assert _calculate_next_review_date(3) == 14
    assert _calculate_next_review_date(4) == 30


def test_overdue(storage_with_overdue):
    assert len(_get_overdue_questions(storage_with_overdue)) >= 1


def test_recommend(storage_with_overdue, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.review.get_storage", lambda: storage_with_overdue)
    r = recommend_review()
    assert "priority_topics" in r and "schedule" in r and len(r["schedule"]) > 0
