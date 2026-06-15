# tests/test_tools_statistics.py
import pytest
from datetime import datetime, timezone
from deep_review_mcp.tools.statistics import get_statistics
from deep_review_mcp.storage import Storage
from deep_review_mcp.models import WrongQuestion, StructuredQuestion, Classification


@pytest.fixture
def storage_with_data(tmp_path):
    s = Storage(base_dir=tmp_path)
    for i, (subj, et) in enumerate([("数学","知识漏洞"),("数学","方法错误"),("英语","粗心失误")]):
        s.save_wrong_question(WrongQuestion(
            question_id=f"wq_{i}", created_at=datetime(2026,6,10+i,10,30,tzinfo=timezone.utc),
            raw_text=f"题目{i}",
            structured=StructuredQuestion(subject=subj, grade_level="初二",
                knowledge_points=["方程" if subj=="数学" else "时态"],
                difficulty="中等", question_type="计算题"),
            classification=Classification(error_type=et, error_category="测试"),
        ))
    return s


def test_by_subject(storage_with_data, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.statistics.get_storage", lambda: storage_with_data)
    assert get_statistics("subject")["total"] == 3


def test_by_error_type(storage_with_data, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.statistics.get_storage", lambda: storage_with_data)
    assert get_statistics("error_type")["total"] == 3
