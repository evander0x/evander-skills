#!/usr/bin/env bash
# 按目录隔离 Git 提交身份：
#   $PERSONAL_DIR 及其子目录 → 个人账号
#   其他目录             → 沿用全局（公司）账号
#
# 用法：
#   bash scripts/setup-git-identity.sh
#   PERSONAL_EMAIL=me@example.com bash scripts/setup-git-identity.sh
#   PERSONAL_DIR=~/projects/personal bash scripts/setup-git-identity.sh

set -euo pipefail

PERSONAL_NAME="${PERSONAL_NAME:-evander0x}"
PERSONAL_EMAIL="${PERSONAL_EMAIL:-evander0x@users.noreply.github.com}"
PERSONAL_DIR="${PERSONAL_DIR:-$HOME/projects/wcj}"

GLOBAL_CONFIG="$HOME/.gitconfig"
PERSONAL_CONFIG="$HOME/.gitconfig-evander"

# 用物理路径（pwd -P）：Git 匹配 gitdir 时解析的是真实路径，符号链接会导致不生效
ABS_DIR="$(cd "$PERSONAL_DIR" 2>/dev/null && pwd -P || true)"
if [ -z "$ABS_DIR" ]; then
  echo "错误：个人项目目录不存在 -> $PERSONAL_DIR"
  exit 1
fi

echo "个人账号目录：$ABS_DIR"
echo "个人身份：$PERSONAL_NAME <$PERSONAL_EMAIL>"
echo

# 1. 写入个人身份文件
cat > "$PERSONAL_CONFIG" <<EOF
[user]
    name = $PERSONAL_NAME
    email = $PERSONAL_EMAIL
EOF
echo "✔ 已写入 $PERSONAL_CONFIG"

# 2. 在全局配置里挂 includeIf（幂等）
MARKER="gitdir:$ABS_DIR/"
if [ -f "$GLOBAL_CONFIG" ] && grep -qF "\"$MARKER\"" "$GLOBAL_CONFIG"; then
  echo "✔ $GLOBAL_CONFIG 已包含 $MARKER，跳过"
else
  if [ -f "$GLOBAL_CONFIG" ]; then
    BACKUP="$GLOBAL_CONFIG.bak-$(date +%Y%m%d%H%M%S)"
    cp "$GLOBAL_CONFIG" "$BACKUP"
    echo "✔ 已备份全局配置 -> $BACKUP"
  fi
  {
    echo ""
    echo "[includeIf \"$MARKER\"]"
    echo "    path = $PERSONAL_CONFIG"
  } >> "$GLOBAL_CONFIG"
  echo "✔ 已在 $GLOBAL_CONFIG 追加 includeIf 规则"
fi

# 3. 结果自检
echo
echo "== 当前生效身份 =="
FIRST_GIT="$(find "$ABS_DIR" -maxdepth 2 -name .git 2>/dev/null | head -1 || true)"
if [ -n "$FIRST_GIT" ]; then
  REPO_DIR="$(dirname "$FIRST_GIT")"
  echo "$REPO_DIR"
  echo "  $(git -C "$REPO_DIR" config user.name) <$(git -C "$REPO_DIR" config user.email)>"
fi

echo "全局（wcj 之外）"
echo "  $(git config --global user.name) <$(git config --global user.email)>"

cat <<'TIP'

== 注意事项 ==
1. 仓库级配置优先级高于 includeIf。若某个仓库曾单独设置过 user.name，需先清理：
     git -C <仓库> config --unset user.name
     git -C <仓库> config --unset user.email
2. 本脚本只影响提交署名，不影响推送权限。推送 GitHub 仍需对应账号的
   HTTPS Token（首次 push 输入）或 SSH key。
3. 个人项目走 SSH 时，建议在 ~/.ssh/config 给个人 key 单独起别名，
   避免和公司 key 冲突：
     Host github-evander
         HostName github.com
         User git
         IdentityFile ~/.ssh/id_ed25519
   远端地址写成 git@github-evander:evander0x/evander-skills.git
TIP
