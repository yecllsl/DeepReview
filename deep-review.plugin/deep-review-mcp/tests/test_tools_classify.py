# tests/test_tools_classify.py
from deep_review_mcp.tools.classify import classify_question


def test_classify_returns_prompt():
    r = classify_question("若x²-5x+6=0，则x=", "数学")
    assert "classify_prompt" in r and "数学" in r["classify_prompt"]
