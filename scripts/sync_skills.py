import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.skill_repo import build_sync_parser, load_config, sync_skills


def main() -> None:
    parser = build_sync_parser()
    args = parser.parse_args()
    config = load_config(args.repo_root, args.config)
    results = sync_skills(args.repo_root, config)
    for group, paths in results.items():
        print(f"[{group}]")
        for path in paths:
            print(path)


if __name__ == "__main__":
    main()
