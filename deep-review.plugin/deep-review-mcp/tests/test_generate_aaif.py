"""generate-aaif-declarations.py 的最小单元测试。

脚本文件名含连字符无法常规 import，故通过 importlib 按路径加载。
仅测试纯解析函数（不触磁盘、不引入 MCP server），覆盖生成声明的核心逻辑。
"""
import importlib.util
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"
SCRIPT_FILE = SCRIPTS_DIR / "generate-aaif-declarations.py"


def _load_module():
    """按文件路径加载脚本模块（文件名含连字符，无法用 import 语句）。"""
    spec = importlib.util.spec_from_file_location(
        "generate_aaif_declarations", SCRIPT_FILE
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _load_module()


def test_parse_frontmatter_extracts_keys():
    text = '---\nname: 批量采集\ncommand: /batch-capture\ndescription: "录入多道错题"\n---\n正文内容'
    fm = gen.parse_frontmatter(text)
    assert fm["name"] == "批量采集"
    assert fm["command"] == "/batch-capture"
    # 双引号和单引号包裹的值应剥除引号
    assert fm["description"] == "录入多道错题"


def test_parse_frontmatter_without_block_returns_empty():
    assert gen.parse_frontmatter("没有 frontmatter 的正文") == {}


def test_extract_when_to_use_between_headings():
    text = "## When to Use\n用于录入错题。\n## Some Other\n不相关"
    assert gen.extract_when_to_use(text) == "用于录入错题。"


def test_extract_when_to_use_missing_returns_empty():
    assert gen.extract_when_to_use("## Review\n无 When to Use 段落") == ""


def test_extract_keywords_picks_quoted_phrases():
    section = '## When to Use\n当用户说"录入错题"或"批量采集"时使用。'
    triggers = gen.extract_keywords(section)
    assert "录入错题" in triggers
    assert "批量采集" in triggers


def test_extract_keywords_supports_chinese_quotes():
    section = '## When to Use\n当用户说\u201c拍照录题\u201d或\u2018上传错题\u2019时使用。'
    triggers = gen.extract_keywords(section)
    assert "拍照录题" in triggers
    assert "上传错题" in triggers


def test_extract_skill_tools_filters_against_known_tools():
    text = "调用 `save_wrong_question` 与 `classify_question` 保存，参数 `group_by` 不匹配。"
    known = ["save_wrong_question", "classify_question"]
    assert gen.extract_skill_tools(text, known) == [
        "save_wrong_question",
        "classify_question",
    ]


def test_extract_skill_tools_keeps_first_appearance_order():
    text = "先 `classify_question`，再 `save_wrong_question`，最后又 `classify_question`。"
    known = ["save_wrong_question", "classify_question"]
    assert gen.extract_skill_tools(text, known) == [
        "classify_question",
        "save_wrong_question",
    ]


def test_derive_command_from_name_strips_known_prefix():
    assert gen.derive_command_from_name("wrong-question-analyze") == "/analyze"
    assert gen.derive_command_from_name("review-plan-generate") == "/plan-generate"


def test_tools_schema_uses_top_level_meta():
    meta = {"name": "deep-review-mcp", "version": "0.5.0", "description": "desc"}
    tools = [{"name": "save_wrong_question", "description": "d", "parameters": {}}]
    doc = gen.generate_tools(meta, tools)
    assert doc["$schema"] == "https://agents.aaif.io/schemas/tools.json"
    assert doc["name"] == "deep-review-mcp"
    assert doc["version"] == "0.5.0"
    assert doc["tools"] == tools


def test_triggers_use_command_and_conversation_types():
    skills = [
        {
            "dir_name": "wrong-question-capture",
            "name": "wrong-question-capture",
            "description": "录入错题",
            "command": "/capture",
            "text": '## When to Use\n用户说"录入错题"时使用。',
        }
    ]
    doc = gen.generate_triggers(skills)
    assert doc["$schema"] == "https://agents.aaif.io/schemas/triggers.json"
    assert doc["triggers"][0]["type"] == "command"
    assert doc["triggers"][0]["pattern"] == "^/capture(\\s.*)?$"
    assert doc["triggers"][1]["type"] == "conversation"
    assert "录入错题" in doc["triggers"][1]["pattern"]


def test_workflows_use_steps_with_action():
    skills = [
        {
            "dir_name": "wrong-question-capture",
            "name": "wrong-question-capture",
            "description": "录入错题",
            "command": "/capture",
            "text": "调用 `classify_question` 与 `save_wrong_question`。",
        }
    ]
    tools = [
        {"name": "classify_question", "description": "分类", "parameters": {}},
        {"name": "save_wrong_question", "description": "保存", "parameters": {}},
    ]
    doc = gen.generate_workflows(skills, tools)
    assert doc["$schema"] == "https://agents.aaif.io/schemas/workflows.json"
    assert doc["workflows"][0]["steps"] == [
        {"action": "classify_question", "description": "调用 classify_question：分类"},
        {"action": "save_wrong_question", "description": "调用 save_wrong_question：保存"},
    ]
