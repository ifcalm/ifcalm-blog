---
title: "Codex CLI 使用手册：安装、命令速查、AGENTS.md、Skills、MCP 与安全实践"
date: 2026-05-24
tags: ["Codex CLI", "AI 工具"]
draft: false
summary: "Codex CLI 完整使用手册，覆盖安装配置、命令速查、沙箱模式、AGENTS.md、Skills、MCP 配置、API 接入与安全实践。"
showToc: true
tocOpen: false
---

## 一、Codex CLI 是什么？

Codex CLI 是 OpenAI 提供的终端 AI 编程助手，可以在本地终端中读取代码、修改文件、运行命令，并协助完成开发任务。

核心命令是：

```bash
codex
```

可以把它理解为：

```text
运行在终端中的 AI 编程 Agent
```

适合这些场景：

- 阅读陌生项目
- 解释代码结构
- 修复 bug
- 编写单元测试
- 重构代码
- 分析日志和构建错误
- 生成文档
- 审查 Git diff
- 生成 commit message
- 使用 AGENTS.md 固化项目规则
- 使用 Skills 沉淀可复用工作流
- 使用 MCP 接入外部工具
- 使用 `codex exec` 做脚本化任务

---

## 二、Codex CLI、Codex App、IDE Extension、Codex Cloud 的区别

| 形态 | 使用位置 | 适合场景 |
|---|---|---|
| Codex CLI | 终端 | 命令行开发、脚本化、服务器环境 |
| Codex App | 桌面应用 | 多任务并行、图形化 diff、worktree 工作流 |
| IDE Extension | VS Code / Cursor / Windsurf | 在编辑器中直接协作 |
| Codex Cloud | 浏览器 / 云端 | 把任务交给云端环境后台执行 |

如果你主要在终端里开发，优先掌握：

```bash
codex
codex exec
codex resume
codex mcp
codex completion
```

如果你常用 VS Code / Cursor，可以结合 Codex IDE Extension。

---

## 三、安装 Codex CLI

### 1. 使用 npm 安装

官方安装命令：

```bash
npm install -g @openai/codex
```

查看版本：

```bash
codex --version
```

升级到最新版：

```bash
npm install -g @openai/codex@latest
```

如果遇到 npm 全局权限问题，不建议直接使用：

```bash
sudo npm install -g @openai/codex
```

更推荐正确配置 npm 全局目录，或者改用 Homebrew。

---

### 2. 使用 Homebrew 安装

macOS 上也可以用 Homebrew：

```bash
brew install codex
```

升级：

```bash
brew update
brew upgrade codex
```

查看安装信息：

```bash
brew info codex
```

查看命令位置：

```bash
which codex
```

---

### 3. 登录与退出

首次运行：

```bash
codex
```

会提示登录。可以使用 ChatGPT 账号，也可以使用 OpenAI API Key。

主动登录：

```bash
codex login
```

退出登录：

```bash
codex logout
```

如果是共享电脑，使用后建议执行：

```bash
codex logout
```

---

## 四、快速开始

进入项目目录：

```bash
cd /path/to/your/project
```

启动 Codex：

```bash
codex
```

带初始问题启动：

```bash
codex "请解释这个项目的目录结构和启动方式"
```

建议第一次进入项目后先让 Codex 做只读分析：

```text
请先阅读项目结构，不要修改代码。请说明技术栈、启动入口、测试命令和主要模块。
```

如果确认要让 Codex 修改代码，建议先建立 Git 检查点：

```bash
git status
git checkout -b codex/your-task
```

---

## 五、常用命令速查

### 1. 基础命令

| 场景 | 命令 |
|---|---|
| 启动交互模式 | `codex` |
| 带问题启动 | `codex "Explain this codebase"` |
| 指定工作目录 | `codex -C /path/to/project` |
| 指定模型 | `codex -m gpt-5.4` |
| 添加额外目录 | `codex --add-dir ../shared` |
| 附加图片 | `codex -i screenshot.png "根据截图修改 UI"` |
| 使用本地开源模型 | `codex --oss` |
| 指定配置项 | `codex -c model_reasoning_effort="high"` |
| 指定配置 profile | `codex -p work` |
| 禁用 TUI alternate screen | `codex --no-alt-screen` |
| 查看帮助 | `codex --help` |
| 查看版本 | `codex --version` |

---

### 2. 审批与沙箱

| 场景 | 命令 |
|---|---|
| 只读沙箱 | `codex -s read-only` |
| 允许工作区写入 | `codex -s workspace-write` |
| 危险全访问 | `codex -s danger-full-access` |
| 不信任模式审批 | `codex -a untrusted` |
| 按需审批 | `codex -a on-request` |
| 不主动询问审批 | `codex -a never` |
| 绕过审批和沙箱 | `codex --yolo` |

推荐日常组合：

```bash
codex -s workspace-write -a on-request
```

高风险命令：

```bash
codex --yolo
```

`--yolo` 会绕过审批和沙箱，只建议在隔离容器、虚拟机或一次性实验目录中使用。

---

### 3. 非交互模式：codex exec

`codex exec` 适合脚本化、CI 或一次性任务。

```bash
codex exec "请总结当前项目结构"
```

短命令别名：

```bash
codex e "请总结当前项目结构"
```

指定工作目录：

```bash
codex exec -C /path/to/project "请分析测试失败原因"
```

从 stdin 读取 prompt：

```bash
cat prompt.txt | codex exec -
```

分析 Git diff：

```bash
git diff | codex exec "请审查这个 diff，重点关注 bug、安全问题和测试覆盖"
```

JSONL 输出：

```bash
codex exec --json "请检查项目中的 TODO"
```

把最终回答写入文件：

```bash
codex exec -o result.md "请生成项目说明文档"
```

结合 JSON 和最终输出文件：

```bash
codex exec --json -o summary.md "请审查当前代码变更"
```

---

### 4. 恢复会话

恢复交互式会话：

```bash
codex resume
```

恢复当前目录最近会话：

```bash
codex resume --last
```

恢复所有目录中最近会话：

```bash
codex resume --last --all
```

恢复指定会话：

```bash
codex resume <SESSION_ID>
```

恢复非交互会话：

```bash
codex exec resume --last
```

恢复非交互会话并追加指令：

```bash
codex exec resume --last "继续完成剩余检查"
```

---

### 5. Codex Cloud

打开云任务选择器：

```bash
codex cloud
```

提交云任务：

```bash
codex cloud exec --env <ENV_ID> "请修复登录失败问题并补充测试"
```

列出云任务：

```bash
codex cloud list
```

JSON 输出：

```bash
codex cloud list --json
```

限制返回数量：

```bash
codex cloud list --limit 10
```

应用云任务 diff 到本地：

```bash
codex apply <TASK_ID>
```

适合场景：

- 任务较长
- 需要云端环境执行
- 想让多个任务并行
- 希望本地继续做其他工作

---

### 6. MCP 命令

查看 MCP server：

```bash
codex mcp list
```

JSON 输出：

```bash
codex mcp list --json
```

添加 stdio MCP server：

```bash
codex mcp add my-server -- node /path/to/server.js
```

添加环境变量：

```bash
codex mcp add my-server --env API_KEY=xxx -- node /path/to/server.js
```

添加 HTTP MCP server：

```bash
codex mcp add docs --url https://example.com/mcp
```

查看配置：

```bash
codex mcp get my-server
```

删除配置：

```bash
codex mcp remove my-server
```

登录支持 OAuth 的 MCP server：

```bash
codex mcp login my-server
```

退出 MCP server 登录：

```bash
codex mcp logout my-server
```

---

### 7. Shell 自动补全

Codex CLI 支持生成 shell completion。

Zsh：

```bash
mkdir -p ~/.zsh/completions
codex completion zsh > ~/.zsh/completions/_codex
```

在 `~/.zshrc` 中加入：

```bash
fpath=(~/.zsh/completions $fpath)
autoload -Uz compinit
compinit
```

重新加载：

```bash
source ~/.zshrc
```

Bash：

```bash
codex completion bash > ~/.codex-completion.bash
echo 'source ~/.codex-completion.bash' >> ~/.bashrc
source ~/.bashrc
```

Fish：

```bash
codex completion fish > ~/.config/fish/completions/codex.fish
```

PowerShell：

```powershell
codex completion power-shell
```

---

### 8. 其他命令

| 命令 | 作用 |
|---|---|
| `codex login` | 登录 |
| `codex logout` | 移除本地凭证 |
| `codex update` | 检查并应用 CLI 更新 |
| `codex completion` | 生成 shell 补全脚本 |
| `codex features list` | 查看 feature flags |
| `codex features enable <feature>` | 启用 feature |
| `codex features disable <feature>` | 禁用 feature |
| `codex debug models` | 打印模型目录 |
| `codex sandbox` | 在 Codex 沙箱中运行命令 |
| `codex execpolicy check` | 检查 execpolicy 规则 |
| `codex mcp-server` | 将 Codex 作为 MCP server 运行 |

---

## 六、交互模式 Slash Commands

进入 `codex` 交互模式后，可以输入：

```text
/
```

打开命令面板。

常用命令：

| Slash Command | 作用 |
|---|---|
| `/init` | 生成 `AGENTS.md` 脚手架 |
| `/model` | 切换模型 |
| `/fast` | 开关 Fast 模式 |
| `/personality` | 调整沟通风格 |
| `/permissions` | 调整审批和权限 |
| `/plan` | 进入计划模式 |
| `/goal` | 设置、暂停、恢复或清除长期目标 |
| `/status` | 查看当前模型、权限、上下文、token 等状态 |
| `/diff` | 查看当前 Git diff |
| `/review` | 审查当前工作区变更 |
| `/clear` | 清空终端并开始新对话 |
| `/new` | 在同一 CLI 会话中开始新对话 |
| `/resume` | 恢复历史会话 |
| `/compact` | 压缩上下文 |
| `/copy` | 复制最近一次完成的 Codex 输出 |
| `/raw` | 切换原始滚动输出模式 |
| `/skills` | 浏览和使用 Skills |
| `/plugins` | 浏览和管理插件 |
| `/mcp` | 查看 MCP 工具 |
| `/hooks` | 查看生命周期 hooks |
| `/memories` | 配置 memory 使用和生成 |
| `/ide` | 拉取 IDE 当前打开文件和选区上下文 |
| `/agent` | 切换 subagent 线程 |
| `/side` | 开启临时侧边对话 |
| `/fork` | 从当前会话 fork 出新线程 |
| `/ps` | 查看实验性后台终端 |
| `/stop` | 停止后台终端 |
| `/theme` | 设置代码高亮主题 |
| `/vim` | 切换 Vim 输入模式 |
| `/keymap` | 修改快捷键 |
| `/debug-config` | 打印配置层和策略诊断 |
| `/exit` 或 `/quit` | 退出 CLI |

推荐常用组合：

```text
/init
/status
/model
/permissions
/plan
/diff
/review
/skills
/compact
```

---

## 七、AGENTS.md：给 Codex 的项目说明书

`AGENTS.md` 是 Codex 的持久项目说明文件。

它适合放：

- 项目简介
- 技术栈
- 构建命令
- 启动命令
- 测试命令
- 代码风格
- 提交规范
- 安全要求
- 不允许修改的目录
- 特定模块注意事项

生成脚手架：

```text
/init
```

或者手动创建：

```bash
touch AGENTS.md
```

示例：

```md
# AGENTS.md

## Project Overview

This is a Go backend project using Gin, Redis, and MySQL.

## Common Commands

- Run all tests: `go test ./...`
- Run one package: `go test ./internal/service/...`
- Start server: `go run ./cmd/server`
- Format code: `gofmt -w .`

## Coding Rules

- Prefer table-driven tests for Go unit tests.
- Keep changes minimal and focused.
- Do not introduce new large dependencies without confirmation.
- Preserve existing public API behavior unless explicitly requested.

## Security Notes

- Do not print passwords, tokens, secrets, or credentials in logs.
- Validate uploaded file size, extension, content type, and storage path.
- Avoid path traversal and command injection.
- Be careful with Redis, TLS, authentication, and session timeout changes.

## Before Finishing

- Run relevant tests if possible.
- Summarize files changed.
- Mention tests run and tests not run.
```

---

## 八、AGENTS.md 的加载顺序

Codex 会在开始工作前读取 `AGENTS.md`。

常见范围：

| 范围 | 路径 | 用途 |
|---|---|---|
| 全局 | `~/.codex/AGENTS.md` | 个人默认偏好 |
| 全局覆盖 | `~/.codex/AGENTS.override.md` | 临时覆盖全局规则 |
| 仓库根目录 | `AGENTS.md` | 当前仓库共享规则 |
| 子目录 | `services/payments/AGENTS.md` | 子模块规则 |
| 子目录覆盖 | `AGENTS.override.md` | 当前目录更高优先级规则 |

建议：

- 全局文件放个人习惯
- 仓库根目录放团队规则
- 子目录放模块规则
- 不要写密码、Token、生产凭证
- 内容要短而准确，不要堆砌空泛规则

---

## 九、config.toml 配置

Codex 用户级配置文件：

```text
~/.codex/config.toml
```

项目级配置：

```text
.codex/config.toml
```

项目级配置只在受信任项目中加载。

配置优先级从高到低大致是：

```text
CLI flags / -c 覆盖
profile
项目 .codex/config.toml
用户 ~/.codex/config.toml
系统 /etc/codex/config.toml
内置默认值
```

---

### 1. 推荐个人配置示例

创建：

```bash
mkdir -p ~/.codex
vim ~/.codex/config.toml
```

示例：

```toml
model = "gpt-5.5"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
model_reasoning_effort = "high"
personality = "friendly"
web_search = "cached"

[features]
shell_snapshot = true
multi_agent = true
personality = true
hooks = true
```

---

### 2. 项目配置示例

创建：

```bash
mkdir -p .codex
vim .codex/config.toml
```

示例：

```toml
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[features]
shell_snapshot = true
```

注意：

- 不要把 API Key 写入项目配置
- 一些机器本地配置，例如 `openai_base_url`、`model_provider`、`model_providers` 等，不应放项目级配置
- 项目级配置适合放团队共享的低风险设置

---

### 3. 临时覆盖配置

临时改模型：

```bash
codex -c model='"gpt-5.4"'
```

临时提高推理强度：

```bash
codex -c model_reasoning_effort='"high"'
```

临时指定日志目录：

```bash
codex -c log_dir='"./.codex-log"'
```

---

## 十、审批与沙箱怎么理解？

Codex 的安全控制主要有两层：

```text
Sandbox：技术边界，限制文件、网络、命令能做什么
Approval：审批策略，决定什么时候需要你确认
```

### 1. Sandbox 模式

| 模式 | 含义 |
|---|---|
| `read-only` | 只读，适合理解项目和审查 |
| `workspace-write` | 可写当前工作区，适合日常开发 |
| `danger-full-access` | 基本放开限制，风险高 |

推荐：

```bash
codex -s workspace-write
```

---

### 2. Approval 策略

| 策略 | 含义 |
|---|---|
| `untrusted` | 更保守，适合陌生项目 |
| `on-request` | 按需询问，适合日常 |
| `never` | 不主动询问，适合自动化但风险更高 |

推荐：

```bash
codex -a on-request
```

---

### 3. 日常推荐组合

```bash
codex -s workspace-write -a on-request
```

只读分析：

```bash
codex -s read-only -a on-request
```

非交互脚本：

```bash
codex exec -s workspace-write -a never "请执行代码检查并输出总结"
```

危险实验环境：

```bash
codex --yolo
```

只建议在隔离环境中使用。

---

## 十一、Skills：可复用能力包

Skills 可以把重复工作流沉淀为可复用能力。

一个 Skill 是一个目录，至少包含：

```text
SKILL.md
```

常见结构：

```text
my-skill/
├── SKILL.md
├── references/
├── scripts/
└── assets/
```

`SKILL.md` 必须包含：

```md
---
name: skill-name
description: Explain exactly when this skill should and should not trigger.
---

Skill instructions for Codex to follow.
```

---

### 1. Skill 存放位置

| 范围 | 路径 |
|---|---|
| 当前目录 | `$CWD/.agents/skills` |
| 仓库上级目录 | `$CWD/../.agents/skills` |
| 仓库根目录 | `$REPO_ROOT/.agents/skills` |
| 用户级 | `$HOME/.agents/skills` |
| 管理员级 | `/etc/codex/skills` |

注意：Codex 的 Skills 目录是：

```text
.agents/skills
```

不是：

```text
.codex/skills
```

---

### 2. 创建 Go 单元测试 Skill

创建目录：

```bash
mkdir -p ~/.agents/skills/go-test-writer
```

创建文件：

```bash
vim ~/.agents/skills/go-test-writer/SKILL.md
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
2. Identify inputs, outputs, errors, and side effects.
3. Prefer table-driven tests.
4. Avoid monkey patching unless explicitly requested.
5. Prefer dependency injection through interfaces.
6. Cover normal, error, nil, empty, and boundary cases.
7. Use `t.Run` for each case.
8. Run the most relevant `go test` command if possible.

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
/skills
```

或者直接在 prompt 中提到：

```text
请使用 $go-test-writer 给这个文件补充单元测试。
```

---

### 3. 使用内置 skill creator

Codex 内置了 skill creator，可以这样使用：

```text
请使用 $skill-creator 创建一个用于生成 Hugo 博客文章的 skill。
```

或者：

```text
请使用 $skill-creator 创建一个 security-log-review skill，用于检查日志中是否包含敏感信息。
```

---

## 十二、MCP：接入外部工具

MCP，即 Model Context Protocol，可以让 Codex 使用外部工具和上下文。

适合接入：

- GitHub
- 文件系统
- 数据库
- Jira / Linear
- 文档系统
- 内部 API
- 浏览器自动化工具
- 自定义脚本

添加 stdio server：

```bash
codex mcp add my-tool -- node /path/to/server.js
```

添加 HTTP server：

```bash
codex mcp add docs --url https://example.com/mcp
```

查看列表：

```bash
codex mcp list
```

查看详情：

```bash
codex mcp get docs
```

删除：

```bash
codex mcp remove docs
```

在会话中查看：

```text
/mcp
```

建议：

- 先只接入只读工具
- 不要让 MCP 工具直接拿生产密钥
- 外部工具的权限越小越好
- 对删除、部署、数据库写入类工具保持审批

---

## 十三、Ollama / 本地开源模型

Codex CLI 支持使用本地开源模型 provider。

前提是本机 Ollama 已运行：

```bash
ollama serve
```

运行 Codex：

```bash
codex --oss
```

也可以在非交互模式使用：

```bash
codex exec --oss "请解释这个项目结构"
```

如果想指定模型，需要结合本地 provider 配置和模型名称。日常更建议先确认 Ollama 模型可运行：

```bash
ollama list
ollama run qwen3
```

然后再使用：

```bash
codex --oss
```

注意：

- 本地模型能力和官方 Codex 模型可能不同
- 工具调用、长上下文、代码修改效果取决于模型能力
- 本地模型更适合学习、实验和隐私敏感场景
- 复杂项目开发仍建议使用官方 Codex 模型

---

## 十四、自定义模型 Provider

Codex 支持通过 `~/.codex/config.toml` 配置模型 provider。

常见字段包括：

```toml
model_provider = "custom"

[model_providers.custom]
name = "Custom Provider"
base_url = "https://example.com/v1"
env_key = "CUSTOM_API_KEY"
wire_api = "responses"
```

然后设置环境变量：

```bash
export CUSTOM_API_KEY="your-api-key"
```

注意：

- Codex 的自定义 provider 需要兼容它使用的 API 协议
- `wire_api` 当前以 `responses` 为主
- 不要把 API Key 直接写进 `config.toml`
- 机密信息用环境变量或密钥管理系统
- 如果第三方服务只兼容 Chat Completions，不一定能直接用于 Codex

对于普通使用者，优先使用：

```text
ChatGPT 登录
OpenAI API Key 登录
Ollama --oss
```

自定义 provider 适合更熟悉模型网关和 API 协议的用户。

---

## 十五、Git 工作流建议

修改前：

```bash
git status
git checkout -b codex/your-task
```

让 Codex 先分析：

```text
请先分析这个需求，不要修改代码。请给出修改计划、影响范围和测试点。
```

确认后再执行：

```text
按计划修改，保持改动范围尽量小。
```

修改后：

```text
/diff
/review
```

运行测试：

```text
请运行相关测试，并解释结果。
```

自己确认后提交：

```bash
git add .
git commit -m "your commit message"
```

不建议一开始就允许 Codex 自动执行：

```bash
git push
```

---

## 十六、常见开发场景 Prompt

### 1. 理解项目

```text
请先不要修改代码。请阅读项目结构，说明技术栈、启动入口、核心模块、测试命令和主要风险点。
```

### 2. 修复 bug

```text
请分析这个 bug 的根因和影响范围，先给出修改计划，不要直接改代码。
```

### 3. 写 Go UT

```text
请为这个 Go 文件补充 table-driven tests，不要使用 monkey patch。修改前先列出测试场景。
```

### 4. 审查 diff

```text
请审查当前 git diff，重点关注空指针、并发安全、错误处理、日志敏感信息和测试覆盖。
```

### 5. 生成 commit message

```text
请根据当前 git diff 生成一条简洁清晰的 commit message。
```

### 6. 生成文档

```text
请根据当前项目生成一份 README 草稿，包括项目简介、启动方式、配置项、测试命令和部署注意事项。
```

---

## 十七、常见问题

### 1. `codex: command not found`

检查：

```bash
which codex
codex --version
echo $PATH
```

npm 安装检查：

```bash
npm list -g @openai/codex
```

Homebrew 检查：

```bash
brew info codex
brew list | grep codex
```

---

### 2. 登录失败

尝试：

```bash
codex logout
codex login
```

检查网络、代理、公司网络策略。

如果使用 API Key，确认 Key 是否有效、额度是否正常。

---

### 3. Codex 改动太大

可以要求：

```text
只做最小必要修改，不要顺手重构无关代码。
```

或者：

```text
本次只允许修改以下文件：
- xxx.go
- xxx_test.go
```

---

### 4. 如何让 Codex 只读分析？

```bash
codex -s read-only
```

然后提问：

```text
请只读分析这个问题，不要修改代码，不要运行写入类命令。
```

---

### 5. 如何处理上下文太长？

使用：

```text
/compact
```

或者开新会话：

```text
/new
```

也可以在 shell 中恢复最近会话：

```bash
codex resume --last
```

---

### 6. 如何查看当前配置？

在交互模式中：

```text
/status
/debug-config
```

查看配置文件：

```bash
cat ~/.codex/config.toml
```

---

### 7. Skills 不生效

检查：

- 是否放在 `.agents/skills` 或 `~/.agents/skills`
- 是否有 `SKILL.md`
- `SKILL.md` 是否包含 `name` 和 `description`
- 是否重启了 Codex
- 是否在 `/skills` 中能看到
- `description` 是否写得太模糊

---

### 8. 不想让 Codex 自动使用某个 Skill

可以在 `~/.codex/config.toml` 中禁用：

```toml
[[skills.config]]
path = "/path/to/skill/SKILL.md"
enabled = false
```

修改后重启 Codex。

---

## 十八、推荐日常工作流

### 1. 第一次进入项目

```bash
cd /path/to/project
codex
```

在交互模式：

```text
/init
请阅读项目结构，帮我完善 AGENTS.md，包含启动、测试、代码风格、安全注意事项。
```

---

### 2. 开发任务

```bash
git checkout -b codex/task-name
codex -s workspace-write -a on-request
```

在交互模式：

```text
请先给出修改计划，不要直接改代码。
```

确认后：

```text
按计划修改，并运行相关测试。
```

---

### 3. 提交前

```text
/diff
/review
请根据当前 diff 生成 commit message。
```

自己检查：

```bash
git diff
git status
```

提交：

```bash
git add .
git commit -m "your message"
```

---

## 十九、推荐配置与个人偏好

### 1. 全局 AGENTS.md

```bash
mkdir -p ~/.codex
vim ~/.codex/AGENTS.md
```

示例：

```md
# Personal Codex Preferences

- Use Chinese for explanations unless I ask for English.
- Before large edits, propose a plan first.
- Keep changes minimal and focused.
- For Go unit tests, prefer table-driven tests.
- Avoid monkey patching unless explicitly requested.
- After changes, run relevant tests when possible.
- Pay attention to security issues, especially sensitive logs, file upload validation, path traversal, command injection, and hardcoded credentials.
```

---

### 2. 全局 config.toml

```bash
vim ~/.codex/config.toml
```

示例：

```toml
model = "gpt-5.5"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
model_reasoning_effort = "high"
personality = "friendly"
web_search = "cached"

[features]
shell_snapshot = true
multi_agent = true
hooks = true
personality = true
```

---

## 二十、命令总表

### 安装与登录

```bash
npm install -g @openai/codex
npm install -g @openai/codex@latest
brew install codex
brew upgrade codex
codex login
codex logout
codex --version
```

### 交互使用

```bash
codex
codex "解释这个项目"
codex -C /path/to/project
codex -m gpt-5.4
codex -s workspace-write -a on-request
codex --add-dir ../shared
codex -i screenshot.png "根据截图修改页面"
```

### 非交互使用

```bash
codex exec "总结项目结构"
codex e "总结项目结构"
cat prompt.txt | codex exec -
git diff | codex exec "审查 diff"
codex exec --json "检查当前项目"
codex exec -o result.md "生成文档"
codex exec resume --last
```

### 会话与云任务

```bash
codex resume
codex resume --last
codex cloud
codex cloud exec --env <ENV_ID> "执行任务"
codex cloud list
codex cloud list --json
codex apply <TASK_ID>
```

### MCP

```bash
codex mcp list
codex mcp list --json
codex mcp add my-server -- node server.js
codex mcp add docs --url https://example.com/mcp
codex mcp get my-server
codex mcp remove my-server
codex mcp login my-server
codex mcp logout my-server
```

### Skills

```bash
mkdir -p ~/.agents/skills/my-skill
vim ~/.agents/skills/my-skill/SKILL.md
```

交互模式：

```text
/skills
$skill-creator
$skill-installer linear
```

### 自动补全

```bash
codex completion zsh > ~/.zsh/completions/_codex
codex completion bash > ~/.codex-completion.bash
codex completion fish > ~/.config/fish/completions/codex.fish
```

---

## 二十一、个人建议

我建议你把 Codex CLI 按三个层次来使用：

```text
第一层：日常开发
codex、/plan、/diff、/review、AGENTS.md

第二层：效率提升
codex exec、codex resume、Skills、shell completion

第三层：扩展集成
MCP、Plugins、Codex Cloud、Ollama --oss、自定义 provider
```

最值得长期沉淀的是：

```text
AGENTS.md + Skills + Git 工作流
```

其中：

- `AGENTS.md` 管项目长期规则
- `Skills` 管重复流程
- `config.toml` 管本机默认行为
- `MCP` 管外部工具能力
- `codex exec` 管自动化任务

最常用的一组命令：

```bash
codex
codex "解释这个项目"
codex -s workspace-write -a on-request
codex exec "请审查当前 git diff"
codex resume --last
codex completion zsh
```

交互中最常用：

```text
/init
/status
/model
/permissions
/plan
/diff
/review
/skills
/compact
```

---

## 参考资料

- Codex CLI：https://developers.openai.com/codex/cli
- Codex Quickstart：https://developers.openai.com/codex/quickstart
- Codex CLI Reference：https://developers.openai.com/codex/cli/reference
- Codex CLI Features：https://developers.openai.com/codex/cli/features
- Codex Slash Commands：https://developers.openai.com/codex/cli/slash-commands
- Codex Config Basics：https://developers.openai.com/codex/config-basic
- Codex Config Reference：https://developers.openai.com/codex/config-reference
- AGENTS.md Guide：https://developers.openai.com/codex/guides/agents-md
- Codex Skills：https://developers.openai.com/codex/skills
- Codex Sandbox：https://developers.openai.com/codex/concepts/sandboxing
- Agent approvals & security：https://developers.openai.com/codex/agent-approvals-security
