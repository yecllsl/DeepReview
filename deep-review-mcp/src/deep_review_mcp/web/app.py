# web/app.py
"""FastAPI 应用工厂与启动入口

创建 FastAPI 应用实例，挂载静态文件，注册路由。
提供 main() 作为 CLI 入口，绑定 127.0.0.1:8001 启动 uvicorn。
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# web 模块根目录，用于定位 templates 和 static
_WEB_DIR = Path(__file__).parent
_TEMPLATES_DIR = _WEB_DIR / "templates"
_STATIC_DIR = _WEB_DIR / "static"

# 全局模板实例，供路由模块复用
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例

    配置 Jinja2 模板引擎、挂载静态文件目录、注册所有路由模块。
    绑定 127.0.0.1 保证仅本机访问，符合数据安全规则。
    """
    app = FastAPI(
        title="DeepReview 可视化",
        description="K12错题数据本地可视化应用",
        version="0.4.0",
    )

    # 挂载静态文件（JS库、CSS）
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    # 根路由：返回单页外壳
    from fastapi import Request
    from fastapi.responses import HTMLResponse

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        """返回单页外壳 base.html"""
        return templates.TemplateResponse(request, "base.html", {})

    # 注册路由模块
    from deep_review_mcp.web.routes import dashboard, questions, stats, review

    app.include_router(dashboard.router)
    app.include_router(questions.router)
    app.include_router(stats.router)
    app.include_router(review.router)

    # 启动时加载持久化的 FSRS 个性化参数（若存在）
    # 用户通过 UI 触发优化并应用后，参数保存到 fsrs_params.json，
    # 下次启动自动加载，无需重新优化
    try:
        from deep_review_mcp.web.services import _get_storage
        from deep_review_mcp.tools.fsrs_scheduler import load_persisted_parameters

        storage = _get_storage()
        loaded = load_persisted_parameters(storage.fsrs_params_file)
        if loaded:
            print(f"[web.app] 已加载持久化 FSRS 参数（desired_retention={loaded['desired_retention']}）")
    except Exception as e:
        # 加载失败不影响应用启动，降级使用默认 21 参数
        print(f"[web.app] 加载 FSRS 持久化参数失败，使用默认参数: {e}")

    return app


def main():
    """CLI 入口：启动 uvicorn 服务

    绑定 127.0.0.1:8001，仅本机访问。
    """
    import uvicorn

    uvicorn.run(
        "deep_review_mcp.web.app:create_app",
        factory=True,
        host="127.0.0.1",
        port=8001,
        reload=False,
    )


if __name__ == "__main__":
    main()
