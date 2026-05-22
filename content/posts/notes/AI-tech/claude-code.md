---
title: "Claude Code：终端里的 AI 编程搭档"
date: 2026-04-18
tags: ["AI", "工具"]
draft: false
summary: "一个在终端里帮你写代码、修 bug、管 git 的 AI 伙伴"
showToc: true
tocOpen: true
ShowShareButtons: false
---

## 这玩意是什么

Claude Code 是 Anthropic 出的一个终端 AI 编程助手。说白了，你打开终端敲 `claude`，它就在里面等着帮你干活——写代码、改 bug、提交 git、跑测试，甚至帮你发 PR。

和 Copilot 那种在 IDE 里悄悄补全的风格不同，Claude Code 更像是一个坐在你旁边的程序员同事，你说话，它干活。它看得懂整个项目，能自己搜文件、读代码，然后动手改。

## 怎么装上

```bash
# 二选一，推荐 brew
brew install claude-code
# 或者
npm install -g @anthropic-ai/claude-code
```

装完敲 `claude` 就进去了。

## 上手三板斧

```bash
# 直接进去聊
claude

# 一句话干完就退（适合管道、脚本）
claude -p "解释一下这个项目的目录结构"

# 把日志丢给它分析
cat error.log | claude -p "这报错是怎么回事"
```

这三招掌握了，日常工作基本够用了。

## 常用姿势

### 选模型

```bash
claude --model opus      # 大活：重构、设计、debug 疑难杂症
claude --model sonnet    # 日常主力，够快够聪明（默认）
claude --model haiku     # 小活：修 typo、格式化、简单问答
```

一个挺实用的小技巧：平时用 sonnet，碰到真的想不明白的硬骨头再切 opus。haiku 适合那种"帮我给这个函数加个注释"级别的活。

### 控制权限

有时候你只想让它看看代码给点建议，不想让它真动手改：

```bash
# 只读模式：只准看，不准碰
claude --permission-mode plan

# 反过来，完全信任它（只在沙箱里用！）
claude --dangerously-skip-permissions
```

日常建议用默认的 `ask` 模式——它每次要做点什么都会问你，你有否决权。这比事后 `git reset --hard` 舒服多了。

### 会话管理

```bash
# 继续上次的对话
claude --continue          # 或者 claude -c

# 回到之前的某个会话（会弹选择器）
claude --resume

# 给会话起个名，好找
claude -n "修登录页bug"
```

这个 `-n` 真的建议养成习惯。等你有七八个 "debug" 会话的时候就知道我的意思了。

### 隔离实验

```bash
# 创建一个独立的工作树，放心折腾
claude --worktree

# 配合 tmux 更爽
claude --worktree --tmux
```

想试个大胆的重构方案但不确定会不会搞砸？用 worktree，搞砸了删掉就行，主分支毫发无伤。

### 代码审查

```bash
# 审查当前分支
claude ultrareview

# 审查指定 PR
claude ultrareview 128

# 跟 main 比
claude ultrareview main
```

它会启动多个 agent 并着审，比一个人的 code review 靠谱。

---

## 会话里能用的斜杠命令

进了交互式会话以后，`/` 开头就是命令。这里只说我真常用的，完整的敲 `/help` 自己看。

### 每天都要用

| 命令 | 干嘛的 | 什么时候用 |
|------|--------|-----------|
| `/clear` | 清空对话 | 话题聊完了想换新话题，别让上下文掺和 |
| `/compact` | 压缩上下文 | 聊太长了有点卡，压缩一下腾空间 |
| `/model` | 换模型 | 发现 sonnet 搞不定，切 opus 再战 |
| `/init` | 生成项目的 CLAUDE.md | 新项目，让 Claude 先了解代码库 |

### 提交代码相关

| 命令 | 干嘛的 |
|------|--------|
| `/review` | 审查当前分支的改动 |
| `/security-review` | 安全检查（上线前跑一下不吃亏） |
| `/simplify` | 检查代码有没有冗余和可优化的地方 |
| `/pr-comments` | 看 PR 上的 review 意见 |

### 偶尔用但很好用

| 命令 | 干嘛的 |
|------|--------|
| `/context` | 看用了多少 token（心里有数） |
| `/cost` | 看这次会话花了多少钱 |
| `/resume` | 回到之前的会话 |
| `/doctor` | 出毛病了诊断一下 |
| `/theme` | 切换亮色/暗色 |
| `/add-dir` | 让它能看到项目外的文件 |

---

## 那些有时候用到的 CLI 参数

前面说的是每天都会碰的，下面这些偶尔也很有用，列出来供检索。

**输入输出：**

```bash
# 输出 JSON（脚本里用）
claude -p --output-format json "列出所有 API 路由"

# 要求输出符合特定结构
claude -p --json-schema schema.json "提取用户信息"

# 实时流式输出
claude -p --output-format stream-json --include-partial-messages "写个服务"
```

**微调：**

```bash
# 让它出工不出力
claude --effort low "写个注释"

# 开足马力
claude --effort max "这个并发 bug 到底什么原因"

# 高峰期 opus 挂了自动切 sonnet
claude -p --fallback-model sonnet "紧急修复"
```

**限制它：**

```bash
# 只允许读，不让写
claude --tools "Read,Grep,Glob"

# 允许 git 操作但不能 rm
claude --allowed-tools "Bash(git *) Edit"

# 禁止删东西
claude --disallowed-tools "Bash(rm *)"
```

---

## 配置小抄

在项目根目录放一个 `CLAUDE.md`，Claude 会自动读。比如：

```markdown
# CLAUDE.md
## 命令
- 测试: `pytest -x --ff`
- Lint: `ruff check .`
- 构建: `make build`
```

然后它就会按你的习惯来干活，不用每次都重复交代。

权限配置在 `settings.json` 里，三个级别：
- **Allow** — 直接干不用问（如 `git status`）
- **Ask** — 干之前问一下（默认，大部分操作）  
- **Deny** — 绝对不许（如 `rm -rf /`）

---

## 接 DeepSeek API

Claude Code 不光能用 Anthropic 自家的模型，还能接 DeepSeek。原理很简单——DeepSeek 提供了一个兼容 Anthropic API 格式的接口，把 `ANTHROPIC_BASE_URL` 指向它就行了。对 Claude Code 来说，它根本不觉得自己在跟 DeepSeek 说话，还以为是调自家的 API。


### 配置

编辑 `~/.claude/settings.json`，没这个文件就新建：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "sk-你的DeepSeek API Key",
    "ANTHROPIC_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-pro",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "API_TIMEOUT_MS": "3000000"
  }
}
```

解释一下关键的那几个：

| 变量 | 干嘛的 |
|------|--------|
| `ANTHROPIC_BASE_URL` | **核心**，指向 DeepSeek 的 Anthropic 兼容接口 |
| `ANTHROPIC_AUTH_TOKEN` | DeepSeek 的 API Key |
| `ANTHROPIC_MODEL` | 默认用哪个模型 |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | 当你敲 `--model opus` 时实际调的是这个 |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | 同理，`--model sonnet` 对应这个 |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | `--model haiku` 对应这个 |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | 关掉非必要的网络请求，省点流量 |
| `API_TIMEOUT_MS` | 超时时间（毫秒），大任务别设太短，3百万毫秒 = 50 分钟 |

### 模型怎么选

DeepSeek 目前就两个 V4 模型，覆盖一切场景：

| 模型 | 一句话 | 适合 |
|------|--------|------|
| `deepseek-v4-flash` | 284B 参数、激活 13B，经济高效 | 日常编码、读文件、简单问答 |
| `deepseek-v4-pro` | 1.6T 参数、激活 49B，旗舰推理 | 复杂重构、架构设计、debug 疑难杂症 |

两个都支持 1M 超长上下文，在模型名后加 `[1m]` 后缀即可——比如 `deepseek-v4-pro[1m]`。不过日常用不需要，默认上下文已经很大了。

### 灵活搭配：不同任务不同模型

日常用便宜的 v4-flash，碰到硬骨头切 v4-pro：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "sk-你的Key",
    "ANTHROPIC_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-pro",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash",
    "CLAUDE_CODE_SUBAGENT_MODEL": "deepseek-v4-flash",
    "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "32000",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "API_TIMEOUT_MS": "3000000"
  }
}
```

这样 `/model sonnet` 走 v4-flash，`/model opus` 走 v4-pro，不用改习惯就能省钱。

### 不想写配置文件也行

直接用环境变量一把梭：

```bash
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_AUTH_TOKEN=sk-你的Key
export ANTHROPIC_MODEL=deepseek-v4-pro
```

然后直接 `claude` 就行。不过这样没法按 opus/sonnet/haiku 区分模型，所有情况都走同一个。

### 可能踩的坑

- 如果遇到 OAuth 认证冲突，启动时加上 `--bare`：`claude --bare --settings ~/.claude/settings.json`
- `--model` 参数只能填 `sonnet`/`opus`/`haiku` 这三个别名，实际模型走配置文件里的映射
- 大任务务必把 `API_TIMEOUT_MS` 设大点，默认超时可能不够

### 回到 Anthropic

哪天想换回 Claude 官方模型，把 `ANTHROPIC_BASE_URL` 那行删掉或注释掉就行，其他不用动。或者直接另开一个终端，不加载那个 settings 文件。

---

没了。打开终端试试吧。
