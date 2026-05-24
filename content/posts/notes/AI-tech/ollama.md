---
title: "Ollama 详细使用手册：本地大模型安装、运行、API、Open WebUI 与常见问题"
date: 2026-05-24
tags: ["Ollama", "AI 工具"]
draft: false
summary: "Ollama 完整使用手册，覆盖安装配置、模型管理、API 调用、OpenAI/Anthropic 兼容接口、Open WebUI 配合、Modelfile 自定义与常见问题排查。"
showToc: true
tocOpen: false
---

## 一、Ollama 是什么？

Ollama 是一个用于在本地运行大语言模型的工具。它可以帮助你下载、运行、管理和调用开源大模型，也可以通过本地 HTTP API 提供服务。

可以把 Ollama 理解为：

```text
本地大模型运行器 + 模型管理工具 + 本地 API 服务
```

它适合这些场景：

- 在本机运行大模型
- 离线或半离线使用 AI
- 学习和测试开源模型
- 给 Open WebUI 提供本地模型能力
- 给应用程序提供本地 LLM API
- 做 RAG、Embedding、代码助手、本地知识库实验
- 给 Claude Code、Codex、OpenClaw 等工具提供模型后端

核心命令是：

```bash
ollama
```

默认本地 API 地址是：

```text
http://localhost:11434
```

Ollama 的 API 默认路径是：

```text
http://localhost:11434/api
```

---

## 二、适合谁使用？

Ollama 很适合以下用户：

| 用户类型 | 使用价值 |
|---|---|
| 开发者 | 本地调试模型、调用 API、构建 AI 应用 |
| 学习者 | 低门槛体验开源模型 |
| 写作者 | 离线辅助写作、摘要、润色 |
| 企业内网用户 | 在受控环境中运行模型 |
| AI 工具用户 | 给 Open WebUI、Claude Code、Codex 等工具提供模型后端 |

如果你的电脑内存较小，建议先从小模型开始，例如 1B、3B、7B 量级模型。

如果你的电脑是 24GB 内存以上的 Apple Silicon，可以尝试 7B、9B、14B，部分量化后的 20B/30B 模型也可以试，但速度和稳定性要看具体模型、量化格式和上下文长度。

---

## 三、安装 Ollama

### 1. macOS 官方安装方式

官方推荐方式是下载 macOS App，安装后会提供图形菜单和 `ollama` CLI。

也可以使用安装脚本：

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

macOS 官方文档要求 macOS Sonoma 14 或更新版本，并说明 Apple M 系列支持 CPU 和 GPU，x86 Mac 主要是 CPU 支持。

---

### 2. 使用 Homebrew 安装 CLI 版本

如果你习惯使用 Homebrew，可以安装 formula：

```bash
brew install ollama
```

查看版本：

```bash
ollama --version
```

启动服务：

```bash
ollama serve
```

或者通过 Homebrew 服务启动：

```bash
brew services start ollama
```

停止服务：

```bash
brew services stop ollama
```

重启服务：

```bash
brew services restart ollama
```

查看服务状态：

```bash
brew services list
```

---

### 3. 使用 Homebrew 安装 macOS App

如果想安装图形化 App：

```bash
brew install --cask ollama-app
```

这类方式更接近从官网下载 `.dmg` 后拖到 Applications 目录。

---

### 4. Docker 安装方式

CPU 版本：

```bash
docker run -d \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama
```

Linux + NVIDIA GPU：

```bash
docker run -d \
  --gpus=all \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama
```

运行模型：

```bash
docker exec -it ollama ollama run llama3.2
```

注意：macOS Docker Desktop 通常无法把 Apple GPU 直通给容器，所以 Mac 上更推荐直接安装 Ollama App 或 CLI，而不是用 Docker 跑模型。

---

## 四、常用命令速查

| 场景 | 命令 |
|---|---|
| 查看帮助 | `ollama --help` |
| 查看版本 | `ollama --version` |
| 启动服务 | `ollama serve` |
| 运行模型 | `ollama run llama3.2` |
| 下载模型 | `ollama pull llama3.2` |
| 查看本地模型 | `ollama list` 或 `ollama ls` |
| 查看运行中模型 | `ollama ps` |
| 停止模型 | `ollama stop llama3.2` |
| 删除模型 | `ollama rm llama3.2` |
| 查看模型信息 | `ollama show llama3.2` |
| 查看模型 Modelfile | `ollama show --modelfile llama3.2` |
| 复制模型名 | `ollama cp llama3.2 my-llama` |
| 创建自定义模型 | `ollama create my-model -f Modelfile` |
| 登录 Ollama | `ollama signin` |
| 退出登录 | `ollama signout` |
| 推送模型 | `ollama push username/model` |
| 启动集成配置 | `ollama launch` |
| 启动 Claude Code 集成 | `ollama launch claude` |
| 启动 Codex 集成 | `ollama launch codex` |

---

## 五、第一次运行模型

### 1. 下载并运行模型

最简单方式：

```bash
ollama run llama3.2
```

如果本地没有该模型，Ollama 会自动下载，然后进入交互式对话。

也可以先下载：

```bash
ollama pull llama3.2
```

再运行：

```bash
ollama run llama3.2
```

---

### 2. 直接带问题运行

```bash
ollama run llama3.2 "用一句话解释什么是区块链"
```

---

### 3. 多行输入

进入交互模式后，如果要输入多行内容，可以使用三引号：

```text
>>> """
请帮我总结下面这段内容：

第一段……
第二段……
"""
```

---

### 4. 退出模型

在交互模式中输入：

```text
/bye
```

或者使用快捷键：

```text
Ctrl + D
```

如果只是想中断当前输出，可以使用：

```text
Ctrl + C
```

---

## 六、模型管理

### 1. 查看已安装模型

```bash
ollama list
```

或者：

```bash
ollama ls
```

输出通常包含：

```text
NAME              ID              SIZE      MODIFIED
llama3.2:latest   xxxx            2.0 GB    2 days ago
```

字段说明：

| 字段 | 含义 |
|---|---|
| `NAME` | 模型名称和 tag |
| `ID` | 模型 ID |
| `SIZE` | 模型大小 |
| `MODIFIED` | 最近修改时间 |

---

### 2. 下载模型

```bash
ollama pull qwen3
```

指定 tag：

```bash
ollama pull qwen3:8b
```

模型名称一般格式是：

```text
model:tag
```

如果不写 tag，通常默认使用：

```text
latest
```

---

### 3. 查看运行中的模型

```bash
ollama ps
```

这个命令可以看到哪些模型正在内存中，以及使用 CPU/GPU 的情况。

如果看到类似：

```text
100% GPU
```

说明模型完全加载到了 GPU。

如果看到：

```text
48%/52% CPU/GPU
```

说明模型部分加载在 CPU，部分加载在 GPU。

---

### 4. 停止运行中的模型

```bash
ollama stop llama3.2
```

如果你发现模型占用内存，可以先查看：

```bash
ollama ps
```

再停止对应模型：

```bash
ollama stop 模型名
```

---

### 5. 删除模型

```bash
ollama rm llama3.2
```

删除后会释放对应模型文件占用的磁盘空间。

---

### 6. 查看模型详情

```bash
ollama show llama3.2
```

查看模型的 Modelfile：

```bash
ollama show --modelfile llama3.2
```

这个命令很适合学习一个模型的模板、参数和系统提示配置。

---

### 7. 复制模型名称

```bash
ollama cp llama3.2 my-llama
```

这个命令常用于兼容某些工具默认识别的模型名称。

例如一些 OpenAI 兼容工具默认使用：

```text
gpt-3.5-turbo
```

可以复制一个本地模型名：

```bash
ollama cp llama3.2 gpt-3.5-turbo
```

这样 OpenAI 兼容工具可以把 `gpt-3.5-turbo` 当成本地 Ollama 模型调用。

---

## 七、选择模型的建议

模型选择和你的机器内存、任务类型有很大关系。

### 1. 按内存粗略选择

| 内存 | 建议模型 |
|---|---|
| 8GB | 1B、3B 小模型 |
| 16GB | 3B、7B、8B 量化模型 |
| 24GB | 7B、8B、9B、14B，部分 20B/30B 量化模型 |
| 32GB+ | 14B、20B、30B 甚至更大模型 |
| 64GB+ | 可尝试 30B、70B 量化模型 |

这只是经验估计，实际能否流畅运行还取决于：

- 模型参数规模
- 量化格式
- 上下文长度
- 是否使用 GPU
- 同时运行的应用数量
- 模型本身结构

---

### 2. 按任务选择

| 任务 | 模型方向 |
|---|---|
| 日常聊天 | llama、gemma、qwen 等通用模型 |
| 代码生成 | qwen coder、deepseek coder、codellama 等代码模型 |
| 中文理解 | qwen、deepseek、glm 等中文能力较强的模型 |
| 推理分析 | deepseek-r1、qwen reasoning、gpt-oss 等推理模型 |
| Embedding | nomic-embed-text、embeddinggemma 等嵌入模型 |
| 图像理解 | 支持 vision 的多模态模型，例如 gemma3 等 |

---

### 3. 不建议一开始就下载大模型

新手建议先用：

```bash
ollama run llama3.2
```

或者：

```bash
ollama run qwen3
```

确认 Ollama 工作正常后，再尝试更大的模型。

---

## 八、运行参数与上下文长度

### 1. 在交互模式中设置参数

进入模型后，可以使用：

```text
/set parameter temperature 0.7
/set parameter num_ctx 8192
```

常见参数：

| 参数 | 含义 |
|---|---|
| `temperature` | 随机性，越高越发散，越低越稳定 |
| `num_ctx` | 上下文窗口大小 |
| `top_p` | 采样范围控制 |
| `top_k` | 候选 token 数量控制 |
| `repeat_penalty` | 重复惩罚 |

适合代码任务的设置：

```text
/set parameter temperature 0.2
```

适合创意写作：

```text
/set parameter temperature 0.8
```

---

### 2. 用环境变量设置默认上下文

例如设置 8K 上下文：

```bash
OLLAMA_CONTEXT_LENGTH=8192 ollama serve
```

如果你通过 macOS App 运行 Ollama，需要用 `launchctl` 设置环境变量。

例如：

```bash
launchctl setenv OLLAMA_CONTEXT_LENGTH "8192"
```

然后重启 Ollama App。

---

### 3. API 中设置上下文

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "请解释什么是上下文窗口",
  "options": {
    "num_ctx": 8192
  }
}'
```

---

### 4. 上下文越大越好吗？

不一定。

上下文越大：

- 占用内存越多
- 速度可能更慢
- 首 token 延迟可能更高
- 部分模型效果不一定提升

建议：

```text
日常聊天：4096 或 8192
代码项目分析：8192、16384 或更高
长文档摘要：根据模型能力逐步提高
```

---

## 九、模型常驻与释放内存

Ollama 默认会把模型在内存中保留一段时间，以便后续请求更快。

### 1. 查看当前加载模型

```bash
ollama ps
```

---

### 2. 手动停止模型

```bash
ollama stop llama3.2
```

---

### 3. API 中设置 keep_alive

让模型一直保留：

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "keep_alive": -1
}'
```

请求完成后立即释放：

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "hello",
  "keep_alive": 0
}'
```

保留 10 分钟：

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "hello",
  "keep_alive": "10m"
}'
```

---

## 十、Modelfile：自定义模型

`Modelfile` 是 Ollama 用来创建自定义模型的配置文件。

它可以设置：

- 基础模型
- 系统提示词
- 模型参数
- Prompt 模板
- 示例消息
- License
- LoRA Adapter

---

### 1. 创建一个简单 Modelfile

创建文件：

```bash
mkdir -p ~/ollama-models/my-assistant
cd ~/ollama-models/my-assistant
vim Modelfile
```

写入：

```text
FROM llama3.2

PARAMETER temperature 0.7
PARAMETER num_ctx 8192

SYSTEM """
你是一个中文技术助手，回答要清晰、务实、结构化。
当用户询问命令行、Go、macOS、Cloudflare、AI 工具时，请优先给出可执行步骤和命令示例。
"""
```

创建模型：

```bash
ollama create my-assistant -f Modelfile
```

运行：

```bash
ollama run my-assistant
```

---

### 2. 查看已有模型的 Modelfile

```bash
ollama show --modelfile llama3.2
```

可以把输出复制出来，在此基础上改成自己的模型配置。

---

### 3. 适合你的个人助手示例

```text
FROM qwen3

PARAMETER temperature 0.3
PARAMETER num_ctx 8192

SYSTEM """
你是我的中文技术助手。
回答风格：
1. 先给结论，再给步骤。
2. 命令必须可以复制执行。
3. 涉及 Go 单元测试时，优先使用 table-driven tests。
4. 涉及安全问题时，提醒日志敏感信息、路径穿越、命令注入、密钥泄露。
5. 涉及 macOS 工具时，优先给出 Homebrew 与终端命令。
"""
```

创建：

```bash
ollama create ifcalm-helper -f Modelfile
```

运行：

```bash
ollama run ifcalm-helper
```

---

## 十一、Ollama API 使用

Ollama 启动后会提供本地 API。

默认地址：

```text
http://localhost:11434/api
```

### 1. 检查服务是否运行

```bash
curl http://localhost:11434
```

如果返回：

```text
Ollama is running
```

说明服务正常。

---

### 2. Generate API

适合单轮生成：

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "请用一句话解释什么是 API",
  "stream": false
}'
```

如果不设置：

```json
"stream": false
```

默认一般会流式返回多行 JSON。

---

### 3. Chat API

适合多轮对话：

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    {
      "role": "user",
      "content": "请解释什么是 Redis"
    }
  ],
  "stream": false
}'
```

带上下文：

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    {
      "role": "system",
      "content": "你是一个中文后端开发助手"
    },
    {
      "role": "user",
      "content": "请解释 Redis Sentinel 的作用"
    }
  ],
  "stream": false
}'
```

---

### 4. Embedding API

先拉取 embedding 模型：

```bash
ollama pull embeddinggemma
```

调用：

```bash
curl http://localhost:11434/api/embed -d '{
  "model": "embeddinggemma",
  "input": "Ollama 可以在本地运行大语言模型"
}'
```

Embedding 常用于：

- 语义搜索
- RAG 知识库
- 文档向量化
- 相似度匹配

---

### 5. API 查看本地模型

```bash
curl http://localhost:11434/api/tags
```

---

### 6. API 查看运行中模型

```bash
curl http://localhost:11434/api/ps
```

---

### 7. API 查看版本

```bash
curl http://localhost:11434/api/version
```

---

## 十二、OpenAI 兼容 API

Ollama 也支持 OpenAI 兼容接口，默认地址：

```text
http://localhost:11434/v1
```

### 1. Chat Completions 示例

```bash
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2",
    "messages": [
      {
        "role": "user",
        "content": "请解释什么是 Docker"
      }
    ]
  }'
```

---

### 2. Python OpenAI SDK 调用 Ollama

安装：

```bash
pip install openai
```

示例：

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # 必填，但本地 Ollama 会忽略
)

response = client.chat.completions.create(
    model="llama3.2",
    messages=[
        {"role": "user", "content": "请用三句话介绍 Ollama"}
    ],
)

print(response.choices[0].message.content)
```

---

### 3. 为什么 OpenAI 兼容接口很有用？

很多工具默认支持 OpenAI API，只要把：

```text
base_url
```

改成：

```text
http://localhost:11434/v1
```

就可以让它们调用本地 Ollama 模型。

例如：

- 自己写的 Python/Node 应用
- 一些 AI IDE 插件
- 一些聊天 UI
- 一些 RAG 框架
- LangChain / LlamaIndex 等框架

---

## 十三、Anthropic 兼容 API 与 Claude Code

Ollama 也提供 Anthropic Messages API 兼容能力，可用于 Claude Code 等工具。

### 1. 快速方式

```bash
ollama launch claude
```

这个命令会引导你选择模型、自动配置 Claude Code 并启动。

只配置不启动：

```bash
ollama launch claude --config
```

指定模型：

```bash
ollama launch claude --model qwen3-coder
```

---

### 2. 手动配置 Claude Code 使用 Ollama

先下载模型：

```bash
ollama pull qwen3-coder
```

然后运行：

```bash
ANTHROPIC_AUTH_TOKEN=ollama \
ANTHROPIC_BASE_URL=http://localhost:11434 \
claude --model qwen3-coder
```

说明：

| 环境变量 | 含义 |
|---|---|
| `ANTHROPIC_AUTH_TOKEN=ollama` | 必填，但本地 Ollama 会忽略 |
| `ANTHROPIC_BASE_URL=http://localhost:11434` | 指向本地 Ollama Anthropic 兼容接口 |
| `--model qwen3-coder` | 指定本地模型 |

---

### 3. 写成 zsh 函数

编辑：

```bash
vim ~/.zshrc
```

添加：

```bash
cc-ollama() {
  ANTHROPIC_AUTH_TOKEN=ollama \
  ANTHROPIC_BASE_URL=http://localhost:11434 \
  claude --model "${1:-qwen3-coder}" "${@:2}"
}
```

加载：

```bash
source ~/.zshrc
```

使用默认模型：

```bash
cc-ollama
```

指定模型：

```bash
cc-ollama qwen3-coder
```

带任务启动：

```bash
cc-ollama qwen3-coder "请分析这个项目结构"
```

---

## 十四、与 Open WebUI 配合

Open WebUI 是一个常见的本地 Web 聊天界面，可以连接 Ollama。

### 1. 安装 Open WebUI

如果 Ollama 运行在本机，使用 Docker：

```bash
docker run -d \
  -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

访问：

```text
http://localhost:3000
```

---

### 2. 如果 Ollama 在另一台机器

```bash
docker run -d \
  -p 3000:8080 \
  -e OLLAMA_BASE_URL=http://你的服务器IP:11434 \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

---

### 3. 常见连接问题

如果 Open WebUI 连接不上 Ollama，重点检查：

```bash
curl http://localhost:11434
```

以及 Docker 容器内能否访问主机：

```bash
docker exec -it open-webui bash
curl http://host.docker.internal:11434
```

如果 Ollama 只监听 `127.0.0.1`，容器可能无法访问。可以考虑让 Ollama 监听：

```text
0.0.0.0:11434
```

macOS App 设置：

```bash
launchctl setenv OLLAMA_HOST "0.0.0.0:11434"
```

然后重启 Ollama App。

注意：暴露到局域网前要考虑安全风险，不建议直接暴露到公网。

---

## 十五、网络访问与远程调用

### 1. 默认只监听本机

Ollama 默认绑定：

```text
127.0.0.1:11434
```

这意味着只有本机可以访问。

---

### 2. 允许局域网访问

macOS App 方式：

```bash
launchctl setenv OLLAMA_HOST "0.0.0.0:11434"
```

然后重启 Ollama App。

CLI 方式：

```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

局域网其他机器访问：

```bash
curl http://你的Mac局域网IP:11434
```

---

### 3. 安全提醒

Ollama 本地服务默认没有复杂认证机制。

不要直接暴露到公网。

如果需要远程访问，建议使用：

- VPN
- 内网
- 反向代理加认证
- Cloudflare Tunnel + Access
- 防火墙限制来源 IP

---

### 4. Cloudflare Tunnel 示例

```bash
cloudflared tunnel --url http://localhost:11434 --http-host-header="localhost:11434"
```

只建议在明确知道安全边界的情况下使用，并配合访问控制。

---

## 十六、代理与下载问题

如果下载模型失败，可能是网络或代理问题。

### 1. 使用 HTTPS_PROXY

```bash
HTTPS_PROXY=http://127.0.0.1:7890 ollama pull llama3.2
```

如果是启动服务时需要代理：

```bash
HTTPS_PROXY=http://127.0.0.1:7890 ollama serve
```

macOS App 方式：

```bash
launchctl setenv HTTPS_PROXY "http://127.0.0.1:7890"
```

然后重启 Ollama App。

---

### 2. 避免误设 HTTP_PROXY

Ollama 拉取模型主要使用 HTTPS。官方 FAQ 特别提醒，不要随意设置 `HTTP_PROXY`，因为它可能影响客户端连接本地 Ollama server。

建议优先使用：

```bash
HTTPS_PROXY
```

---

## 十七、模型存储位置与磁盘管理

### 1. 默认模型位置

macOS：

```text
~/.ollama/models
```

Linux：

```text
/usr/share/ollama/.ollama/models
```

Windows：

```text
C:\Users\%username%\.ollama\models
```

---

### 2. 查看磁盘占用

```bash
du -sh ~/.ollama
du -sh ~/.ollama/models
```

查看每个目录大小：

```bash
du -h -d 1 ~/.ollama/models
```

---

### 3. 删除不用的模型

```bash
ollama list
ollama rm 不需要的模型
```

---

### 4. 更改模型存储位置

如果你的系统盘空间不够，可以设置：

```bash
OLLAMA_MODELS=/Volumes/ExternalDisk/ollama-models ollama serve
```

macOS App 方式：

```bash
launchctl setenv OLLAMA_MODELS "/Volumes/ExternalDisk/ollama-models"
```

然后重启 Ollama App。

---

## 十八、日志与排错

### 1. macOS 日志位置

Ollama macOS 文档说明常见位置：

```text
~/.ollama/logs
```

常见日志：

```text
~/.ollama/logs/app.log
~/.ollama/logs/server.log
```

查看最近日志：

```bash
tail -f ~/.ollama/logs/server.log
```

---

### 2. 检查服务是否正常

```bash
curl http://localhost:11434
```

查看端口：

```bash
lsof -i :11434
```

或者：

```bash
netstat -an | grep 11434
```

---

### 3. 常见问题：端口被占用

报错类似：

```text
address already in use
```

查找进程：

```bash
lsof -i :11434
```

结束进程：

```bash
kill -9 <PID>
```

更稳妥方式是通过 Ollama App 菜单退出，或者：

```bash
brew services stop ollama
```

---

### 4. 常见问题：模型运行很慢

可能原因：

- 模型太大
- 内存不足
- 没有使用 GPU
- 上下文窗口太大
- 同时运行了多个模型
- Docker 环境没有 GPU 加速
- 电脑处于低电量或节能模式

排查：

```bash
ollama ps
```

查看模型是否在 GPU 上。

---

### 5. 常见问题：内存占用高

查看运行中模型：

```bash
ollama ps
```

停止不用的模型：

```bash
ollama stop 模型名
```

或者等待模型自动释放。

---

## 十九、本地隐私与云功能

本地运行模型时，Ollama 的模型推理在本机完成。

如果使用 Ollama Cloud 模型或相关云功能，请注意数据会发送到云端服务处理。

如果你希望禁用云功能，可以创建：

```bash
vim ~/.ollama/server.json
```

写入：

```json
{
  "disable_ollama_cloud": true
}
```

或者设置环境变量：

```bash
OLLAMA_NO_CLOUD=1 ollama serve
```

macOS App：

```bash
launchctl setenv OLLAMA_NO_CLOUD "1"
```

然后重启 Ollama。

---

## 二十、常用场景示例

### 1. 英文学习助手

```bash
ollama run llama3.2 "请解释 entrepreneur 的发音、含义，并给 3 个例句"
```

---

### 2. Go 代码解释

```bash
cat main.go | ollama run qwen3 "请解释这段 Go 代码的作用，并指出潜在问题"
```

---

### 3. 日志分析

```bash
cat error.log | ollama run qwen3 "请分析这个错误日志，给出可能原因和排查步骤"
```

---

### 4. Git diff 审查

```bash
git diff | ollama run qwen3 "请审查这次代码变更，重点关注空指针、并发、安全和测试覆盖"
```

---

### 5. 生成 Markdown 文档

```bash
ollama run qwen3 "请生成一份 macOS say 命令使用手册，Markdown 格式"
```

---

### 6. RAG 知识库基础流程

一个简单 RAG 流程通常是：

```text
文档切块 -> 生成 embedding -> 写入向量数据库 -> 用户提问 -> 检索相关片段 -> 拼接上下文 -> 调用模型回答
```

Ollama 可以承担两部分：

```text
Embedding 模型：生成向量
Chat 模型：基于检索结果回答
```

---

## 二十一、推荐的日常工作流

### 1. 第一次使用

```bash
brew install ollama
ollama serve
ollama run llama3.2
```

---

### 2. 每天使用

```bash
ollama list
ollama ps
ollama run qwen3
```

---

### 3. 磁盘清理

```bash
ollama list
ollama rm 不需要的模型
du -sh ~/.ollama/models
```

---

### 4. 开发 API 应用

```bash
ollama serve
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    {"role": "user", "content": "hello"}
  ],
  "stream": false
}'
```

---

### 5. 使用 Web UI

```bash
docker run -d \
  -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

打开：

```text
http://localhost:3000
```

---

## 二十二、推荐保留的快捷命令

可以在 `~/.zshrc` 加一些快捷函数。

### 1. 快速查看状态

```bash
ollama-status() {
  echo "== Ollama version =="
  ollama --version
  echo
  echo "== Local models =="
  ollama list
  echo
  echo "== Running models =="
  ollama ps
}
```

使用：

```bash
ollama-status
```

---

### 2. 快速分析日志

```bash
ollama-log-analyze() {
  local model="${1:-qwen3}"
  local file="$2"

  if [ -z "$file" ]; then
    echo "Usage: ollama-log-analyze [model] <log-file>"
    return 1
  fi

  cat "$file" | ollama run "$model" "请分析这个日志，输出根因、影响范围和排查建议。"
}
```

使用：

```bash
ollama-log-analyze qwen3 error.log
```

---

### 3. 快速代码审查

```bash
ollama-review() {
  local model="${1:-qwen3}"
  git diff | ollama run "$model" "请审查当前 git diff，重点关注 bug、安全、兼容性和测试覆盖。"
}
```

使用：

```bash
ollama-review
```

---

## 二十三、卸载 Ollama

### 1. Homebrew formula

```bash
brew services stop ollama
brew uninstall ollama
```

---

### 2. Homebrew cask App

```bash
brew uninstall --cask ollama-app
```

---

### 3. 官方 macOS App 完全清理

谨慎执行：

```bash
sudo rm -rf /Applications/Ollama.app
sudo rm -f /usr/local/bin/ollama
rm -rf ~/Library/Application\ Support/Ollama
rm -rf ~/Library/Saved\ Application\ State/com.electron.ollama.savedState
rm -rf ~/Library/Caches/com.electron.ollama
rm -rf ~/Library/Caches/ollama
rm -rf ~/Library/WebKit/com.electron.ollama
rm -rf ~/.ollama
```

注意：

```bash
rm -rf ~/.ollama
```

会删除本地模型、配置和日志。

---

## 二十四、常见问题速查

### 1. Ollama 是否会自动把提示词发到云端？

本地模型推理在本机进行。使用 cloud 模型或云功能时，请按云服务规则理解数据流。如果想更保守，可以禁用云功能。

---

### 2. 为什么模型下载很慢？

可能是网络、代理或模型较大。可以设置：

```bash
HTTPS_PROXY=http://127.0.0.1:7890 ollama pull 模型名
```

---

### 3. 为什么电脑很卡？

可能是模型过大或多个模型同时常驻内存。

```bash
ollama ps
ollama stop 模型名
```

---

### 4. 为什么 Open WebUI 看不到模型？

先确认本机 Ollama 正常：

```bash
ollama list
curl http://localhost:11434
```

再确认 Docker 容器能访问 Ollama：

```bash
docker exec -it open-webui bash
curl http://host.docker.internal:11434
```

---

### 5. 如何让其他设备访问我的 Ollama？

设置：

```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

或 macOS App：

```bash
launchctl setenv OLLAMA_HOST "0.0.0.0:11434"
```

然后重启 Ollama。

注意不要直接暴露到公网。

---

### 6. 如何查看模型是否使用 GPU？

```bash
ollama ps
```

查看 `PROCESSOR` 列。

---

### 7. 模型文件在哪里？

macOS：

```text
~/.ollama/models
```

---

### 8. 如何更换模型存储目录？

```bash
OLLAMA_MODELS=/path/to/models ollama serve
```

macOS App：

```bash
launchctl setenv OLLAMA_MODELS "/path/to/models"
```

然后重启 Ollama。

---

## 二十五、个人建议

如果你主要是在 Mac 上学习和开发，我建议按这个顺序掌握：

```text
1. ollama run
2. ollama pull / list / ps / stop / rm
3. ollama serve
4. /api/chat 和 /api/generate
5. Open WebUI
6. Modelfile
7. OpenAI / Anthropic 兼容接口
8. Claude Code / Codex / OpenClaw 集成
```

最常用的一组命令：

```bash
ollama serve
ollama run qwen3
ollama list
ollama ps
ollama stop qwen3
ollama rm qwen3
curl http://localhost:11434/api/chat -d '{"model":"qwen3","messages":[{"role":"user","content":"hello"}],"stream":false}'
```

Ollama 的核心价值是：让本地模型像一个稳定的本地服务一样运行起来。命令行适合快速测试，API 适合开发集成，Open WebUI 适合日常聊天和管理，自定义 Modelfile 适合沉淀个人助手。

---

## 参考资料

- Ollama 官网：https://ollama.com/
- Ollama 下载：https://ollama.com/download
- Ollama CLI Reference：https://docs.ollama.com/cli
- Ollama API Introduction：https://docs.ollama.com/api/introduction
- Ollama Generate API：https://docs.ollama.com/api/generate
- Ollama Chat API：https://docs.ollama.com/api/chat
- Ollama Embedding API：https://docs.ollama.com/api/embed
- Ollama OpenAI Compatibility：https://docs.ollama.com/api/openai-compatibility
- Ollama Anthropic Compatibility：https://docs.ollama.com/api/anthropic-compatibility
- Ollama Modelfile Reference：https://docs.ollama.com/modelfile
- Ollama macOS 文档：https://docs.ollama.com/macos
- Ollama Docker 文档：https://docs.ollama.com/docker
- Ollama FAQ：https://docs.ollama.com/faq
- Ollama GitHub：https://github.com/ollama/ollama
- Open WebUI Quick Start：https://docs.openwebui.com/getting-started/quick-start/
