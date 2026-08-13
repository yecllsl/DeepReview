---
name: remove-ocr-multimodal-import
overview: 删除项目中全部 PaddleOCR 本地 OCR 实现（MCP 工具、依赖、测试、配置声明、安装脚本与文档），改为仅依赖宿主 LLM 多模态直接读取图片并结构化解析导入错题；同时彻底移除数据模型 raw_text 字段及其在 web/存储层的引用。
todos:
  - id: remove-ocr-service
    content: 删除 OCR 实现：删 ocr_recognize.py、structure_parse.py、server.py 注册、pyproject [ocr] extra
    status: completed
  - id: migrate-model
    content: models.py 移除 raw_text，StructuredQuestion 新增 question_content/options 字段
    status: completed
    dependencies:
      - remove-ocr-service
  - id: migrate-business-refs
    content: 改造 analyze/export/web services/routes 及 5 个模板，raw_text 迁移到 structured.question_content
    status: completed
    dependencies:
      - migrate-model
  - id: clean-tests
    content: 删除 test_tools_ocr.py，清理 12 个测试文件 raw_text 构造与断言，跑 pytest/ruff/mypy 验证
    status: completed
    dependencies:
      - migrate-business-refs
  - id: update-skills
    content: 用 [skill:wrong-question-capture] 与 [skill:wrong-question-batch-capture] 改造两个采集 SKILL.md 为宿主 LLM 多模态解析流程，同步更新 .agents/AGENTS.md
    status: completed
  - id: regen-sync-configs
    content: 重跑 generate-aaif-declarations.py 生成 AAIF 声明，再跑 sync-agent-configs.ps1 同步四平台配置
    status: completed
    dependencies:
      - update-skills
      - remove-ocr-service
  - id: update-docs-version
    content: 更新根 AGENTS.md/README/QUICKSTART/DEPLOY/CHANGELOG 去 OCR 表述，版本统一 0.4.0，install 脚本删 OCR 步骤并重编号
    status: completed
---

## 用户需求
项目实测 PaddleOCR OCR 方案效果不佳，删除项目中全部 OCR 实现方案（PaddleOCR 依赖、ocr_recognize MCP 工具、OCR 流程与相关文档），图片导入改为仅依赖宿主 LLM 多模态能力直接解析图片。

## 产品概述
错题采集入口从「OCR 识别 → AI 解析」简化为「宿主 LLM 多模态直接看图解析」：用户提供图片路径或直接输入文本，由宿主 LLM 读取图片并按结构化解析提示提取题目数据，经用户确认后保存。MCP 端不再提供任何图片解析工具，PaddleOCR 相关依赖、代码、配置、文档全部移除。

## 核心功能
- 删除 `ocr_recognize` MCP 工具注册及其实现（`tools/ocr_recognize.py`、`prompts/structure_parse.py`）
- 删除 PaddleOCR 可选依赖（`pyproject.toml` `[ocr] extra`）及安装脚本中的 OCR 安装步骤
- 删除 `WrongQuestion.raw_text` 字段，新增 `StructuredQuestion.question_content`（题目内容）与 `options` 字段承载题目文本，保证 analyze/export/web 展示与搜索功能完整
- 采集 Skill（单题/批量）流程改为：获取图片路径 → 宿主 LLM 多模态直接看图 → 内联结构化解析 → 展示确认 → 智能分类 → 用户确认 → 保存
- 同步清理配置层（.agents/ 真相源）、四平台生成目录、根文档与版本号（0.3.0 → 0.4.0）

## 技术栈
- Python 3.12+ / FastMCP / Pydantic v2（服务层不变）
- 图片解析：宿主 LLM 多模态能力（MCP 侧零图像处理代码）
- 数据存储：本地 JSON（不变）

## 实施方式
采用「彻底删除 + 字段迁移」策略：删除 PaddleOCR 全部实现与依赖；由于 `raw_text` 是题目文本唯一载体，在 `StructuredQuestion` 中新增带默认值的 `question_content`/`options` 字段承接（与旧 `STRUCTURE_PARSE_PROMPT` 输出 JSON 结构一致），使 analyze/export/web 全链路改用 `structured.question_content`，避免功能缺失。

## 关键决策
- **工具删除而非改造**：用户确认 MCP 端不留任何图片解析工具，解析提示内联进 Skill（5 平台同步维护）；代价是 prompt 冗余，换取最小代码面
- **question_content 带默认值**：兼容旧数据（Pydantic 默认忽略 raw_text、缺失字段取默认值），不破坏已有 JSON 加载
- **AAIF 声明靠脚本重生成**：tools.json/workflows.json 是 `generate-aaif-declarations.py` 生成产物，禁止手改，改 server.py/SKILL.md 后重跑生成
- **配置同步强约束**：只改 `.agents/`，再跑 `scripts/sync-agent-configs.ps1` 同步四平台生成目录
- **性能**：删除 OCR 懒加载引擎，服务启动不再有 PaddleOCR 模型加载开销；无新增热路径

## 架构设计
```
用户交互层（/capture、/batch-capture 等命令，由宿主 LLM 执行）
  │  提供图片路径 / 输入文本
  ▼
宿主 LLM 多模态直接读取图片（无 MCP 图片解析工具）
  │  按 Skill 内联结构化解析提示输出 JSON
  ▼
MCP 服务层（classify_question → save_wrong_question）
  │  Pydantic 模型校验（硬防线）
  ▼
数据存储层（本地 JSON，image_path 保留、raw_text 移除）
```

## 实施要点
- 修改服务层后重跑 `generate-aaif-declarations.py` 使 ocr_recognize 从 AAIF 声明中消失，再同步四平台
- 所有 raw_text 引用点（analyze/export/web services/routes/5 个模板/12 个测试文件）统一迁移到 `structured.question_content`，编辑表单字段名同步改名
- web 端 question_content 为空（旧数据）时展示"暂无内容"兜底，避免模板报错
- 版本号 0.4.0 在 pyproject.toml / `__init__.py` / web/app.py / install 脚本 / build-release 脚本保持一致
- 验证：pytest（-m "not e2e"）+ ruff + mypy 全绿

## 目录结构
```
deep-review-mcp/
├── pyproject.toml                            # [MODIFY] 删除 [ocr] extra；版本 0.4.0
├── src/deep_review_mcp/
│   ├── __init__.py                           # [MODIFY] 版本 0.4.0
│   ├── server.py                             # [MODIFY] 删除 ocr_recognize 工具注册
│   ├── models.py                             # [MODIFY] 删 raw_text；StructuredQuestion 增 question_content/options
│   ├── prompts/structure_parse.py            # [DELETE] 整体删除（仅 ocr_recognize 引用）
│   ├── tools/ocr_recognize.py                # [DELETE] 整体删除
│   ├── tools/analyze.py                      # [MODIFY] question_text 改用 structured.question_content
│   ├── tools/export.py                       # [MODIFY] 导出文本改用 structured.question_content
│   └── web/
│       ├── app.py                            # [MODIFY] 版本 0.4.0
│       ├── services.py                       # [MODIFY] upcoming/patch 字段改用 question_content
│       ├── routes/questions.py               # [MODIFY] 搜索改用 structured.question_content
│       └── templates/partials/
│           ├── question_detail.html          # [MODIFY] 删 raw_text 区块，保留图片区块
│           ├── question_edit.html            # [MODIFY] textarea name → question_content
│           ├── question_cards.html           # [MODIFY] 摘要改用 question_content
│           ├── review.html                   # [MODIFY] item.raw_text → item.question_content
│           └── dashboard.html                # [MODIFY] item.raw_text → item.question_content
├── tests/
│   ├── test_tools_ocr.py                     # [DELETE] 整体删除
│   └── 其余 12 个测试文件                    # [MODIFY] raw_text 构造/断言改为 question_content
.agents/
├── AGENTS.md                                 # [MODIFY] 架构/技术栈/规则/MCP 参考表去 OCR
├── skills/wrong-question-capture/SKILL.md    # [MODIFY] 流程改为宿主 LLM 多模态看图解析
├── skills/wrong-question-batch-capture/SKILL.md  # [MODIFY] 同上
├── tools.json                               # [REGEN] 重跑 generate-aaif-declarations.py 生成
└── workflows.json                           # [REGEN] 同上
根目录
├── AGENTS.md                                # [MODIFY] 同步架构/技术栈/规则表述
├── README.md                                # [MODIFY] 去 OCR 功能/依赖/FAQ/目录结构/安全声明
├── QUICKSTART.md                            # [MODIFY] 去 OCR 安装与示例表述
├── DEPLOY.md                                # [MODIFY] 去 OCR 安装询问与 FAQ
├── CHANGELOG.md                             # [MODIFY] 新增 [0.4.0] 条目
├── install.ps1 / install.sh                 # [MODIFY] 删 OCR 安装步骤并重新编号
└── scripts/build-release.ps1 / .sh          # [MODIFY] 默认版本 0.4.0
```

## 关键代码结构
```python
class StructuredQuestion(BaseModel):
    """结构化题目信息"""
    subject: str = Field(description="学科")
    grade_level: str = Field(description="年级段")
    knowledge_points: list[str] = Field(description="知识点标签列表")
    difficulty: str = Field(description="难度：基础/中等/困难")
    question_type: str = Field(description="题型")
    question_content: str = Field(default="", description="题目内容")
    options: list[str] = Field(default_factory=list, description="选项列表")

class WrongQuestion(BaseModel):
    """错题核心模型"""
    question_id: str = Field(description="错题唯一ID")
    created_at: datetime = Field(description="创建时间")
    image_path: Optional[str] = Field(default=None)
    structured: Optional[StructuredQuestion] = Field(default=None)
    classification: Optional[Classification] = Field(default=None)
    analysis: Optional[Analysis] = Field(default=None)
    improvement: Optional[Improvement] = Field(default=None)
    user_answer: Optional[str] = Field(default=None)
    correct_answer: Optional[str] = Field(default=None)
    # raw_text 已移除
```

## Agent Extensions
### Skill
- **wrong-question-capture**
  - 用途：改造单题采集 Skill，将"OCR 识别"步骤替换为"宿主 LLM 多模态直接读取图片并按内联提示解析"
  - 预期产出：SKILL.md 流程、Quick Reference、Common Mistakes 全部去 OCR 化，解析提示内联 JSON 输出格式（含 question_content/options）
- **wrong-question-batch-capture**
  - 用途：改造批量采集 Skill 的 2a/2b 步骤、异常处理与 Quick Reference，图片输入改为宿主 LLM 多模态解析
  - 预期产出：批量采集流程不再引用 ocr_recognize 与 parse_prompt，内联结构化解析提示
