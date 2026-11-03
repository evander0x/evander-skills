---
name: smart-commit
description: 根据 git 暂存/未暂存的变更自动生成简洁清晰的提交说明，并执行 git add / commit（可选 push）。当用户说「提交代码」「写个 commit」「生成提交信息并 commit」「帮我把改动提交一下」时使用。
---

# smart-commit

根据当前工作区变更，生成一条符合 Angular Commit 规范的中文提交信息，并完成提交。

## 何时使用

- 用户想把当前改动提交，但不想自己写 commit message
- 用户说「提交代码」「写个 commit」「帮我把改动提交一下」
- 用户想先预览将要生成的提交信息，再决定是否提交

## 执行流程

1. 检查仓库状态：运行 `git status` 与 `git diff`（含 `--staged` 与未暂存差异），确认有可提交内容；无变更时直接告知用户并停止。
2. 判断范围：
   - 已有 staged 内容 → 直接基于 staged 生成说明。
   - 无 staged 内容 → 默认把所有改动 `git add -A` 后再提交；若用户只点名部分文件，则只 `git add` 指定文件。
3. 生成 commit message：阅读 diff，按下方「说明格式」生成符合 Angular 规范的提交信息；其中 `<issue>` 优先取用户提供的 GitHub issue 号（如 `#1`），其次从分支名（如 `fix/issue-1-...`）提取，都没有则留空。
4. 提交：执行 `git commit -m "<说明>"`。
5. 推送（可选）：除非用户明确说「push」「推上去」，否则不自动推送。

## 说明格式

格式：

```text
<type>(<scope>): <issue> <subject>
```

约束：

- `type` 使用英文，从下列取值：`feat`、`fix`、`docs`、`style`、`refactor`、`perf`、`test`、`chore`、`build`、`ci`、`revert`。
- `scope` 可选，建议使用中文模块名，如 `登录页`、`导出模块`；无明确模块时省略（写成 `<type>: <subject>`）。
- `issue` 可选，填写 GitHub issue 号（如 `#1`）；取值时必须去除首尾空格；没有则不写。可用正文 `Closes #1` / `Fixes #1` 关闭对应 issue。
- `subject` 必须中文，准确描述本次**实际改动**，避免空泛词（如「优化」「更新」「修改代码」「调整」这类看不出内容的词不要单独使用，需补具体对象或行为）。
- 需要补充背景时，空一行后写正文（body），说明原因或影响，每行 ≤ 72 字；正文里可用 `Closes <issue>` 关闭单号。

type 选择速查：

| type | 适用场景 |
|---|---|
| `feat` | 新增功能或能力 |
| `fix` | 修复缺陷 / bug |
| `docs` | 文档改动（无代码逻辑变化） |
| `style` | 不影响逻辑的格式调整（空格、缩进、分号） |
| `refactor` | 重构，既不修 bug 也不加功能 |
| `perf` | 性能优化 |
| `test` | 增删测试用例 |
| `chore` | 构建、依赖、杂项等无关业务逻辑的改动 |
| `build` | 构建系统 / 外部依赖变动 |
| `ci` | CI 配置文件 / 脚本变动 |
| `revert` | 回退某次提交 |

## 示例

改了登录页按钮在窄屏下溢出，且关联 issue `#1`：

```bash
git add -A
git commit -m "fix(登录页): #1 修复窄屏下按钮溢出遮挡文案"
```

无单号、改了导出模块的新功能：

```bash
git commit -m "feat(导出模块): 支持导出 CSV 格式"
```

分支名为 `fix/issue-1-auth-token`、修复了鉴权 token 刷新：

```bash
git commit -m "fix(鉴权): #1 抽离 token 刷新逻辑到独立服务"
```

## 注意事项

- 提交前确认 `git status` 不含敏感文件（密钥、`.env`、凭据）；如有，先提醒用户并排除，不要提交。
- 不在 commit message 里粘贴大段 diff 或报错原文。
- 用户要求「先看一眼」时，只输出将要执行的命令与生成的说明，等确认后再真正运行 `git commit`。
- 引用仓库内资源一律用相对路径，不写死本机绝对路径。
