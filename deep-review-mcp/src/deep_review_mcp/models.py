# src/deep_review_mcp/models.py
"""数据模型定义 - K12错题收集与智能分析系统的核心数据结构

包含: StructuredQuestion, Classification, Analysis, Improvement,
      WrongQuestion, ReviewScheduleItem, ReviewPlan, QueryFilters, StatisticsResult
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class StructuredQuestion(BaseModel):
    """结构化题目信息"""
    subject: str = Field(description="学科")
    grade_level: str = Field(description="年级段")
    knowledge_points: list[str] = Field(description="知识点标签列表")
    difficulty: str = Field(description="难度：基础/中等/困难")
    question_type: str = Field(description="题型")


class Classification(BaseModel):
    """错题分类信息"""
    error_type: str = Field(description="错误类型：知识漏洞/粗心失误/方法错误/审题失误")
    error_category: str = Field(description="错误细分类别")

    @field_validator("error_type")
    @classmethod
    def validate_error_type(cls, v: str) -> str:
        """校验错误类型必须为预定义值"""
        valid_types = {"知识漏洞", "粗心失误", "方法错误", "审题失误"}
        if v not in valid_types:
            raise ValueError(f"error_type必须是{valid_types}之一，收到: {v}")
        return v


class Analysis(BaseModel):
    """错题分析结果"""
    root_cause: str = Field(description="根本原因")
    cause_category: str = Field(description="原因类别")
    diagnosis_detail: str = Field(description="详细诊断说明")


class Improvement(BaseModel):
    """改进建议"""
    plan: str = Field(description="具体学习动作")
    similar_topics: list[str] = Field(description="同类题推荐方向")
    study_resources: list[str] = Field(default_factory=list, description="学习资源推荐")
    review_count: int = Field(default=0, description="已复习次数（兼容字段，由 FSRS 调度驱动）")
    next_review_date: Optional[str] = Field(default=None, description="下次复习日期（兼容字段，由 FSRS due 回填）")
    # FSRS v6 Card 序列化状态（JSON 字符串），存放 due/stability/difficulty/state/step/last_review
    # 为 None 表示尚未启用 FSRS 调度，首次 mark_reviewed 时自动初始化
    fsrs_state: Optional[str] = Field(default=None, description="FSRS Card 序列化状态(JSON)")


class WrongQuestion(BaseModel):
    """错题核心模型"""
    question_id: str = Field(description="错题唯一ID")
    created_at: datetime = Field(description="创建时间")
    image_path: Optional[str] = Field(default=None)
    raw_text: str = Field(description="OCR原始文本")
    structured: Optional[StructuredQuestion] = Field(default=None)
    classification: Optional[Classification] = Field(default=None)
    analysis: Optional[Analysis] = Field(default=None)
    improvement: Optional[Improvement] = Field(default=None)
    user_answer: Optional[str] = Field(default=None)
    correct_answer: Optional[str] = Field(default=None)


class ReviewScheduleItem(BaseModel):
    """复习计划条目"""
    date: str = Field(description="复习日期")
    question_ids: list[str] = Field(description="错题ID列表")
    subject: str = Field(description="学科")
    estimated_minutes: int = Field(description="预计时长(分钟)")


class ReviewPlan(BaseModel):
    """复习计划"""
    plan_id: str = Field(description="计划ID")
    created_at: datetime = Field(description="创建时间")
    priority_topics: list[str] = Field(description="优先复习知识点")
    schedule: list[ReviewScheduleItem] = Field(description="每日安排")


class QueryFilters(BaseModel):
    """查询过滤条件"""
    subject: Optional[str] = Field(default=None)
    knowledge_point: Optional[str] = Field(default=None)
    error_type: Optional[str] = Field(default=None)
    date_range: Optional[dict[str, str]] = Field(default=None)


class StatisticsResult(BaseModel):
    """统计结果"""
    group_by: str
    items: list[dict]
    total: int
