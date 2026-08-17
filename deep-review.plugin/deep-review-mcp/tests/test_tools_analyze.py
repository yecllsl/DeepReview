# tests/test_tools_analyze.py
from datetime import UTC, datetime

import pytest

from deep_review_mcp.models import Classification, StructuredQuestion, WrongQuestion
from deep_review_mcp.storage import Storage
from deep_review_mcp.tools.analyze import analyze_error


@pytest.fixture
def storage_with_q(tmp_path):
    s = Storage(base_dir=tmp_path)
    s.save_wrong_question(WrongQuestion(
        question_id="wq_001", created_at=datetime(2026, 6, 15, 10, 30, tzinfo=UTC),
        structured=StructuredQuestion(subject="数学", grade_level="初二",
            knowledge_points=["一元二次方程"], difficulty="中等", question_type="计算题",
            question_content="若x²-5x+6=0，则x="),
        classification=Classification(error_type="方法错误", error_category="测试"),
        user_answer="x=1", correct_answer="x=2,3",
    ))
    return s


def test_analyze_returns_prompt(storage_with_q, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.analyze.get_storage", lambda: storage_with_q)
    r = analyze_error("wq_001", "x=1", "x=2,3")
    assert "analyze_prompt" in r and "一元二次方程" in r["analyze_prompt"]


def test_analyze_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.analyze.get_storage", lambda: Storage(base_dir=tmp_path))
    r = analyze_error("wq_xxx")
    assert "error" in r
