---
title: "Open WebUI：搭建专属的 AI 对话平台"
date: 2026-04-18
tags: ["AI", "工具"]
draft: false
summary: "Open WebUI 自托管 AI 对话界面的使用指南"
showToc: true
tocOpen: true
ShowShareButtons: false
---

## 简介

Open WebUI（原 Ollama WebUI）是一个自托管的 AI 对话平台，提供类似 ChatGPT 的完整网页界面。它最初为 Ollama 设计，但现已支持 OpenAI API 兼容的所有后端，包括 Claude API、vLLM、Ollama 等。功能涵盖对话、RAG（文档检索增强生成）、模型管理、用户权限等。

## 安装

### Docker 部署（推荐，搭配 Ollama）

```bash
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

如果 Ollama 安装在同一台机器上，容器内通过 `host.docker.internal:11434` 访问 Ollama API。

### Docker Compose 部署（含 Ollama）

```yaml
# docker-compose.yml
version: '3.8'
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

### 直接安装

```bash
# 需要 Python 3.11+ 和 Node.js
git clone https://github.com/open-webui/open-webui.git
cd open-webui

# 后端
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080

# 前端
cd frontend
npm install
npm run dev
```

## 基本使用

安装后访问 `http://localhost:3000`。

### 初次设置

1. **注册管理员账号** - 第一个注册的用户自动成为管理员
2. **配置模型连接** - 在设置中添加 Ollama 或其他 API 后端
3. **开始对话** - 选择模型，输入消息

### 连接不同后端

**Ollama（默认）:**
```
OLLAMA_BASE_URL=http://localhost:11434
```

**OpenAI API:**
在设置中添加 API Key 和 Base URL（如 `https://api.openai.com/v1`）。

**Claude API（Anthropic）:**
在设置中填写 Anthropic API Key。注意 Anthropic 的 URL 是 `https://api.anthropic.com`，不是 OpenAI 兼容格式。

**其他兼容 OpenAI 格式的服务:**
填写 Base URL 和 API Key 即可，兼容任何 `/v1/chat/completions` 端点。

## 核心功能

### 对话界面

- **多模型切换** - 同一对话中切换不同模型
- **Markdown 渲染** - 代码高亮、表格、数学公式
- **对话历史** - 完整的聊天记录管理和搜索
- **消息编辑** - 编辑历史消息重新生成回复
- **分支对话** - 从任意消息分叉出新对话

### RAG（文档检索增强生成）

上传文档后，AI 可以基于文档内容回答问题：

1. 点击"文档"上传 PDF、TXT、MD 等文件
2. 系统自动向量化并存入数据库
3. 对话时选择关联的文档，AI 回答会引用文档内容

支持的文件格式：PDF、TXT、Markdown、CSV、JSON、代码文件等。

### 模型管理

在管理面板中：

- **下载模型**: 直接从 Ollama 拉取新模型
- **删除模型**: 清理不再使用的模型
- **模型参数**: 调整 temperature、context window、system prompt 等 per-model 设置

### 提示词(Prompt)管理

可以创建和管理预设提示词模板：

- 保存常用 prompt 为模板
- 对话时一键应用模板
- 支持变量插值

### 多用户管理

- **角色系统**: 管理员、普通用户（默认注册开启后可关闭）
- **权限控制**: 控制谁能使用哪些模型
- **使用统计**: 查看用户的对话和 token 消耗

## 高级配置

### 环境变量

关键环境变量，在 Docker 启动时通过 `-e` 设置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OLLAMA_BASE_URL` | Ollama 服务地址 | `http://localhost:11434` |
| `OPENAI_API_BASE_URL` | OpenAI API 地址 | `https://api.openai.com/v1` |
| `WEBUI_SECRET_KEY` | 会话加密密钥 | 随机 |
| `ENABLE_SIGNUP` | 允许注册 | `true` |
| `DEFAULT_MODELS` | 默认可见模型 | 空（全部） |
| `DEFAULT_USER_ROLE` | 新用户默认角色 | `pending` |
| `WEBUI_NAME` | 页面标题 | `Open WebUI` |

### 关闭公开注册

```bash
docker run ... -e WEBUI_AUTH=true ...
```

### HTTPS 配置

生产环境建议前置 Nginx/Caddy 提供 HTTPS：

```nginx
# Nginx 反向代理示例
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
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 数据备份

所有数据存储在 Docker volume 中：

```bash
# 备份数据
docker run --rm -v open-webui:/data -v $(pwd):/backup alpine \
  tar czf /backup/open-webui-backup.tar.gz -C /data .

# 恢复数据
docker run --rm -v open-webui:/data -v $(pwd):/backup alpine \
  tar xzf /backup/open-webui-backup.tar.gz -C /data
```

## Web 搜索集成

Open WebUI 可以集成搜索引擎，让 AI 获取实时信息：

- **SearXNG** - 自托管搜索聚合（推荐）
- **Google PSE** - Google Programmable Search Engine
- **Brave Search** - 隐私友好的搜索

配置方式：在管理面板 → 设置 → Web Search 中填写 API Key。

## PWA 支持

Open WebUI 支持 PWA（Progressive Web App），可以在手机或桌面安装为独立应用，体验接近原生 App。

## 移动端访问

1. 确保服务监听在 `0.0.0.0` 上（Docker 默认）
2. 手机上访问 `http://<你的电脑IP>:3000`
3. 添加到手机主屏幕即可获得类 App 体验

## 与其他工具的关系

| 工具 | 定位 |
|------|------|
| Ollama | 模型运行后端（引擎） |
| Open WebUI | 前端界面（UI 层） |
| Claude Code | 终端编程 Agent |
| Codex CLI | 终端编程 Agent |

常见组合：**Ollama（模型引擎）+ Open WebUI（交互界面）** 实现完全本地化的 ChatGPT 替代方案。

## 常见问题

**Docker 内无法连接宿主机 Ollama？**
确保使用 `host.docker.internal` 而非 `localhost`，Linux 需加 `--add-host=host.docker.internal:host-gateway`。

**模型加载太慢？**
Ollama 默认会在闲置后卸载模型以节省内存，可以在 Ollama 设置中延长 keep-alive 时间。
