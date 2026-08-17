# tests/test_tools_crud.py
import pytest
from datetime import datetime, timezone
from deep_review_mcp.tools.crud import save_wrong_question, query_wrong_questions
from deep_review_mcp.storage import Storage


@pytest.fixture
def tmp_storage(tmp_path):
    return Storage(base_dir=tmp_path)


def test_save_tool(tmp_storage, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.crud.get_storage", lambda: tmp_storage)
    result = save_wrong_question(question_data={
        "question_id": "wq_20260615_001",
        "created_at": datetime(2026, 6, 15, 10, 30, tzinfo=timezone.utc).isoformat(),
    })
    assert result["question_id"] == "wq_20260615_001"


def test_save_fills_required_defaults(tmp_storage, monkeypatch):
    """structured/classification 缺失时填充规则默认值（业务规则 #6，回归 I1）"""
    monkeypatch.setattr("deep_review_mcp.tools.crud.get_storage", lambda: tmp_storage)
    save_wrong_question(question_data={
        "question_id": "wq_20260615_002",
        "created_at": datetime(2026, 6, 15, 10, 30, tzinfo=timezone.utc).isoformat(),
    })
    saved = query_wrong_questions(filters={})["questions"][0]
    assert saved["structured"]["subject"] == "数学"
    assert saved["structured"]["difficulty"] == "中等"
    assert saved["classification"]["error_type"] == "知识漏洞"


def test_query_tool(tmp_storage, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.crud.get_storage", lambda: tmp_storage)
    save_wrong_question(question_data={
        "question_id": "wq_20260615_001",
        "created_at": datetime(2026, 6, 15, 10, 30, tzinfo=timezone.utc).isoformat(),
        "structured": {
            "subject": "数学", "grade_level": "初二",
            "knowledge_points": ["方程"], "difficulty": "基础", "question_type": "计算题",
            "question_content": "测试",
        },
    })
    assert query_wrong_questions(filters={"subject": "数学"})["total_count"] == 1
