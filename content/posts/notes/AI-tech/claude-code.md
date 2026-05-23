---
title: "Claude Code：终端里的 AI 编程搭档"
date: 2026-04-18
tags: ["Claude Code", "AI", "Skills", "开发工具"]
draft: false
summary: "Claude Code CLI 的完整使用指南，覆盖安装配置、Skills 工作流、API 接入、Hooks 自动化、IDE 集成与常见问题排查。"
showToc: true
tocOpen: false
---

## 一、Claude Code CLI 是什么？

Claude Code 是 Anthropic 提供的终端 AI 编程助手。它可以理解代码仓库、读取文件、修改代码、运行命令，并协助完成开发任务。

核心命令是：

```bash
claude
```

常见使用场景：

- 阅读和解释项目代码
- 查找功能实现位置
- 修复 bug
- 编写单元测试
- 重构代码
- 分析日志和构建错误
- 生成文档
- 辅助 Git diff 审查
- 生成 commit message
- 通过 Skills 沉淀可复用流程
- 通过兼容 API 或网关接入外部模型

---

## 二、安装 Claude Code CLI

### 1. 官方安装方式

macOS / Linux / WSL 可以使用：

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

安装完成后检查：

```bash
claude --version
```

---

### 2. 使用 Homebrew 安装

稳定版：

```bash
brew install --cask claude-code
```

最新通道：

```bash
brew install --cask claude-code@latest
```

升级稳定版：

```bash
brew update
brew upgrade claude-code
```

升级最新通道：

```bash
brew update
brew upgrade claude-code@latest
```

日常开发建议优先使用稳定版：

```bash
brew install --cask claude-code
```

---

### 3. 使用 npm 安装

```bash
npm install -g @anthropic-ai/claude-code
```

升级：

```bash
npm install -g @anthropic-ai/claude-code@latest
```

不建议使用：

```bash
sudo npm install -g @anthropic-ai/claude-code
```

避免引入全局权限和文件归属问题。

---

## 三、首次启动与登录

进入项目目录：

```bash
cd /path/to/your/project
```

启动 Claude Code：

```bash
claude
```

首次启动会引导登录或授权。

如果浏览器没有自动打开，可以根据终端提示复制登录链接到浏览器完成登录。

查看认证状态：

```bash
claude auth status
```

登录：

```bash
claude auth login
```

退出登录：

```bash
claude auth logout
```

---

## 四、Claude Code CLI 命令速查

### 1. 基础启动命令

| 场景 | 命令 | 说明 |
|---|---|---|
| 启动交互模式 | `claude` | 进入 Claude Code 会话 |
| 带初始问题启动 | `claude "explain this project"` | 启动后先执行一个问题 |
| 单次执行并退出 | `claude -p "explain this function"` | 适合脚本和一次性查询 |
| 处理管道输入 | `cat error.log \| claude -p "分析错误原因"` | 适合分析日志、diff、文本 |
| 查看版本 | `claude --version` | 输出版本号 |
| 查看帮助 | `claude --help` | 查看常见帮助 |

示例：

```bash
claude "请解释这个项目的目录结构"
```

```bash
cat build.log | claude -p "请分析构建失败的根因"
```

---

### 2. 会话管理命令

| 场景 | 命令 | 说明 |
|---|---|---|
| 继续最近会话 | `claude -c` | 继续当前目录最近一次会话 |
| 继续最近会话并提问 | `claude -c -p "继续检查剩余问题"` | 非交互方式继续最近会话 |
| 恢复指定会话 | `claude -r "<session>"` | 通过会话 ID 或名称恢复 |
| 恢复并执行问题 | `claude -r "auth-refactor" "继续完成 PR"` | 恢复指定会话并继续任务 |
| 给会话命名 | `claude -n "my-feature-work"` | 便于后续查找和恢复 |
| 指定 session id | `claude --session-id "<uuid>"` | 用固定 session id 启动 |

示例：

```bash
claude -n "login-refactor"
```

```bash
claude -r "login-refactor"
```

---

### 3. 模型与推理强度

| 场景 | 命令 | 说明 |
|---|---|---|
| 指定模型启动 | `claude --model sonnet` | 当前会话使用指定模型 |
| 指定完整模型名 | `claude --model claude-sonnet-4-6` | 使用完整模型名称 |
| 指定推理强度 | `claude --effort high` | 当前会话提高推理强度 |
| 交互内切换模型 | `/model` | 打开模型选择器 |
| 交互内调整推理强度 | `/effort` | 调整当前会话推理强度 |

示例：

```bash
claude --model sonnet --effort high
```

说明：`--model` 和 `ANTHROPIC_MODEL` 只影响当前启动的会话；如果要长期保存默认模型，应使用用户设置或 `/model` 选择器中的保存能力。

---

### 4. 目录、上下文与配置

| 场景 | 命令 | 说明 |
|---|---|---|
| 添加额外目录 | `claude --add-dir ../shared ../docs` | 让 Claude 访问多个目录 |
| 指定设置文件 | `claude --settings ./settings.json` | 当前启动使用指定配置 |
| 指定设置来源 | `claude --setting-sources user,project` | 限制加载哪些设置来源 |
| 加载 MCP 配置 | `claude --mcp-config ./mcp.json` | 加载 MCP server 配置 |
| 严格使用指定 MCP | `claude --strict-mcp-config --mcp-config ./mcp.json` | 忽略其他 MCP 配置 |
| 最小模式 | `claude --bare -p "query"` | 跳过自动加载 hooks、skills、plugins、MCP、CLAUDE.md |

示例：

```bash
claude --add-dir ../frontend ../backend
```

```bash
claude --bare -p "请总结这个文件的作用"
```

---

### 5. 权限与工具控制

| 场景 | 命令 | 说明 |
|---|---|---|
| 指定权限模式 | `claude --permission-mode plan` | 以计划模式启动 |
| 自动接受编辑 | `claude --permission-mode acceptEdits` | 编辑类操作更少确认 |
| 自动模式 | `claude --permission-mode auto` | 让 Claude 自动判断权限 |
| 跳过权限确认 | `claude --dangerously-skip-permissions` | 高风险，不建议日常使用 |
| 允许特定工具 | `claude --allowedTools "Bash(git diff *)" "Read"` | 对指定工具免确认 |
| 禁止特定工具 | `claude --disallowedTools "Bash(rm *)" "Edit"` | 拒绝危险操作 |
| 限制可用工具 | `claude --tools "Bash,Edit,Read"` | 只给指定工具 |
| 禁用所有工具 | `claude --tools ""` | 只让 Claude 输出建议 |

示例：

```bash
claude --permission-mode plan
```

```bash
claude --allowedTools "Bash(git status *)" "Bash(git diff *)" "Read"
```

谨慎使用：

```bash
claude --dangerously-skip-permissions
```

这个参数会跳过很多权限确认，不建议在公司项目、生产环境、包含密钥的仓库中使用。

---

### 6. 非交互模式与脚本集成

| 场景 | 命令 | 说明 |
|---|---|---|
| 单次查询 | `claude -p "query"` | 输出结果后退出 |
| JSON 输出 | `claude -p "query" --output-format json` | 适合脚本解析 |
| 流式 JSON 输出 | `claude -p "query" --output-format stream-json` | 适合长任务 |
| 限制轮次 | `claude -p --max-turns 3 "query"` | 防止代理循环过久 |
| 限制预算 | `claude -p --max-budget-usd 5 "query"` | 控制成本 |
| 禁用会话保存 | `claude -p --no-session-persistence "query"` | 不保存本次会话 |
| 指定输出 JSON Schema | `claude -p --json-schema '<schema>' "query"` | 获取结构化输出 |

示例：

```bash
git diff | claude -p "请总结本次代码变更，并指出风险点"
```

```bash
claude -p "请输出项目模块清单" --output-format json
```

```bash
go test ./... 2>&1 | claude -p "请分析测试失败原因" --max-turns 3
```

---

### 7. 系统提示与临时规则

| 场景 | 命令 | 说明 |
|---|---|---|
| 追加系统提示 | `claude --append-system-prompt "Always use Chinese"` | 保留默认 Claude Code 行为并追加规则 |
| 从文件追加提示 | `claude --append-system-prompt-file ./rules.txt` | 适合临时规则 |
| 替换系统提示 | `claude --system-prompt "You are a Python expert"` | 完全替换默认提示 |
| 从文件替换提示 | `claude --system-prompt-file ./prompt.txt` | 自定义 Agent 场景 |

日常更推荐使用追加：

```bash
claude --append-system-prompt "请用中文解释，但代码注释保持英文。"
```

替换系统提示会移除 Claude Code 默认行为，使用时要更谨慎。

---

### 8. 后台任务与远程控制

| 场景 | 命令 | 说明 |
|---|---|---|
| 后台运行 | `claude --bg "investigate flaky test"` | 作为后台 agent 运行 |
| 查看后台 agent | `claude agents` | 打开 agent 管理视图 |
| JSON 查看后台 agent | `claude agents --json` | 脚本化查看 |
| 查看后台日志 | `claude logs <id>` | 打印后台任务输出 |
| 连接后台任务 | `claude attach <id>` | 接入某个后台任务 |
| 停止后台任务 | `claude stop <id>` | 停止后台任务 |
| 删除后台任务记录 | `claude rm <id>` | 从列表移除 |
| 重启后台任务 | `claude respawn <id>` | 重启任务 |
| 远程控制 | `claude --remote-control "My Project"` | 可从 Claude.ai 或 App 控制 |
| 创建 Web 任务 | `claude --remote "Fix login bug"` | 创建 Web 会话 |

示例：

```bash
claude --bg "请检查这个项目中可能缺失的单元测试"
```

```bash
claude agents --json
```

---

### 9. 更新、安装与本地状态管理

| 场景 | 命令 | 说明 |
|---|---|---|
| 更新 Claude Code | `claude update` | 更新到最新版本 |
| 安装稳定版 | `claude install stable` | 安装或重装 stable |
| 安装指定版本 | `claude install 2.1.118` | 安装指定版本 |
| 健康检查 | `claude doctor` | 检查安装和配置 |
| 查看日志 | `claude logs <id>` | 查看后台 agent 日志 |
| 清理项目状态预览 | `claude project purge ~/work/repo --dry-run` | 预览将删除哪些本地状态 |
| 清理项目状态 | `claude project purge ~/work/repo` | 删除本地会话、日志等项目状态 |

说明：如果是通过 Homebrew 安装，也可以继续使用：

```bash
brew update
brew upgrade claude-code
```

---

### 10. MCP 与插件命令

| 场景 | 命令 | 说明 |
|---|---|---|
| 管理 MCP | `claude mcp` | 配置 MCP servers |
| 加载 MCP 配置 | `claude --mcp-config ./mcp.json` | 启动时加载 |
| 管理插件 | `claude plugin` | 管理 Claude Code 插件 |
| 插件命令别名 | `claude plugins` | 同上 |
| 临时加载插件目录 | `claude --plugin-dir ./my-plugin` | 当前会话加载本地插件 |
| 临时加载插件 URL | `claude --plugin-url https://example.com/plugin.zip` | 当前会话加载远程插件 |

示例：

```bash
claude --mcp-config ./mcp.json
```

```bash
claude --plugin-dir ./my-plugin
```

---

## 五、交互内 Slash Commands 速查

进入 `claude` 交互模式后，可以输入 `/` 查看当前可用命令。

| 命令 | 用途 |
|---|---|
| `/help` | 查看帮助 |
| `/init` | 初始化或改进 `CLAUDE.md` |
| `/memory` | 查看和管理项目记忆 |
| `/config` | 打开配置界面 |
| `/status` | 查看当前状态和设置来源 |
| `/doctor` | 检查安装、配置、MCP、上下文等问题 |
| `/permissions` | 管理工具权限 |
| `/model` | 查看或切换模型 |
| `/effort` | 调整推理强度 |
| `/plan` | 进入计划模式 |
| `/context` | 查看上下文使用情况 |
| `/compact` | 压缩上下文 |
| `/clear` | 清空当前会话上下文 |
| `/diff` | 查看本次修改差异 |
| `/code-review` | 对当前变更做代码审查 |
| `/resume` | 恢复历史会话 |
| `/rename` | 给当前会话命名 |
| `/agents` | 管理 subagents 或并行任务 |
| `/tasks` | 查看当前后台任务 |
| `/background` | 将当前会话转为后台运行 |
| `/mcp` | 管理 MCP 相关能力 |
| `/plugin` | 管理插件 |
| `/skills` | 查看或调用 Skills |
| `/add-dir` | 在会话中添加额外目录 |
| `/exit` | 退出当前会话 |

常用组合：

```text
/init
```

```text
请先阅读项目结构，不要修改代码，先给我一个修改计划。
```

```text
/diff
/code-review
```

```text
/context
/compact
```

---

## 六、推荐项目工作流

### 1. 新项目第一次使用

```bash
cd /path/to/project
claude
```

进入后执行：

```text
/init
```

然后让 Claude 阅读项目：

```text
请阅读项目结构，整理项目技术栈、启动命令、测试命令和核心模块说明。
```

---

### 2. 开始具体任务

建议先让 Claude 分析，不要直接改代码：

```text
请先分析这个需求，不要修改代码。请给出修改计划、影响范围和需要验证的测试点。
```

确认后再执行：

```text
按这个计划修改代码，保持改动范围尽量小。
```

---

### 3. 修改完成后

查看改动：

```text
/diff
```

代码审查：

```text
/code-review
```

运行测试：

```text
请运行相关测试，并解释测试结果。
```

生成提交说明：

```text
请根据当前 git diff 生成一条清晰的 commit message。
```

---

## 七、CLAUDE.md：项目说明文件

`CLAUDE.md` 是给 Claude Code 的项目说明书。

适合放：

- 项目简介
- 技术栈
- 目录结构
- 启动命令
- 测试命令
- 代码风格
- Git 提交规范
- 安全注意事项
- 不希望 Claude 修改的目录或文件

示例：

```md
# Project Guide for Claude Code

## Project Overview

This is a Go backend project using Gin.

## Common Commands

- Run tests: `go test ./...`
- Start server: `go run ./cmd/server`
- Run lint: `golangci-lint run`

## Coding Style

- Prefer table-driven tests.
- Keep changes minimal and focused.
- Do not introduce large dependencies without confirmation.
- Use explicit error handling.

## Security Notes

- Do not print passwords, tokens, secrets, or credentials in logs.
- Validate file upload size, extension, content type, and storage path.
- Avoid path traversal and command injection risks.
```

常见位置：

| 文件 | 作用 |
|---|---|
| `~/.claude/CLAUDE.md` | 个人全局说明 |
| `./CLAUDE.md` | 当前项目说明，可提交到 Git |
| `./CLAUDE.local.md` | 当前项目个人说明，不建议提交 |
| `.claude/settings.local.json` | 本项目个人配置，通常不提交 |

---

## 八、Skills：可复用能力包

Skills 适合把重复任务沉淀成固定流程。

一个 Skill 通常是一个目录，里面至少包含：

```text
SKILL.md
```

个人全局 Skill：

```text
~/.claude/skills/go-test-writer/SKILL.md
```

项目级 Skill：

```text
.claude/skills/go-test-writer/SKILL.md
```

判断原则：

```text
项目事实放 CLAUDE.md
重复流程做成 Skill
```

---

## 九、自定义 Skill 示例：Go 单元测试

创建目录：

```bash
mkdir -p ~/.claude/skills/go-test-writer
```

创建文件：

```bash
vim ~/.claude/skills/go-test-writer/SKILL.md
```

内容：

```md
---
name: go-test-writer
description: Generate or improve Go unit tests using table-driven tests. Use when the user asks for Go UT, unit tests, test coverage, or test cases.
---

# Go Test Writer

When writing Go unit tests:

1. Read the target function and related dependencies.
2. Identify input, output, errors, and side effects.
3. Prefer table-driven tests.
4. Avoid monkey patching unless explicitly requested.
5. Prefer dependency injection through interfaces.
6. Cover normal cases, error cases, nil cases, empty values, and boundary values.
7. Use clear test case names.
8. Use `t.Run` for each case.
9. Run the most relevant `go test` command if possible.

Before editing:

- List the test scenarios.
- Identify hard-to-test dependencies.

After editing:

- Summarize added test cases.
- Mention whether tests were run.
- If tests fail, explain the failure.
```

使用：

```text
/go-test-writer
```

或者自然语言触发：

```text
请帮我为这个 Go 文件生成表格驱动单元测试。
```

---

## 十、官方 anthropics/skills 仓库

官方 Skills 示例仓库：

```text
https://github.com/anthropics/skills
```

添加官方 Skills marketplace：

```text
/plugin marketplace add anthropics/skills
```

安装文档处理 Skills：

```text
/plugin install document-skills@anthropic-agent-skills
```

安装示例 Skills：

```text
/plugin install example-skills@anthropic-agent-skills
```

查看插件：

```text
/plugin
```

查看 Skills：

```text
/skills
```

---

## 十一、Skills 编写建议

### 1. description 要清楚

不推荐：

```md
description: Help with tests.
```

推荐：

```md
description: Generate Go table-driven unit tests. Use when the user asks for Go unit tests, UT, test coverage, or test cases.
```

---

### 2. 有副作用的 Skill 不要自动触发

例如部署、发布、删除文件、推送代码等任务，建议加：

```md
---
name: deploy
description: Deploy the application.
disable-model-invocation: true
---
```

这样只能手动调用：

```text
/deploy
```

---

### 3. 不要在 Skill 中写密钥

不要写：

```text
API_KEY=xxx
PASSWORD=xxx
TOKEN=xxx
```

如果需要环境变量，只写变量名，不写真实值。

---

### 4. 适合沉淀的个人 Skills

| Skill 名称 | 用途 |
|---|---|
| `go-test-writer` | 生成 Go 表格驱动 UT |
| `security-log-review` | 检查日志敏感信息 |
| `monthly-summary-writer` | 生成月度工作总结 |
| `blog-writer` | 生成 Hugo 博客文章 |
| `commit-message-writer` | 按公司格式生成提交说明 |
| `hugo-papermod-helper` | 排查 Hugo / PaperMod 配置 |
| `redis-troubleshooter` | 排查 Redis 连接、TLS、认证问题 |
| `spring-session-helper` | 分析 Spring Session 配置影响 |

---

## 十二、Claude Code 接入外部 API 大模型

Claude Code 不一定只能使用默认 Claude 服务。

如果外部模型或模型网关兼容 Claude Code 需要的 Anthropic API 格式，就可以通过环境变量把请求路由到外部 API。

常见方式：

1. 外部服务直接提供 Anthropic API 兼容接口
2. 通过 LLM Gateway 把不同模型统一转换成 Claude Code 可用接口

下面以 DeepSeek API 为例。

---

## 十三、案例：Claude Code 接入 DeepSeek API

### 1. 原理说明

DeepSeek 提供 Anthropic API 兼容接口，base URL 为：

```text
https://api.deepseek.com/anthropic
```

Claude Code 可以通过环境变量切换请求地址和模型。

| 变量 | 含义 |
|---|---|
| `ANTHROPIC_BASE_URL` | 指向 DeepSeek 的 Anthropic 兼容接口 |
| `ANTHROPIC_AUTH_TOKEN` | DeepSeek API Key |
| `ANTHROPIC_MODEL` | 默认模型 |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | Opus 档位映射模型 |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | Sonnet 档位映射模型 |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | Haiku 档位映射模型 |
| `CLAUDE_CODE_SUBAGENT_MODEL` | 子代理使用模型 |
| `CLAUDE_CODE_EFFORT_LEVEL` | 推理强度 |

---

### 2. 临时方式：当前终端生效

适合临时测试。

```bash
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_AUTH_TOKEN=<your DeepSeek API Key>
export ANTHROPIC_MODEL=deepseek-v4-pro[1m]
export ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-v4-pro[1m]
export ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-v4-pro[1m]
export ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-flash
export CLAUDE_CODE_SUBAGENT_MODEL=deepseek-v4-flash
export CLAUDE_CODE_EFFORT_LEVEL=max

cd /path/to/your/project
claude
```

注意：

```text
<your DeepSeek API Key>
```

需要替换为你自己的 DeepSeek API Key。

不要把真实 Key 写进博客、Git 仓库、截图或共享文档。

---

### 3. 推荐方式：用 zsh 函数隔离 DeepSeek

如果不想影响默认 Claude Code，可以在 `~/.zshrc` 中加一个函数：

```bash
cc-deepseek() {
  ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic \
  ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY" \
  ANTHROPIC_MODEL="deepseek-v4-pro[1m]" \
  ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro[1m]" \
  ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro[1m]" \
  ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek-v4-flash" \
  CLAUDE_CODE_SUBAGENT_MODEL="deepseek-v4-flash" \
  CLAUDE_CODE_EFFORT_LEVEL=max \
  claude "$@"
}
```

再设置 DeepSeek Key：

```bash
export DEEPSEEK_API_KEY="你的 DeepSeek API Key"
```

加载配置：

```bash
source ~/.zshrc
```

使用：

```bash
cd /path/to/your/project
cc-deepseek
```

带问题启动：

```bash
cc-deepseek "请解释这个项目结构"
```

这个方式的优点：

- 默认 `claude` 仍然走原来的 Claude 配置
- 只有执行 `cc-deepseek` 时才走 DeepSeek
- 不污染全局环境
- 方便对比不同模型效果

---

### 4. 长期方式：写入个人 settings.json

如果希望所有 Claude Code 默认都走 DeepSeek，可以写入用户配置：

```bash
mkdir -p ~/.claude
vim ~/.claude/settings.json
```

内容：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "<your DeepSeek API Key>",
    "ANTHROPIC_MODEL": "deepseek-v4-pro[1m]",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-pro[1m]",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-pro[1m]",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash",
    "CLAUDE_CODE_SUBAGENT_MODEL": "deepseek-v4-flash",
    "CLAUDE_CODE_EFFORT_LEVEL": "max"
  }
}
```

不建议把 API Key 写到：

```text
.claude/settings.json
```

因为项目级 `.claude/settings.json` 可能会被提交到 Git。

更适合本机个人配置的是：

```text
~/.claude/settings.json
```

或项目本地个人配置：

```text
.claude/settings.local.json
```

---

### 5. 验证是否生效

启动后可以查看状态：

```text
/status
```

也可以运行：

```bash
claude doctor
```

检查环境变量：

```bash
echo $ANTHROPIC_BASE_URL
echo $ANTHROPIC_MODEL
```

不要在公开终端、截图或日志中输出 API Key。

---

### 6. 恢复默认 Claude Code

如果使用临时环境变量：

```bash
unset ANTHROPIC_BASE_URL
unset ANTHROPIC_AUTH_TOKEN
unset ANTHROPIC_MODEL
unset ANTHROPIC_DEFAULT_OPUS_MODEL
unset ANTHROPIC_DEFAULT_SONNET_MODEL
unset ANTHROPIC_DEFAULT_HAIKU_MODEL
unset CLAUDE_CODE_SUBAGENT_MODEL
unset CLAUDE_CODE_EFFORT_LEVEL
```

如果写入了 `~/.claude/settings.json`，删除其中的 DeepSeek 配置后重新打开终端。

---

### 7. 使用 DeepSeek API 的注意事项

1. **模型能力可能不同**  
   Claude Code 的部分能力是围绕 Claude 模型设计的。切到外部模型后，代码理解、工具调用、长上下文、子代理表现可能不同。

2. **费用和额度走 DeepSeek**  
   配置 DeepSeek 后，调用费用和额度通常按 DeepSeek API 规则计算。

3. **数据会发送到 DeepSeek**  
   使用外部 API 时，代码上下文、提示词和工具结果可能发送给对应服务。公司代码、敏感日志、密钥和生产配置要谨慎处理。

4. **不要把 Key 提交到 Git**  
   API Key 只放在个人本地配置或安全的密钥管理系统中。

5. **模型名称可能变化**  
   DeepSeek 官方文档中的模型名可能更新。如果调用失败，应以 DeepSeek 官方文档为准。

---

## 十四、权限与安全建议

建议保守放权：

```text
允许：git diff、git status、go test、npm test、npm run lint、npm run build
谨慎：rm、git clean、git push、kubectl、terraform、数据库操作、生产环境命令
```

进入权限管理：

```text
/permissions
```

建议原则：

```text
让 Claude 多分析、多辅助，但关键操作由自己确认。
```

尤其是这些操作：

- 删除文件
- 推送代码
- 修改生产配置
- 操作数据库
- 执行部署
- 处理密钥和密码

都应该人工确认。

---

## 十五、与 Git 配合

修改前：

```bash
git status
```

修改后：

```text
/diff
```

或：

```bash
git diff
```

审查：

```text
/code-review
```

生成提交信息：

```text
请根据当前 git diff 生成 commit message。
```

自己确认后提交：

```bash
git add .
git commit -m "your commit message"
```

不建议一开始就允许 Claude 自动执行：

```bash
git push
```

---

## 十六、常见问题

### 1. `claude: command not found`

检查：

```bash
which claude
claude --version
echo $PATH
```

如果是 Homebrew 安装：

```bash
brew list --cask | grep claude
brew info --cask claude-code
```

---

### 2. 登录失败或授权异常

检查：

```bash
claude doctor
claude auth status
```

如果是网络问题，需要检查代理、DNS、公司网络策略等。

---

### 3. Claude 改动太大

可以提前约束：

```text
请只做最小必要修改，不要顺手重构无关代码。
```

或者：

```text
本次只允许修改以下文件：
- xxx.go
- xxx_test.go
```

---

### 4. 上下文太长

查看上下文：

```text
/context
```

压缩上下文：

```text
/compact
```

切换任务时清空上下文：

```text
/clear
```

---

### 5. 如何避免误删文件

建议：

- 使用 Git 保持可回滚
- 修改前先 `git status`
- 大改动前新建分支
- 对 `rm -rf`、`git clean`、`git push` 保持手动确认
- 不要轻易使用 `--dangerously-skip-permissions`

---

## 十七、个人推荐配置

可以把下面内容放进 `CLAUDE.local.md`：

```md
# Personal Preferences

- Use Chinese for explanations unless I ask for English.
- For Go unit tests, prefer table-driven tests.
- Avoid monkey patching unless there is no better option.
- Before large changes, explain the plan first.
- Keep changes minimal and focused.
- After code changes, run relevant tests if possible.
- Pay attention to security issues, especially sensitive logs, path traversal, file upload validation, command injection, and hardcoded credentials.
```

---

## 十八、最常用命令总结

日常开发最常用：

```bash
claude
claude "explain this project"
claude -p "explain this function"
cat error.log | claude -p "分析错误原因"
claude -c
claude -r "session-name"
claude --add-dir ../shared
claude --model sonnet --effort high
claude --permission-mode plan
claude doctor
```

交互内最常用：

```text
/init
/status
/model
/effort
/permissions
/context
/compact
/clear
/diff
/code-review
/skills
/plugin
```

DeepSeek 隔离启动：

```bash
cc-deepseek
```

整体建议：

```text
先理解项目 -> 写入 CLAUDE.md -> 小步修改 -> 运行测试 -> 查看 diff -> 代码审查 -> 人工确认提交
```

---

## 参考资料

- Claude Code CLI Reference: https://code.claude.com/docs/en/cli-reference
- Claude Code Commands: https://code.claude.com/docs/en/commands
- Claude Code Settings: https://code.claude.com/docs/zh-CN/settings
- Claude Code Model Configuration: https://code.claude.com/docs/en/model-config
- Claude Code Skills: https://code.claude.com/docs/en/skills
- Anthropic Skills GitHub Repository: https://github.com/anthropics/skills
- DeepSeek Claude Code Integration: https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code
- DeepSeek Anthropic API: https://api-docs.deepseek.com/guides/anthropic_api
