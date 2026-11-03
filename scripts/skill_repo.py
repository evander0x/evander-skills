"""Skill 仓库公共逻辑：创建、列举、同步到全局工具目录、安装到本地项目。"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    # 全局工具目录：软链接方式，一次同步全机器可用
    "global_targets": {
        "codex": "~/.codex/skills/skills",
        "codebuddy": "~/.codebuddy/skills",
        "lingma": "~/.lingma/skills",
        "claude": "~/.claude/skills",
        "qoder_cn": "~/.qoder-cn/skills",
    },
    # Cursor 用导出的 .mdc 规则
    "cursor_export_dir": "exports/cursor-rules",
    "cursor_projects": [],
    # 安装到本地项目时的默认目标目录（相对项目根目录）
    "project_install_dirs": [".codebuddy/skills"],
}

DEFAULT_PROJECT_INSTALL_DIRS = [".codebuddy/skills"]

SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9-]+$")

# 复制技能目录时跳过的内容
IGNORED_COPY_NAMES = ("__pycache__", "node_modules", ".DS_Store", ".git", "dist")


# --------------------------------------------------------------------------
# 技能发现与创建
# --------------------------------------------------------------------------

def create_skill(repo_root: str | Path, name: str, description: str = "") -> Path:
    """在 skills/ 下创建一个最小的技能骨架。"""
    validate_skill_name(name)
    repo_root = Path(repo_root).expanduser().resolve()
    skill_path = repo_root / "skills" / name
    if skill_path.exists():
        raise FileExistsError(f"技能已存在: {skill_path}")

    (skill_path / "agents").mkdir(parents=True, exist_ok=False)
    (skill_path / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                f"name: {name}",
                f"description: {description or '描述这个技能在什么场景下使用。'}",
                "---",
                "",
                f"# {name}",
                "",
                "## 何时使用",
                "",
                "- 换成该技能的触发条件。",
                "",
                "## 执行流程",
                "",
                "1. 换成该技能的可复用步骤。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (skill_path / "agents" / "openai.yaml").write_text(
        "\n".join(
            [
                "interface:",
                f'  display_name: "{name}"',
                f'  short_description: "{description or "描述这个技能的用途"}"',
                f'  default_prompt: "使用 ${name} 完成对应任务。"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return skill_path


def iter_skill_dirs(skills_root: Path) -> list[Path]:
    """列出所有包含 SKILL.md 的技能目录。"""
    if not skills_root.exists():
        return []
    return sorted(
        path
        for path in skills_root.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    )


def select_skills(skills_root: Path, names: list[str] | None) -> list[Path]:
    """按名称挑选技能；names 为 None 时返回全部，名称不存在时报错。"""
    all_skills = iter_skill_dirs(skills_root)
    if names is None:
        return all_skills

    index = {skill.name: skill for skill in all_skills}
    missing = [name for name in names if name not in index]
    if missing:
        raise KeyError(f"未找到技能: {', '.join(missing)}；可用技能: {', '.join(index) or '无'}")
    return [index[name] for name in names]


def validate_skill_name(name: str) -> None:
    if not SKILL_NAME_PATTERN.match(name):
        raise ValueError("技能目录名只能使用小写字母、数字和连字符。")


# --------------------------------------------------------------------------
# 读取与导出
# --------------------------------------------------------------------------

def read_skill_file(skill_file: Path) -> tuple[dict[str, str], str]:
    """拆出 SKILL.md 的 frontmatter 与正文。"""
    text = skill_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    metadata: dict[str, str] = {}
    for line in parts[1].strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, parts[2].lstrip("\n")


def render_cursor_rule(skill_dir: Path) -> str:
    """把 SKILL.md 转成 Cursor 的 .mdc 规则。"""
    metadata, body = read_skill_file(skill_dir / "SKILL.md")
    description = metadata.get("description", "Imported from repository skill.")
    return "\n".join(
        [
            "---",
            f"description: {description}",
            "globs:",
            "alwaysApply: false",
            "---",
            "",
            f"# Skill: {metadata.get('name', skill_dir.name)}",
            "",
            "Generated from the shared skill repository. Use this rule when the request matches the skill description.",
            "",
            body.strip(),
            "",
        ]
    )


# --------------------------------------------------------------------------
# 安装到本地项目（复制 / 软链）
# --------------------------------------------------------------------------

def install_to_project(
    repo_root: str | Path,
    project_root: str | Path,
    skill_names: list[str] | None = None,
    target_dirs: list[str] | None = None,
    mode: str = "copy",
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, list[Path]]:
    """把技能安装到指定项目的 target_dirs 下。

    mode="copy"    复制文件，随项目一起提交（默认）
    mode="symlink" 建软链接，跟随仓库更新
    """
    if mode not in ("copy", "symlink"):
        raise ValueError(f"不支持的安装方式: {mode}")

    repo_root = Path(repo_root).expanduser().resolve()
    project_root = Path(project_root).expanduser().resolve()
    if not project_root.is_dir():
        raise FileNotFoundError(f"项目目录不存在: {project_root}")

    skills = select_skills(repo_root / "skills", skill_names)
    if not skills:
        raise FileNotFoundError(f"{repo_root / 'skills'} 下没有任何技能")

    dirs = target_dirs or DEFAULT_PROJECT_INSTALL_DIRS
    results: dict[str, list[Path]] = {"installed": [], "linked": [], "skipped": []}

    for target_dir in dirs:
        for skill_dir in skills:
            dest = project_root / target_dir / skill_dir.name
            if dry_run:
                results["skipped"].append(dest)
                continue

            already_linked = dest.is_symlink() and dest.resolve() == skill_dir.resolve()
            if dest.is_symlink() or dest.exists():
                if not already_linked:
                    if not force:
                        results["skipped"].append(dest)
                        continue
                    remove_path(dest)

            if mode == "symlink":
                ensure_symlink(dest, skill_dir)
                results["linked"].append(dest)
                continue

            if not already_linked:
                copy_skill_tree(skill_dir, dest)
            results["installed"].append(dest)

    return results


def copy_skill_tree(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, dest, ignore=shutil.ignore_patterns(*IGNORED_COPY_NAMES))


# --------------------------------------------------------------------------
# 同步到全局 AI 工具目录
# --------------------------------------------------------------------------

def sync_skills(repo_root: str | Path, config: dict[str, Any] | None = None) -> dict[str, list[Path]]:
    """把技能软链到各 AI 工具的全局技能目录，并导出 Cursor 规则。"""
    repo_root = Path(repo_root).expanduser().resolve()
    merged = load_config(repo_root, None, config)

    blacklisted = set(load_blacklist(repo_root))
    all_skills = iter_skill_dirs(repo_root / "skills")
    active_skills = [skill for skill in all_skills if skill.name not in blacklisted]

    results: dict[str, list[Path]] = {key: [] for key in merged["global_targets"]}
    results["cursor_exports"] = []
    results["cursor_projects"] = []

    for group, raw_dir in merged["global_targets"].items():
        target_dir = resolve_path(repo_root, raw_dir)
        for skill_dir in all_skills:
            if skill_dir.name in blacklisted:
                remove_path(target_dir / skill_dir.name)
        for skill_dir in active_skills:
            link_path = target_dir / skill_dir.name
            ensure_symlink(link_path, skill_dir)
            results[group].append(link_path)

    cursor_export_dir = resolve_path(repo_root, merged["cursor_export_dir"])
    cursor_export_dir.mkdir(parents=True, exist_ok=True)
    for skill_dir in all_skills:
        if skill_dir.name in blacklisted:
            remove_path(cursor_export_dir / f"{skill_dir.name}.mdc")
    for skill_dir in active_skills:
        rule_path = cursor_export_dir / f"{skill_dir.name}.mdc"
        rule_path.write_text(render_cursor_rule(skill_dir), encoding="utf-8")
        results["cursor_exports"].append(rule_path)

    for project in merged.get("cursor_projects", []):
        rules_dir = resolve_path(repo_root, project) / ".cursor" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        for skill_dir in all_skills:
            if skill_dir.name in blacklisted:
                remove_path(rules_dir / f"{skill_dir.name}.mdc")
        for rule_path in results["cursor_exports"]:
            link_path = rules_dir / rule_path.name
            ensure_symlink(link_path, rule_path)
            results["cursor_projects"].append(link_path)

    return results


# --------------------------------------------------------------------------
# 通用工具
# --------------------------------------------------------------------------

def ensure_symlink(link_path: Path, target_path: Path) -> None:
    target_path = target_path.resolve()
    link_path.parent.mkdir(parents=True, exist_ok=True)

    if link_path.is_symlink():
        if link_path.resolve() == target_path:
            return
        link_path.unlink()
    elif link_path.exists():
        backup_path = next_backup_path(link_path)
        shutil.move(str(link_path), str(backup_path))

    link_path.symlink_to(target_path)


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    if path.is_dir():
        shutil.rmtree(path)


def next_backup_path(path: Path) -> Path:
    candidate = path.with_name(f"{path.name}.backup")
    index = 1
    while candidate.exists() or candidate.is_symlink():
        candidate = path.with_name(f"{path.name}.backup-{index}")
        index += 1
    return candidate


def resolve_path(base: Path, raw_path: str) -> Path:
    expanded = Path(os.path.expanduser(raw_path))
    if expanded.is_absolute():
        return expanded
    return (base / expanded).resolve()


def load_blacklist(repo_root: Path) -> list[str]:
    """同步黑名单：仓库根目录 blacklist.json 的 blacklist 字段，缺省为空。"""
    blacklist_file = repo_root / "blacklist.json"
    if not blacklist_file.exists():
        return []

    loaded = json.loads(blacklist_file.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return []
    blacklist = loaded.get("blacklist", [])
    if not isinstance(blacklist, list):
        return []
    return [name for name in blacklist if isinstance(name, str)]


def load_config(
    repo_root: str | Path,
    config_path: str | Path | None = None,
    override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repo_root = Path(repo_root).expanduser().resolve()
    config_file = repo_root / "skill-targets.json" if config_path is None else Path(config_path)
    if not config_file.is_absolute():
        config_file = (repo_root / config_file).resolve()

    merged: dict[str, Any] = json.loads(json.dumps(DEFAULT_CONFIG))
    if config_file.exists():
        loaded = json.loads(config_file.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            for key, value in loaded.items():
                if isinstance(value, dict) and isinstance(merged.get(key), dict):
                    merged[key] = {**merged[key], **value}
                else:
                    merged[key] = value
    if override:
        merged.update(override)
    # 黑名单只认 blacklist.json，忽略配置里的同名键
    merged.pop("blacklist", None)
    return merged


def parse_skill_list(raw: str | None) -> list[str] | None:
    """解析 --skills a,b,c 或 --skills a --skills b 形式的输入。"""
    if not raw:
        return None
    names = [name.strip() for chunk in raw.split(",") for name in [chunk]]
    names = [name for name in names if name]
    return names or None


# --------------------------------------------------------------------------
# 命令行参数
# --------------------------------------------------------------------------

def build_new_skill_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="在技能仓库中创建新技能骨架。")
    parser.add_argument("name", help="技能目录名，例如 evander-code-review")
    parser.add_argument("--description", default="", help="技能的触发描述")
    parser.add_argument("--repo-root", default=".", help="技能仓库根目录")
    return parser


def build_sync_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="把技能同步到本机各 AI 工具的全局技能目录。")
    parser.add_argument("--repo-root", default=".", help="技能仓库根目录")
    parser.add_argument("--config", default="skill-targets.json", help="同步配置文件")
    return parser


def build_install_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="把技能安装到指定本地项目的技能目录。")
    parser.add_argument("--project", default=".", help="目标项目根目录")
    parser.add_argument("--skills", default=None, help="技能名，逗号分隔；缺省安装全部")
    parser.add_argument("--target", action="append", default=None,
                        help="目标子目录，可重复；缺省读配置 project_install_dirs")
    parser.add_argument("--mode", choices=["copy", "symlink"], default="copy",
                        help="copy=复制文件（默认），symlink=软链接")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的技能目录")
    parser.add_argument("--dry-run", action="store_true", help="只打印将要执行的操作")
    parser.add_argument("--list", action="store_true", help="列出仓库内所有技能后退出")
    parser.add_argument("--repo-root", default=".", help="技能仓库根目录")
    return parser


def build_list_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="列出技能仓库中的所有技能。")
    parser.add_argument("--repo-root", default=".", help="技能仓库根目录")
    return parser
