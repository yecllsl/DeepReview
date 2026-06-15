# tests/test_tools_export.py
import pytest
from pathlib import Path
from datetime import datetime, timezone
from deep_review_mcp.tools.export import export_data
from deep_review_mcp.storage import Storage
from deep_review_mcp.models import WrongQuestion


@pytest.fixture
def storage_with_q(tmp_path):
    s = Storage(base_dir=tmp_path)
    s.save_wrong_question(WrongQuestion(
        question_id="wq_001", created_at=datetime(2026,6,15,10,30,tzinfo=timezone.utc),
        raw_text="测试题目"))
    return s


def test_export_json(storage_with_q, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.export.get_storage", lambda: storage_with_q)
    r = export_data("json", {})
    assert "file_path" in r and Path(r["file_path"]).exists()


def test_export_markdown(storage_with_q, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.export.get_storage", lambda: storage_with_q)
    r = export_data("markdown", {})
    assert "file_path" in r and "测试题目" in Path(r["file_path"]).read_text(encoding="utf-8")
