# evander-skills

技能（Skill）总仓库。所有可复用技能只在这里维护一份，再分发到各本地项目或各 AI 工具的全局技能目录。

- **唯一真源**：[skills](skills)
- **分发方式一**：复制安装到某个本地项目的 `.codebuddy/skills/`（随项目走，可提交进项目仓库）
- **分发方式二**：软链到本机各 AI 工具的全局技能目录（一次同步，全机器可用）

## 目录结构

```text
evander-skills/
├── skills/                 # 唯一真源，每个子目录就是一个技能
│   └── example-skill/
│       ├── SKILL.md        # 必需：name / description + 正文
│       └── agents/
│           └── openai.yaml # 界面显示名、短描述、默认提示词
├── scripts/
│   ├── new_skill.py        # 新建技能骨架
│   ├── install_skills.py   # 安装到本地项目（核心）
│   ├── sync_skills.py      # 同步到全局 AI 工具目录
│   └── skill_repo.py       # 公共逻辑
├── skill-targets.json      # 全局同步配置
└── .gitignore
```

## 快速开始

### 1. 拿到仓库

```bash
git clone <仓库地址> evander-skills
cd evander-skills
```

### 2. 安装到本地项目

```bash
# 安装全部技能到某项目
python3 scripts/install_skills.py --project ~/projects/your-app

# 只装指定技能
python3 scripts/install_skills.py --project ../your-app --skills example-skill

# 先看会装到哪，不落盘
python3 scripts/install_skills.py --project ../your-app --dry-run

# 覆盖已存在的同名技能
python3 scripts/install_skills.py --project ../your-app --force
```

默认安装到 `<项目>/.codebuddy/skills/<skill-name>/`，用 `--target` 可改：

```bash
# 同时装到多个目录
python3 scripts/install_skills.py --project ../your-app \
  --target .codebuddy/skills --target .claude/skills
```

> 默认 `--mode copy`：把技能文件**复制**进项目，可随项目一起提交，团队成员 clone 项目即有同一份技能。
> 想跟随仓库更新用 `--mode symlink`（不推荐用于需要提交的项目）。

### 3. 常用的三个命令

```bash
python3 scripts/install_skills.py --list          # 列出仓库里有哪些技能
python3 scripts/new_skill.py my-skill --description "什么时候用它"   # 新建技能
python3 scripts/sync_skills.py                    # 同步到全局 AI 工具目录
```

## 命令说明

### install_skills.py

| 参数 | 说明 |
|---|---|
| `--project` | 目标项目根目录，默认当前目录 |
| `--skills` | 技能名，逗号分隔；缺省安装全部 |
| `--target` | 目标子目录，可重复；缺省读 `skill-targets.json` 的 `project_install_dirs` |
| `--mode` | `copy`（默认，复制）或 `symlink`（软链） |
| `--force` | 覆盖已存在的同名技能 |
| `--dry-run` | 只输出将要执行的操作 |
| `--list` | 列出仓库内所有技能 |

### sync_skills.py

把 `skills/<skill>` 软链到 `skill-targets.json` 中 `global_targets` 配置的目录：

- CodeBuddy → `~/.codebuddy/skills/<skill>`
- Codex → `~/.codex/skills/skills/<skill>`
- Lingma → `~/.lingma/skills/<skill>`
- Claude → `~/.claude/skills/<skill>`
- Qoder CN → `~/.qoder-cn/skills/<skill>`
- Cursor → 导出 `.mdc` 到 `exports/cursor-rules/`

已存在的同名目录会被重命名成 `.backup` 后再建链接，不会直接删除。

如需把 Cursor 规则也挂到某些项目，在 `skill-targets.json` 里补 `cursor_projects`：

```json
{
  "cursor_projects": [
    "/absolute/path/to/project-a"
  ]
}
```

## 新增技能

```bash
python3 scripts/new_skill.py evander-code-review --description "审查本地变更或远程 PR，输出分级审查报告"
```

生成的骨架包含 `SKILL.md` 与 `agents/openai.yaml`，改完内容后按需补资源目录：

| 目录 | 什么时候需要 |
|---|---|
| `references/` | 有放不进 SKILL.md 的长知识：字段表、接口清单、模式库、踩坑记录 |
| `templates/` | 每次要产出形状固定的文件，且会被复制进用户工程再改写 |
| `assets/` | 被脚本或输出直接消费的成品模板，比如 HTML 报告模板 |
| `scripts/` | 需要确定性执行、或同一段代码被反复手写 |

SKILL.md 的 `description` 决定技能会不会被触发，要写清具体场景和用户会说的话。技能内引用资源一律用相对技能目录的路径。

## 同步黑名单

不希望被同步/安装的技能，在仓库根目录建 `blacklist.json`（已在 `.gitignore` 中，属于个人配置）：

```json
{
  "blacklist": ["example-skill"]
}
```

## 多 Git 账号隔离

公司仓库用公司账号、个人仓库用个人账号时，用 `includeIf` 按目录切换，不用逐个仓库配置：

```bash
# 默认把 ~/projects/wcj 及其子目录切到 evander0x，其他目录沿用全局账号
bash scripts/setup-git-identity.sh

# 自定义目录或邮箱
PERSONAL_DIR=~/projects/personal PERSONAL_EMAIL=me@example.com bash scripts/setup-git-identity.sh
```

脚本做三件事：写入 `~/.gitconfig-evander`、在 `~/.gitconfig` 追加 `includeIf "gitdir:<目录>/"`、打印当前生效身份。重复执行安全（已有规则会跳过），改动全局配置前会备份成 `~/.gitconfig.bak-<时间>`。

注意：

- 只影响**提交署名**，不影响推送权限。推送 GitHub 仍需对应账号的 HTTPS Token 或 SSH key。
- 仓库级 `user.name` 优先级高于 `includeIf`，曾单独设置过的仓库需先 `git -C <仓库> config --unset user.name`。
- 个人项目走 SSH 时，给个人 key 单独起别名（如 `Host github-evander`），避免和公司 key 冲突。
