# src/deep_review_mcp/tools/export.py
"""数据导出Tool

支持将错题数据导出为JSON或Markdown格式文件。
"""

import json
from datetime import UTC, datetime

from deep_review_mcp.tools.crud import get_storage


def _json_default(obj):
    """JSON序列化自定义处理：datetime转为ISO格式字符串

    query_wrong_questions 返回 model_dump() 后的 dict，
    其中 created_at 仍为 datetime 对象，json.dumps 需要此 handler 序列化。
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def export_data(format: str = "json", filters: dict | None = None) -> dict:
    """导出错题数据到文件

    Args:
        format: 导出格式，支持 "json" 和 "markdown"
        filters: 过滤条件字典，同query_wrong_questions的filters参数

    Returns:
        包含file_path的字典，指向导出文件路径
    """
    storage = get_storage()
    questions = storage.query_wrong_questions(filters=filters or {})["questions"]
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    # 复用 storage.base_dir 避免重复定义数据目录
    export_dir = storage.base_dir / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    if format == "markdown":
        fp = export_dir / f"wrong_questions_{ts}.md"
        lines = ["# 错题导出报告\n"]
        for q in questions:
            lines.append(f"## {q.get('question_id','?')}\n- 原始文本: {(q.get('structured') or {}).get('question_content','')}\n")
            if q.get("structured"):
                s = q["structured"]
                lines.append(f"- 学科: {s.get('subject','')}\n- 知识点: {', '.join(s.get('knowledge_points',[]))}\n")
            if q.get("classification"):
                lines.append(f"- 错误类型: {q['classification'].get('error_type','')}\n")
            if q.get("analysis"):
                lines.append(f"- 根本原因: {q['analysis'].get('root_cause','')}\n")
            lines.append("\n---\n")
        fp.write_text("".join(lines), encoding="utf-8")
    else:
        fp = export_dir / f"wrong_questions_{ts}.json"
        fp.write_text(
            json.dumps(questions, indent=2, ensure_ascii=False, default=_json_default),
            encoding="utf-8",
        )
    return {"file_path": str(fp)}
