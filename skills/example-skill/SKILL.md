---
name: example-skill
description: 示例技能，演示 evander-skills 仓库的技能结构与资源约定（SKILL.md + agents/ + 可选 references / templates / assets / scripts）。当需要新建技能、确认目录约定，或验证「把技能安装到本地项目」的流程时使用。
---

# example-skill

本技能不解决具体业务，只作为模板存在。新建技能时复制它的结构，改掉 `name`、`description` 与正文即可。

## 何时使用

- 需要在本仓库新增技能，想确认目录该怎么放
- 需要验证 `scripts/install_skills.py` 能否把技能正确装进某个项目
- 需要向别人演示技能从仓库分发到项目的完整链路

## 执行流程

1. 确认技能先落在本仓库的 `skills/<skill-name>/` 下，而不是直接写进业务项目。
2. 只写 `SKILL.md` 即可跑通；出现下列信号时再补资源目录：
   - 正文被大段字段表、接口说明撑长 → 拆到 `references/`
   - 每次都要生成形状固定的文件 → 放 `templates/`（要被改写进工程）或 `assets/`（被脚本直接消费）
   - 同一段代码被反复手写、或需要确定性执行 → 抽到 `scripts/`
3. 补 `agents/openai.yaml`，让技能在对话工具里有可读的显示名与默认提示词。
4. 运行 `python3 scripts/install_skills.py --project <项目路径>` 安装到目标项目验证。

## 目录约定

```text
skills/example-skill/
├── SKILL.md              # 必需，含 name / description frontmatter
├── agents/openai.yaml    # 界面显示名、短描述、默认提示词
├── references/           # 按需加载的知识文档
├── templates/            # 可复制进工程的脚手架
├── assets/               # 脚本或输出直接消费的成品模板
└── scripts/              # 需要确定性执行的程序
```

## 注意事项

- `SKILL.md` 只写「做什么、什么时候做、怎么做」，长资料放 `references/`。
- `description` 决定技能会不会被触发，要写清具体场景和用户会说的话。
- 技能内引用资源一律用相对技能目录的路径，不要写死本机绝对路径。
