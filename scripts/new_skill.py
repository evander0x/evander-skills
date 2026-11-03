import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.skill_repo import build_new_skill_parser, create_skill


def main() -> None:
    parser = build_new_skill_parser()
    args = parser.parse_args()
    skill_path = create_skill(args.repo_root, args.name, description=args.description)
    print(skill_path)


if __name__ == "__main__":
    main()
