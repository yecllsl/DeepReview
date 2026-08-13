# src/deep_review_mcp/server.py
"""DeepReview MCP Server入口

注册所有MCP工具（4个CRUD + 7个业务工具），通过FastMCP框架对外提供服务。
业务工具模块使用懒导入（函数体内import），确保server.py本身可正常加载，
后续Task会逐个实现这些业务模块。
"""

from fastmcp import FastMCP

mcp = FastMCP(name="deep-review-mcp", instructions="K12错题收集与智能分析MCP Server")


# ──────────────────────────────────────────
# CRUD 工具（已实现）
# ──────────────────────────────────────────

@mcp.tool()
def save_wrong_question(question_data: dict) -> dict:
    """保存错题记录到本地JSON文件"""
    from deep_review_mcp.tools.crud import save_wrong_question as _save
    return _save(question_data)


@mcp.tool()
def query_wrong_questions(filters: dict) -> dict:
    """按条件查询错题"""
    from deep_review_mcp.tools.crud import query_wrong_questions as _query
    return _query(filters)


@mcp.tool()
def update_wrong_question(question_data: dict) -> dict:
    """更新错题记录"""
    from deep_review_mcp.tools.crud import update_wrong_question as _update
    return _update(question_data)


@mcp.tool()
def delete_wrong_question(question_id: str) -> dict:
    """删除错题记录"""
    from deep_review_mcp.tools.crud import delete_wrong_question as _delete
    return _delete(question_id)


# ──────────────────────────────────────────
# 业务工具（懒导入，后续Task逐个实现）
# ──────────────────────────────────────────

@mcp.tool()
def classify_question(question_text: str, subject: str = "") -> dict:
    """AI驱动智能分类错题"""
    from deep_review_mcp.tools.classify import classify_question as _classify
    return _classify(question_text, subject)


@mcp.tool()
def analyze_error(question_id: str, user_answer: str = "", correct_answer: str = "") -> dict:
    """深度分析错题错误原因"""
    from deep_review_mcp.tools.analyze import analyze_error as _analyze
    return _analyze(question_id, user_answer, correct_answer)


@mcp.tool()
def generate_improvement(question_id: str, analysis_result: dict) -> dict:
    """生成个性化改进方案"""
    from deep_review_mcp.tools.improvement import generate_improvement as _gen
    return _gen(question_id, analysis_result)


@mcp.tool()
def recommend_review(time_range: str = "", subject: str = "") -> dict:
    """基于遗忘曲线生成复习推荐"""
    from deep_review_mcp.tools.review import recommend_review as _rec
    return _rec(time_range, subject)


@mcp.tool()
def get_statistics(group_by: str) -> dict:
    """统计分析错题分布和趋势"""
    from deep_review_mcp.tools.statistics import get_statistics as _stats
    return _stats(group_by)


@mcp.tool()
def export_data(format: str = "json", filters: dict = None) -> dict:
    """导出错题数据"""
    from deep_review_mcp.tools.export import export_data as _export
    return _export(format, filters or {})


def main():
    """启动MCP Server（stdio传输模式）"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
