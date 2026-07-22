# web/schemas.py
"""Web 请求/响应 Pydantic 模型

定义 Web 层特有的数据结构，与 models.py 中的核心模型分离。
用于 API 请求体验证和响应序列化。
"""
from typing import Optional

from pydantic import BaseModel


class QuestionUpdateRequest(BaseModel):
    """错题编辑保存请求体

    所有字段可选，只更新提交的字段。
    """
    raw_text: Optional[str] = None
    user_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    # structured 嵌套字段
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    knowledge_points: Optional[list[str]] = None
    difficulty: Optional[str] = None
    question_type: Optional[str] = None
    # classification 嵌套字段
    error_type: Optional[str] = None
    error_category: Optional[str] = None
    # analysis 嵌套字段
    root_cause: Optional[str] = None
    cause_category: Optional[str] = None
    diagnosis_detail: Optional[str] = None
    # improvement 嵌套字段
    plan: Optional[str] = None
    similar_topics: Optional[list[str]] = None
    study_resources: Optional[list[str]] = None
    next_review_date: Optional[str] = None


class ReviewDoneResponse(BaseModel):
    """标记复习完成响应"""
    question_id: str
    review_count: int
    next_review_date: str
