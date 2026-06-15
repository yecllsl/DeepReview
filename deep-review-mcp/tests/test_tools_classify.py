# tests/test_tools_classify.py
from deep_review_mcp.tools.classify import classify_question, _validate_classification


def test_validate_valid():
    assert _validate_classification("数学", "知识漏洞", "中等")["valid"] is True


def test_validate_invalid_subject():
    r = _validate_classification("体育", "知识漏洞", "中等")
    assert r["valid"] is False and "subject" in r["errors"]


def test_validate_invalid_error_type():
    r = _validate_classification("数学", "态度问题", "中等")
    assert r["valid"] is False and "error_type" in r["errors"]


def test_classify_returns_prompt():
    r = classify_question("若x²-5x+6=0，则x=", "数学")
    assert "classify_prompt" in r and "数学" in r["classify_prompt"]
