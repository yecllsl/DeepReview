# src/deep_review_mcp/tools/analyze.py
"""错误原因分析Tool

根据错题ID加载错题记录，结合用户答案与正确答案，
生成上下文感知的分析提示词，供LLM进行深度原因分析。
"""

from deep_review_mcp.prompts.analyze_prompt import ANALYZE_PROMPT
from deep_review_mcp.tools.crud import get_storage


def analyze_error(question_id: str, user_answer: str = "", correct_answer: str = "") -> dict:
    """分析错题原因，生成上下文感知的分析提示词

    Args:
        question_id: 错题ID
        user_answer: 用户答案（可选，为空时使用错题记录中的答案）
        correct_answer: 正确答案（可选，为空时使用错题记录中的答案）

    Returns:
        包含analyze_prompt、question_id、subject、knowledge_points的字典；
        若错题不存在则返回包含error的字典
    """
    storage = get_storage()
    wq = storage.load_wrong_question(question_id)
    if wq is None:
        return {"error": f"错题不存在: {question_id}"}

    # 提取结构化信息，缺失时使用默认值
    subject = wq.structured.subject if wq.structured else "未知"
    kps = ", ".join(wq.structured.knowledge_points) if wq.structured else "未知"

    # 答案优先使用传入参数，其次使用错题记录中的值
    ua = user_answer or wq.user_answer or "未提供"
    ca = correct_answer or wq.correct_answer or "未提供"

    # 使用模板生成分析提示词
    prompt = ANALYZE_PROMPT.format(
        question_text=wq.structured.question_content if wq.structured else "",
        subject=subject,
        knowledge_points=kps,
        user_answer=ua,
        correct_answer=ca,
    )

    return {
        "analyze_prompt": prompt,
        "question_id": question_id,
        "subject": subject,
        "knowledge_points": kps,
    }
