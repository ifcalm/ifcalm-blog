---
title: "Ollama：在本地跑起你的第一个大模型"
date: 2026-04-18
tags: ["AI", "工具"]
draft: false
summary: "不联网、不花钱、一行命令在本地运行大语言模型"
showToc: true
tocOpen: true
ShowShareButtons: false
---

## 它能干嘛

Ollama 让你在自己的电脑上跑大语言模型。不用联网、不用 API Key、数据不出你的机器。Llama、DeepSeek、Qwen、Mistral——一行命令下载，一行命令跑起来。

适合：想玩模型但不想花钱充 API、处理敏感数据不能上云、断网环境下想有个 AI 用。

## 安装

```bash
brew install ollama
```

macOS 上装完它会在后台自动跑一个服务（端口 11434），不用手动启动。

Linux：

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

## 第一把就玩起来

```bash
# 下模型
ollama pull llama3.3

# 跑起来
ollama run llama3.3
```

然后就能直接聊天了。想退敲 `/bye`。

如果不知道下哪个，推荐这几个：

```bash
ollama pull llama3.3          # Meta 的，英文强
ollama pull qwen3              # 阿里的，中英双语
ollama pull deepseek-r1:7b     # DeepSeek 推理模型
ollama pull codellama          # 专门写代码的
ollama pull mistral            # 轻快，适合配置一般的机器
```

## 日常操作

```bash
# 看下了哪些模型
ollama list

# 一句话提问不聊天
ollama run llama3.3 "用 Go 写一个 HTTP server"

# 看模型详情
ollama show llama3.3

# 删掉不用的
ollama rm llama3.2
```

## 模型标签

模型使用 `name:tag` 格式区分版本：

```bash
ollama pull llama3.3          # :latest
ollama pull llama3.3:70b      # 70B 大杯
ollama pull deepseek-r1:7b    # 7B 小杯，配置低也能跑
```

机器内存不够就别碰 70B 了，7B-14B 日常玩玩完全够。

## 调参数

进了对话以后，`/set` 调各种参数：

```bash
>>> /set temperature 0.8     # 要不要创意，0-2，越高越放飞
>>> /set num_ctx 8192        # 上下文窗口
>>> /set num_predict 1024    # 最大输出长度
>>> /show parameters         # 看当前是什么配置
```

## 定制自己的模型

用 Modelfile 基于已有模型创建自定义模型：

```dockerfile
FROM llama3.3

SYSTEM "你是一个精通 Go 的后端工程师，回答简洁，给代码不给废话。"

PARAMETER temperature 0.7
PARAMETER num_ctx 8192
```

```bash
ollama create my-coder -f Modelfile
ollama run my-coder
```

这样你就有了一个专属的编程助手，不需要每次对话都重新交代"你是后端工程师"。

## API 接口

Ollama 提供了 HTTP API，默认 `localhost:11434`，跟 OpenAI 的格式兼容：

```bash
# Chat 风格
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.3",
  "messages": [{"role": "user", "content": "介绍一下 Go 语言"}],
  "stream": false
}'

# 直接生成
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.3",
  "prompt": "写一个快速排序",
  "stream": false
}'
```

代码里怎么用：

```python
import requests

r = requests.post("http://localhost:11434/api/chat", json={
    "model": "llama3.3",
    "messages": [{"role": "user", "content": "写一个冒泡排序"}],
    "stream": False
})
print(r.json()["message"]["content"])
```

## 局域网共享

家里有多台电脑，不想每台都下一遍模型：

```bash
# 让 Ollama 监听所有网卡
export OLLAMA_HOST=0.0.0.0:11434
```

然后其他机器就能通过 `http://你电脑IP:11434` 调用了。

几个有用的环境变量：

```bash
export OLLAMA_NUM_PARALLEL=4        # 同时处理几个请求
export OLLAMA_MAX_LOADED_MODELS=2   # 最多同时驻留几个模型在内存
```

## 模型存哪里了

- macOS: `~/.ollama/models/`
- Linux: `/usr/share/ollama/.ollama/models/`

磁盘告急时知道去哪砍。

## 配 Open WebUI

Ollama 本身只有命令行和 API，想要网页版界面就接 Open WebUI：

```bash
docker run -d -p 3000:8080 \
  -v open-webui:/app/backend/data \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

然后浏览器打开 `http://localhost:3000` 就能用了。

## 选模型参考

| 模型 | 大小 | 适合 |
|------|------|------|
| llama3.3 | 8B/70B | 通用对话，英文强 |
| deepseek-r1 | 7B-671B | 推理强，逻辑分析 |
| qwen3 | 0.6B-235B | 中文最好 |
| codellama | 7B-70B | 写代码 |
| mistral | 7B-8x22B | 快，轻量 |
| gemma3 | 1B-27B | Google 的 |
| llava | 7B/13B | 能看图的 |

## 性能贴士

- 7B 模型大概吃 8GB 内存，70B 要 40GB+
- Apple Silicon 自动用 GPU 加速，不用配
- Linux 上有 NVIDIA 卡会自动用 CUDA
- 模型默认 Q4_0 量化，精度和速度的折中

---

没了。下次断网的时候试试，你会发现本地有个 AI 跑着还挺踏实的。
