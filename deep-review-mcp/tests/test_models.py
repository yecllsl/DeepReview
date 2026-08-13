# tests/test_models.py
import pytest
from datetime import datetime, timezone
from deep_review_mcp.models import (
    StructuredQuestion, Classification, Analysis, Improvement,
    WrongQuestion,
)


def test_structured_question_creation():
    sq = StructuredQuestion(
        subject="数学", grade_level="初二",
        knowledge_points=["一元二次方程", "因式分解"],
        difficulty="中等", question_type="计算题",
    )
    assert sq.subject == "数学"
    assert len(sq.knowledge_points) == 2


def test_classification_error_type_validation():
    with pytest.raises(ValueError):
        Classification(error_type="无效类型", error_category="测试")


def test_classification_valid_error_types():
    for et in ["知识漏洞", "粗心失误", "方法错误", "审题失误"]:
        c = Classification(error_type=et, error_category="测试分类")
        assert c.error_type == et


def test_wrong_question_creation():
    wq = WrongQuestion(
        question_id="wq_20260615_001",
        created_at=datetime.now(timezone.utc),
    )
    assert wq.question_id == "wq_20260615_001"
    assert wq.structured is None


def test_wrong_question_full():
    wq = WrongQuestion(
        question_id="wq_20260615_002",
        created_at=datetime.now(timezone.utc),
        structured=StructuredQuestion(
            subject="数学", grade_level="初二",
            knowledge_points=["方程"], difficulty="基础", question_type="填空题",
            question_content="测试题目",
        ),
        classification=Classification(error_type="知识漏洞", error_category="方程概念不清"),
    )
    assert wq.structured.subject == "数学"
    assert wq.classification.error_type == "知识漏洞"
