"""generate-aaif-declarations.py 的最小单元测试。

脚本文件名含连字符无法常规 import，故通过 importlib 按路径加载。
仅测试纯解析函数（不触磁盘、不引入 MCP server），覆盖生成声明的核心逻辑。
"""
import importlib.util
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
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


def test_extract_conversational_triggers_picks_quoted_phrases():
    section = '当用户说"录入错题"或"批量采集"时使用。'
    triggers = gen.extract_conversational_triggers(section)
    assert "录入错题" in triggers
    assert "批量采集" in triggers


def test_extract_skill_tools_filters_against_known_tools():
    text = "调用 `save_wrong_question` 与 `classify_question` 保存，参数 `group_by` 不匹配。"
    known = {"save_wrong_question", "classify_question"}
    assert gen.extract_skill_tools(text, known) == [
        "save_wrong_question",
        "classify_question",
    ]


def test_extract_skill_tools_without_known_filter_keeps_snake_names():
    text = "相关工具 `save_wrong_question`、`analyze_prompt`。"
    # known_tools 为 None 时保留所有蛇形命名 token
    assert gen.extract_skill_tools(text, None) == [
        "save_wrong_question",
        "analyze_prompt",
    ]


def test_derive_command_from_name_strips_known_prefix():
    assert gen.derive_command_from_name("wrong-question-analyze") == "/analyze"
    assert gen.derive_command_from_name("review-plan-generate") == "/plan-generate"


def test_header_marks_generated_files():
    assert gen.HEADER["generated_by"] == "scripts/generate-aaif-declarations.py"
    assert gen.HEADER["manual_edits_will_be_overwritten"] is True