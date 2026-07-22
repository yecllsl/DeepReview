# routes/review.py
"""复习追踪路由

提供复习追踪页面片段和标记复习 API。
"""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

from deep_review_mcp.web.app import templates
from deep_review_mcp.web import services
from deep_review_mcp.storage import REVIEW_INTERVALS

router = APIRouter()


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

    return templates.TemplateResponse(
        "partials/review.html",
        {
            "request": request,
            "upcoming": upcoming,
            "calendar_days": calendar_days,
            "current_month": today.strftime("%Y年%m月"),
            "subject_progress": subject_progress,
            "forgetting_curve": forgetting_curve,
            "review_intervals": REVIEW_INTERVALS,
        },
    )


@router.get("/api/review/upcoming")
async def upcoming_reviews_api():
    """返回待复习列表 JSON"""
    return {"items": services.get_upcoming_reviews()}


@router.post("/api/review/{question_id}/done", response_class=HTMLResponse)
async def mark_review_done(request: Request, question_id: str):
    """标记错题为已复习，返回更新后的复习页片段"""
    result = services.mark_question_reviewed(question_id)
    if result is None:
        raise HTTPException(status_code=404, detail="错题不存在或无复习信息")

    # 重新渲染复习页
    return await review_partial(request)
