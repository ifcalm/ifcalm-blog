---
title: "Claude Code：终端里的 AI 编程搭档"
date: 2026-04-18
tags: ["AI", "工具"]
draft: false
summary: "Claude Code 终端 AI 编程助手全部命令详解"
showToc: true
tocOpen: true
ShowShareButtons: false
---

## 简介

Claude Code 是 Anthropic 推出的终端内 AI 编程助手，直接在你的终端中运行，理解整个代码库上下文，帮助你编写代码、调试问题、管理 git 等工作流。

## 安装

```bash
# macOS / Linux
npm install -g @anthropic-ai/claude-code

# 或通过 Homebrew
brew install claude-code
```

安装后执行 `claude` 进入交互式会话。

## CLI 选项（Flags）

### 会话模式

| 选项 | 说明 | 使用场景 |
|------|------|---------|
| `-p, --print` | 非交互模式，输出结果后退出 | 脚本/管道中使用，如 `claude -p "解释这段代码"`。注意：此模式下跳过工作区信任弹窗 |
| `-c, --continue` | 继续当前目录下最近一次会话 | 终端关了想接着上次继续聊 |
| `-r, --resume [session-id]` | 恢复指定会话，不传参数则打开交互选择器 | 回到之前的某个会话；支持模糊搜索 |
| `--from-pr [pr-number]` | 恢复与某个 PR 关联的会话 | 继续评审之前那个 PR |
| `--fork-session` | 恢复会话时创建新 session ID，不覆盖原会话 | 想基于历史对话开个新分支，保留原会话不变 |
| `-n, --name <name>` | 为会话设置显示名称 | 多个并行任务时方便区分，名称会显示在提示框和 `/resume` 选择器中 |
| `--session-id <uuid>` | 指定固定 session ID | 需要可预测的 session ID 时使用（如脚本自动化） |
| `--no-session-persistence` | 不保存会话到磁盘 | 仅 `-p` 模式可用。临时问答不想留历史记录 |

### 模型与推理

| 选项 | 说明 | 使用场景 |
|------|------|---------|
| `--model <model>` | 指定模型，可用别名（`sonnet`/`opus`/`haiku`）或全名 | `claude --model opus` 用于复杂推理；`claude --model haiku` 用于简单快速任务 |
| `--effort <level>` | 推理努力程度：`low / medium / high / xhigh / max` | 复杂问题用 `max`，简单问题用 `low` 省 token |
| `--fallback-model <model>` | 默认模型过载时自动降级到备选模型 | 仅 `-p` 模式可用。高峰期 opus 过载自动用 sonnet |

### 输入输出

| 选项 | 说明 | 使用场景 |
|------|------|---------|
| `--input-format <format>` | 输入格式：`text`（默认）或 `stream-json` | `stream-json` 用于实时流式输入，仅 `-p` 模式 |
| `--output-format <format>` | 输出格式：`text`（默认）/ `json` / `stream-json` | `json` 适合脚本解析；`stream-json` 实时流式输出，仅 `-p` 模式 |
| `--include-partial-messages` | 输出中包含部分消息块 | 配合 `--print --output-format=stream-json` 实现打字机效果 |
| `--include-hook-events` | 输出流中包含所有 hook 生命周期事件 | 调试 hook 或构建自定义前端时使用，需配合 `stream-json` |
| `--replay-user-messages` | 将 stdin 的用户消息回显到 stdout | 需要确认输入已被接收的场景，需同时使用 `stream-json` 输入输出 |
| `--json-schema <schema>` | 指定 JSON Schema 约束输出格式 | 需要结构化输出时（如提取数据、生成配置），仅 `-p` 模式 |
| `--verbose` | 覆盖配置中的 verbose 设置 | 想看更多执行细节时 |

### 权限控制

| 选项 | 说明 | 使用场景 |
|------|------|---------|
| `--permission-mode <mode>` | 权限模式：`acceptEdits` / `auto` / `bypassPermissions` / `default` / `dontAsk` / `plan` | `plan` 模式只规划不执行；`acceptEdits` 自动接受编辑但命令需确认；`bypassPermissions` 完全跳过确认 |
| `--allowed-tools <tools...>` | 允许的工具列表，逗号或空格分隔 | `--allowed-tools "Bash(git *) Edit"` 只允许 git 命令和编辑操作 |
| `--disallowed-tools <tools...>` | 禁止的工具列表 | `--disallowed-tools "Bash(rm *)"` 禁止删除命令 |
| `--dangerously-skip-permissions` | 跳过所有权限检查 | 仅限无网络沙箱环境 |
| `--allow-dangerously-skip-permissions` | 允许在会话中使用跳过权限的选项（不默认开启） | 同上，但需要用户主动选择启用 |

### 上下文与工具

| 选项 | 说明 | 使用场景 |
|------|------|---------|
| `--add-dir <dirs...>` | 添加额外目录供工具访问 | 需要访问项目外的代码或文档时 |
| `--tools <tools...>` | 指定可用工具集，`""` 禁用全部，`default` 用全部，或列出工具名 | 只读审查时用 `--tools "Read,Grep,Glob"` |
| `--system-prompt <prompt>` | 替换默认 system prompt | 自定义 Claude 的行为指令 |
| `--append-system-prompt <prompt>` | 在默认 system prompt 后追加内容 | 在默认行为基础上增加额外指令 |
| `--agents <json>` | JSON 定义自定义 agent | `--agents '{"reviewer":{"description":"Reviews code","prompt":"You are a code reviewer"}}'` |
| `--agent <agent>` | 当前会话使用的 agent | 覆盖 settings 中的 agent 设置 |
| `--betas <betas...>` | 启用 beta 功能头 | API key 用户使用，用于体验未正式发布的功能 |

### MCP 配置

| 选项 | 说明 | 使用场景 |
|------|------|---------|
| `--mcp-config <configs...>` | 加载 MCP 服务器配置（JSON 文件或字符串） | 临时加载额外的 MCP 服务器，不修改全局配置 |
| `--strict-mcp-config` | 仅使用 `--mcp-config` 指定的服务器，忽略其他所有 MCP 配置 | 完全隔离的 MCP 环境，用于测试或安全场景 |

### 插件

| 选项 | 说明 | 使用场景 |
|------|------|---------|
| `--plugin-dir <path>` | 从目录或 .zip 加载插件（可重复） | 临时加载本地开发的插件进行测试 |
| `--plugin-url <url>` | 从 URL 获取插件 .zip 加载（可重复） | 临时加载远程插件 |

### 工作树与会话隔离

| 选项 | 说明 | 使用场景 |
|------|------|---------|
| `-w, --worktree [name]` | 创建 git worktree 隔离本次修改 | 实验性改动不想污染当前分支；可选指定 worktree 名称 |
| `--tmux` | 为 worktree 创建 tmux 会话 | 配合 `--worktree` 使用，自动用 iTerm2 原生面板或传统 tmux |

### IDE 与浏览器集成

| 选项 | 说明 | 使用场景 |
|------|------|---------|
| `--ide` | 自动连接可用的 IDE | 让 Claude Code 直接在编辑器中应用修改 |
| `--chrome` | 启用 Chrome 集成 | 让 Claude Code 控制和查看浏览器 |
| `--no-chrome` | 禁用 Chrome 集成 | 覆盖配置中的 Chrome 集成设置 |

### 调试与日志

| 选项 | 说明 | 使用场景 |
|------|------|---------|
| `-d, --debug [filter]` | 开启调试日志，可选过滤分类 | `--debug api,hooks` 只看 API 和 hook 日志 |
| `--debug-file <path>` | 调试日志写入指定文件 | 持久化日志用于事后分析（隐式启用 debug 模式） |
| `--bare` | 极简模式 | 跳过 hook、LSP、插件同步、自动记忆、自动 CLAUDE.md 发现等。需要显式传上下文，适用于最小化启动开销的场景 |

### 其他选项

| 选项 | 说明 | 使用场景 |
|------|------|---------|
| `--disable-slash-commands` | 禁用所有 slash 命令 | 限制 Claude 只能执行自然语言任务 |
| `--exclude-dynamic-system-prompt-sections` | 将 cwd、env、git status 等动态信息从 system prompt 移入首条用户消息 | 改善跨用户 prompt 缓存命中率 |
| `--max-budget-usd <amount>` | API 调用最大费用上限 | 仅 `-p` 模式。防止脚本中意外消耗过多 |
| `--setting-sources <sources>` | 指定加载哪些 settings 来源：`user / project / local` | 调试 settings 问题或隔离配置 |
| `--settings <file-or-json>` | 加载额外的 settings JSON 文件或字符串 | 临时覆盖或补充配置 |
| `--brief` | 启用 SendUserMessage 工具 | agent 可以向用户发送消息进行沟通 |
| `--file <specs...>` | 启动时下载文件资源 | `--file file_abc:doc.txt file_def:img.png` |
| `--remote-control [name]` | 启动可远程控制的交互会话 | 允许外部程序通过 Remote Control 协议控制 Claude Code |
| `--remote-control-session-name-prefix <prefix>` | 自动生成的 Remote Control 会话名前缀 | 默认用 hostname，自定义前缀便于区分 |
| `-h, --help` | 显示帮助 | `claude --help` |
| `-v, --version` | 显示版本号 | `claude --version` |

---

## CLI 子命令

### `claude auth` - 身份认证管理

| 子命令 | 说明 |
|--------|------|
| `claude auth login` | 登录 Anthropic 账号 |
| `claude auth logout` | 退出登录 |
| `claude auth status` | 查看认证状态 |

使用场景：首次使用时需登录；切换账号时先 logout 再 login。

### `claude mcp` - MCP 服务器管理

| 子命令 | 说明 |
|--------|------|
| `claude mcp add <name> <command-or-url> [args...]` | 添加 MCP 服务器 |
| `claude mcp add-json <name> <json>` | 用 JSON 字符串添加 MCP 服务器 |
| `claude mcp add-from-claude-desktop` | 从 Claude Desktop 导入 MCP 配置（仅 Mac/WSL） |
| `claude mcp get <name>` | 查看某个 MCP 服务器详情 |
| `claude mcp list` | 列出所有已配置的 MCP 服务器 |
| `claude mcp remove <name>` | 移除 MCP 服务器 |
| `claude mcp reset-project-choices` | 重置当前项目中所有已批准/拒绝的 .mcp.json 服务器 |
| `claude mcp serve` | 启动 Claude Code MCP 服务器 |

添加 MCP 服务器的常见用法：

```bash
# HTTP 传输
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp

# HTTP 带请求头
claude mcp add --transport http corridor https://app.corridor.dev/api/mcp \
  --header "Authorization: Bearer ..."

# stdio 传输
claude mcp add my-server -- npx my-mcp-server

# stdio 带环境变量
claude mcp add -e API_KEY=xxx my-server -- npx my-mcp-server
```

### `claude plugin` / `claude plugins` - 插件管理

| 子命令 | 说明 |
|--------|------|
| `claude plugin install <plugin>` | 安装插件，可用 `plugin@marketplace` 指定来源 |
| `claude plugin uninstall <plugin>` | 卸载插件 |
| `claude plugin list` | 列出已安装插件 |
| `claude plugin enable <plugin>` | 启用已安装但被禁用的插件 |
| `claude plugin disable [plugin]` | 禁用插件（不传参禁用当前项目插件） |
| `claude plugin update <plugin>` | 更新插件到最新版本（需重启生效） |
| `claude plugin details <name>` | 查看插件的组件清单和 token 消耗预估 |
| `claude plugin validate <path>` | 验证插件或 marketplace manifest 格式 |
| `claude plugin tag [path]` | 为插件发布打 git tag |
| `claude plugin prune` | 清理不再需要的自动安装依赖 |
| `claude plugin marketplace` | 管理 marketplace（添加/移除/列出） |

### `claude agents` - 后台 Agent 管理

| 选项 | 说明 |
|------|------|
| `claude agents` | 列出所有后台 agent |
| `--cwd <path>` | 只显示指定路径下启动的后台会话 |

### `claude project` - 项目管理

| 子命令 | 说明 |
|--------|------|
| `claude project purge [path]` | 删除项目的所有 Claude Code 状态（对话记录、任务、文件历史、配置条目） |

使用场景：项目结束想清理 Claude Code 产生的所有本地数据。

### `claude doctor` - 健康检查

```bash
claude doctor
```

检查自动更新程序是否正常。注意：跳过工作区信任弹窗并会启动 .mcp.json 中的 stdio 服务器进行健康检查。

### `claude install` - 安装原生构建

```bash
claude install           # 安装当前版本
claude install stable    # 安装稳定版
claude install latest    # 安装最新版
claude install --force    # 强制重新安装
```

### `claude update` / `claude upgrade` - 更新

```bash
claude update
claude upgrade
```

检查更新并在有可用更新时安装。

### `claude setup-token` - 长期认证令牌

```bash
claude setup-token
```

设置长期有效的认证令牌（需要 Claude 订阅）。适用于 CI/CD 或无法交互式登录的环境。

### `claude ultrareview` - 云端多 Agent 代码审查

```bash
# 审查当前分支
claude ultrareview

# 审查指定 PR
claude ultrareview 128

# 审查与 main 的差异
claude ultrareview main

# 输出原始 JSON
claude ultrareview --json

# 设置超时（分钟，默认 30）
claude ultrareview --timeout 60
```

云端启动多 agent 并行审查当前分支变更，打印发现的问题。

---

## 交互会话内斜杠命令

以下命令在进入交互式会话后使用，以 `/` 开头。

### 会话管理

| 命令 | 说明 | 使用场景 |
|------|------|---------|
| `/clear` | 清空当前对话历史 | 话题切换，清除上下文避免干扰 |
| `/compact` | 压缩对话上下文 | 对话很长接近 token 上限时，压缩历史保留关键信息 |
| `/resume` | 恢复历史会话（交互选择器） | 回到之前的某个对话 |
| `/fork-session` | 从当前位置分叉为新会话 | 想基于当前对话创建独立分支继续探索 |
| `/name <name>` | 设置当前会话名称 | 给会话命名便于后续 `/resume` 识别 |
| `/rename` | 重命名当前会话 | 同上 |

### 模型与推理

| 命令 | 说明 | 使用场景 |
|------|------|---------|
| `/model` | 切换模型 | 复杂问题时切 opus，简单操作切 haiku |
| `/effort` | 设置推理努力程度 | 调高用于深入分析，调低用于快速回复 |
| `/fast` | 切换 fast 模式 | fast 模式使用 Opus 但输出更快 |
| `/thinking` | 切换思考模式开关 | 需要看推理过程时开启 |

### 配置与权限

| 命令 | 说明 | 使用场景 |
|------|------|---------|
| `/config` | 打开配置面板 | 修改主题、模型、权限等设置 |
| `/permissions` | 管理工具权限 | 允许/禁止特定工具或命令 |
| `/allowed-tools` | 管理允许的工具列表 | 限制 Claude 只能使用特定工具 |
| `/disallowed-tools` | 管理禁止的工具列表 | 禁止某些危险操作 |
| `/update-config` | 更新 settings.json 配置 | 配置 hook、权限、环境变量等 |
| `/settings` | 管理 settings 文件 | 查看和编辑用户/项目/本地配置 |

### 项目与代码

| 命令 | 说明 | 使用场景 |
|------|------|---------|
| `/init` | 分析项目并生成 CLAUDE.md | 新项目让 Claude 快速了解代码库 |
| `/review` | 审查当前分支变更 | PR 前的自我 code review |
| `/security-review` | 安全审查当前分支 | 上线前检查安全漏洞 |
| `/simplify` | 审查代码质量并优化 | 重构后检查冗余和可改进之处 |
| `/pr-comments` | 查看 PR 评论 | 查看当前分支对应 PR 的 review 意见 |
| `/ultrareview` | 云端多 agent 审查 | 深度代码审查，多 agent 并行 |

### 工作区

| 命令 | 说明 | 使用场景 |
|------|------|---------|
| `/add-dir` | 添加目录到工作区 | 需要 Claude 访问项目外的代码/文档 |
| `/workspace` | 管理工作区设置 | 配置工作区相关选项 |
| `/terminal-setup` | 设置终端集成 | 配置终端相关的快捷键和行为 |

### 自动化与会话循环

| 命令 | 说明 | 使用场景 |
|------|------|---------|
| `/loop` | 按间隔重复运行任务 | "每 5 分钟检查部署状态" |
| `/auto-mode` | 管理自动模式分类器 | 配置哪些操作自动执行无需确认 |
| `/agents` | 管理后台 agent | 查看和控制后台运行的 agent 任务 |
| `/bashes` | 列出后台 bash 任务 | 查看后台运行的 shell 命令 |

### IDE 与浏览器

| 命令 | 说明 | 使用场景 |
|------|------|---------|
| `/ide` | IDE 集成管理 | 连接/断开 VS Code 或 JetBrains |
| `/install-github-app` | 安装 GitHub App | 集成 GitHub 仓库访问 |

### MCP 与插件

| 命令 | 说明 | 使用场景 |
|------|------|---------|
| `/mcp` | 管理 MCP 服务器 | 添加/移除/查看 MCP 连接 |
| `/plugin` | 管理插件 | 安装/卸载/启用/禁用插件 |

### 认证

| 命令 | 说明 | 使用场景 |
|------|------|---------|
| `/login` | 登录 Anthropic 账号 | 认证过期或首次使用 |
| `/logout` | 退出登录 | 切换账号 |

### 信息与调试

| 命令 | 说明 | 使用场景 |
|------|------|---------|
| `/context` | 查看上下文使用情况 | 了解当前上下文窗口消耗 |
| `/cost` | 查看 token 消耗和费用 | 了解本次会话花了多少钱 |
| `/doctor` | 诊断系统状态 | 排查 Claude Code 异常 |
| `/status` | 查看会话状态 | 查看当前会话的模型、权限等配置 |
| `/stats` | 查看使用统计 | 查看历史使用数据 |
| `/release-notes` | 显示版本更新日志 | 了解新版本功能 |
| `/help` | 显示帮助信息 | 忘了命令时随时查看 |
| `/cli` | CLI 帮助 | 查看可用的命令行选项 |
| `/changelog` | 查看变更日志 | 了解最近的改动 |

### 用户界面

| 命令 | 说明 | 使用场景 |
|------|------|---------|
| `/theme` | 切换主题 | 亮色/暗色模式切换 |
| `/statusline` | 配置状态行 | 自定义终端底部状态栏显示内容 |
| `/keybindings` | 管理快捷键 | 自定义键盘绑定 |
| `/output-style` | 更改输出样式 | 调整 Claude 回复的排版风格 |
| `/shift-enter` | 换行键行为配置 | 设置 Shift+Enter 的行为 |
| `/terminal-wrapper` | 终端包装器设置 | 配置终端集成方式 |
| `/sandbox` | 沙箱设置 | 管理系统沙箱相关配置 |
| `/locale` | 语言区域设置 | 设置界面语言 |

### 输出格式

| 命令 | 说明 | 使用场景 |
|------|------|---------|
| `/output-format` | 切换输出格式（text/json/stream-json） | 需要结构化输出时 |
| `/stream-json` | 切换流式 JSON 输出 | 构建实时消费 Claude 输出的前端 |
| `/json-schema` | 设置 JSON Schema 约束 | 指定输出必须符合的数据结构 |
| `/structured` | 管理结构化输出设置 | 自定义结构化输出行为 |

### 其他

| 命令 | 说明 | 使用场景 |
|------|------|---------|
| `/export` | 导出对话记录 | 保存会话内容为文件 |
| `/remember` | 记住某条信息 | 让 Claude 持久化保存重要信息到记忆中 |
| `/hooks` | 管理 hook | 配置事件触发的自动化行为 |
| `/tag` | 打 Git tag | 发布版本时打标签 |
| `/screenshot` | 截取终端内容 | 分享或记录当前终端状态 |
| `/pricing` | 查看定价信息 | 了解不同模型的费用 |
| `/pipeline` | 管道模式 | 配置管道输入输出行为 |
| `/todos` | 查看任务列表 | 查看 Claude Code 追踪的任务进度 |
| `/vim` | 切换 Vim 模式 | 输入框支持 Vim 快捷键 |
| `/posthog` | PostHog 分析设置 | 控制匿名使用数据收集 |
| `/token` | 查看 token 使用详情 | 深入分析 token 消耗分布 |
| `/upgrade` | 检查并安装更新 | 升级到最新版本 |

---

## 权限控制

Claude Code 的权限分为三个层级：

- **Allow**: 自动执行，无需确认。适合安全的只读操作（如 `git status`）
- **Ask**: 每次执行前弹窗询问。大部分写操作的默认级别
- **Deny**: 完全禁止。用于阻止危险操作（如 `rm -rf`）

权限可以在全局、项目、或会话级别配置，支持按工具过滤（如 `Bash(curl *)` 只允许 curl 命令）。

---

## 与 GitHub Copilot 的区别

| 特性 | Claude Code | GitHub Copilot |
|------|------------|----------------|
| 交互方式 | 终端 Agent | IDE 补全 + Chat |
| 代码库理解 | 全仓库搜索 | 当前文件 + 打开 tab |
| 执行能力 | 可执行终端命令、git 操作 | 仅代码建议 |
| 工作区操作 | 创建 worktree、运行测试 | 仅编辑器内 |
| 自定义 | CLAUDE.md + settings.json | .github/copilot-instructions.md |
