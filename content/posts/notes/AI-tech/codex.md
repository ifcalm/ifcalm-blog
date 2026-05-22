---
title: "Codex CLI：OpenAI 的终端编程助手"
date: 2026-04-18
tags: ["AI", "工具"]
draft: false
summary: "OpenAI Codex CLI 终端 AI 编程助手全部命令详解"
showToc: true
tocOpen: true
ShowShareButtons: false
---

## 简介

Codex CLI 是 OpenAI 推出的终端 AI 编程助手，直接在终端中运行。基于 GPT-5 / o 系列模型，支持交互式 TUI 和非交互式批处理两种模式。它采用 Agent 架构，能自主搜索代码、编辑文件、执行终端命令并验证结果。

## 安装

```bash
# macOS
brew install codex

# npm 全局安装
npm install -g @openai/codex
```

安装后运行 `codex` 进入交互式 TUI 会话。

## 基本用法

```bash
# 启动交互式 TUI
codex

# 带初始 prompt 启动
codex "帮我在 User 模型加一个 email_verified 字段"

# 非交互执行（执行后退出）
codex exec "分析这个项目的结构"

# 从 stdin 传入内容
cat error.log | codex exec "分析这个错误日志"
```

---

## CLI 选项（Flags）

以下选项适用于 `codex`（交互式）和 `codex exec`（非交互式）。部分选项为 `exec` 专属。

### 会话模式

| 选项 | 说明 | 适用命令 | 使用场景 |
|------|------|---------|---------|
| `[PROMPT]` | 初始提示词，位置参数 | `codex`, `codex exec` | 启动时直接给出任务描述 |

### 模型与配置

| 选项 | 说明 | 适用命令 | 使用场景 |
|------|------|---------|---------|
| `-m, --model <MODEL>` | 指定模型 | 全部 | `-m o3` 深度推理，`-m gpt-5` 平衡 |
| `-c, --config <key=value>` | 覆盖 config.toml 中的配置项 | 全部 | `-c model="o3"` 临时切换配置。支持嵌套路径如 `-c sandbox_permissions='["disk-full-read-access"]'`。值解析为 TOML，失败则当作原始字符串 |
| `-p, --profile <NAME>` | 使用 config.toml 中预定义的配置 profile | 全部 | 预设多套配置（工作/个人），快速切换 |
| `--oss` | 使用本地开源模型（Ollama / LM Studio） | 全部 | 离线或隐私敏感场景，需本地运行 Ollama 或 LM Studio |
| `--local-provider <PROVIDER>` | 指定本地模型提供商（`lmstudio` 或 `ollama`） | 全部 | 配合 `--oss` 精确选择后端 |
| `-i, --image <FILE>` | 附加图片到初始 prompt | 全部 | 多模态任务：分析截图、UI 设计稿等 |

### 沙箱与权限

| 选项 | 说明 | 适用命令 | 使用场景 |
|------|------|---------|---------|
| `-s, --sandbox <MODE>` | 沙箱策略 | 全部 | `read-only` 只能读文件（审查/分析任务）；`workspace-write` 可写工作区（代码修改）；`danger-full-access` 完全访问（仅限信任环境） |
| `-a, --ask-for-approval <POLICY>` | 审批策略 | 全部 | `untrusted` 只自动执行可信命令（ls、cat、sed 等）；`on-request` 模型自行判断是否需确认（推荐交互模式）；`never` 从不询问（推荐非交互模式） |
| `--full-auto` | 低摩擦自动执行别名 | 全部 | 等同于 `-a on-request --sandbox workspace-write`，适合半自动化工作流 |
| `--dangerously-bypass-approvals-and-sandbox` | 跳过所有确认和沙箱 | 全部 | **极其危险**，仅限外部已有沙箱的隔离环境 |

### 目录与上下文

| 选项 | 说明 | 适用命令 | 使用场景 |
|------|------|---------|---------|
| `-C, --cd <DIR>` | 指定工作根目录 | 全部 | 不在目标项目目录时指定工作路径 |
| `--add-dir <DIR>` | 添加额外可写目录 | 全部 | 需要访问工作区外的代码或文档，可重复使用 |
| `--search` | 启用实时网络搜索 | 全部 | 需要查阅最新文档或 API 变更时 |

### 特性开关

| 选项 | 说明 | 适用命令 | 使用场景 |
|------|------|---------|---------|
| `--enable <FEATURE>` | 启用某个特性 | 全部 | 临时开启实验性功能，可重复 |
| `--disable <FEATURE>` | 禁用某个特性 | 全部 | 临时关闭某个功能 |

### 输出格式（exec 专属）

| 选项 | 说明 | 使用场景 |
|------|------|---------|
| `--json` | 事件以 JSONL 格式输出到 stdout | 脚本解析，构建自定义前端 |
| `-o, --output-last-message <FILE>` | 最后一条消息写入指定文件 | 提取最终结果用于下游处理 |
| `--output-schema <FILE>` | 指定 JSON Schema 文件约束输出结构 | 需要结构化数据提取 |
| `--color <COLOR>` | 颜色设置：`always`/`never`/`auto` | CI 日志中禁用颜色：`--color never` |
| `--ephemeral` | 不持久化会话到磁盘 | 临时一次性任务 |

### TUI 选项

| 选项 | 说明 | 使用场景 |
|------|------|---------|
| `--no-alt-screen` | 禁用交替屏幕模式，内联运行 | 终端复用器（如 Zellij）中保留滚动历史 |
| `--remote <ADDR>` | 连接到远程 app server websocket | 远程开发场景：`ws://host:port` 或 `wss://host:port` |
| `--remote-auth-token-env <ENV_VAR>` | 远程连接时从环境变量读取 bearer token | 配合 `--remote` 认证 |

---

## CLI 子命令

### `codex exec` - 非交互执行

```
Usage: codex exec [OPTIONS] [PROMPT]
Aliases: e
```

直接执行任务并退出，适合脚本、CI/CD、管道场景。

```bash
# 基本用法
codex exec "生成一个用户注册的单元测试"

# 管道输入
git diff HEAD~1 | codex exec "审查这些改动"

# 输出 JSON 格式
codex exec --json "列出所有 API 端点" > result.jsonl

# 约束输出结构
codex exec --output-schema schema.json "提取用户信息"

# 临时会话（不保存）
codex exec --ephemeral "快速修复这个 typo"
```

**子命令：**

| 子命令 | 说明 |
|--------|------|
| `codex exec resume` | 恢复之前的非交互会话 |
| `codex exec review` | 对当前仓库运行 code review |

### `codex review` - 代码审查

```
Usage: codex review [OPTIONS] [PROMPT]
```

非交互式代码审查，审查当前分支的改动。

```bash
# 审查未提交的改动（staged + unstaged + untracked）
codex review --uncommitted

# 审查与 main 分支的差异
codex review --base main

# 审查指定 commit
codex review --commit abc1234

# 带自定义审查说明
codex review "重点关注 SQL 注入和安全问题"
```

| 选项 | 说明 |
|------|------|
| `--uncommitted` | 审查所有未提交改动（staged + unstaged + untracked） |
| `--base <BRANCH>` | 审查与指定分支的差异 |
| `--commit <SHA>` | 审查某个 commit 引入的改动 |

### `codex resume` - 恢复会话

```
Usage: codex resume [OPTIONS] [SESSION_ID] [PROMPT]
```

恢复之前的交互式会话。不传参显示会话选择器。

```bash
# 交互式选择
codex resume

# 直接恢复最近会话
codex resume --last

# 恢复指定会话
codex resume abc123-def456

# 显示所有会话
codex resume --all

# 包含非交互会话
codex resume --include-non-interactive
```

| 选项 | 说明 |
|------|------|
| `--last` | 直接恢复最近会话（跳过选择器） |
| `--all` | 显示所有会话（不限当前目录） |
| `--include-non-interactive` | 选择器中包含 `exec` 等非交互会话 |

### `codex fork` - 分叉会话

```
Usage: codex fork [OPTIONS] [SESSION_ID] [PROMPT]
```

基于历史会话创建新分支，保留原会话不变。

```bash
# 交互式选择要分叉的会话
codex fork

# 分叉最近的会话
codex fork --last

# 分叉指定会话并给出新任务
codex fork abc123 "换一种实现方式"
```

使用场景：在历史对话基础上尝试不同方案，又不想污染原会话。

### `codex apply` - 应用 diff

```
Usage: codex apply <TASK_ID>
Aliases: a
```

将 Codex agent 生成的最新 diff 通过 `git apply` 应用到本地工作树。

```bash
# 应用指定 task 的 diff
codex apply task-abc123
```

### `codex cloud` - Codex Cloud（实验性）

云端任务管理，让任务在远程运行，然后将改动拉回本地。

```bash
# 浏览云端任务
codex cloud

# 提交新任务
codex cloud exec --env my-env "修复登录页的 bug"

# 列出任务
codex cloud list --env my-env --limit 10

# 查看任务状态
codex cloud status task-123

# 查看任务 diff
codex cloud diff task-123

# 应用任务改动到本地
codex cloud apply task-123
```

| 子命令 | 说明 |
|--------|------|
| `codex cloud exec` | 提交云端任务（需 `--env` 指定环境） |
| `codex cloud status <TASK_ID>` | 查看任务状态 |
| `codex cloud list` | 列出云端任务，支持 `--env`/`--limit`/`--cursor` 分页 |
| `codex cloud apply <TASK_ID>` | 将云端任务 diff 应用到本地 |
| `codex cloud diff <TASK_ID>` | 查看云端任务的 unified diff |

### `codex login` / `codex logout` - 认证

```bash
# 登录
codex login

# 使用 API Key 登录（从环境变量读）
printenv OPENAI_API_KEY | codex login --with-api-key

# 查看状态
codex login status

# 退出
codex logout
```

### `codex mcp` - MCP 服务器管理

管理 Codex 的外部 MCP 服务器连接。

```bash
# HTTP 服务器
codex mcp add --url https://mcp.example.com my-server

# stdio 服务器
codex mcp add my-server -- npx my-mcp-server

# stdio 带环境变量
codex mcp add --env KEY=value my-server -- my-command

# 查看服务器详情
codex mcp get my-server
codex mcp get --json my-server

# 列出所有
codex mcp list
codex mcp list --json

# 移除
codex mcp remove my-server
```

### `codex mcp-server` - 作为 MCP 服务器

```
Usage: codex mcp-server [OPTIONS]
```

将 Codex 自身作为 MCP 服务器启动（stdio 传输），让其他 MCP 客户端可以调用 Codex 的能力。

### `codex sandbox` - 沙箱命令执行

```
Usage: codex sandbox <SUBCOMMAND> [COMMAND...]
```

在不同平台的沙箱中隔离执行命令。

```bash
# macOS Seatbelt 沙箱
codex sandbox macos -- ./my-script.sh
codex sandbox macos --full-auto -- npm test
codex sandbox macos --log-denials -- ./untrusted-binary

# Linux bubblewrap 沙箱
codex sandbox linux -- npm install
codex sandbox linux --full-auto -- make build

# Windows 受限令牌
codex sandbox windows -- .\my-script.ps1
```

| 子命令 | 平台 | 说明 |
|--------|------|------|
| `macos` / `seatbelt` | macOS | 基于 Seatbelt 的沙箱，可选 `--log-denials` 记录拒绝事件 |
| `linux` / `landlock` | Linux | 基于 bubblewrap 的沙箱 |
| `windows` | Windows | 基于受限令牌的沙箱 |

### `codex app` - 桌面应用

```
Usage: codex app [PATH]
```

启动 Codex 桌面应用（macOS）。首次运行自动下载安装器。

```bash
codex app           # 在当前目录打开
codex app ~/project # 指定工作区
```

### `codex app-server` - 应用服务器（实验性）

```
Usage: codex app-server [OPTIONS] [COMMAND]
```

以独立服务器模式运行，供外部 GUI 客户端连接。

```bash
# 默认 stdio 传输
codex app-server

# WebSocket 传输
codex app-server --listen ws://0.0.0.0:9000

# WebSocket + 认证
codex app-server --listen ws://0.0.0.0:9000 --ws-auth capability-token
```

### `codex exec-server` - 执行服务器（实验性）

独立的 exec-server 服务，以 WebSocket 方式提供服务。

```bash
codex exec-server --listen ws://127.0.0.1:9999
```

### `codex features` - 特性开关管理

```bash
# 列出所有特性及其状态
codex features list

# 启用特性
codex features enable experimental-feature

# 禁用特性
codex features disable experimental-feature
```

### `codex completion` - Shell 补全

```bash
codex completion bash
codex completion zsh
codex completion fish
codex completion powershell
codex completion elvish
```

### `codex debug` - 调试工具

```bash
# 查看发送给模型的完整 prompt（含系统指令、工具定义、消息历史）
codex debug prompt-input "用户提示词"

# 调试 app-server
codex debug app-server send-message-v2
```

### `codex marketplace` - 插件市场管理

```bash
codex marketplace add <url>
```

### `codex doctor` - 健康检查

（此子命令属于 claude-code，codex 无此命令）

---

## 配置文件

Codex CLI 的配置文件位于 `~/.codex/config.toml`。所有选项都可以通过 `-c` 临时覆盖。

```toml
# ~/.codex/config.toml 示例
model = "gpt-5"
sandbox = "workspace-write"

[profile.work]
model = "gpt-5"

[profile.oss]
model_provider = "oss"
```

```bash
# 使用预设 profile
codex -p work "实现这个功能"

# 临时覆盖配置值
codex -c model="o3" -c sandbox="read-only" "审查这段代码"
```

---

## 审批策略详解

| 策略 | 行为 | 适用场景 |
|------|------|---------|
| `untrusted` | 只自动执行可信命令（ls、cat、sed等白名单），其他需确认 | 安全优先的交互场景 |
| `on-request` | 模型自行判断是否需确认，可自主执行大部分操作 | 推荐的交互模式 |
| `never` | 永不询问，失败直接返回给模型 | 非交互/CI 场景 |
| `on-failure` | **已弃用**。失败时才询问 | 不建议使用 |

## 沙箱模式详解

| 模式 | 可读 | 可写 | 网络 | 适用场景 |
|------|------|------|------|---------|
| `read-only` | 全部文件 | 无 | 否 | 代码审查、代码分析、文档 |
| `workspace-write` | 全部文件 | 工作区 + /tmp | 否 | 代码修改、重构、测试 |
| `danger-full-access` | 全部 | 全部 | 是 | 需网络访问的任务（仅限信任环境） |

## 与 Claude Code 的对比

| 特性 | Codex CLI | Claude Code |
|------|-----------|-------------|
| 底层模型 | GPT-5 / o3 / o4 | Claude Opus / Sonnet / Haiku |
| 沙箱机制 | 三层沙箱（read-only / workspace-write / danger-full-access） | 权限型确认（Allow / Ask / Deny） |
| 审批策略 | 4 级策略（含白名单机制） | 按工具类别配置 |
| 非交互输出 | `--json` + `--output-schema` | `--output-format json` |
| 会话管理 | resume / fork 子命令 | `--resume` / `--continue` / `--fork-session` |
| 云端执行 | Cloud 实验性功能 | 无 |
| 本地模型 | `--oss` 直连 Ollama / LM Studio | 需通过 API 代理 |
| 桌面应用 | `codex app` | 无 |
| IDE 集成 | 通过 app-server 连接 | 原生 VSCode / JetBrains 插件 |
| 配置文件 | `~/.codex/config.toml` | `settings.json` + `CLAUDE.md` |
