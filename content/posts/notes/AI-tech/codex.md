---
title: "Codex CLI：OpenAI 的终端编程助手"
date: 2026-04-18
tags: ["AI", "工具"]
draft: false
summary: "OpenAI 出的终端 AI 编程助手，跟 Claude Code 定位类似但又不太一样"
showToc: true
tocOpen: true
ShowShareButtons: false
---

## 这是什么

Codex CLI 是 OpenAI 出的终端 AI 编程助手，基于 GPT-5 / o 系列模型。在终端里帮你写代码、搜文件、跑命令。

它有两个模式：交互式 TUI（进去聊）和非交互式（一句干活，干完走人）。

## 安装

```bash
brew install codex
# 或者
npm install -g @openai/codex
```

## 上手三招

```bash
# 进去聊天
codex

# 一句干活
codex exec "给 User 模型加个 email_verified 字段"

# 管道丢数据给它
git diff HEAD~1 | codex exec "审查这些改动"
```

## 常用姿势

### 选模型

```bash
codex -m gpt-5     # 日常主力
codex -m o3         # 深度推理，跟 opus 一个定位
```

GPT-5 日常够用，o3 留给那种 debug 半天搞不定的场景。

### 沙箱模式

这是 Codex CLI 的特色——它执行命令前默认跑在沙箱里，不让它乱来：

```bash
# 只能看，不能碰（审查代码用）
codex -s read-only

# 能写工作区但不能上网（日常开发用）
codex -s workspace-write

# 放飞自我（仅在自己机器上）
codex -s danger-full-access
```

一般用 `workspace-write` 就够了，既能改代码又不会乱访问外网。

### 审批策略

```bash
# 只自动执行安全命令（ls、cat、sed 之类），危险的要你点头
codex -a untrusted

# 让它自己判断要不要问你（推荐）
codex -a on-request

# 不废话直接干（CI 里用）
codex -a never
```

### 省事组合拳

```bash
# 懒得分别设，一把梭
codex --full-auto
```

等同于 `-a on-request -s workspace-write`，日常够用了。

### 指定工作目录

```bash
# 不在项目根目录也能干活
codex -C ~/projects/my-app
```

### 用本地模型

```bash
# 走 Ollama 或 LM Studio
codex --oss

# 指定后端
codex --local-provider ollama
```

这样全部本地跑，不用连 OpenAI 的服务器。

---

## CLI 子命令

### `codex exec` — 一句干活就走

```bash
codex exec "生成用户注册的测试"
codex exec --json "列出所有 API" > result.jsonl
codex exec --output-schema schema.json "提取用户信息"
codex exec --ephemeral "临时看一下不保存"
```

### `codex review` — 代码审查

```bash
codex review --uncommitted      # 审查还没提交的
codex review --base main         # 跟 main 比
codex review --commit abc1234    # 审查某个 commit
```

### `codex resume` / `codex fork` — 会话管理

```bash
codex resume              # 弹选择器回到之前的会话
codex resume --last        # 直接回最近的
codex fork --last          # 基于最近的会话分叉一个出来
```

### `codex cloud` — 云端任务（实验性）

```bash
codex cloud exec --env my-env "修 bug"
codex cloud list --env my-env
codex cloud apply task-123   # 把云端结果拉下来
```

适合那种本地跑太慢、想丢到云上干的活。

### `codex sandbox` — 沙箱里跑任意命令

```bash
codex sandbox macos -- ./untrusted-script.sh
codex sandbox linux -- npm install
```

### `codex app` — 桌面应用

```bash
codex app              # 在当前目录打开
codex app ~/project    # 指定目录
```

启动 macOS 桌面版，首次会自动下载。

### `codex mcp` — 管理 MCP 服务器

```bash
codex mcp add --url https://mcp.example.com my-server
codex mcp add my-server -- npx my-mcp-server
codex mcp list
codex mcp remove my-server
```

### `codex login` — 认证

```bash
codex login
codex login --with-api-key   # 从 stdin 读 key
codex login status
codex logout
```

### 其他

```bash
codex features list           # 看特性开关
codex completion zsh           # 生成 shell 补全
codex debug prompt-input "...  # 看发给模型的完整 prompt
```

---

## 配置文件

配置在 `~/.codex/config.toml`，所有选项都能用 `-c` 临时覆盖：

```toml
model = "gpt-5"
sandbox = "workspace-write"

[profile.work]
model = "gpt-5"
```

```bash
codex -p work "干个活"
codex -c model="o3" "这个难，切 o3"
```

---

## 沙箱怎么选

| 模式 | 可读 | 可写 | 能上网 | 用在哪 |
|------|------|------|--------|--------|
| `read-only` | 全文件 | ✗ | ✗ | 代码审查、分析 |
| `workspace-write` | 全文件 | 工作区+/tmp | ✗ | 日常开发 |
| `danger-full-access` | 全部 | 全部 | ✓ | 需要联网的任务 |

日常 `workspace-write` 足够，出不了事。

---

没了。试试看吧。
