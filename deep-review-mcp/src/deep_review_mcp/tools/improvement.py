# src/deep_review_mcp/tools/improvement.py
"""改进方案生成Tool"""

from deep_review_mcp.prompts.improvement_prompt import IMPROVEMENT_PROMPT


def generate_improvement(question_id: str, analysis_result: dict) -> dict:
    """根据错题分析结果生成改进方案提示词。

    Args:
        question_id: 错题ID
        analysis_result: 错题分析结果字典，包含 root_cause、error_type 等字段

    Returns:
        包含 improvement_prompt 和 question_id 的字典
    """
    prompt = IMPROVEMENT_PROMPT.format(
        question_text=analysis_result.get("question_text", ""),
        subject=analysis_result.get("subject", "未知学科"),
        knowledge_points=analysis_result.get("knowledge_points", "未知知识点"),
        error_type=analysis_result.get("error_type", "未知类型"),
        root_cause=analysis_result.get("root_cause", "未知原因"))
    return {"improvement_prompt": prompt, "question_id": question_id}
