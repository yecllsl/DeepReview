# src/deep_review_mcp/tools/classify.py
"""智能分类Tool - 对错题进行学科、错误类型、难度分类"""

from deep_review_mcp.knowledge_map import SUBJECTS, ERROR_TYPES, DIFFICULTY_LEVELS, get_knowledge_points
from deep_review_mcp.prompts.classify_prompt import CLASSIFY_PROMPT


def classify_question(question_text: str, subject: str = "") -> dict:
    """对错题进行智能分类，返回分类提示词和可用分类选项

    Args:
        question_text: 题目文本内容
        subject: 学科名称，为空时由LLM自动判断

    Returns:
        包含分类提示词、可用学科/错误类型/难度/知识点列表的字典
    """
    prompt = CLASSIFY_PROMPT.format(
        question_text=question_text,
        subject=subject or "请根据题目内容判断"
    )
    result = {
        "classify_prompt": prompt,
        "available_subjects": SUBJECTS,
        "available_error_types": ERROR_TYPES,
        "available_difficulty": DIFFICULTY_LEVELS,
    }
    # 如果指定了合法学科，附带该学科的知识点列表
    if subject and subject in SUBJECTS:
        result["available_knowledge_points"] = get_knowledge_points(subject)
    return result
