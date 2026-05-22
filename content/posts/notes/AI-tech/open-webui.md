---
title: "Open WebUI：搭建专属的 AI 对话平台"
date: 2026-04-18
tags: ["AI", "工具"]
draft: false
summary: "自托管 AI 对话网页，可接 Ollama 或任何 OpenAI 兼容的 API"
showToc: true
tocOpen: true
ShowShareButtons: false
---

## 这是什么

Open WebUI 是一个自托管的 AI 对话网页，数据全在你自己手里。最早是给 Ollama 做前端的，现在也能接 OpenAI、Claude 等各种 API。配合 Ollama，模型跑在本地，界面跑在 Open WebUI，数据不出机器，不用月费。

## 装起来

### 最简安装（Docker）

```bash
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

然后浏览器访问 `http://localhost:3000`。

### 和 Ollama 一起部署（Docker Compose）

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
    restart: always

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    volumes:
      - open-webui_data:/app/backend/data
    depends_on:
      - ollama
    restart: always

volumes:
  ollama_data:
  open-webui_data:
```

```bash
docker-compose up -d
```

## 第一步

1. 浏览器打开 `http://localhost:3000`
2. 注册账号——第一个注册的人自动是管理员
3. 如果 Ollama 在本地跑着，它会自动检测到，直接用就行不需要额外配置

## 接不同的后端

**连 Ollama（默认）：**
默认就能用，不需要配置。如果不是本机的 Ollama，在设置里改 Base URL。

**连 OpenAI：**
在设置填 API Key 和 Base URL（默认 `https://api.openai.com/v1`）。

**连 Claude：**
填 Anthropic API Key 就行。注意 Anthropic 的 API 地址不是 OpenAI 兼容格式，在设置里找到 Anthropic 的选项单填。

**连其他兼容 OpenAI 格式的服务：**
填 Base URL + API Key，任何 `/v1/chat/completions` 端点都能接。

## 日常会用到的功能

### 对话

- 同一个聊天里随时切换模型——比如先让 llama 写代码，再让 deepseek 审查
- Markdown 渲染、代码高亮、数学公式都支持
- 历史记录可搜索
- 编辑已发的消息，重新生成回复
- 从任意一条消息分叉出新对话

### 上传文档提问（RAG）

有时候你有一堆 PDF 或者代码文件，想问"这个文档里讲了什么"或"这个项目的架构是什么"：

1. 点"文档"上传 PDF、TXT、MD、CSV、代码文件等
2. Open WebUI 自动把内容向量化存起来
3. 聊天时关联文档，AI 回答会引用文档内容

比手动翻文件快多了。

### 模型管理

管理面板里能直接下载 Ollama 模型、删掉不用的、调每个模型的参数（temperature、context window、system prompt）。

### 提示词模板

把常用的 prompt 存成模板，下次一点就应用。比如"你是一个 SRE 工程师，请分析这段日志"，不用每次重新打。

### 多用户

可以开多个账号，控制谁能用哪些模型。家里或小团队共享一台机器的时候有用——你老婆用 llama 聊天，你用 deepseek 写代码，互不干扰。

## 进阶配置

### 关键环境变量

| 变量 | 干嘛的 | 默认值 |
|------|--------|--------|
| `OLLAMA_BASE_URL` | Ollama 在哪 | `http://localhost:11434` |
| `WEBUI_SECRET_KEY` | 加密会话的 | 自动生成 |
| `ENABLE_SIGNUP` | 允不允许新注册 | `true` |
| `WEBUI_NAME` | 页面标题 | `Open WebUI` |
| `DEFAULT_USER_ROLE` | 新用户默认角色 | `pending` |

### 关掉公开注册

不想让别人注册：

```bash
docker run ... -e WEBUI_AUTH=true ...
```

### 配 HTTPS

生产环境前挂一个 Nginx：

```nginx
server {
    listen 443 ssl;
    server_name chat.yourdomain.com;

    ssl_certificate     /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### 备份

数据在 Docker volume 里：

```bash
# 备份
docker run --rm -v open-webui:/data -v $(pwd):/backup alpine \
  tar czf /backup/open-webui-backup.tar.gz -C /data .

# 恢复
docker run --rm -v open-webui:/data -v $(pwd):/backup alpine \
  tar xzf /backup/open-webui-backup.tar.gz -C /data
```

## Web 搜索

可以接搜索引擎让 AI 查实时信息：

- SearXNG（自托管，推荐）
- Google PSE
- Brave Search

在管理面板 → 设置 → Web Search 配。

## 手机上用

1. 确保服务监听在 `0.0.0.0`（Docker 默认就是这样）
2. 手机浏览器访问 `http://<你电脑IP>:3000`
3. Safari/Chrome 里点"添加到主屏幕"

Open WebUI 支持 PWA，可以安装到桌面作为独立应用使用。

## 常见组合

| 工具 | 角色 |
|------|------|
| Ollama | 模型引擎 |
| Open WebUI | 聊天界面 |
| Claude Code / Codex CLI | 终端编程 Agent |

Ollama + Open WebUI 的组合可以搭建一套完全本地化的 AI 对话系统。

---

没了。如果你的 Ollama 已经在跑了，一个 Docker 命令就能把界面搭起来，试试看。
