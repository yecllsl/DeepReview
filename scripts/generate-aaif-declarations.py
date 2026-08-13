#!/usr/bin/env python3
"""Generate AAIF declaration files from the real DeepReview sources.

The three files this script produces — tools.json, triggers.json and
workflows.json — are part of the AAIF (Agent Agnostic Interface Format)
standard and MUST NOT be edited by hand. They are generated from:

- MCP tools: introspected from the live FastMCP server (tools.json).
- Skills: parsed from .agents/skills/*/SKILL.md frontmatter + body
  (triggers.json, workflows.json).

Run this script through the MCP package environment so the deep_review_mcp
module is importable:

    uv run --no-sync --directory deep-review-mcp python scripts/generate-aaif-declarations.py

Generated files (.agents/tools.json / triggers.json / workflows.json):
- tools.json     — MCP tool declarations (name / description / parameters).
- triggers.json  — command triggers (/command) and conversational triggers
                   extracted from each SKILL.md "When to Use" section.
- workflows.json — tool invocations referenced by each skill's workflow.
"""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = PROJECT_ROOT / ".agents"
SKILLS_DIR = AGENTS_DIR / "skills"
MCP_PYPROJECT = PROJECT_ROOT / "deep-review-mcp" / "pyproject.toml"

TOOLS_OUT = AGENTS_DIR / "tools.json"
TRIGGERS_OUT = AGENTS_DIR / "triggers.json"
WORKFLOWS_OUT = AGENTS_DIR / "workflows.json"

HEADER = {
    "schema": "https://agents.aaif.io/schemas/tools.json",
    "generated_by": "scripts/generate-aaif-declarations.py",
    "generated_from": "deep-review-mcp (MCP introspection) + .agents/skills/*/SKILL.md",
    "manual_edits_will_be_overwritten": True,
}


# ──────────────────────────────────────────────────────────
# MCP tool introspection
# ──────────────────────────────────────────────────────────
def load_package_meta() -> dict[str, str]:
    """Read name/version/description from pyproject.toml (stdlib tomllib)."""
    try:
        import tomllib
    except ImportError:  # pragma: no cover - Python < 3.11
        import tomli as tomllib  # type: ignore
    data = tomllib.loads(MCP_PYPROJECT.read_text(encoding="utf-8"))
    proj = data.get("project", {})
    return {
        "name": proj.get("name", "deep-review-mcp"),
        "version": proj.get("version", ""),
        "description": proj.get("description", ""),
    }


def introspect_tools() -> list[dict[str, Any]]:
    """Introspect the live FastMCP server's registered tools."""
    from deep_review_mcp import server  # local import; run via uv --directory

    async def _list() -> Any:
        return await server.mcp.list_tools()

    tools = asyncio.run(_list())
    return [
        {
            "name": t.name,
            "description": t.description or "",
            "parameters": (getattr(t, "parameters", None) or {"type": "object", "properties": {}}),
        }
        for t in tools
    ]


# ──────────────────────────────────────────────────────────
# SKILL.md parsing
# ──────────────────────────────────────────────────────────
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict[str, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    data: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def extract_when_to_use(text: str) -> str:
    """Return the text between '## When to Use' and the next '## ' heading."""
    m = re.search(r"## When to Use\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def extract_conversational_triggers(section: str) -> list[str]:
    """Extract quoted trigger phrases from the 'When to Use' section."""
    triggers: list[str] = []
    for m in re.finditer(r"[\"\u201c\u201d\u2018\u2019]([^\"\n]{2,60})[\"\u201c\u201d\u2018\u2019]", section):
        phrase = m.group(1).strip()
        if phrase and phrase not in triggers:
            triggers.append(phrase)
    return triggers


def extract_skill_tools(text: str, known_tools: set[str] | None = None) -> list[str]:
    """Extract backtick-quoted MCP tool names in first-appearance order.

    Only names matching the actual MCP tool registry (introspected from the
    live server) are kept; prompt-template names (e.g. ``analyze_prompt``) or
    parameter names (e.g. ``group_by``) are filtered out.
    """
    tools: list[str] = []
    # 工具名形如 save_wrong_question / ocr_recognize（蛇形命名，含下划线）。
    pattern = re.compile(r"`([a-z][a-z0-9]*(?:_[a-z0-9]+)+)`")
    for m in pattern.finditer(text):
        name = m.group(1)
        if name in tools:
            continue
        if known_tools is not None and name not in known_tools:
            continue
        tools.append(name)
    return tools


def iter_skills() -> list[tuple[str, str, dict[str, str], str]]:
    """Yield (dir_name, command, frontmatter, full_text) for each skill."""
    skills: list[tuple[str, str, dict[str, str], str]] = []
    if not SKILLS_DIR.is_dir():
        return skills
    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    for skill_dir in skill_dirs:
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        text = skill_file.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        command = fm.get("command", "")
        skills.append((skill_dir.name, command, fm, text))
    return skills


def derive_command_from_name(skill_name: str) -> str:
    """Fallback: derive a /command from the skill directory name.

    Prefer the explicit `command:` frontmatter key; this fallback strips
    known prefixes and maps what remains to a slash command.
    """
    base = skill_name
    for prefix in ("wrong-question-", "review-", "deep-review-"):
        if base.startswith(prefix):
            base = base[len(prefix):]
            break
    base = base.replace("_", "-").lower()
    return f"/{base}" if base else f"/{skill_name}"


# ──────────────────────────────────────────────────────────
# JSON writers
# ──────────────────────────────────────────────────────────
def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    package = load_package_meta()
    skills = iter_skills()

    # tools.json
    tools = introspect_tools()
    known_tool_names = {t["name"] for t in tools}
    write_json(
        TOOLS_OUT,
        {
            **HEADER,
            "package": package,
            "tools": tools,
        },
    )
    print(f"已生成 {TOOLS_OUT.name}: {len(tools)} 个 MCP Tools")

    # triggers.json
    triggers: dict[str, Any] = {"schema": "https://agents.aaif.io/schemas/triggers.json", "triggers": []}
    for skill_name, command, fm, text in skills:
        entry: dict[str, Any] = {
            "skill": skill_name,
            "name": fm.get("name", skill_name),
            "description": fm.get("description", ""),
        }
        if command:
            entry["command"] = command
        else:
            entry["command"] = derive_command_from_name(skill_name)
        when = extract_when_to_use(text)
        conversational = extract_conversational_triggers(when)
        entry["conversational"] = conversational
        entry["when_to_use"] = when
        triggers["triggers"].append(entry)
    write_json(TRIGGERS_OUT, triggers)
    print(f"已生成 {TRIGGERS_OUT.name}: {len(triggers['triggers'])} 个 Skill 触发器")

    # workflows.json
    workflows: dict[str, Any] = {"schema": "https://agents.aaif.io/schemas/workflows.json", "workflows": []}
    for skill_name, command, fm, text in skills:
        workflows["workflows"].append(
            {
                "skill": skill_name,
                "name": fm.get("name", skill_name),
                "command": command or derive_command_from_name(skill_name),
                "tools": extract_skill_tools(text, known_tool_names),
            }
        )
    write_json(WORKFLOWS_OUT, workflows)
    print(f"已生成 {WORKFLOWS_OUT.name}: {len(workflows['workflows'])} 个 Skill 工作流")


if __name__ == "__main__":
    main()
