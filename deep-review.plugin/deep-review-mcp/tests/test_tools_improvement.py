# tests/test_tools_improvement.py
from deep_review_mcp.tools.improvement import generate_improvement


def test_returns_prompt():
    r = generate_improvement("wq_001", {"root_cause": "未掌握十字相乘法", "error_type": "知识漏洞"})
    assert "improvement_prompt" in r and "十字相乘法" in r["improvement_prompt"]


def test_with_context():
    r = generate_improvement("wq_001", {
        "root_cause": "方法错误", "error_type": "方法错误",
        "subject": "数学", "knowledge_points": ["因式分解"],
        "question_text": "若x²-5x+6=0，则x=",
    })
    assert "improvement_prompt" in r
