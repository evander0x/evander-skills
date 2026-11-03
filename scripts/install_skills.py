from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.skill_repo import (
    build_install_parser,
    install_to_project,
    iter_skill_dirs,
    load_blacklist,
    load_config,
    parse_skill_list,
    read_skill_file,
)


def print_skills(repo_root: Path) -> None:
    skills = iter_skill_dirs(repo_root / "skills")
    if not skills:
        print("仓库内暂无技能")
        return
    for skill_dir in skills:
        metadata, _ = read_skill_file(skill_dir / "SKILL.md")
        print(f"{skill_dir.name}\t{metadata.get('description', '')}")


def resolve_skill_names(repo_root: Path, raw_skills: str | None) -> list[str]:
    names = parse_skill_list(raw_skills)
    if names is not None:
        return names
    # 未显式指定时跳过 blacklist 中的技能；显式点名则尊重用户意图
    blacklisted = set(load_blacklist(repo_root))
    return [skill.name for skill in iter_skill_dirs(repo_root / "skills") if skill.name not in blacklisted]


def report(results: dict[str, list[Path]], project_root: Path, mode: str, dry_run: bool) -> None:
    labels = {
        "installed": "已复制" if mode == "copy" else "已安装",
        "linked": "已软链",
        "skipped": "已跳过（已存在或 dry-run）",
    }
    for key in ("installed", "linked", "skipped"):
        paths = results[key]
        if not paths:
            continue
        print(f"[{labels[key]}]")
        for path in paths:
            print(path.relative_to(project_root))
    if results["skipped"] and not dry_run:
        print("提示：已存在的技能需加 --force 覆盖。")


def main() -> None:
    parser = build_install_parser()
    args = parser.parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()

    if args.list:
        print_skills(repo_root)
        return

    skill_names = resolve_skill_names(repo_root, args.skills)
    if not skill_names:
        print("没有可安装的技能（仓库为空，或技能都在 blacklist 中）")
        return

    config = load_config(repo_root)
    project_root = Path(args.project).expanduser().resolve()

    try:
        results = install_to_project(
            repo_root=repo_root,
            project_root=project_root,
            skill_names=skill_names,
            target_dirs=args.target or config["project_install_dirs"],
            mode=args.mode,
            force=args.force,
            dry_run=args.dry_run,
        )
    except (KeyError, ValueError, FileNotFoundError) as error:
        message = error.args[0] if error.args else str(error)
        print(f"安装失败：{message}")
        sys.exit(1)

    report(results, project_root, args.mode, args.dry_run)


if __name__ == "__main__":
    main()
