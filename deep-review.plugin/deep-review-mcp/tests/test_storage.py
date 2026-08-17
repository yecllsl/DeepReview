# tests/test_storage.py
from datetime import UTC, datetime

import pytest

from deep_review_mcp.models import Classification, StructuredQuestion, WrongQuestion
from deep_review_mcp.storage import Storage


@pytest.fixture
def tmp_storage(tmp_path):
    return Storage(base_dir=tmp_path)


@pytest.fixture
def sample_question():
    return WrongQuestion(
        question_id="wq_20260615_001",
        created_at=datetime(2026, 6, 15, 10, 30, tzinfo=UTC),
        structured=StructuredQuestion(
            subject="数学", grade_level="初二",
            knowledge_points=["一元二次方程", "因式分解"],
            difficulty="中等", question_type="计算题",
            question_content="若x²-5x+6=0，则x=",
        ),
    )


def test_save_and_load(tmp_storage, sample_question):
    result = tmp_storage.save_wrong_question(sample_question)
    assert result["question_id"] == "wq_20260615_001"
    loaded = tmp_storage.load_wrong_question("wq_20260615_001")
    assert loaded.structured.question_content == sample_question.structured.question_content


def test_query_by_subject(tmp_storage, sample_question):
    tmp_storage.save_wrong_question(sample_question)
    assert tmp_storage.query_wrong_questions(filters={"subject": "数学"})["total_count"] == 1
    assert tmp_storage.query_wrong_questions(filters={"subject": "语文"})["total_count"] == 0


def test_query_by_error_type(tmp_storage, sample_question):
    sample_question.classification = Classification(error_type="知识漏洞", error_category="测试")
    tmp_storage.save_wrong_question(sample_question)
    assert tmp_storage.query_wrong_questions(filters={"error_type": "知识漏洞"})["total_count"] == 1


def test_update(tmp_storage, sample_question):
    tmp_storage.save_wrong_question(sample_question)
    sample_question.structured.question_content = "更新后"
    tmp_storage.update_wrong_question(sample_question)
    assert tmp_storage.load_wrong_question("wq_20260615_001").structured.question_content == "更新后"


def test_delete(tmp_storage, sample_question):
    tmp_storage.save_wrong_question(sample_question)
    tmp_storage.delete_wrong_question("wq_20260615_001")
    assert tmp_storage.load_wrong_question("wq_20260615_001") is None


def test_list_ids(tmp_storage, sample_question):
    tmp_storage.save_wrong_question(sample_question)
    assert "wq_20260615_001" in tmp_storage.list_all_question_ids()
