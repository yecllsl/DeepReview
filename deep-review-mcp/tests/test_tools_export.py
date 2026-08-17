# tests/test_tools_export.py
import pytest
from pathlib import Path
from datetime import datetime, timezone
from deep_review_mcp.tools.export import export_data
from deep_review_mcp.storage import Storage
from deep_review_mcp.models import StructuredQuestion, WrongQuestion


@pytest.fixture
def storage_with_q(tmp_path):
    s = Storage(base_dir=tmp_path)
    s.save_wrong_question(WrongQuestion(
        question_id="wq_001", created_at=datetime(2026,6,15,10,30,tzinfo=timezone.utc),
        structured=StructuredQuestion(
            subject="数学", grade_level="初二",
            knowledge_points=["方程"], difficulty="中等", question_type="计算题",
            question_content="测试题目")))
    return s


@pytest.fixture
def storage_with_unstructured(tmp_path):
    """含 structured=None 的存量记录（回填前兼容场景）"""
    s = Storage(base_dir=tmp_path)
    s.save_wrong_question(WrongQuestion(
        question_id="wq_null", created_at=datetime(2026,6,16,10,30,tzinfo=timezone.utc),
        structured=None))
    return s


def test_export_json(storage_with_q, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.export.get_storage", lambda: storage_with_q)
    r = export_data("json", {})
    assert "file_path" in r and Path(r["file_path"]).exists()


def test_export_markdown(storage_with_q, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.export.get_storage", lambda: storage_with_q)
    r = export_data("markdown", {})
    assert "file_path" in r and "测试题目" in Path(r["file_path"]).read_text(encoding="utf-8")


def test_export_markdown_with_unstructured(storage_with_unstructured, monkeypatch):
    """structured=None 记录在 markdown 导出时不崩溃（回归 I2）"""
    monkeypatch.setattr("deep_review_mcp.tools.export.get_storage",
                        lambda: storage_with_unstructured)
    r = export_data("markdown", {})
    assert "file_path" in r and "wq_null" in Path(r["file_path"]).read_text(encoding="utf-8")
