# routes/review.py
"""复习追踪路由

提供复习追踪页面片段和标记复习 API。
"""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from deep_review_mcp.web.app import templates
from deep_review_mcp.web import services
from deep_review_mcp.storage import REVIEW_INTERVALS

router = APIRouter()


class FSRSApplyRequest(BaseModel):
    """应用 FSRS 优化参数的请求体"""
    parameters: list[float] = Field(..., description="FSRS 21 个优化参数")
    desired_retention: float = Field(..., ge=0.5, le=1.0, description="目标保持率 0.5-1.0")


@router.get("/partials/review", response_class=HTMLResponse)
async def review_partial(request: Request):
    """返回复习追踪页片段"""
    upcoming = services.get_upcoming_reviews()

    # 复习日历数据：当前月每天的复习任务数
    today = datetime.now(timezone.utc)
    month_start = today.replace(day=1)
    # 计算当月天数
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
    month_days = (next_month - month_start).days

    # 从所有错题的 next_review_date 统计每天复习数
    from deep_review_mcp.web.services import _get_storage
    storage = _get_storage()
    review_calendar: dict[str, int] = {}
    for qid in storage.list_all_question_ids():
        wq = storage.load_wrong_question(qid)
        if wq and wq.improvement and wq.improvement.next_review_date:
            date_str = wq.improvement.next_review_date
            if date_str.startswith(today.strftime("%Y-%m")):
                review_calendar[date_str] = review_calendar.get(date_str, 0) + 1

    # 生成日历天数据
    calendar_days = []
    for day in range(1, month_days + 1):
        date_str = month_start.replace(day=day).strftime("%Y-%m-%d")
        calendar_days.append({
            "day": day,
            "date": date_str,
            "count": review_calendar.get(date_str, 0),
            "is_today": date_str == today.strftime("%Y-%m-%d"),
        })

    # 各学科复习完成率
    subject_stats: dict[str, dict] = {}
    for qid in storage.list_all_question_ids():
        wq = storage.load_wrong_question(qid)
        if not wq or not wq.structured or not wq.improvement:
            continue
        subj = wq.structured.subject
        if subj not in subject_stats:
            subject_stats[subj] = {"total": 0, "reviewed": 0}
        subject_stats[subj]["total"] += 1
        if wq.improvement.review_count > 0:
            subject_stats[subj]["reviewed"] += 1
    subject_progress = [
        {"subject": s, "total": d["total"], "reviewed": d["reviewed"],
         "rate": int(d["reviewed"] / d["total"] * 100) if d["total"] > 0 else 0}
        for s, d in subject_stats.items()
    ]

    # 遗忘曲线数据
    forgetting_curve = []
    for i, interval in enumerate(REVIEW_INTERVALS):
        # 理论保留率：首次学习后遗忘曲线的近似
        if i == 0:
            retention = 100  # 刚学
        retention = max(100 - (i + 1) * 15, 30)  # 简化模型
        forgetting_curve.append({"review": i, "interval": interval, "retention": retention})

    # FSRS 参数优化面板状态（供 UI 展示当前调度器信息 + ReviewLog 进度）
    fsrs_status = services.get_fsrs_optimization_status()

    return templates.TemplateResponse(
        request,
        "partials/review.html",
        {
            "upcoming": upcoming,
            "calendar_days": calendar_days,
            "current_month": today.strftime("%Y年%m月"),
            "subject_progress": subject_progress,
            "forgetting_curve": forgetting_curve,
            "review_intervals": REVIEW_INTERVALS,
            "fsrs_status": fsrs_status,
        },
    )


@router.get("/api/review/upcoming")
async def upcoming_reviews_api():
    """返回待复习列表 JSON"""
    return {"items": services.get_upcoming_reviews()}


@router.post("/api/review/{question_id}/done", response_class=HTMLResponse)
async def mark_review_done(request: Request, question_id: str, rating: int = Form(3)):
    """标记错题为已复习，基于 FSRS 4 档评分调度

    接收表单 rating 字段（HTMX hx-vals 传递），调用 FSRS 更新 Card 状态。
    默认 rating=3（Good）保持向后兼容（老客户端无 rating 字段时按"顺利"处理）。

    Args:
        rating: 1=Again忘记 2=Hard吃力 3=Good顺利 4=Easy秒懂
    """
    result = services.mark_question_reviewed(question_id, rating)
    if result is None:
        raise HTTPException(status_code=404, detail="错题不存在或无复习信息")

    # 重新渲染复习页
    return await review_partial(request)


# ──────────────────────────────────────────
# FSRS 参数优化（UI 主动触发）
# ──────────────────────────────────────────

@router.get("/api/fsrs/status")
async def fsrs_status_api():
    """获取 FSRS 参数优化状态

    返回当前调度器信息（默认/个性化）、ReviewLog 积累进度、是否有持久化参数。
    供前端 JS 渲染优化面板的初始状态。
    """
    return services.get_fsrs_optimization_status()


@router.post("/api/fsrs/optimize")
async def fsrs_optimize_api():
    """触发 FSRS 参数优化计算

    读取全部 ReviewLog，调用 Optimizer 计算 21 个个性化参数。
    不自动应用，仅返回结果供 UI 展示，用户确认后再调用 /api/fsrs/apply。

    耗时约 2-5 秒（1000+ 记录时），前端需显示 loading 状态。
    """
    result = services.run_fsrs_optimization()
    return result


@router.post("/api/fsrs/apply")
async def fsrs_apply_api(params: FSRSApplyRequest):
    """应用优化后的 FSRS 参数到全局调度器并持久化

    接收 JSON body：{"parameters": [...21 个 float], "desired_retention": 0.85}
    应用后替换全局 _scheduler 单例，并写入 fsrs_params.json（下次启动自动加载）。

    仅影响未来的复习调度，已存在的 Card 状态不会自动重算。
    """
    result = services.apply_fsrs_parameters(params.parameters, params.desired_retention)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result
