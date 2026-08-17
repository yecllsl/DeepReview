# web/services.py
"""Web 服务层 — 编排 storage / statistics / review

作为路由层和数据层之间的薄编排层，不复制数据访问逻辑。
所有读写都通过 storage / statistics / review 完成。
"""
from collections import Counter
from datetime import UTC, datetime, timedelta

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

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    week_ago = (datetime.now(UTC) - timedelta(days=7)).strftime("%Y-%m-%d")

    # KPI 指标
    total = len(questions)
    today_pending = sum(
        1 for wq in questions
        if wq.improvement and wq.improvement.next_review_date
        and wq.improvement.next_review_date <= today
    )
    week_new = 0
    for wq in questions:
        if wq.created_at and wq.created_at.strftime("%Y-%m-%d") >= week_ago:
            week_new += 1
    week_reviewed = sum(
        1 for wq in questions
        if wq.improvement and wq.improvement.review_count > 0
        # 简化：统计已复习过的错题数
    )

    # 学科分布
    subject_counter: Counter[str] = Counter()
    error_type_counter: Counter[str] = Counter()
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
    trend_counter: Counter[str] = Counter()
    for wq in questions:
        if wq.created_at:
            trend_counter[wq.created_at.strftime("%Y-%m-%d")] += 1
    # 补全最近30天（含无错题的日期）
    trends: dict[str, int] = {}
    for i in range(30):
        day = (datetime.now(UTC) - timedelta(days=29 - i)).strftime("%Y-%m-%d")
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
    difficulty_data: dict[str, Counter[str]] = {}
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
    error_type_counter: Counter[str] = Counter()
    for wq in questions:
        if wq.classification:
            error_type_counter[wq.classification.error_type] += 1
    error_type_radar = [
        {"name": et, "value": error_type_counter.get(et, 0)}
        for et in ["知识漏洞", "粗心失误", "方法错误", "审题失误"]
    ]

    # 时间趋势（最近30天）
    trend_counter: Counter[str] = Counter()
    for wq in questions:
        if wq.created_at:
            trend_counter[wq.created_at.strftime("%Y-%m-%d")] += 1
    trend_data: list[dict[str, str | int]] = []
    for i in range(30):
        day = (datetime.now(UTC) - timedelta(days=29 - i)).strftime("%Y-%m-%d")
        count: int = trend_counter.get(day, 0)
        trend_data.append({"date": day, "count": count})

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
    today = datetime.now(UTC).strftime("%Y-%m-%d")

    upcoming: list[dict[str, object]] = []
    for qid in storage.list_all_question_ids():
        wq = storage.load_wrong_question(qid)
        if not wq or not wq.improvement:
            continue
        if not wq.improvement.next_review_date:
            continue
        if wq.improvement.next_review_date <= today:
            qc = wq.structured.question_content if wq.structured and wq.structured.question_content else "暂无内容"
            upcoming.append({
                "question_id": wq.question_id,
                "question_content": qc[:100] + ("..." if len(qc) > 100 else ""),
                "subject": wq.structured.subject if wq.structured else "未分类",
                "error_type": wq.classification.error_type if wq.classification else "未分类",
                "next_review_date": wq.improvement.next_review_date,
                "review_count": wq.improvement.review_count,
                "is_overdue": wq.improvement.next_review_date < today,
            })

    # 按到期日期升序（next_review_date 为 "YYYY-MM-DD" 字符串）
    upcoming.sort(key=lambda x: str(x["next_review_date"]))
    return upcoming


# ──────────────────────────────────────────
# 标记复习
# ──────────────────────────────────────────

def mark_question_reviewed(question_id: str, rating: int = 3) -> dict | None:
    """标记错题为已复习，基于 FSRS 调度

    Args:
        question_id: 错题ID
        rating: 1=Again 2=Hard 3=Good 4=Easy（默认 Good，向后兼容）
    """
    storage = _get_storage()
    updated = storage.mark_reviewed(question_id, rating)
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

def update_question(question_id: str, data: dict) -> WrongQuestion | None:
    """编辑保存错题

    将扁平的表单数据转换为嵌套的 patch 结构，调用 storage.patch_wrong_question。
    当原始数据的嵌套字段为 null 时，先填入默认值模板确保 Pydantic 必填字段不缺失。
    """
    storage = _get_storage()
    existing = storage.load_wrong_question(question_id)
    if existing is None:
        return None

    patch: dict = {}

    # 顶层字段
    for field in ["user_answer", "correct_answer"]:
        if field in data and data[field] is not None:
            patch[field] = data[field]

    # structured 嵌套字段
    # 如果原始 structured 为 null，先填入默认值模板，避免 Pydantic 校验缺少必填字段
    structured_patch: dict = {}
    if existing.structured is None:
        structured_patch = {
            "subject": "数学",
            "grade_level": "高中",
            "knowledge_points": [],
            "difficulty": "中等",
            "question_type": "其他",
        }
    for field in ["subject", "grade_level", "knowledge_points", "difficulty", "question_type", "question_content"]:
        if field in data and data[field] is not None:
            structured_patch[field] = data[field]
    if structured_patch:
        patch["structured"] = structured_patch

    # classification 嵌套字段
    classification_patch: dict = {}
    if existing.classification is None:
        classification_patch = {
            "error_type": "知识漏洞",
            "error_category": "待分类",
        }
    for field in ["error_type", "error_category"]:
        if field in data and data[field] is not None:
            classification_patch[field] = data[field]
    if classification_patch:
        patch["classification"] = classification_patch

    # analysis 嵌套字段
    analysis_patch: dict = {}
    if existing.analysis is None:
        analysis_patch = {
            "root_cause": "待分析",
            "cause_category": "待分析",
            "diagnosis_detail": "",
        }
    for field in ["root_cause", "cause_category", "diagnosis_detail"]:
        if field in data and data[field] is not None:
            analysis_patch[field] = data[field]
    if analysis_patch:
        patch["analysis"] = analysis_patch

    # improvement 嵌套字段
    improvement_patch: dict = {}
    if existing.improvement is None:
        improvement_patch = {
            "plan": "",
            "similar_topics": [],
        }
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

def get_question_detail(question_id: str) -> WrongQuestion | None:
    """获取单题详情"""
    return _get_storage().load_wrong_question(question_id)


# ──────────────────────────────────────────
# FSRS 参数优化（UI 主动触发）
# ──────────────────────────────────────────

def get_fsrs_optimization_status() -> dict:
    """获取 FSRS 参数优化的当前状态（供 UI 展示）

    返回：
        - current_scheduler: 当前调度器信息（默认/个性化、目标保持率等）
        - review_log_count: 已积累的 ReviewLog 数量
        - progress: 进度比例（count/1000），用于 UI 进度条
        - has_persisted_params: 是否有已持久化的优化参数
    """
    # 局部导入避免 services ↔ tools 循环依赖
    from deep_review_mcp.tools.fsrs_scheduler import get_current_scheduler_info

    storage = _get_storage()
    all_logs = storage.list_all_review_logs()
    scheduler_info = get_current_scheduler_info()

    # 检查是否有持久化参数文件
    has_persisted = storage.fsrs_params_file.exists()

    return {
        "current_scheduler": scheduler_info,
        "review_log_count": len(all_logs),
        "progress": round(len(all_logs) / 1000, 4),  # 0-1，UI 进度条用
        "has_persisted_params": has_persisted,
    }


def run_fsrs_optimization() -> dict:
    """触发 FSRS 参数优化计算（不应用，仅返回结果供 UI 展示）

    Returns:
        optimize_parameters 的返回结果，含 success/parameters/desired_retention/warning/error
    """
    from deep_review_mcp.tools.fsrs_scheduler import optimize_parameters

    storage = _get_storage()
    all_logs = storage.list_all_review_logs()
    # 提取 review_log JSON 字符串列表
    review_log_jsons = [log["review_log"] for log in all_logs]
    return optimize_parameters(review_log_jsons)


def apply_fsrs_parameters(parameters, desired_retention: float) -> dict:
    """应用优化后的 FSRS 参数到全局调度器并持久化

    UI 用户点击「应用参数」确认后调用。

    Args:
        parameters: 21 个参数的列表
        desired_retention: 目标保持率

    Returns:
        {"success": bool, "error": str|None}
    """
    from deep_review_mcp.tools.fsrs_scheduler import (
        apply_optimized_parameters,
        save_persisted_parameters,
    )

    try:
        # 1. 替换全局 _scheduler 单例
        apply_optimized_parameters(parameters, desired_retention)
        # 2. 持久化到 fsrs_params.json（下次启动自动加载）
        storage = _get_storage()
        save_persisted_parameters(storage.fsrs_params_file, parameters, desired_retention)
        return {"success": True, "error": None}
    except (ValueError, TypeError) as e:
        return {"success": False, "error": str(e)}
