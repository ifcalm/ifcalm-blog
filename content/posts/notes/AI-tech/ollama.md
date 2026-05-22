---
title: "Ollama：在本地跑起你的第一个大模型"
date: 2026-04-18
tags: ["AI", "工具"]
draft: false
summary: "Ollama 本地大模型部署工具的使用指南"
showToc: true
tocOpen: true
ShowShareButtons: false
---

## 简介

Ollama 是一个让你在本地轻松运行大语言模型（LLM）的工具。无需云端 API，无需联网，一个命令就能下载并运行 Llama、Mistral、Qwen、DeepSeek、Gemma 等开源模型。所有数据都留在本地，适合隐私敏感场景和离线开发。

## 安装

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# 或下载 macOS 桌面应用
# https://ollama.com/download
```

安装后，Ollama 作为后台服务运行（默认端口 11434）。

```bash
# 启动服务（macOS 桌面应用会自动启动）
ollama serve
```

## 基本使用

### 拉取和运行模型

```bash
# 拉取模型
ollama pull llama3.3          # Meta Llama 3.3
ollama pull qwen3              # 阿里通义千问 3
ollama pull deepseek-r1:7b     # DeepSeek R1 7B
ollama pull mistral            # Mistral 7B
ollama pull gemma3             # Google Gemma 3
ollama pull codellama          # 代码专用模型

# 列出现有模型
ollama list

# 运行模型（交互式对话）
ollama run llama3.3
ollama run deepseek-r1:7b

# 查看模型详情
ollama show llama3.3
```

### 单次问答（非交互）

```bash
# 直接提问并退出
ollama run llama3.3 "用 Go 写一个 HTTP 服务器"

# 从文件读取 prompt
ollama run llama3.3 < prompt.txt
```

### 删除模型

```bash
ollama rm llama3.2    # 删除指定模型
ollama rm $(ollama list | tail -n +2 | awk '{print $1}')  # 删除所有模型
```

## 模型管理

### 查看已下载模型

```bash
ollama list
# 输出示例:
# NAME              ID              SIZE      MODIFIED
# llama3.3:latest   1234abcd5678    4.7 GB    2 days ago
# qwen3:latest      5678efgh9012    4.9 GB    5 days ago
```

### 模型标签和版本

Ollama 模型使用 `name:tag` 格式，类似于 Docker 镜像：

```bash
ollama pull llama3.3              # :latest 标签
ollama pull llama3.3:70b          # 70B 参数版本
ollama pull deepseek-r1:7b        # 7B 版本
```

### 自定义 Modelfile

可以基于现有模型创建自定义模型，类似 Dockerfile：

```dockerfile
# Modelfile
FROM llama3.3

# 设置系统提示词
SYSTEM "你是一个精通 Go 语言的后端工程师，回答要简洁专业。"

# 设置温度
PARAMETER temperature 0.7

# 设置最大 token
PARAMETER num_ctx 4096
```

```bash
# 创建自定义模型
ollama create my-assistant -f Modelfile

# 运行自定义模型
ollama run my-assistant
```

### 模型存储位置

- **macOS**: `~/.ollama/models/`
- **Linux**: `/usr/share/ollama/.ollama/models/`

## 常用参数配置

在运行模型时可以调整参数：

```bash
# 交互模式下设置参数
ollama run llama3.3
>>> /set temperature 0.8    # 创意度 0-2
>>> /set num_ctx 8192       # 上下文窗口大小
>>> /set num_predict 1024   # 最大生成长度
>>> /set seed 42            # 随机种子
>>> /show parameters        # 查看当前参数
```

## API 接口

Ollama 提供与 OpenAI 兼容的 API，默认监听 `http://localhost:11434`。

### Chat API

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.3",
  "messages": [
    {"role": "user", "content": "你好，请介绍一下 Go 语言的特点"}
  ],
  "stream": false
}'
```

### Generate API

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.3",
  "prompt": "用 Go 写一个快速排序算法",
  "stream": false
}'
```

### 列出模型（API）

```bash
curl http://localhost:11434/api/tags
```

### 在代码中调用

```python
# Python 示例
import requests

response = requests.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "llama3.3",
        "messages": [{"role": "user", "content": "你好"}],
        "stream": False
    }
)
print(response.json()["message"]["content"])
```

```go
// Go 示例
import "github.com/ollama/ollama/api"
// 使用官方 Go SDK 调用 Ollama
```

## 搭配 Open WebUI

Ollama 本身只有命令行和 API，配合 Open WebUI 可以获得类似 ChatGPT 的网页界面：

```bash
docker run -d -p 3000:8080 \
  -v open-webui:/app/backend/data \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

之后访问 `http://localhost:3000` 即可使用。

## 常用模型推荐

| 模型 | 参数量 | 适用场景 |
|------|-------|---------|
| llama3.3 | 70B/8B | 通用对话，Meta 旗舰 |
| deepseek-r1 | 7B-671B | 深度推理，逻辑分析 |
| qwen3 | 0.6B-235B | 中英文双语，阿里 |
| codellama | 7B-70B | 代码生成和补全 |
| mistral | 7B-8x22B | 通用推理，速度快 |
| gemma3 | 1B-27B | Google 开源模型 |
| nomic-embed-text | - | 文本嵌入向量 |
| llava | 7B/13B | 多模态（图片理解） |

## 进阶技巧

### 并发运行多个模型

```bash
# 同时启动不同实例
ollama serve --port 11435 &   # 第二个实例用不同端口
OLLAMA_HOST=0.0.0.0:11435 ollama serve &
```

### 设置环境变量

```bash
# macOS/Linux 配置
export OLLAMA_HOST=0.0.0.0:11434    # 允许局域网访问
export OLLAMA_NUM_PARALLEL=4         # 最大并行请求数
export OLLAMA_MAX_LOADED_MODELS=2    # 同时加载的模型数
```

### 性能优化

- **内存**: 7B 模型需约 8GB RAM，70B 模型需约 40GB+
- **GPU**: Apple Silicon 自动利用 Metal GPU，Linux 支持 NVIDIA CUDA
- **量化**: 模型自动使用 Q4_0 量化，需要更高精度可通过 Modelfile 指定

## 常见问题

**模型下载速度慢？**
可以设置镜像加速或手动导入 GGUF 格式模型文件。

**内存不足？**
选择更小的量化版本，如 `llama3.3:7b` 替代 `llama3.3:70b`。
