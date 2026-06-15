# src/deep_review_mcp/tools/statistics.py
"""统计查询Tool

提供多维度错题统计功能，支持按学科、错误类型、知识点、日期分组统计，
并返回最近30天的日期趋势数据。
"""

from collections import Counter
from deep_review_mcp.tools.crud import get_storage


def get_statistics(group_by: str) -> dict:
    """按指定维度统计错题分布

    Args:
        group_by: 分组维度，支持 subject/error_type/knowledge_point/date

    Returns:
        包含 items(分组统计列表)、total(总数)、trends(日期趋势) 的字典
    """
    storage = get_storage()
    questions = storage.get_all_questions_for_statistics()

    # 无数据时返回空结果
    if not questions:
        return {"items": [], "total": 0, "trends": {}}

    # 按指定维度计数
    counter = Counter()
    for wq in questions:
        if group_by == "subject":
            key = wq.structured.subject if wq.structured else "未分类"
        elif group_by == "error_type":
            key = wq.classification.error_type if wq.classification else "未分类"
        elif group_by == "knowledge_point":
            # 知识点是一对多关系，每个知识点单独计数
            if wq.structured:
                for kp in wq.structured.knowledge_points:
                    counter[kp] += 1
                continue
            key = "未分类"
        elif group_by == "date":
            key = wq.created_at.strftime("%Y-%m-%d") if wq.created_at else "未知"
        else:
            key = "未知"
        counter[key] += 1

    # 按计数降序排列
    items = [{"name": k, "count": v} for k, v in counter.most_common()]

    # 日期趋势：最近30天的每日错题数量
    dc = Counter()
    for wq in questions:
        if wq.created_at:
            dc[wq.created_at.strftime("%Y-%m-%d")] += 1

    return {"items": items, "total": len(questions), "trends": dict(sorted(dc.items())[-30:])}
