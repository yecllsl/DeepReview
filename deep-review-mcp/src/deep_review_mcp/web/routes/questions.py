# routes/questions.py
"""错题列表与详情路由

提供列表筛选、详情展示、编辑表单和保存功能。
"""
from urllib.parse import parse_qs, urlparse

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from deep_review_mcp.web.app import templates
from deep_review_mcp.web import services
from deep_review_mcp.knowledge_map import SUBJECTS, ERROR_TYPES, DIFFICULTY_LEVELS, KNOWLEDGE_MAP, get_knowledge_points

router = APIRouter()


def _truncate(text: str, length: int = 80) -> str:
    """截断文本，超长加省略号"""
    if not text:
        return ""
    return text[:length] + ("..." if len(text) > length else "")


@router.get("/partials/questions", response_class=HTMLResponse)
async def question_list_partial(
    request: Request,
    subject: str = "",
    error_type: str = "",
    knowledge_point: str = "",
    date_start: str = "",
    date_end: str = "",
    search: str = "",
):
    """返回错题列表片段（带筛选）"""
    # 构建筛选条件
    filters: dict = {}
    if subject:
        filters["subject"] = subject
    if error_type:
        filters["error_type"] = error_type
    if knowledge_point:
        filters["knowledge_point"] = knowledge_point
    if date_start or date_end:
        filters["date_range"] = {"start": date_start, "end": date_end}

    result = services.get_filtered_questions(filters)
    questions = result["questions"]

    # 额外的文本搜索
    if search:
        questions = [q for q in questions if search.lower() in (q.get("raw_text") or "").lower()]

    # 收集所有知识点供下拉筛选
    all_knowledge_points: set[str] = set()
    for q in questions:
        if q.get("structured") and q["structured"].get("knowledge_points"):
            all_knowledge_points.update(q["structured"]["knowledge_points"])

    return templates.TemplateResponse(
        request,
        "partials/question_list.html",
        {
            "questions": questions,
            "total": len(questions),
            "subjects": SUBJECTS,
            "error_types": ERROR_TYPES,
            "knowledge_points": sorted(all_knowledge_points),
            "current_subject": subject,
            "current_error_type": error_type,
            "current_knowledge_point": knowledge_point,
            "current_date_start": date_start,
            "current_date_end": date_end,
            "current_search": search,
            "truncate": _truncate,
        },
    )


@router.get("/partials/questions/{question_id}", response_class=HTMLResponse)
async def question_detail_partial(request: Request, question_id: str):
    """返回单题详情片段（只读）"""
    wq = services.get_question_detail(question_id)
    if wq is None:
        raise HTTPException(status_code=404, detail="错题不存在")
    return templates.TemplateResponse(
        request,
        "partials/question_detail.html",
        {"wq": wq, "truncate": _truncate},
    )


@router.get("/partials/questions/{question_id}/edit", response_class=HTMLResponse)
async def question_edit_partial(request: Request, question_id: str):
    """返回单题编辑表单片段"""
    wq = services.get_question_detail(question_id)
    if wq is None:
        raise HTTPException(status_code=404, detail="错题不存在")

    # 获取当前学科的知识点列表
    current_subject = wq.structured.subject if wq.structured else ""
    kp_options = get_knowledge_points(current_subject) if current_subject else []

    return templates.TemplateResponse(
        request,
        "partials/question_edit.html",
        {
            "wq": wq,
            "subjects": SUBJECTS,
            "error_types": ERROR_TYPES,
            "difficulty_levels": DIFFICULTY_LEVELS,
            "knowledge_point_options": kp_options,
            "knowledge_map": KNOWLEDGE_MAP,
        },
    )


@router.put("/api/questions/{question_id}")
async def update_question_api(question_id: str, request: Request):
    """编辑保存错题，写回 JSON

    返回内容包含两部分：
    1. 主响应：更新后的错题详情片段，替换 #detail-panel
    2. OOB 片段：左侧错题卡片列表，替换 #question-list-container
    这样保存后左右两侧都会自动刷新，无需手动刷新页面。
    """
    # 接收表单数据
    form = await request.form()
    data: dict = {}
    for key, value in form.items():
        if value:
            # 知识点和同类题可能需要特殊处理（逗号分隔）
            if key in ("knowledge_points", "similar_topics", "study_resources"):
                data[key] = [v.strip() for v in value.split(",") if v.strip()]
            else:
                data[key] = value

    updated = services.update_question(question_id, data)
    if updated is None:
        raise HTTPException(status_code=404, detail="错题不存在")

    # 根据当前 URL 的筛选条件重新查询列表，保持左侧列表与筛选状态一致
    current_url = request.headers.get("hx-current-url", "")
    query = parse_qs(urlparse(current_url).query)
    filters: dict = {}
    if query.get("subject", [""])[0]:
        filters["subject"] = query["subject"][0]
    if query.get("error_type", [""])[0]:
        filters["error_type"] = query["error_type"][0]
    if query.get("knowledge_point", [""])[0]:
        filters["knowledge_point"] = query["knowledge_point"][0]
    date_start = query.get("date_start", [""])[0]
    date_end = query.get("date_end", [""])[0]
    if date_start or date_end:
        filters["date_range"] = {"start": date_start, "end": date_end}

    result = services.get_filtered_questions(filters)
    questions = result["questions"]
    search = query.get("search", [""])[0]
    if search:
        questions = [q for q in questions if search.lower() in (q.get("raw_text") or "").lower()]

    # 渲染详情片段
    detail_html = templates.get_template("partials/question_detail.html").render(
        request=request, wq=updated, truncate=_truncate
    )

    # 渲染左侧列表片段（OOB 交换）
    cards_html = templates.get_template("partials/question_cards.html").render(
        request=request, questions=questions, total=len(questions), truncate=_truncate
    )

    return HTMLResponse(
        content=detail_html + f'<div id="question-list-container" hx-swap-oob="true">{cards_html}</div>'
    )
