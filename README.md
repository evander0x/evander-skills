# evander-skills

可复用 AI 技能的**唯一真源**仓库。所有技能只在这里维护一份，再分发到本地项目或本机各 AI 工具的全局技能目录。

两种分发方式：

- **装到项目**（随项目提交，团队共享）：复制 `skills/<skill>` 到项目的 `.codebuddy/skills/`。
- **同步到全局**（本机通用，一次同步全机器可用）：软链到各 AI 工具的全局技能目录。

## 目录结构

```text
evander-skills/
├── skills/                 # 唯一真源，每个子目录 = 一个技能
│   └── <skill>/
│       ├── SKILL.md        # 必需：name / description + 使用说明（CodeBuddy/Claude 读取）
│       ├── agents/
│       │   └── openai.yaml # OpenAI 兼容界面的显示名 / 简介 / 默认提示词
│       ├── references/     # 可选：长知识文档（字段表、接口清单、踩坑记录）
│       ├── templates/      # 可选：会被复制进工程再改写的脚手架
│       ├── assets/         # 可选：脚本/输出直接消费的成品模板
│       └── scripts/        # 可选：需确定性执行的程序
├── scripts/
│   ├── new_skill.py        # 新建技能骨架
│   ├── install_skills.py   # 安装到本地项目
│   ├── sync_skills.py      # 同步到全局 AI 工具目录
│   └── skill_repo.py       # 上面的公共逻辑
├── skill-targets.json      # 全局同步配置（global_targets / project_install_dirs / cursor_projects）
└── .gitignore
```

`example-skill/` 是一个演示骨架结构的模板技能，可删除或当作新建技能的出发点。

## 快速开始

### 1. 拿到仓库

```bash
git clone <仓库地址> evander-skills
cd evander-skills
```

### 2. 安装到本地项目

```bash
# 安装全部技能
python3 scripts/install_skills.py --project ~/projects/your-app

# 只装指定技能
python3 scripts/install_skills.py --project ../your-app --skills example-skill

# 先看会装到哪，不落盘
python3 scripts/install_skills.py --project ../your-app --dry-run

# 覆盖已存在的同名技能
python3 scripts/install_skills.py --project ../your-app --force
```

默认装到 `<项目>/.codebuddy/skills/<skill-name>/`，可用 `--target` 改目标子目录：

```bash
python3 scripts/install_skills.py --project ../your-app \
  --target .codebuddy/skills --target .claude/skills
```

> `--mode copy`（默认）：把技能**复制**进项目，可随项目一起提交，团队成员 clone 即有一份相同技能。
> `--mode symlink`：软链跟随仓库更新，但不推荐用于需要提交的项目。

### 3. 同步到全局 AI 工具目录

```bash
python3 scripts/sync_skills.py
```

把 `skills/<skill>` 软链到 `skill-targets.json` 里 `global_targets` 配置的目录（已存在的同名目录会先改名成 `.backup`，不会直接删除）：

- CodeBuddy → `~/.codebuddy/skills/<skill>`
- Codex → `~/.codex/skills/skills/<skill>`
- Lingma → `~/.lingma/skills/<skill>`
- Claude → `~/.claude/skills/<skill>`
- Qoder CN → `~/.qoder-cn/skills/<skill>`
- Cursor → 导出 `.mdc` 到 `exports/cursor-rules/`

### 4. 新建技能

```bash
python3 scripts/new_skill.py my-skill --description "什么时候用它"
```

生成 `SKILL.md` 与 `agents/openai.yaml` 骨架，再按需要补 `references/`、`templates/`、`assets/`、`scripts/`。

## 技能结构

每个技能是一个目录，核心是两份描述文件，面向不同的消费方：

- **`SKILL.md`**：给 CodeBuddy / Claude 这类读取 Markdown 的加载器用，写「做什么、什么时候做、怎么做」。其中的 `description` 决定技能会不会被触发，要写清具体场景和用户会说的话。
- **`agents/openai.yaml`**：给 OpenAI 兼容对话界面用，提供可读的 `display_name`、`short_description` 和触发时的 `default_prompt`。它是 `SKILL.md` 的「OpenAI 接口版名片」，由脚手架自动生成。

资源目录按需添加，技能内引用资源一律用相对技能目录的路径（不要写死本机绝对路径）：

| 目录 | 什么时候需要 |
|---|---|
| `references/` | 有放不进 SKILL.md 的长知识：字段表、接口清单、模式库、踩坑记录 |
| `templates/` | 每次要产出形状固定的文件，且会被复制进用户工程再改写 |
| `assets/` | 被脚本或输出直接消费的成品模板，比如 HTML 报告模板 |
| `scripts/` | 需要确定性执行、或同一段代码被反复手写 |

## 命令参考

### install_skills.py

| 参数 | 说明 |
|---|---|
| `--project` | 目标项目根目录，默认当前目录 |
| `--skills` | 技能名，逗号分隔；缺省安装全部 |
| `--target` | 目标子目录，可重复；缺省读 `skill-targets.json` 的 `project_install_dirs` |
| `--mode` | `copy`（默认）或 `symlink` |
| `--force` | 覆盖已存在的同名技能 |
| `--dry-run` | 只输出将要执行的操作 |
| `--list` | 列出仓库内所有技能 |

### sync_skills.py

| 参数 | 说明 |
|---|---|
| `--repo-root` | 技能仓库根目录，默认当前目录 |
| `--config` | 同步配置文件，默认 `skill-targets.json` |

效果见上方「3. 同步到全局 AI 工具目录」。

### new_skill.py

| 参数 | 说明 |
|---|---|
| `name` | 技能目录名，例如 `evander-code-review`（必需） |
| `--description` | 技能的触发描述 |
| `--repo-root` | 技能仓库根目录，默认当前目录 |

## 进阶配置

### skill-targets.json

同步/安装的目标目录都从这里读，常见字段：

- `global_targets`：各 AI 工具的全局技能目录映射（见 sync 说明）。
- `project_install_dirs`：install 不传 `--target` 时的默认安装目录。
- `cursor_projects`：需要把 Cursor 规则也挂上去的项目绝对路径列表。

```json
{
  "cursor_projects": [
    "/absolute/path/to/project-a"
  ]
}
```

### 同步黑名单

不希望被同步/安装的技能，在仓库根目录建 `blacklist.json`（已在 `.gitignore` 中，属个人配置）：

```json
{
  "blacklist": ["example-skill"]
}
```
