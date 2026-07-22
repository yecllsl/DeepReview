# web/services.py
"""Web 服务层 — 编排 storage / statistics / review

作为路由层和数据层之间的薄编排层，不复制数据访问逻辑。
所有读写都通过 storage / statistics / review 完成。
"""
from collections import Counter
from datetime import datetime, timezone, timedelta
from typing import Optional

from deep_review_mcp.models import WrongQuestion
from deep_review_mcp.storage import Storage
from deep_review_mcp.tools.crud import get_storage as _default_get_storage
from deep_review_mcp.tools.statistics import get_statistics


def _get_storage() -> Storage:
    """获取 Storage 实例（可被测试 monkeypatch 覆盖）"""
    return _default_get_storage()


# ──────────────────────────────────────────
# Dashboard 概览
# ──────────────────────────────────────────

def get_dashboard_summary() -> dict:
    """获取 Dashboard 概览数据

    返回：KPI 指标 + 学科分布 + 错误类型分布 + 30天趋势
    """
    storage = _get_storage()
    questions = storage.get_all_questions_for_statistics()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

    # KPI 指标
    total = len(questions)
    today_pending = sum(
        1 for wq in questions
        if wq.improvement and wq.improvement.next_review_date
        and wq.improvement.next_review_date <= today
    )
    week_new = sum(
        1 for wq in questions
        if wq.created_at and wq.created_at.strftime("%Y-%m-%d") >= week_ago
    )
    week_reviewed = sum(
        1 for wq in questions
        if wq.improvement and wq.improvement.review_count > 0
        # 简化：统计已复习过的错题数
    )

    # 学科分布
    subject_counter = Counter()
    error_type_counter = Counter()
    for wq in questions:
        if wq.structured:
            subject_counter[wq.structured.subject] += 1
        else:
            subject_counter["未分类"] += 1
        if wq.classification:
            error_type_counter[wq.classification.error_type] += 1
        else:
            error_type_counter["未分类"] += 1

    # 30天趋势
    trend_counter = Counter()
    for wq in questions:
        if wq.created_at:
            trend_counter[wq.created_at.strftime("%Y-%m-%d")] += 1
    # 补全最近30天（含无错题的日期）
    trends = {}
    for i in range(30):
        day = (datetime.now(timezone.utc) - timedelta(days=29 - i)).strftime("%Y-%m-%d")
        trends[day] = trend_counter.get(day, 0)

    return {
        "total": total,
        "today_pending": today_pending,
        "week_new": week_new,
        "week_reviewed": week_reviewed,
        "subject_distribution": [
            {"name": k, "value": v} for k, v in subject_counter.most_common()
        ],
        "error_type_distribution": [
            {"name": k, "value": v} for k, v in error_type_counter.most_common()
        ],
        "trends": trends,
    }


# ──────────────────────────────────────────
# 多维统计（统计图表页）
# ──────────────────────────────────────────

def get_multi_dim_stats() -> dict:
    """获取多维度统计数据

    返回：知识点热力图数据、难度分布、错误类型雷达、时间趋势
    """
    storage = _get_storage()
    questions = storage.get_all_questions_for_statistics()

    # 知识点热力图：[学科, 知识点, 错误次数]
    kp_counter: dict[tuple[str, str], int] = {}
    for wq in questions:
        if wq.structured:
            subj = wq.structured.subject
            for kp in wq.structured.knowledge_points:
                key = (subj, kp)
                kp_counter[key] = kp_counter.get(key, 0) + 1
    knowledge_heatmap = [
        {"subject": subj, "knowledge_point": kp, "count": count}
        for (subj, kp), count in sorted(kp_counter.items())
    ]

    # 难度分布：按学科分难度
    difficulty_data: dict[str, Counter] = {}
    for wq in questions:
        if wq.structured:
            subj = wq.structured.subject
            diff = wq.structured.difficulty
            if subj not in difficulty_data:
                difficulty_data[subj] = Counter()
            difficulty_data[subj][diff] += 1
    difficulty_distribution = [
        {"subject": subj, "basic": data.get("基础", 0),
         "medium": data.get("中等", 0), "hard": data.get("困难", 0)}
        for subj, data in difficulty_data.items()
    ]

    # 错误类型雷达
    error_type_counter = Counter()
    for wq in questions:
        if wq.classification:
            error_type_counter[wq.classification.error_type] += 1
    error_type_radar = [
        {"name": et, "value": error_type_counter.get(et, 0)}
        for et in ["知识漏洞", "粗心失误", "方法错误", "审题失误"]
    ]

    # 时间趋势（最近30天）
    trend_counter = Counter()
    for wq in questions:
        if wq.created_at:
            trend_counter[wq.created_at.strftime("%Y-%m-%d")] += 1
    trend_data = []
    for i in range(30):
        day = (datetime.now(timezone.utc) - timedelta(days=29 - i)).strftime("%Y-%m-%d")
        trend_data.append({"date": day, "count": trend_counter.get(day, 0)})

    return {
        "knowledge_heatmap": knowledge_heatmap,
        "difficulty_distribution": difficulty_distribution,
        "error_type_radar": error_type_radar,
        "trend_data": trend_data,
        "total": len(questions),
    }


# ──────────────────────────────────────────
# 统计查询（复用 statistics 模块）
# ──────────────────────────────────────────

def get_stats_by_dimension(group_by: str) -> dict:
    """按维度获取统计（复用 statistics.get_statistics）"""
    return get_statistics(group_by=group_by)


# ──────────────────────────────────────────
# 待复习列表
# ──────────────────────────────────────────

def get_upcoming_reviews() -> list[dict]:
    """获取待复习错题列表

    返回已到期（next_review_date <= 今天）的错题列表，
    按到期日期升序排列。
    """
    storage = _get_storage()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    upcoming = []
    for qid in storage.list_all_question_ids():
        wq = storage.load_wrong_question(qid)
        if not wq or not wq.improvement:
            continue
        if not wq.improvement.next_review_date:
            continue
        if wq.improvement.next_review_date <= today:
            upcoming.append({
                "question_id": wq.question_id,
                "raw_text": wq.raw_text[:100] + ("..." if len(wq.raw_text) > 100 else ""),
                "subject": wq.structured.subject if wq.structured else "未分类",
                "error_type": wq.classification.error_type if wq.classification else "未分类",
                "next_review_date": wq.improvement.next_review_date,
                "review_count": wq.improvement.review_count,
                "is_overdue": wq.improvement.next_review_date < today,
            })

    # 按到期日期升序
    upcoming.sort(key=lambda x: x["next_review_date"])
    return upcoming


# ──────────────────────────────────────────
# 标记复习
# ──────────────────────────────────────────

def mark_question_reviewed(question_id: str) -> Optional[dict]:
    """标记错题为已复习

    递增 review_count，重算 next_review_date。
    """
    storage = _get_storage()
    updated = storage.mark_reviewed(question_id)
    if updated is None or updated.improvement is None:
        return None
    return {
        "question_id": updated.question_id,
        "review_count": updated.improvement.review_count,
        "next_review_date": updated.improvement.next_review_date or "",
    }


# ──────────────────────────────────────────
# 编辑保存
# ──────────────────────────────────────────

def update_question(question_id: str, data: dict) -> Optional[WrongQuestion]:
    """编辑保存错题

    将扁平的表单数据转换为嵌套的 patch 结构，调用 storage.patch_wrong_question。
    """
    storage = _get_storage()
    patch: dict = {}

    # 顶层字段
    for field in ["raw_text", "user_answer", "correct_answer"]:
        if field in data and data[field] is not None:
            patch[field] = data[field]

    # structured 嵌套字段
    structured_patch: dict = {}
    for field in ["subject", "grade_level", "knowledge_points", "difficulty", "question_type"]:
        if field in data and data[field] is not None:
            structured_patch[field] = data[field]
    if structured_patch:
        patch["structured"] = structured_patch

    # classification 嵌套字段
    classification_patch: dict = {}
    for field in ["error_type", "error_category"]:
        if field in data and data[field] is not None:
            classification_patch[field] = data[field]
    if classification_patch:
        patch["classification"] = classification_patch

    # analysis 嵌套字段
    analysis_patch: dict = {}
    for field in ["root_cause", "cause_category", "diagnosis_detail"]:
        if field in data and data[field] is not None:
            analysis_patch[field] = data[field]
    if analysis_patch:
        patch["analysis"] = analysis_patch

    # improvement 嵌套字段
    improvement_patch: dict = {}
    for field in ["plan", "similar_topics", "study_resources", "next_review_date"]:
        if field in data and data[field] is not None:
            improvement_patch[field] = data[field]
    if improvement_patch:
        patch["improvement"] = improvement_patch

    return storage.patch_wrong_question(question_id, patch)


# ──────────────────────────────────────────
# 筛选查询
# ──────────────────────────────────────────

def get_filtered_questions(filters: dict) -> dict:
    """获取筛选后的错题列表

    复用 storage.query_wrong_questions。
    """
    return _get_storage().query_wrong_questions(filters=filters)


# ──────────────────────────────────────────
# 单题详情
# ──────────────────────────────────────────

def get_question_detail(question_id: str) -> Optional[WrongQuestion]:
    """获取单题详情"""
    return _get_storage().load_wrong_question(question_id)
