# DeepReview 错题收集与智能分析Agent 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建基于Trae Work平台的K12错题收集与智能分析Agent，通过MCP Tools + Skills + Rules实现拍照识别、智能分类、原因分析、改进方案和复习推荐的完整闭环。

**Architecture:** 单体MCP Server（deep-review-mcp）承载所有Tools，Skills负责流程编排，Rules约束行为。数据存储在本地JSON文件，OCR使用PaddleOCR本地部署，AI能力使用Trae内置模型。

**Tech Stack:** Python 3.12+, FastMCP, PaddleOCR, uv, Pydantic

---

## File Structure

```
deep-review-mcp/
├── pyproject.toml
├── src/deep_review_mcp/
│   ├── __init__.py
│   ├── server.py
│   ├── models.py
│   ├── storage.py
│   ├── knowledge_map.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── ocr_recognize.py
│   │   ├── classify.py
│   │   ├── analyze.py
│   │   ├── improvement.py
│   │   ├── review.py
│   │   ├── crud.py
│   │   ├── statistics.py
│   │   └── export.py
│   └── prompts/
│       ├── __init__.py
│       ├── structure_parse.py
│       ├── classify_prompt.py
│       ├── analyze_prompt.py
│       └── improvement_prompt.py
├── data/
│   ├── wrong_questions/
│   ├── analysis_reports/
│   └── review_plans/
├── tests/
├── skills/
│   ├── wrong-question-capture.md
│   ├── wrong-question-analyze.md
│   ├── review-plan-generate.md
│   └── wrong-question-stats.md
└── rules/
    ├── classification-rules.md
    ├── analysis-rules.md
    ├── data-safety-rules.md
    └── interaction-rules.md
```

---

## Task 1: 项目初始化与基础配置

**Files:**
- Create: `deep-review-mcp/pyproject.toml`
- Create: `deep-review-mcp/src/deep_review_mcp/__init__.py`

- [ ] **Step 1: 初始化项目目录结构**

```powershell
cd d:\yecll\Documents\LocalCode\DeepReview
mkdir -p deep-review-mcp/src/deep_review_mcp/tools,deep-review-mcp/src/deep_review_mcp/prompts,deep-review-mcp/data/wrong_questions,deep-review-mcp/data/analysis_reports,deep-review-mcp/data/review_plans,deep-review-mcp/tests,deep-review-mcp/skills,deep-review-mcp/rules
```

- [ ] **Step 2: 创建 pyproject.toml**

```toml
[project]
name = "deep-review-mcp"
version = "0.1.0"
description = "K12错题收集与智能分析MCP Server"
requires-python = ">=3.12"
dependencies = [
    "fastmcp>=0.1.0",
    "pydantic>=2.0.0",
    "paddleocr>=2.7.0",
    "paddlepaddle>=2.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]

[project.scripts]
deep-review-mcp = "deep_review_mcp.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 3: 创建 __init__.py**

```python
"""DeepReview MCP Server - K12错题收集与智能分析"""
__version__ = "0.1.0"
```

- [ ] **Step 4: 使用uv安装依赖**

```powershell
cd d:\yecll\Documents\LocalCode\DeepReview\deep-review-mcp
uv venv
uv pip install -e ".[dev]"
```

- [ ] **Step 5: 验证安装**

```powershell
uv run python -c "import fastmcp; print('FastMCP:', fastmcp.__version__)"
```

Expected: 输出FastMCP版本号

- [ ] **Step 6: 提交**

```powershell
git add deep-review-mcp/pyproject.toml deep-review-mcp/src/deep_review_mcp/__init__.py
git commit -m "feat: initialize project with pyproject.toml and dependencies"
```

---

## Task 2: Pydantic数据模型定义

**Files:**
- Create: `deep-review-mcp/src/deep_review_mcp/models.py`
- Create: `deep-review-mcp/tests/test_models.py`

- [ ] **Step 1: 编写数据模型测试**

```python
# tests/test_models.py
import pytest
from datetime import datetime, timezone
from deep_review_mcp.models import (
    StructuredQuestion, Classification, Analysis, Improvement,
    WrongQuestion, ReviewPlan, ReviewScheduleItem,
)


def test_structured_question_creation():
    sq = StructuredQuestion(
        subject="数学", grade_level="初二",
        knowledge_points=["一元二次方程", "因式分解"],
        difficulty="中等", question_type="计算题",
    )
    assert sq.subject == "数学"
    assert len(sq.knowledge_points) == 2


def test_classification_error_type_validation():
    with pytest.raises(ValueError):
        Classification(error_type="无效类型", error_category="测试")


def test_classification_valid_error_types():
    for et in ["知识漏洞", "粗心失误", "方法错误", "审题失误"]:
        c = Classification(error_type=et, error_category="测试分类")
        assert c.error_type == et


def test_wrong_question_creation():
    wq = WrongQuestion(
        question_id="wq_20260615_001",
        created_at=datetime.now(timezone.utc),
        raw_text="若x²-5x+6=0，则x=",
    )
    assert wq.question_id == "wq_20260615_001"
    assert wq.structured is None


def test_wrong_question_full():
    wq = WrongQuestion(
        question_id="wq_20260615_002",
        created_at=datetime.now(timezone.utc),
        raw_text="测试题目",
        structured=StructuredQuestion(
            subject="数学", grade_level="初二",
            knowledge_points=["方程"], difficulty="基础", question_type="填空题",
        ),
        classification=Classification(error_type="知识漏洞", error_category="方程概念不清"),
    )
    assert wq.structured.subject == "数学"
    assert wq.classification.error_type == "知识漏洞"


def test_review_schedule_item():
    item = ReviewScheduleItem(
        date="2026-06-17", question_ids=["wq_001", "wq_002"],
        subject="数学", estimated_minutes=30,
    )
    assert item.estimated_minutes == 30


def test_review_plan():
    plan = ReviewPlan(
        plan_id="rp_20260615_001",
        created_at=datetime.now(timezone.utc),
        priority_topics=["一元二次方程", "因式分解"],
        schedule=[ReviewScheduleItem(
            date="2026-06-17", question_ids=["wq_001"],
            subject="数学", estimated_minutes=20,
        )],
    )
    assert len(plan.schedule) == 1
```

- [ ] **Step 2: 运行测试确认失败**

```powershell
cd d:\yecll\Documents\LocalCode\DeepReview\deep-review-mcp
uv run pytest tests/test_models.py -v
```

Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现数据模型**

```python
# src/deep_review_mcp/models.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class StructuredQuestion(BaseModel):
    subject: str = Field(description="学科")
    grade_level: str = Field(description="年级段")
    knowledge_points: list[str] = Field(description="知识点标签列表")
    difficulty: str = Field(description="难度：基础/中等/困难")
    question_type: str = Field(description="题型")


class Classification(BaseModel):
    error_type: str = Field(description="错误类型：知识漏洞/粗心失误/方法错误/审题失误")
    error_category: str = Field(description="错误细分类别")

    @field_validator("error_type")
    @classmethod
    def validate_error_type(cls, v: str) -> str:
        valid_types = {"知识漏洞", "粗心失误", "方法错误", "审题失误"}
        if v not in valid_types:
            raise ValueError(f"error_type必须是{valid_types}之一，收到: {v}")
        return v


class Analysis(BaseModel):
    root_cause: str = Field(description="根本原因")
    cause_category: str = Field(description="原因类别")
    diagnosis_detail: str = Field(description="详细诊断说明")


class Improvement(BaseModel):
    plan: str = Field(description="具体学习动作")
    similar_topics: list[str] = Field(description="同类题推荐方向")
    study_resources: list[str] = Field(default_factory=list, description="学习资源推荐")
    review_count: int = Field(default=0, description="已复习次数")
    next_review_date: Optional[str] = Field(default=None, description="下次复习日期")


class WrongQuestion(BaseModel):
    question_id: str = Field(description="错题唯一ID")
    created_at: datetime = Field(description="创建时间")
    image_path: Optional[str] = Field(default=None)
    raw_text: str = Field(description="OCR原始文本")
    structured: Optional[StructuredQuestion] = Field(default=None)
    classification: Optional[Classification] = Field(default=None)
    analysis: Optional[Analysis] = Field(default=None)
    improvement: Optional[Improvement] = Field(default=None)
    user_answer: Optional[str] = Field(default=None)
    correct_answer: Optional[str] = Field(default=None)


class ReviewScheduleItem(BaseModel):
    date: str = Field(description="复习日期")
    question_ids: list[str] = Field(description="错题ID列表")
    subject: str = Field(description="学科")
    estimated_minutes: int = Field(description="预计时长(分钟)")


class ReviewPlan(BaseModel):
    plan_id: str = Field(description="计划ID")
    created_at: datetime = Field(description="创建时间")
    priority_topics: list[str] = Field(description="优先复习知识点")
    schedule: list[ReviewScheduleItem] = Field(description="每日安排")


class QueryFilters(BaseModel):
    subject: Optional[str] = Field(default=None)
    knowledge_point: Optional[str] = Field(default=None)
    error_type: Optional[str] = Field(default=None)
    date_range: Optional[dict[str, str]] = Field(default=None)


class StatisticsResult(BaseModel):
    group_by: str
    items: list[dict]
    total: int
```

- [ ] **Step 4: 运行测试确认通过**

```powershell
uv run pytest tests/test_models.py -v
```

Expected: 全部PASS

- [ ] **Step 5: 提交**

```powershell
git add deep-review-mcp/src/deep_review_mcp/models.py deep-review-mcp/tests/test_models.py
git commit -m "feat: add Pydantic data models for wrong questions, classification, analysis, and review"
```

---

## Task 3: 本地JSON存储引擎

**Files:**
- Create: `deep-review-mcp/src/deep_review_mcp/storage.py`
- Create: `deep-review-mcp/tests/test_storage.py`

- [ ] **Step 1: 编写存储引擎测试**

```python
# tests/test_storage.py
import pytest
from pathlib import Path
from datetime import datetime, timezone
from deep_review_mcp.storage import Storage
from deep_review_mcp.models import WrongQuestion, StructuredQuestion, Classification


@pytest.fixture
def tmp_storage(tmp_path):
    return Storage(base_dir=tmp_path)


@pytest.fixture
def sample_question():
    return WrongQuestion(
        question_id="wq_20260615_001",
        created_at=datetime(2026, 6, 15, 10, 30, tzinfo=timezone.utc),
        raw_text="若x²-5x+6=0，则x=",
        structured=StructuredQuestion(
            subject="数学", grade_level="初二",
            knowledge_points=["一元二次方程", "因式分解"],
            difficulty="中等", question_type="计算题",
        ),
    )


def test_save_and_load(tmp_storage, sample_question):
    result = tmp_storage.save_wrong_question(sample_question)
    assert result["question_id"] == "wq_20260615_001"
    loaded = tmp_storage.load_wrong_question("wq_20260615_001")
    assert loaded.raw_text == sample_question.raw_text


def test_query_by_subject(tmp_storage, sample_question):
    tmp_storage.save_wrong_question(sample_question)
    assert tmp_storage.query_wrong_questions(filters={"subject": "数学"})["total_count"] == 1
    assert tmp_storage.query_wrong_questions(filters={"subject": "语文"})["total_count"] == 0


def test_query_by_error_type(tmp_storage, sample_question):
    sample_question.classification = Classification(error_type="知识漏洞", error_category="测试")
    tmp_storage.save_wrong_question(sample_question)
    assert tmp_storage.query_wrong_questions(filters={"error_type": "知识漏洞"})["total_count"] == 1


def test_update(tmp_storage, sample_question):
    tmp_storage.save_wrong_question(sample_question)
    sample_question.raw_text = "更新后"
    tmp_storage.update_wrong_question(sample_question)
    assert tmp_storage.load_wrong_question("wq_20260615_001").raw_text == "更新后"


def test_delete(tmp_storage, sample_question):
    tmp_storage.save_wrong_question(sample_question)
    tmp_storage.delete_wrong_question("wq_20260615_001")
    assert tmp_storage.load_wrong_question("wq_20260615_001") is None


def test_list_ids(tmp_storage, sample_question):
    tmp_storage.save_wrong_question(sample_question)
    assert "wq_20260615_001" in tmp_storage.list_all_question_ids()
```

- [ ] **Step 2: 运行测试确认失败**

```powershell
uv run pytest tests/test_storage.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现存储引擎**

```python
# src/deep_review_mcp/storage.py
import json
from pathlib import Path
from typing import Optional
from deep_review_mcp.models import WrongQuestion, ReviewPlan


class Storage:
    """本地JSON文件存储引擎"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.questions_dir = base_dir / "wrong_questions"
        self.reports_dir = base_dir / "analysis_reports"
        self.plans_dir = base_dir / "review_plans"
        for d in [self.questions_dir, self.reports_dir, self.plans_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def save_wrong_question(self, question: WrongQuestion) -> dict:
        fp = self.questions_dir / f"{question.question_id}.json"
        fp.write_text(question.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
        return {"question_id": question.question_id, "saved_path": str(fp)}

    def load_wrong_question(self, question_id: str) -> Optional[WrongQuestion]:
        fp = self.questions_dir / f"{question_id}.json"
        if not fp.exists():
            return None
        return WrongQuestion.model_validate(json.loads(fp.read_text(encoding="utf-8")))

    def update_wrong_question(self, question: WrongQuestion) -> dict:
        return self.save_wrong_question(question)

    def delete_wrong_question(self, question_id: str) -> bool:
        fp = self.questions_dir / f"{question_id}.json"
        if fp.exists():
            fp.unlink()
            return True
        return False

    def list_all_question_ids(self) -> list[str]:
        return [f.stem for f in self.questions_dir.glob("wq_*.json")]

    def query_wrong_questions(self, filters: dict) -> dict:
        questions = []
        for qid in self.list_all_question_ids():
            wq = self.load_wrong_question(qid)
            if wq and self._matches(wq, filters):
                questions.append(wq.model_dump())
        questions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return {"questions": questions, "total_count": len(questions)}

    def _matches(self, wq: WrongQuestion, f: dict) -> bool:
        if not f:
            return True
        if f.get("subject") and (not wq.structured or wq.structured.subject != f["subject"]):
            return False
        if f.get("knowledge_point") and (not wq.structured or f["knowledge_point"] not in wq.structured.knowledge_points):
            return False
        if f.get("error_type") and (not wq.classification or wq.classification.error_type != f["error_type"]):
            return False
        dr = f.get("date_range")
        if dr:
            c = wq.created_at.isoformat()[:10]
            if dr.get("start") and c < dr["start"]:
                return False
            if dr.get("end") and c > dr["end"]:
                return False
        return True

    def save_review_plan(self, plan: ReviewPlan) -> dict:
        fp = self.plans_dir / f"{plan.plan_id}.json"
        fp.write_text(plan.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
        return {"plan_id": plan.plan_id, "saved_path": str(fp)}

    def load_review_plan(self, plan_id: str) -> Optional[ReviewPlan]:
        fp = self.plans_dir / f"{plan_id}.json"
        if not fp.exists():
            return None
        return ReviewPlan.model_validate(json.loads(fp.read_text(encoding="utf-8")))

    def get_all_questions_for_statistics(self) -> list[WrongQuestion]:
        return [wq for qid in self.list_all_question_ids() if (wq := self.load_wrong_question(qid))]
```

- [ ] **Step 4: 运行测试确认通过**

```powershell
uv run pytest tests/test_storage.py -v
```

Expected: 全部PASS

- [ ] **Step 5: 提交**

```powershell
git add deep-review-mcp/src/deep_review_mcp/storage.py deep-review-mcp/tests/test_storage.py
git commit -m "feat: add local JSON storage engine with CRUD and query support"
```

---

## Task 4: K12知识点映射表

**Files:**
- Create: `deep-review-mcp/src/deep_review_mcp/knowledge_map.py`

- [ ] **Step 1: 实现知识点映射表**

```python
# src/deep_review_mcp/knowledge_map.py
"""K12学科知识点映射表"""

SUBJECTS = ["语文", "数学", "英语", "物理", "化学", "生物", "政治", "历史", "地理"]
ERROR_TYPES = ["知识漏洞", "粗心失误", "方法错误", "审题失误"]
DIFFICULTY_LEVELS = ["基础", "中等", "困难"]

KNOWLEDGE_MAP: dict[str, list[str]] = {
    "数学": ["有理数", "整式", "一元一次方程", "二元一次方程组", "一元二次方程",
             "不等式", "函数基础", "一次函数", "二次函数", "反比例函数",
             "三角形", "四边形", "圆", "相似", "全等",
             "概率", "统计", "因式分解", "分式", "根式",
             "向量", "数列", "极限", "导数", "积分"],
    "语文": ["字音字形", "词语运用", "病句辨析", "修辞手法", "标点符号",
             "文言文阅读", "现代文阅读", "古诗词鉴赏", "名著阅读",
             "记叙文写作", "议论文写作", "说明文写作"],
    "英语": ["名词", "代词", "形容词", "副词", "动词时态", "被动语态",
             "非谓语动词", "定语从句", "状语从句", "名词性从句",
             "阅读理解", "完形填空", "书面表达", "听力"],
    "物理": ["力学", "运动学", "牛顿定律", "功和能", "动量",
             "电学", "电路", "电磁感应", "光学", "热学", "声学", "浮力", "压强"],
    "化学": ["物质结构", "元素周期律", "化学键", "氧化还原反应",
             "酸碱盐", "有机化学基础", "化学反应速率", "化学平衡",
             "电化学", "溶液", "离子反应"],
    "生物": ["细胞结构", "细胞代谢", "细胞分裂", "遗传与变异",
             "基因表达", "进化", "生态学", "人体生理", "植物生理", "微生物"],
    "政治": ["经济生活", "政治生活", "文化生活", "哲学", "法律常识", "时事政治"],
    "历史": ["中国古代史", "中国近代史", "中国现代史", "世界古代史", "世界近代史", "世界现代史"],
    "地理": ["自然地理", "人文地理", "区域地理", "地图", "气候", "地形", "人口与城市"],
}


def get_knowledge_points(subject: str) -> list[str]:
    return KNOWLEDGE_MAP.get(subject, [])


def find_closest_knowledge_point(subject: str, text: str) -> str | None:
    for point in get_knowledge_points(subject):
        if point in text.lower() or text.lower() in point:
            return point
    return None


def validate_subject(subject: str) -> bool:
    return subject in SUBJECTS
```

- [ ] **Step 2: 提交**

```powershell
git add deep-review-mcp/src/deep_review_mcp/knowledge_map.py
git commit -m "feat: add K12 knowledge point mapping for classification consistency"
```

---

## Task 5: Prompt模板定义

**Files:**
- Create: `deep-review-mcp/src/deep_review_mcp/prompts/__init__.py`
- Create: `deep-review-mcp/src/deep_review_mcp/prompts/structure_parse.py`
- Create: `deep-review-mcp/src/deep_review_mcp/prompts/classify_prompt.py`
- Create: `deep-review-mcp/src/deep_review_mcp/prompts/analyze_prompt.py`
- Create: `deep-review-mcp/src/deep_review_mcp/prompts/improvement_prompt.py`

- [ ] **Step 1: 创建 prompts/__init__.py**

```python
"""AI Prompt模板集合"""
```

- [ ] **Step 2: 创建结构化解析Prompt**

```python
# src/deep_review_mcp/prompts/structure_parse.py
STRUCTURE_PARSE_PROMPT = """你是一位K12教育领域的题目结构化专家。请将以下OCR识别出的题目文本解析为结构化数据。

OCR原始文本：
{raw_text}

请按以下JSON格式输出（不要输出其他内容）：
{{
    "subject": "学科（语文/数学/英语/物理/化学/生物/政治/历史/地理）",
    "grade_level": "年级段（小学/初一/初二/初三/高一/高二/高三）",
    "knowledge_points": ["知识点1", "知识点2"],
    "difficulty": "难度（基础/中等/困难）",
    "question_type": "题型（选择题/填空题/计算题/证明题/应用题/其他）",
    "question_content": "题目内容（修正OCR错误后的完整题目）",
    "options": ["选项A", "选项B", "选项C", "选项D"],
    "correct_answer": "正确答案（如果能推断出）"
}}

注意事项：
1. 修正OCR识别中的明显错误（如乱码、错别字）
2. 数学公式用LaTeX格式表示
3. 如果无法确定某个字段，填null
4. knowledge_points必须从该学科的标准知识点中选择
"""
```

- [ ] **Step 3: 创建分类Prompt**

```python
# src/deep_review_mcp/prompts/classify_prompt.py
CLASSIFY_PROMPT = """你是一位K12错题分类专家。请对以下错题进行分类。

题目内容：{question_text}
学科：{subject}

请按以下JSON格式输出（不要输出其他内容）：
{{
    "error_type": "错误类型（知识漏洞/粗心失误/方法错误/审题失误）",
    "error_category": "错误细分类别",
    "knowledge_points": ["相关知识点1", "相关知识点2"],
    "difficulty": "难度（基础/中等/困难）"
}}

分类标准：
- 知识漏洞：对某个知识点完全不理解或理解有误
- 粗心失误：计算错误、抄写错误、符号看错等
- 方法错误：解题方法选择错误或步骤有误
- 审题失误：未正确理解题意、遗漏条件等
"""
```

- [ ] **Step 4: 创建分析Prompt**

```python
# src/deep_review_mcp/prompts/analyze_prompt.py
ANALYZE_PROMPT = """你是一位K12教育诊断专家。请对以下错题进行深度原因分析。

题目内容：{question_text}
学科：{subject}
知识点：{knowledge_points}
用户答案：{user_answer}
正确答案：{correct_answer}

请按以下JSON格式输出（不要输出其他内容）：
{{
    "root_cause": "根本原因（必须具体到知识点层面，禁止笼统结论）",
    "cause_category": "原因类别（知识漏洞/粗心失误/方法错误/审题失误）",
    "diagnosis_detail": "详细诊断（分析错误发生的具体环节和原因，100-200字）"
}}

分析要求：
1. root_cause必须指出具体是哪个知识点的哪个方面出了问题
2. diagnosis_detail需要还原学生的错误思维过程
3. 如果是知识漏洞，指出缺失的具体知识点
4. 如果是方法错误，指出错误的方法和正确方法的区别
"""
```

- [ ] **Step 5: 创建改进方案Prompt**

```python
# src/deep_review_mcp/prompts/improvement_prompt.py
IMPROVEMENT_PROMPT = """你是一位K12学习规划专家。请基于以下错题分析结果，生成个性化改进方案。

题目内容：{question_text}
学科：{subject}
知识点：{knowledge_points}
错误类型：{error_type}
根本原因：{root_cause}

请按以下JSON格式输出（不要输出其他内容）：
{{
    "plan": "具体学习动作（必须包含：做什么+怎么做+建议时长+验证方式）",
    "similar_topics": ["同类题方向1", "同类题方向2", "同类题方向3"],
    "study_resources": ["推荐学习资源1", "推荐学习资源2"]
}}

改进方案要求：
1. plan必须是可执行的具体动作，而非泛泛建议
   - 错误示范："多练习方程题"
   - 正确示范："复习十字相乘法的3个适用条件（建议30分钟），完成后做3道因式分解方程题验证"
2. similar_topics至少3个方向
3. study_resources推荐免费可获取的学习资源类型
"""
```

- [ ] **Step 6: 提交**

```powershell
git add deep-review-mcp/src/deep_review_mcp/prompts/
git commit -m "feat: add AI prompt templates for structure parsing, classification, analysis, and improvement"
```

---

## Task 6: MCP Server骨架与CRUD Tools

**Files:**
- Create: `deep-review-mcp/src/deep_review_mcp/server.py`
- Create: `deep-review-mcp/src/deep_review_mcp/tools/__init__.py`
- Create: `deep-review-mcp/src/deep_review_mcp/tools/crud.py`
- Create: `deep-review-mcp/tests/test_tools_crud.py`

- [ ] **Step 1: 编写CRUD Tools测试**

```python
# tests/test_tools_crud.py
import pytest
from datetime import datetime, timezone
from deep_review_mcp.tools.crud import save_wrong_question, query_wrong_questions
from deep_review_mcp.storage import Storage


@pytest.fixture
def tmp_storage(tmp_path):
    return Storage(base_dir=tmp_path)


def test_save_tool(tmp_storage, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.crud.get_storage", lambda: tmp_storage)
    result = save_wrong_question(question_data={
        "question_id": "wq_20260615_001",
        "created_at": datetime(2026, 6, 15, 10, 30, tzinfo=timezone.utc).isoformat(),
        "raw_text": "若x²-5x+6=0，则x=",
    })
    assert result["question_id"] == "wq_20260615_001"


def test_query_tool(tmp_storage, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.crud.get_storage", lambda: tmp_storage)
    save_wrong_question(question_data={
        "question_id": "wq_20260615_001",
        "created_at": datetime(2026, 6, 15, 10, 30, tzinfo=timezone.utc).isoformat(),
        "raw_text": "测试", "structured": {
            "subject": "数学", "grade_level": "初二",
            "knowledge_points": ["方程"], "difficulty": "基础", "question_type": "计算题",
        },
    })
    assert query_wrong_questions(filters={"subject": "数学"})["total_count"] == 1
```

- [ ] **Step 2: 运行测试确认失败**

```powershell
uv run pytest tests/test_tools_crud.py -v
```

Expected: FAIL

- [ ] **Step 3: 创建 tools/__init__.py**

```python
"""MCP Tools模块"""
```

- [ ] **Step 4: 实现 CRUD Tools**

```python
# src/deep_review_mcp/tools/crud.py
"""错题数据CRUD操作Tools"""

from pathlib import Path
from deep_review_mcp.models import WrongQuestion
from deep_review_mcp.storage import Storage

_DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"


def get_storage() -> Storage:
    return Storage(base_dir=_DEFAULT_DATA_DIR)


def save_wrong_question(question_data: dict) -> dict:
    storage = get_storage()
    wq = WrongQuestion.model_validate(question_data)
    return storage.save_wrong_question(wq)


def query_wrong_questions(filters: dict) -> dict:
    return get_storage().query_wrong_questions(filters=filters)


def update_wrong_question(question_data: dict) -> dict:
    storage = get_storage()
    wq = WrongQuestion.model_validate(question_data)
    return storage.update_wrong_question(wq)


def delete_wrong_question(question_id: str) -> dict:
    success = get_storage().delete_wrong_question(question_id)
    return {"deleted": success, "question_id": question_id}
```

- [ ] **Step 5: 运行测试确认通过**

```powershell
uv run pytest tests/test_tools_crud.py -v
```

Expected: 全部PASS

- [ ] **Step 6: 实现MCP Server入口**

```python
# src/deep_review_mcp/server.py
"""DeepReview MCP Server入口"""

from fastmcp import FastMCP

mcp = FastMCP(name="deep-review-mcp", description="K12错题收集与智能分析MCP Server")


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


@mcp.tool()
def ocr_recognize(image_path: str) -> dict:
    """OCR识别图片中的错题内容并结构化解析"""
    from deep_review_mcp.tools.ocr_recognize import ocr_recognize as _ocr
    return _ocr(image_path)


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
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

- [ ] **Step 7: 验证Server可启动**

```powershell
uv run python -c "from deep_review_mcp.server import mcp; print('Tools:', [t.name for t in mcp._tools.values()])"
```

Expected: 输出9个Tool名称

- [ ] **Step 8: 提交**

```powershell
git add deep-review-mcp/src/deep_review_mcp/server.py deep-review-mcp/src/deep_review_mcp/tools/ deep-review-mcp/tests/test_tools_crud.py
git commit -m "feat: add MCP Server skeleton with CRUD tools registered"
```

---

## Task 7: OCR识别Tool

**Files:**
- Create: `deep-review-mcp/src/deep_review_mcp/tools/ocr_recognize.py`
- Create: `deep-review-mcp/tests/test_tools_ocr.py`

- [ ] **Step 1: 编写OCR Tool测试**

```python
# tests/test_tools_ocr.py
import pytest
from unittest.mock import patch, MagicMock
from deep_review_mcp.tools.ocr_recognize import ocr_recognize, _run_paddle_ocr


def test_ocr_with_mock():
    with patch("deep_review_mcp.tools.ocr_recognize.PaddleOCR") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.ocr.return_value = [[None, [("若x²-5x+6=0", 0.95)]]]
        mock_cls.return_value = mock_instance
        text = _run_paddle_ocr("fake.jpg")
        assert "若x²-5x+6=0" in text


def test_ocr_fallback():
    with patch("deep_review_mcp.tools.ocr_recognize._run_paddle_ocr", side_effect=Exception("失败")):
        result = ocr_recognize("nonexistent.jpg")
        assert result["raw_text"] == ""
        assert "error" in result
```

- [ ] **Step 2: 运行测试确认失败**

```powershell
uv run pytest tests/test_tools_ocr.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现OCR识别Tool**

```python
# src/deep_review_mcp/tools/ocr_recognize.py
"""OCR识别+AI结构化解析Tool"""

from pathlib import Path
from deep_review_mcp.prompts.structure_parse import STRUCTURE_PARSE_PROMPT

_ocr_engine = None


def _get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        from paddleocr import PaddleOCR
        _ocr_engine = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
    return _ocr_engine


def _run_paddle_ocr(image_path: str) -> str:
    engine = _get_ocr_engine()
    result = engine.ocr(image_path, cls=True)
    lines = []
    if result and result[0]:
        for line in result[0]:
            if line and len(line) >= 2:
                lines.append(line[1][0])
    return "\n".join(lines)


def ocr_recognize(image_path: str) -> dict:
    if not Path(image_path).exists():
        return {"raw_text": "", "structured_question": None, "subject": "",
                "grade_level": "", "error": f"图片文件不存在: {image_path}"}
    try:
        raw_text = _run_paddle_ocr(image_path)
    except Exception as e:
        return {"raw_text": "", "structured_question": None, "subject": "",
                "grade_level": "", "error": f"OCR识别失败: {str(e)}，请尝试手动输入题目文本"}
    if not raw_text.strip():
        return {"raw_text": "", "structured_question": None, "subject": "",
                "grade_level": "", "error": "OCR未识别到任何文字，请尝试手动输入"}
    return {"raw_text": raw_text, "structured_question": None, "subject": "",
            "grade_level": "", "parse_prompt": STRUCTURE_PARSE_PROMPT.format(raw_text=raw_text)}
```

- [ ] **Step 4: 运行测试确认通过**

```powershell
uv run pytest tests/test_tools_ocr.py -v
```

Expected: 全部PASS

- [ ] **Step 5: 提交**

```powershell
git add deep-review-mcp/src/deep_review_mcp/tools/ocr_recognize.py deep-review-mcp/tests/test_tools_ocr.py
git commit -m "feat: add OCR recognition tool with PaddleOCR and fallback handling"
```

---

## Task 8: 智能分类Tool

**Files:**
- Create: `deep-review-mcp/src/deep_review_mcp/tools/classify.py`
- Create: `deep-review-mcp/tests/test_tools_classify.py`

- [ ] **Step 1: 编写分类Tool测试**

```python
# tests/test_tools_classify.py
from deep_review_mcp.tools.classify import classify_question, _validate_classification


def test_validate_valid():
    assert _validate_classification("数学", "知识漏洞", "中等")["valid"] is True


def test_validate_invalid_subject():
    r = _validate_classification("体育", "知识漏洞", "中等")
    assert r["valid"] is False and "subject" in r["errors"]


def test_validate_invalid_error_type():
    r = _validate_classification("数学", "态度问题", "中等")
    assert r["valid"] is False and "error_type" in r["errors"]


def test_classify_returns_prompt():
    r = classify_question("若x²-5x+6=0，则x=", "数学")
    assert "classify_prompt" in r and "数学" in r["classify_prompt"]
```

- [ ] **Step 2: 运行测试确认失败**

```powershell
uv run pytest tests/test_tools_classify.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现分类Tool**

```python
# src/deep_review_mcp/tools/classify.py
"""智能分类Tool"""

from deep_review_mcp.knowledge_map import SUBJECTS, ERROR_TYPES, DIFFICULTY_LEVELS, get_knowledge_points
from deep_review_mcp.prompts.classify_prompt import CLASSIFY_PROMPT


def _validate_classification(subject: str, error_type: str, difficulty: str) -> dict:
    errors = {}
    if subject not in SUBJECTS:
        errors["subject"] = f"学科必须是{SUBJECTS}之一"
    if error_type not in ERROR_TYPES:
        errors["error_type"] = f"错误类型必须是{ERROR_TYPES}之一"
    if difficulty not in DIFFICULTY_LEVELS:
        errors["difficulty"] = f"难度必须是{DIFFICULTY_LEVELS}之一"
    return {"valid": len(errors) == 0, "errors": errors}


def classify_question(question_text: str, subject: str = "") -> dict:
    prompt = CLASSIFY_PROMPT.format(question_text=question_text, subject=subject or "请根据题目内容判断")
    result = {"classify_prompt": prompt, "available_subjects": SUBJECTS,
              "available_error_types": ERROR_TYPES, "available_difficulty": DIFFICULTY_LEVELS}
    if subject and subject in SUBJECTS:
        result["available_knowledge_points"] = get_knowledge_points(subject)
    return result
```

- [ ] **Step 4: 运行测试确认通过**

```powershell
uv run pytest tests/test_tools_classify.py -v
```

Expected: 全部PASS

- [ ] **Step 5: 提交**

```powershell
git add deep-review-mcp/src/deep_review_mcp/tools/classify.py deep-review-mcp/tests/test_tools_classify.py
git commit -m "feat: add classification tool with rule validation and knowledge point mapping"
```

---

## Task 9: 错误原因分析Tool

**Files:**
- Create: `deep-review-mcp/src/deep_review_mcp/tools/analyze.py`
- Create: `deep-review-mcp/tests/test_tools_analyze.py`

- [ ] **Step 1: 编写分析Tool测试**

```python
# tests/test_tools_analyze.py
import pytest
from datetime import datetime, timezone
from deep_review_mcp.tools.analyze import analyze_error
from deep_review_mcp.storage import Storage
from deep_review_mcp.models import WrongQuestion, StructuredQuestion, Classification


@pytest.fixture
def storage_with_q(tmp_path):
    s = Storage(base_dir=tmp_path)
    s.save_wrong_question(WrongQuestion(
        question_id="wq_001", created_at=datetime(2026, 6, 15, 10, 30, tzinfo=timezone.utc),
        raw_text="若x²-5x+6=0，则x=",
        structured=StructuredQuestion(subject="数学", grade_level="初二",
            knowledge_points=["一元二次方程"], difficulty="中等", question_type="计算题"),
        classification=Classification(error_type="方法错误", error_category="测试"),
        user_answer="x=1", correct_answer="x=2,3",
    ))
    return s


def test_analyze_returns_prompt(storage_with_q, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.analyze.get_storage", lambda: storage_with_q)
    r = analyze_error("wq_001", "x=1", "x=2,3")
    assert "analyze_prompt" in r and "一元二次方程" in r["analyze_prompt"]


def test_analyze_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.analyze.get_storage", lambda: Storage(base_dir=tmp_path))
    r = analyze_error("wq_xxx")
    assert "error" in r
```

- [ ] **Step 2: 运行测试确认失败**

```powershell
uv run pytest tests/test_tools_analyze.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现分析Tool**

```python
# src/deep_review_mcp/tools/analyze.py
"""错误原因分析Tool"""

from deep_review_mcp.prompts.analyze_prompt import ANALYZE_PROMPT
from deep_review_mcp.tools.crud import get_storage


def analyze_error(question_id: str, user_answer: str = "", correct_answer: str = "") -> dict:
    storage = get_storage()
    wq = storage.load_wrong_question(question_id)
    if wq is None:
        return {"error": f"错题不存在: {question_id}"}
    subject = wq.structured.subject if wq.structured else "未知"
    kps = ", ".join(wq.structured.knowledge_points) if wq.structured else "未知"
    ua = user_answer or wq.user_answer or "未提供"
    ca = correct_answer or wq.correct_answer or "未提供"
    prompt = ANALYZE_PROMPT.format(
        question_text=wq.raw_text, subject=subject,
        knowledge_points=kps, user_answer=ua, correct_answer=ca)
    return {"analyze_prompt": prompt, "question_id": question_id,
            "subject": subject, "knowledge_points": kps}
```

- [ ] **Step 4: 运行测试确认通过**

```powershell
uv run pytest tests/test_tools_analyze.py -v
```

Expected: 全部PASS

- [ ] **Step 5: 提交**

```powershell
git add deep-review-mcp/src/deep_review_mcp/tools/analyze.py deep-review-mcp/tests/test_tools_analyze.py
git commit -m "feat: add error analysis tool with context-aware prompt generation"
```

---

## Task 10: 改进方案生成Tool

**Files:**
- Create: `deep-review-mcp/src/deep_review_mcp/tools/improvement.py`
- Create: `deep-review-mcp/tests/test_tools_improvement.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_tools_improvement.py
from deep_review_mcp.tools.improvement import generate_improvement


def test_returns_prompt():
    r = generate_improvement("wq_001", {"root_cause": "未掌握十字相乘法", "error_type": "知识漏洞"})
    assert "improvement_prompt" in r and "十字相乘法" in r["improvement_prompt"]


def test_with_context():
    r = generate_improvement("wq_001", {
        "root_cause": "方法错误", "error_type": "方法错误",
        "subject": "数学", "knowledge_points": ["因式分解"],
        "question_text": "若x²-5x+6=0，则x=",
    })
    assert "improvement_prompt" in r
```

- [ ] **Step 2: 运行测试确认失败**

```powershell
uv run pytest tests/test_tools_improvement.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现**

```python
# src/deep_review_mcp/tools/improvement.py
"""改进方案生成Tool"""

from deep_review_mcp.prompts.improvement_prompt import IMPROVEMENT_PROMPT


def generate_improvement(question_id: str, analysis_result: dict) -> dict:
    prompt = IMPROVEMENT_PROMPT.format(
        question_text=analysis_result.get("question_text", ""),
        subject=analysis_result.get("subject", "未知学科"),
        knowledge_points=analysis_result.get("knowledge_points", "未知知识点"),
        error_type=analysis_result.get("error_type", "未知类型"),
        root_cause=analysis_result.get("root_cause", "未知原因"))
    return {"improvement_prompt": prompt, "question_id": question_id}
```

- [ ] **Step 4: 运行测试确认通过**

```powershell
uv run pytest tests/test_tools_improvement.py -v
```

Expected: 全部PASS

- [ ] **Step 5: 提交**

```powershell
git add deep-review-mcp/src/deep_review_mcp/tools/improvement.py deep-review-mcp/tests/test_tools_improvement.py
git commit -m "feat: add improvement generation tool with structured prompt"
```

---

## Task 11: 复习推荐Tool

**Files:**
- Create: `deep-review-mcp/src/deep_review_mcp/tools/review.py`
- Create: `deep-review-mcp/tests/test_tools_review.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_tools_review.py
import pytest
from datetime import datetime, timezone, timedelta
from deep_review_mcp.tools.review import recommend_review, _calculate_next_review_date, _get_overdue_questions
from deep_review_mcp.storage import Storage
from deep_review_mcp.models import WrongQuestion, StructuredQuestion, Improvement


@pytest.fixture
def storage_with_overdue(tmp_path):
    s = Storage(base_dir=tmp_path)
    for i, (offset, cnt) in enumerate([(0, 0), (5, 1), (10, 2)]):
        nr = (datetime.now(timezone.utc) - timedelta(days=offset)).strftime("%Y-%m-%d")
        s.save_wrong_question(WrongQuestion(
            question_id=f"wq_{i}", created_at=datetime(2026, 6, 10+i, 10, 30, tzinfo=timezone.utc),
            raw_text=f"题目{i}",
            structured=StructuredQuestion(subject="数学", grade_level="初二",
                knowledge_points=["方程"], difficulty="基础", question_type="计算题"),
            improvement=Improvement(plan="复习", similar_topics=["a","b","c"],
                review_count=cnt, next_review_date=nr),
        ))
    return s


def test_intervals():
    assert _calculate_next_review_date(0) == 1
    assert _calculate_next_review_date(1) == 3
    assert _calculate_next_review_date(2) == 7
    assert _calculate_next_review_date(3) == 14
    assert _calculate_next_review_date(4) == 30


def test_overdue(storage_with_overdue):
    assert len(_get_overdue_questions(storage_with_overdue)) >= 1


def test_recommend(storage_with_overdue, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.review.get_storage", lambda: storage_with_overdue)
    r = recommend_review()
    assert "priority_topics" in r and "schedule" in r and len(r["schedule"]) > 0
```

- [ ] **Step 2: 运行测试确认失败**

```powershell
uv run pytest tests/test_tools_review.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现**

```python
# src/deep_review_mcp/tools/review.py
"""复习推荐Tool - 基于遗忘曲线"""

from datetime import datetime, timezone, timedelta
from collections import Counter
from deep_review_mcp.tools.crud import get_storage
from deep_review_mcp.models import WrongQuestion

REVIEW_INTERVALS = [1, 3, 7, 14, 30]


def _calculate_next_review_date(review_count: int) -> int:
    return REVIEW_INTERVALS[review_count] if review_count < len(REVIEW_INTERVALS) else 30


def _get_overdue_questions(storage) -> list[WrongQuestion]:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return [wq for qid in storage.list_all_question_ids()
            if (wq := storage.load_wrong_question(qid))
            and wq.improvement and wq.improvement.next_review_date
            and wq.improvement.next_review_date <= today]


def recommend_review(time_range: str = "", subject: str = "") -> dict:
    storage = get_storage()
    overdue = _get_overdue_questions(storage)
    if subject:
        overdue = [wq for wq in overdue if wq.structured and wq.structured.subject == subject]
    if not overdue:
        return {"review_plan": None, "priority_topics": [], "schedule": [], "message": "当前没有需要复习的错题"}

    tc = Counter()
    for wq in overdue:
        if wq.structured:
            for kp in wq.structured.knowledge_points:
                tc[kp] += 1
    priority = [t for t, _ in tc.most_common(10)]

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
```

- [ ] **Step 4: 运行测试确认通过**

```powershell
uv run pytest tests/test_tools_review.py -v
```

Expected: 全部PASS

- [ ] **Step 5: 提交**

```powershell
git add deep-review-mcp/src/deep_review_mcp/tools/review.py deep-review-mcp/tests/test_tools_review.py
git commit -m "feat: add review recommendation tool with Ebbinghaus forgetting curve"
```

---

## Task 12: 统计查询Tool

**Files:**
- Create: `deep-review-mcp/src/deep_review_mcp/tools/statistics.py`
- Create: `deep-review-mcp/tests/test_tools_statistics.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_tools_statistics.py
import pytest
from datetime import datetime, timezone
from deep_review_mcp.tools.statistics import get_statistics
from deep_review_mcp.storage import Storage
from deep_review_mcp.models import WrongQuestion, StructuredQuestion, Classification


@pytest.fixture
def storage_with_data(tmp_path):
    s = Storage(base_dir=tmp_path)
    for i, (subj, et) in enumerate([("数学","知识漏洞"),("数学","方法错误"),("英语","粗心失误")]):
        s.save_wrong_question(WrongQuestion(
            question_id=f"wq_{i}", created_at=datetime(2026,6,10+i,10,30,tzinfo=timezone.utc),
            raw_text=f"题目{i}",
            structured=StructuredQuestion(subject=subj, grade_level="初二",
                knowledge_points=["方程" if subj=="数学" else "时态"],
                difficulty="中等", question_type="计算题"),
            classification=Classification(error_type=et, error_category="测试"),
        ))
    return s


def test_by_subject(storage_with_data, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.statistics.get_storage", lambda: storage_with_data)
    assert get_statistics("subject")["total"] == 3


def test_by_error_type(storage_with_data, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.statistics.get_storage", lambda: storage_with_data)
    assert get_statistics("error_type")["total"] == 3
```

- [ ] **Step 2: 运行测试确认失败**

```powershell
uv run pytest tests/test_tools_statistics.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现**

```python
# src/deep_review_mcp/tools/statistics.py
"""统计查询Tool"""

from collections import Counter
from deep_review_mcp.tools.crud import get_storage


def get_statistics(group_by: str) -> dict:
    storage = get_storage()
    questions = storage.get_all_questions_for_statistics()
    if not questions:
        return {"items": [], "total": 0, "trends": {}}

    counter = Counter()
    for wq in questions:
        if group_by == "subject":
            key = wq.structured.subject if wq.structured else "未分类"
        elif group_by == "error_type":
            key = wq.classification.error_type if wq.classification else "未分类"
        elif group_by == "knowledge_point":
            if wq.structured:
                for kp in wq.structured.knowledge_points:
                    counter[kp] += 1
                continue
            key = "未分类"
        elif group_by == "date":
            key = wq.created_at.strftime("%Y-%m-%d") if wq.created_at else "未知"
        else:
            key = "未知"
        counter[key] += 1

    items = [{"name": k, "count": v} for k, v in counter.most_common()]
    dc = Counter()
    for wq in questions:
        if wq.created_at:
            dc[wq.created_at.strftime("%Y-%m-%d")] += 1
    return {"items": items, "total": len(questions), "trends": dict(sorted(dc.items())[-30:])}
```

- [ ] **Step 4: 运行测试确认通过**

```powershell
uv run pytest tests/test_tools_statistics.py -v
```

Expected: 全部PASS

- [ ] **Step 5: 提交**

```powershell
git add deep-review-mcp/src/deep_review_mcp/tools/statistics.py deep-review-mcp/tests/test_tools_statistics.py
git commit -m "feat: add statistics tool with multi-dimensional grouping and trends"
```

---

## Task 13: 数据导出Tool

**Files:**
- Create: `deep-review-mcp/src/deep_review_mcp/tools/export.py`
- Create: `deep-review-mcp/tests/test_tools_export.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_tools_export.py
import pytest
from pathlib import Path
from datetime import datetime, timezone
from deep_review_mcp.tools.export import export_data
from deep_review_mcp.storage import Storage
from deep_review_mcp.models import WrongQuestion


@pytest.fixture
def storage_with_q(tmp_path):
    s = Storage(base_dir=tmp_path)
    s.save_wrong_question(WrongQuestion(
        question_id="wq_001", created_at=datetime(2026,6,15,10,30,tzinfo=timezone.utc),
        raw_text="测试题目"))
    return s


def test_export_json(storage_with_q, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.export.get_storage", lambda: storage_with_q)
    r = export_data("json", {})
    assert "file_path" in r and Path(r["file_path"]).exists()


def test_export_markdown(storage_with_q, monkeypatch):
    monkeypatch.setattr("deep_review_mcp.tools.export.get_storage", lambda: storage_with_q)
    r = export_data("markdown", {})
    assert "file_path" in r and "测试题目" in Path(r["file_path"]).read_text(encoding="utf-8")
```

- [ ] **Step 2: 运行测试确认失败**

```powershell
uv run pytest tests/test_tools_export.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现**

```python
# src/deep_review_mcp/tools/export.py
"""数据导出Tool"""

import json
from datetime import datetime, timezone
from pathlib import Path
from deep_review_mcp.tools.crud import get_storage

_DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"


def export_data(format: str = "json", filters: dict = None) -> dict:
    storage = get_storage()
    questions = storage.query_wrong_questions(filters=filters or {})["questions"]
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    export_dir = _DEFAULT_DATA_DIR / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    if format == "markdown":
        fp = export_dir / f"wrong_questions_{ts}.md"
        lines = ["# 错题导出报告\n"]
        for q in questions:
            lines.append(f"## {q.get('question_id','?')}\n- 原始文本: {q.get('raw_text','')}\n")
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
        fp.write_text(json.dumps(questions, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"file_path": str(fp)}
```

- [ ] **Step 4: 运行测试确认通过**

```powershell
uv run pytest tests/test_tools_export.py -v
```

Expected: 全部PASS

- [ ] **Step 5: 提交**

```powershell
git add deep-review-mcp/src/deep_review_mcp/tools/export.py deep-review-mcp/tests/test_tools_export.py
git commit -m "feat: add data export tool supporting JSON and Markdown formats"
```

---

## Task 14: Skills技能模块编写

**Files:**
- Create: `deep-review-mcp/skills/wrong-question-capture.md`
- Create: `deep-review-mcp/skills/wrong-question-analyze.md`
- Create: `deep-review-mcp/skills/review-plan-generate.md`
- Create: `deep-review-mcp/skills/wrong-question-stats.md`

- [ ] **Step 1: 编写 wrong-question-capture Skill**

```markdown
---
name: wrong-question-capture
description: 错题采集流程编排 - 拍照识别→结构化解析→分类→保存
triggers:
  - command: /capture
  - keywords: ["录入错题", "拍照录题", "添加错题", "上传错题"]
---

# 错题采集流程

你是一个K12错题采集助手。按以下流程执行：

1. **获取图片**：要求用户提供错题图片路径，或允许直接输入题目文本
2. **OCR识别**：调用 `ocr_recognize` Tool
   - 失败时提示用户手动输入
3. **AI结构化解析**：用返回的 `parse_prompt` 调用AI模型解析
4. **展示确认**：请用户确认或修改解析结果
5. **智能分类**：调用 `classify_question` Tool，用 `classify_prompt` 调用AI分类
6. **展示分类**：请用户确认或修改
7. **保存记录**：调用 `save_wrong_question`，question_id格式 wq_YYYYMMDD_NNN

降级方案：OCR失败→手动输入；AI不确定→标记待确认
```

- [ ] **Step 2: 编写 wrong-question-analyze Skill**

```markdown
---
name: wrong-question-analyze
description: 错题分析流程编排 - 查询→原因分析→改进方案→更新记录
triggers:
  - command: /analyze
  - keywords: ["分析错题", "错题分析", "为什么做错", "分析原因"]
---

# 错题分析流程

你是一个K12错题诊断专家。按以下流程执行：

1. **确定目标**：根据用户指定或查询未分析的错题
2. **收集信息**：询问用户答案和正确答案
3. **原因分析**：调用 `analyze_error`，用 `analyze_prompt` 调用AI
4. **展示报告**：结构化呈现错误类型→根因→诊断
5. **生成改进**：调用 `generate_improvement`，用 `improvement_prompt` 调用AI
6. **展示方案**：请用户确认
7. **更新记录**：调用 `update_wrong_question`，计算 next_review_date（1天后）

约束：分析必须具体到知识点；改进方案必须可执行；用户确认后才写入
```

- [ ] **Step 3: 编写 review-plan-generate Skill**

```markdown
---
name: review-plan-generate
description: 复习计划生成流程编排
triggers:
  - command: /review
  - keywords: ["复习计划", "复习推荐", "该复习什么"]
---

# 复习计划生成流程

1. **获取到期错题**：调用 `recommend_review`
2. **展示概览**：到期数量、薄弱知识点排名
3. **展示每日计划**：按日期展示复习清单
4. **用户确认**：确认或调整
5. **保存计划**

遗忘曲线间隔：1天→3天→7天→14天→30天
```

- [ ] **Step 4: 编写 wrong-question-stats Skill**

```markdown
---
name: wrong-question-stats
description: 错题统计查询流程编排
triggers:
  - command: /stats
  - keywords: ["错题统计", "查看统计", "错题分布", "薄弱点"]
---

# 错题统计查询流程

1. **确定维度**：subject/error_type/knowledge_point/date
2. **查询统计**：调用 `get_statistics`
3. **格式化输出**：Markdown表格展示

支持导出：调用 `export_data` 导出为JSON或Markdown
```

- [ ] **Step 5: 提交**

```powershell
git add deep-review-mcp/skills/
git commit -m "feat: add Skills for capture, analyze, review, and stats workflows"
```

---

## Task 15: Rules规则模块编写

**Files:**
- Create: `deep-review-mcp/rules/classification-rules.md`
- Create: `deep-review-mcp/rules/analysis-rules.md`
- Create: `deep-review-mcp/rules/data-safety-rules.md`
- Create: `deep-review-mcp/rules/interaction-rules.md`

- [ ] **Step 1: 编写分类规则**

```markdown
---
name: classification-rules
scope: classify_question, wrong-question-capture
---

# 分类规则

1. 学科必须从K12标准列表选择：语文/数学/英语/物理/化学/生物/政治/历史/地理
2. 错误类型限定4类：知识漏洞/粗心失误/方法错误/审题失误
3. 知识点标签必须来自学科知识图谱，不可自由生成
4. 难度分3级：基础/中等/困难
5. 分类结果必须经用户确认后才保存
```

- [ ] **Step 2: 编写分析规则**

```markdown
---
name: analysis-rules
scope: analyze_error, generate_improvement, wrong-question-analyze
---

# 分析规则

1. 原因分析必须具体到知识点层面，禁止笼统结论（如"不够认真"）
2. 改进方案必须包含：具体学习动作+建议时长+验证方式
3. 同类题推荐至少3个方向
4. 分析结果必须用户确认后才写入记录
5. 改进方案中的学习动作必须是可执行的，禁止泛泛建议
```

- [ ] **Step 3: 编写数据安全规则**

```markdown
---
name: data-safety-rules
scope: all
---

# 数据安全规则

1. 所有数据仅存储在本地，禁止上传到任何外部服务
2. 图片文件存储在项目目录下，不外传
3. 导出数据前需用户确认
4. 不记录用户姓名等个人身份信息
5. OCR本地部署，不调用外部OCR API
```

- [ ] **Step 4: 编写交互规则**

```markdown
---
name: interaction-rules
scope: all skills
---

# 交互规则

1. 命令格式：/capture、/analyze、/review、/stats、/export
2. 自然语言关键词：录入/分析/复习/统计/导出
3. 每次操作结果必须给出明确反馈
4. 错误发生时提供降级方案而非直接报错
5. OCR失败时允许手动输入
6. AI分析异常时提供友好提示和重试机制
```

- [ ] **Step 5: 提交**

```powershell
git add deep-review-mcp/rules/
git commit -m "feat: add Rules for classification, analysis, data safety, and interaction"
```

---

## Task 16: 端到端集成验证

**Files:**
- Modify: `deep-review-mcp/src/deep_review_mcp/server.py` (如有调整)

- [ ] **Step 1: 运行全部测试**

```powershell
cd d:\yecll\Documents\LocalCode\DeepReview\deep-review-mcp
uv run pytest tests/ -v
```

Expected: 全部PASS

- [ ] **Step 2: 验证MCP Server启动**

```powershell
uv run python -c "from deep_review_mcp.server import mcp; print('Tools:', [t.name for t in mcp._tools.values()])"
```

Expected: 输出9个Tool名称（save_wrong_question, query_wrong_questions, update_wrong_question, delete_wrong_question, ocr_recognize, classify_question, analyze_error, generate_improvement, recommend_review, get_statistics, export_data）

- [ ] **Step 3: 验证数据目录结构**

```powershell
ls deep-review-mcp/data/
```

Expected: wrong_questions/, analysis_reports/, review_plans/ 目录存在

- [ ] **Step 4: 最终提交**

```powershell
git add -A
git commit -m "feat: complete DeepReview MCP Server with all tools, skills, and rules"
```
