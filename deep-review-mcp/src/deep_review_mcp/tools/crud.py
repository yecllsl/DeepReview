# src/deep_review_mcp/tools/crud.py
"""错题数据CRUD操作Tools

提供错题的保存、查询、更新、删除功能，作为MCP Tool的业务逻辑层。
底层调用 Storage 引擎完成实际的文件IO操作。
"""

from pathlib import Path
from deep_review_mcp.models import (
    Classification,
    StructuredQuestion,
    WrongQuestion,
)
from deep_review_mcp.storage import Storage

# 默认数据目录：项目根目录下的 data/ 文件夹
_DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"


def _fill_required_defaults(question_data: dict) -> dict:
    """为缺失的 structured/classification 填充规则默认值（业务规则 #6）

    structured 与 classification 是统计分析的前置条件（规则 #5），
    缺失会导致数据不可用。AI 未解析出结构时用待确认默认值填充，
    structured 缺失默认 subject=数学/difficulty=中等，
    classification 缺失默认 error_type=知识漏洞。
    """
    data = dict(question_data)
    if not data.get("structured"):
        data["structured"] = StructuredQuestion(
            subject="数学",
            grade_level="待确认",
            knowledge_points=[],
            difficulty="中等",
            question_type="待确认",
        ).model_dump()
    if not data.get("classification"):
        data["classification"] = Classification(
            error_type="知识漏洞",
            error_category="待确认",
        ).model_dump()
    return data


def get_storage() -> Storage:
    """获取默认Storage实例（指向项目data目录）"""
    return Storage(base_dir=_DEFAULT_DATA_DIR)


def save_wrong_question(question_data: dict) -> dict:
    """保存错题记录

    Args:
        question_data: 错题数据字典，需符合WrongQuestion模型结构

    Returns:
        包含question_id和saved_path的字典
    """
    storage = get_storage()
    filled = _fill_required_defaults(question_data)
    wq = WrongQuestion.model_validate(filled)
    return storage.save_wrong_question(wq)


def query_wrong_questions(filters: dict) -> dict:
    """按条件查询错题

    Args:
        filters: 过滤条件字典，支持subject/knowledge_point/error_type/date_range

    Returns:
        包含questions列表和total_count的字典
    """
    return get_storage().query_wrong_questions(filters=filters)


def update_wrong_question(question_data: dict) -> dict:
    """更新错题记录（覆盖写入）

    Args:
        question_data: 完整的错题数据字典，需包含question_id

    Returns:
        包含question_id和saved_path的字典
    """
    storage = get_storage()
    wq = WrongQuestion.model_validate(question_data)
    return storage.update_wrong_question(wq)


def delete_wrong_question(question_id: str) -> dict:
    """删除错题记录

    Args:
        question_id: 要删除的错题ID

    Returns:
        包含deleted状态和question_id的字典
    """
    success = get_storage().delete_wrong_question(question_id)
    return {"deleted": success, "question_id": question_id}
