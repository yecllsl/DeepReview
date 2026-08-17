# tests/test_tools_crud.py
from datetime import UTC, datetime

import pytest

from deep_review_mcp.storage import Storage
from deep_review_mcp.tools.crud import (
    query_wrong_questions,
    save_wrong_question,
    update_wrong_question,
)


@pytest.fixture
def tmp_storage(tmp_path):
    return Storage(base_dir=tmp_path)


def test_save_tool(tmp_storage, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.crud.get_storage", lambda: tmp_storage)
    result = save_wrong_question(question_data={
        "question_id": "wq_20260615_001",
        "created_at": datetime(2026, 6, 15, 10, 30, tzinfo=UTC).isoformat(),
    })
    assert result["question_id"] == "wq_20260615_001"


def test_save_fills_required_defaults(tmp_storage, monkeypatch):
    """structured/classification 缺失时填充规则默认值（业务规则 #6，回归 I1）"""
    monkeypatch.setattr("deep_review_mcp.tools.crud.get_storage", lambda: tmp_storage)
    save_wrong_question(question_data={
        "question_id": "wq_20260615_002",
        "created_at": datetime(2026, 6, 15, 10, 30, tzinfo=UTC).isoformat(),
    })
    saved = query_wrong_questions(filters={})["questions"][0]
    assert saved["structured"]["subject"] == "数学"
    assert saved["structured"]["difficulty"] == "中等"
    assert saved["classification"]["error_type"] == "知识漏洞"


def test_query_tool(tmp_storage, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.crud.get_storage", lambda: tmp_storage)
    save_wrong_question(question_data={
        "question_id": "wq_20260615_001",
        "created_at": datetime(2026, 6, 15, 10, 30, tzinfo=UTC).isoformat(),
        "structured": {
            "subject": "数学", "grade_level": "初二",
            "knowledge_points": ["方程"], "difficulty": "基础", "question_type": "计算题",
            "question_content": "测试",
        },
    })
    assert query_wrong_questions(filters={"subject": "数学"})["total_count"] == 1


def test_update_tool(tmp_storage, monkeypatch):
    """update 覆盖写入时保留原字段（回归：不误伤已有数据）"""
    monkeypatch.setattr("deep_review_mcp.tools.crud.get_storage", lambda: tmp_storage)
    question_data = {
        "question_id": "wq_20260615_003",
        "created_at": datetime(2026, 6, 15, 10, 30, tzinfo=UTC).isoformat(),
        "structured": {
            "subject": "数学", "grade_level": "初二",
            "knowledge_points": ["方程"], "difficulty": "基础", "question_type": "计算题",
            "question_content": "原题",
        },
        "classification": {"error_type": "审题失误", "error_category": "细分类别"},
    }
    update_wrong_question(question_data=question_data)
    saved = query_wrong_questions(filters={})["questions"][0]
    assert saved["structured"]["question_content"] == "原题"
    assert saved["classification"]["error_type"] == "审题失误"


def test_update_fills_required_defaults(tmp_storage, monkeypatch):
    """update 传回全量记录缺 structured/classification 时兜底默认值（回归 I2）"""
    monkeypatch.setattr("deep_review_mcp.tools.crud.get_storage", lambda: tmp_storage)
    update_wrong_question(question_data={
        "question_id": "wq_20260615_004",
        "created_at": datetime(2026, 6, 15, 10, 30, tzinfo=UTC).isoformat(),
    })
    saved = query_wrong_questions(filters={})["questions"][0]
    assert saved["structured"]["subject"] == "数学"
    assert saved["classification"]["error_type"] == "知识漏洞"
