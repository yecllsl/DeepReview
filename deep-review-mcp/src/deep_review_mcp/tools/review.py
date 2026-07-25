# src/deep_review_mcp/tools/review.py
"""复习推荐Tool - 基于遗忘曲线

根据艾宾浩斯遗忘曲线，为用户推荐需要复习的错题，
生成优先知识点列表和每日复习计划。
"""

from datetime import datetime, timezone, timedelta
from collections import Counter
from deep_review_mcp.tools.crud import get_storage
from deep_review_mcp.models import WrongQuestion


def _get_overdue_questions(storage) -> list[WrongQuestion]:
    """获取已到复习日期的错题

    遍历所有错题，筛选出improvement中next_review_date
    已到期（<=今天）的错题列表。

    Args:
        storage: Storage实例

    Returns:
        需要复习的错题列表
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return [wq for qid in storage.list_all_question_ids()
            if (wq := storage.load_wrong_question(qid))
            and wq.improvement and wq.improvement.next_review_date
            and wq.improvement.next_review_date <= today]


def recommend_review(time_range: str = "", subject: str = "") -> dict:
    """生成复习推荐计划

    基于遗忘曲线，获取所有到期需要复习的错题，
    按知识点统计优先级，并生成每日复习计划（每天最多5题）。

    Args:
        time_range: 时间范围过滤（预留参数）
        subject: 学科过滤，为空则不过滤

    Returns:
        包含review_plan、priority_topics、schedule的字典
    """
    storage = get_storage()
    overdue = _get_overdue_questions(storage)

    # 按学科过滤
    if subject:
        overdue = [wq for wq in overdue if wq.structured and wq.structured.subject == subject]

    # 没有需要复习的错题
    if not overdue:
        return {"review_plan": None, "priority_topics": [], "schedule": [],
                "message": "当前没有需要复习的错题"}

    # 统计知识点出现频率，取前10作为优先复习知识点
    tc = Counter()
    for wq in overdue:
        if wq.structured:
            for kp in wq.structured.knowledge_points:
                tc[kp] += 1
    priority = [t for t, _ in tc.most_common(10)]

    # 生成每日复习计划，每天最多5题
    schedule, cur, daily, subj = [], datetime.now(timezone.utc), [], ""
    for wq in overdue:
        if len(daily) >= 5:
            schedule.append({"date": cur.strftime("%Y-%m-%d"), "question_ids": daily,
                             "subject": subj, "estimated_minutes": len(daily) * 15})
            cur += timedelta(days=1)
            daily = []
        daily.append(wq.question_id)
        if wq.structured:
            subj = wq.structured.subject
    if daily:
        schedule.append({"date": cur.strftime("%Y-%m-%d"), "question_ids": daily,
                         "subject": subj, "estimated_minutes": len(daily) * 15})

    return {"review_plan": {"total_questions": len(overdue), "total_days": len(schedule)},
            "priority_topics": priority, "schedule": schedule}
