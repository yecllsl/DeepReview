#!/usr/bin/env python3
"""从真实源生成 AAIF 包声明文件。

产出 `deep-review.plugin/` 下三个 AAIF 标准声明文件：
  - tools.json      ← 自省实时 MCP 服务（deep_review_mcp.server）得到工具与参数 schema
  - triggers.json   ← 聚合各 Skill 的「When to Use」自然语言触发词 + 命令别名
  - workflows.json  ← 聚合各 Skill 实际引用的 MCP 工具（按文中出现顺序）

这些文件是 AAIF 工具链（`agents publish deep-review.plugin`）消费的声明产物，属**生成文件**，
请勿手工编辑；运行本脚本或 `scripts/sync-agent-configs` 即可重新生成。

工具自省依赖 deep-review-mcp 的运行环境，因此须通过 uv 运行（脚本位于项目级
根目录 scripts/，故 --directory 后需用 ../../scripts/ 相对路径指向它，因为 uv 会把
工作目录切到 deep-review.plugin/deep-review-mcp 下）：

    uv run --no-sync --directory deep-review.plugin/deep-review-mcp python ../../scripts/generate-aaif-declarations.py
"""
from __future__ import annotations

import asyncio
import json
import re
import tomllib
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = PROJECT_ROOT / "deep-review.plugin"
SKILLS_DIR = PLUGIN_DIR / "skills"
MCP_PYPROJECT = PLUGIN_DIR / "deep-review-mcp" / "pyproject.toml"

TOOLS_SCHEMA = "https://agents.aaif.io/schemas/tools.json"
TRIGGERS_SCHEMA = "https://agents.aaif.io/schemas/triggers.json"
WORKFLOWS_SCHEMA = "https://agents.aaif.io/schemas/workflows.json"


def load_package_meta() -> dict[str, str]:
    """从 pyproject.toml 读取 name/version/description（stdlib tomllib）。"""
    data = tomllib.loads(MCP_PYPROJECT.read_text(encoding="utf-8"))
    project = data.get("project", {})
    return {
        "name": project.get("name", "deep-review-mcp"),
        "version": project.get("version", ""),
        "description": project.get("description", ""),
    }


def introspect_tools() -> list[dict[str, Any]]:
    """读取实时 MCP 工具注册表（FastMCP 自省）。"""
    try:
        from deep_review_mcp import server  # local import; run via uv --directory
    except ImportError as exc:  # 环境守卫：必须在 uv 环境运行
        raise SystemExit(
            "无法导入 deep_review_mcp。请通过 uv 运行本脚本：\n"
            "  uv run --no-sync --directory deep-review.plugin/deep-review-mcp "
            "python ../../scripts/generate-aaif-declarations.py"
        ) from exc
    tools = asyncio.run(server.mcp.list_tools())
    return [
        {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": getattr(tool, "parameters", None)
            or {"type": "object", "properties": {}},
        }
        for tool in tools
    ]


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict[str, str]:
    """解析 SKILL.md frontmatter（name/command/description 等键）。"""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    data: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def iter_skills() -> list[dict[str, Any]]:
    """收集 deep-review.plugin/skills/ 下每个 SKILL.md 的元数据与正文。"""
    skills: list[dict[str, Any]] = []
    if not SKILLS_DIR.is_dir():
        return skills
    for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8")
        meta = parse_frontmatter(text)
        skills.append(
            {
                "dir_name": skill_md.parent.name,
                "name": meta.get("name", skill_md.parent.name),
                "description": meta.get("description", ""),
                "command": meta.get("command", ""),
                "text": text,
            }
        )
    return skills


def derive_command_from_name(skill_name: str) -> str:
    """Fallback: derive a /command from the skill directory name.

    Prefer the explicit `command:` frontmatter key; this fallback strips
    known prefixes and maps what remains to a slash command.
    """
    base = skill_name
    for prefix in ("wrong-question-", "review-", "deep-review-"):
        if base.startswith(prefix):
            base = base[len(prefix) :]
            break
    base = base.replace("_", "-").lower()
    return f"/{base}" if base else f"/{skill_name}"


def extract_when_to_use(text: str) -> str:
    """返回 '## When to Use' 与下一个 '## ' 标题之间的文本。"""
    m = re.search(r"##\s*When to Use\s*\n(.*?)(?=\n##\s|\Z)", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def extract_keywords(text: str) -> list[str]:
    """从 'When to Use' 提取带引号的触发短语（支持中英文引号）。"""
    wtu = extract_when_to_use(text)
    found = re.findall(
        r"[\"\u201c\u201d\u2018\u2019]([^\"\n\u201c\u201d\u2018\u2019]{2,60})"
        r"[\"\u201c\u201d\u2018\u2019]",
        wtu,
    )
    # 仅保留含中/英文字的触发短语，剔除包含 "|" 的代码片段
    keywords = [k for k in found if "|" not in k and re.search(r"[\u4e00-\u9fffA-Za-z]", k)]
    seen: set[str] = set()
    out: list[str] = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def extract_skill_tools(text: str, known: list[str]) -> list[str]:
    """按文中首次出现顺序提取反引号引用的 MCP 工具名，仅保留真实存在者。"""
    order: list[str] = []
    for m in re.finditer(r"`([a-z_]+)`", text):
        name = m.group(1)
        if name in known and name not in order:
            order.append(name)
    return order


def generate_tools(meta: dict[str, str], tools: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "$schema": TOOLS_SCHEMA,
        "name": meta["name"],
        "version": meta["version"],
        "description": meta["description"],
        "tools": tools,
    }


def generate_triggers(skills: list[dict[str, Any]]) -> dict[str, Any]:
    triggers: list[dict[str, str]] = []
    for skill in skills:
        command = skill["command"] or derive_command_from_name(skill["dir_name"])
        triggers.append(
            {
                "type": "command",
                "pattern": f"^{re.escape(command)}(\\s.*)?$",
                "handler": "handle_command",
                "description": f"{skill['name']} 命令触发器",
            }
        )
        keywords = extract_keywords(skill["text"])
        if keywords:
            pattern = "(?i)(" + "|".join(re.escape(k) for k in keywords) + ")"
            triggers.append(
                {
                    "type": "conversation",
                    "pattern": pattern,
                    "handler": "handle_trigger",
                    "description": f"{skill['name']} 对话触发器",
                }
            )
    return {"$schema": TRIGGERS_SCHEMA, "triggers": triggers}


def generate_workflows(
    skills: list[dict[str, Any]], tools: list[dict[str, Any]]
) -> dict[str, Any]:
    known = [t["name"] for t in tools]
    desc_by_tool = {t["name"]: t["description"] for t in tools}
    workflows: list[dict[str, Any]] = []
    for skill in skills:
        steps = [
            {
                "action": tool_name,
                "description": f"调用 {tool_name}：{desc_by_tool.get(tool_name, '')}",
            }
            for tool_name in extract_skill_tools(skill["text"], known)
        ]
        workflows.append(
            {"name": skill["name"], "description": skill["description"], "steps": steps}
        )
    return {"$schema": WORKFLOWS_SCHEMA, "workflows": workflows}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"已生成 {path.relative_to(PROJECT_ROOT)}")


def main() -> None:
    meta = load_package_meta()
    tools = introspect_tools()
    skills = iter_skills()
    write_json(PLUGIN_DIR / "tools.json", generate_tools(meta, tools))
    write_json(PLUGIN_DIR / "triggers.json", generate_triggers(skills))
    write_json(PLUGIN_DIR / "workflows.json", generate_workflows(skills, tools))
    print("AAIF 声明文件已重新生成（请勿手工编辑，由脚本从真实源生成）")


if __name__ == "__main__":
    main()
