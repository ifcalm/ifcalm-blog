---
title: "Open WebUI 使用手册：安装、Ollama 接入、模型配置、知识库与运维"
date: 2026-05-24
tags: ["Open WebUI", "AI 工具"]
draft: false
summary: "Open WebUI 完整使用手册，覆盖 Docker 安装、Ollama 接入、模型管理、OpenAI 兼容 API、知识库/RAG、用户权限、备份恢复与反向代理配置。"
showToc: true
tocOpen: false
---

## 一、Open WebUI 是什么？

Open WebUI 是一个开源、自托管的 AI Web 界面，可以连接本地模型和远程大模型 API。

它常用于：

- 给 Ollama 提供一个网页聊天界面
- 管理多个模型
- 接入 OpenAI 兼容 API
- 搭建本地知识库 / RAG
- 管理用户、权限、模型访问
- 接入 Tools、Functions、Pipelines、MCP、OpenAPI Server
- 在本地或服务器上搭建私有 AI 助手

可以简单理解为：

```text
Open WebUI = 自托管版 ChatGPT Web 界面 + 模型管理 + 知识库 + 工具扩展平台
```

常见访问地址：

```text
http://localhost:3000
```

容器内部服务端口通常是：

```text
8080
```

所以 Docker 常用端口映射是：

```text
-p 3000:8080
```

---

## 二、Open WebUI 与 Ollama 的关系

Ollama 负责在本地运行模型。

Open WebUI 负责提供网页界面、用户管理、聊天记录、知识库、模型配置和扩展能力。

两者关系可以这样理解：

```text
浏览器
  ↓
Open WebUI
  ↓
Ollama
  ↓
本地模型，例如 qwen、llama、gemma、deepseek-r1
```

如果你只是命令行使用本地模型，Ollama 就够了。

如果你希望像 ChatGPT 一样用网页界面聊天、上传文档、保存会话、管理多个模型，就适合使用 Open WebUI。

---

## 三、安装前准备

建议先准备：

- Docker 或 OrbStack
- Ollama
- 至少一个本地模型，例如 `qwen3`、`llama3.2`
- 浏览器
- 终端基础操作能力

确认 Ollama 是否运行：

```bash
curl http://localhost:11434
```

如果返回：

```text
Ollama is running
```

说明 Ollama 正常。

查看本地模型：

```bash
ollama list
```

如果没有模型，可以先下载一个：

```bash
ollama pull qwen3
```

---

## 四、最推荐安装方式：Docker + 本机 Ollama

如果 Ollama 已经安装在你的 Mac 上，Open WebUI 跑在 Docker 中，推荐使用下面命令。

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

说明：

| 参数 | 含义 |
|---|---|
| `-d` | 后台运行 |
| `-p 3000:8080` | 把容器 8080 映射到本机 3000 |
| `--add-host=host.docker.internal:host-gateway` | 让容器访问宿主机服务 |
| `-v open-webui:/app/backend/data` | 持久化聊天记录、配置、上传文件等数据 |
| `--name open-webui` | 容器名称 |
| `--restart always` | Docker 启动后自动拉起 |
| `ghcr.io/open-webui/open-webui:main` | Open WebUI 镜像 |

首次访问时创建的第一个账号通常会成为管理员账号，请保存好账号和密码。

---

## 五、使用 Docker Compose 安装

如果你更喜欢把配置写成文件，可以创建：

```bash
mkdir -p ~/docker/open-webui
cd ~/docker/open-webui
vim docker-compose.yml
```

写入：

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    ports:
      - "3000:8080"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      - open-webui:/app/backend/data
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
      - WEBUI_SECRET_KEY=replace-with-your-secret-key
    restart: always

volumes:
  open-webui:
```

生成 `WEBUI_SECRET_KEY`：

```bash
openssl rand -hex 32
```

启动：

```bash
docker compose up -d
```

查看状态：

```bash
docker compose ps
```

查看日志：

```bash
docker compose logs -f
```

停止：

```bash
docker compose down
```

注意：

```bash
docker compose down
```

不会删除 volume。

如果执行：

```bash
docker compose down -v
```

会删除 volume，也就是删除聊天记录、配置、知识库等数据。这个命令要非常谨慎。

---

## 六、一体化安装：Open WebUI + Ollama 同容器

如果你不想单独安装 Ollama，可以使用 Open WebUI 官方提供的 `:ollama` 镜像。

CPU 版本：

```bash
docker run -d \
  -p 3000:8080 \
  -v ollama:/root/.ollama \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:ollama
```

NVIDIA GPU 版本：

```bash
docker run -d \
  -p 3000:8080 \
  --gpus=all \
  -v ollama:/root/.ollama \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:ollama
```

这种方式适合 Linux 服务器。

如果你是 macOS，通常更推荐：

```text
Ollama 直接安装在 Mac 上
Open WebUI 通过 Docker 运行
```

因为 macOS Docker 容器通常无法像 Linux 那样直接使用 Apple GPU 加速。

---

## 七、只使用远程 Ollama 服务

如果 Ollama 跑在另一台机器上，可以指定：

```bash
docker run -d \
  -p 3000:8080 \
  -e OLLAMA_BASE_URL=http://你的服务器IP:11434 \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

例如：

```bash
-e OLLAMA_BASE_URL=http://192.168.1.20:11434
```

注意：远程 Ollama 服务不要直接暴露到公网，建议使用内网、VPN、Cloudflare Access 或反向代理认证。

---

## 八、常用 Docker 命令速查

| 场景 | 命令 |
|---|---|
| 查看容器 | `docker ps` |
| 查看所有容器 | `docker ps -a` |
| 查看日志 | `docker logs -f open-webui` |
| 停止容器 | `docker stop open-webui` |
| 启动容器 | `docker start open-webui` |
| 重启容器 | `docker restart open-webui` |
| 删除容器 | `docker rm -f open-webui` |
| 查看镜像 | `docker images` |
| 删除镜像 | `docker rmi ghcr.io/open-webui/open-webui:main` |
| 查看 volume | `docker volume ls` |
| 查看 volume 详情 | `docker volume inspect open-webui` |
| 进入容器 | `docker exec -it open-webui bash` |
| 查看容器资源 | `docker stats open-webui` |

---

## 九、首次进入 Open WebUI

访问：

```text
http://localhost:3000
```

首次进入时通常需要创建账号。

注意：

- 第一个注册账号通常是管理员
- 管理员可以管理用户、模型、连接和系统设置
- 如果忘记第一个管理员账号密码，后续处理会比较麻烦
- 建议保存好管理员账号和密码
- 多人使用时，建议关闭公开注册或设置审批

---

## 十、连接 Ollama

### 1. 默认连接

如果使用 Docker 运行 Open WebUI，并且 Ollama 在宿主机上，常用配置是：

```text
http://host.docker.internal:11434
```

如果 Open WebUI 和 Ollama 在同一个容器中，通常是：

```text
http://localhost:11434
```

如果 Ollama 在另一台服务器：

```text
http://服务器IP:11434
```

---

### 2. 通过环境变量配置

```bash
-e OLLAMA_BASE_URL=http://host.docker.internal:11434
```

Docker Compose：

```yaml
environment:
  - OLLAMA_BASE_URL=http://host.docker.internal:11434
```

---

### 3. 在管理界面配置

进入 Open WebUI 后：

```text
Admin Panel / 管理员面板
  → Settings / 设置
  → Connections / 连接
  → Ollama
```

填写 Ollama 地址：

```text
http://host.docker.internal:11434
```

保存后刷新模型列表。

---

### 4. 检查连接

宿主机检查：

```bash
curl http://localhost:11434
```

容器内检查：

```bash
docker exec -it open-webui bash
curl http://host.docker.internal:11434
```

如果容器内访问失败，通常是 Docker 网络或 Ollama 监听地址问题。

---

## 十一、让 Ollama 允许 Docker 容器访问

如果 Open WebUI 连接不上本机 Ollama，可能是 Ollama 只监听了：

```text
127.0.0.1
```

可以让 Ollama 监听：

```text
0.0.0.0:11434
```

macOS App 方式：

```bash
launchctl setenv OLLAMA_HOST "0.0.0.0:11434"
```

然后退出并重新启动 Ollama App。

命令行方式：

```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

验证：

```bash
curl http://localhost:11434
```

注意：监听 `0.0.0.0` 可能让局域网设备访问 Ollama，不要暴露到公网。

---

## 十二、模型管理

### 1. 在 Ollama 中下载模型

```bash
ollama pull qwen3
ollama pull llama3.2
ollama pull deepseek-r1
```

查看模型：

```bash
ollama list
```

运行测试：

```bash
ollama run qwen3 "你好，请介绍一下你自己"
```

---

### 2. 在 Open WebUI 中刷新模型

进入：

```text
Admin Panel
  → Settings
  → Connections
```

确认 Ollama 连接正常后，返回聊天页面，模型下拉框里应该能看到 Ollama 模型。

---

### 3. 修改模型显示名和参数

进入：

```text
Workspace
  → Models
```

可以对模型进行配置，例如：

- 显示名称
- 描述
- 默认系统提示词
- 模型可见性
- Advanced Parameters
- 权限控制

常见参数：

| 参数 | 含义 |
|---|---|
| `temperature` | 随机性，越低越稳定 |
| `top_p` | 采样范围 |
| `num_ctx` | 上下文长度 |
| `repeat_penalty` | 重复惩罚 |

代码任务建议：

```text
temperature = 0.2
```

写作任务可以高一些：

```text
temperature = 0.7
```

---

## 十三、接入 OpenAI 兼容 API

Open WebUI 可以连接 OpenAI，也可以连接其他 OpenAI-compatible 服务，例如：

- OpenAI
- DeepSeek
- SiliconFlow
- OpenRouter
- LocalAI
- LiteLLM
- Ollama 的 OpenAI 兼容 API

---

### 1. 通过环境变量配置

示例：接入 OpenAI 官方 API。

```bash
docker run -d \
  -p 3000:8080 \
  -e OPENAI_API_BASE_URL=https://api.openai.com/v1 \
  -e OPENAI_API_KEY=你的OpenAI_API_Key \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

不要把真实 API Key 写进博客、仓库或截图。

---

### 2. 接入 DeepSeek API 示例

DeepSeek 提供 OpenAI 兼容 API，通常可配置为：

```text
OPENAI_API_BASE_URL=https://api.deepseek.com
OPENAI_API_KEY=你的 DeepSeek API Key
```

Docker Compose 示例：

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    ports:
      - "3000:8080"
    volumes:
      - open-webui:/app/backend/data
    environment:
      - OPENAI_API_BASE_URL=https://api.deepseek.com
      - OPENAI_API_KEY=${DEEPSEEK_API_KEY}
      - WEBUI_SECRET_KEY=${WEBUI_SECRET_KEY}
    restart: always

volumes:
  open-webui:
```

启动前创建 `.env`：

```bash
DEEPSEEK_API_KEY=你的 DeepSeek API Key
WEBUI_SECRET_KEY=使用 openssl rand -hex 32 生成
```

启动：

```bash
docker compose up -d
```

---

### 3. 通过管理界面配置

也可以在 UI 中配置：

```text
Admin Panel
  → Settings
  → Connections
  → OpenAI API
```

填写：

```text
API Base URL
API Key
```

这种方式适合临时测试。

如果是正式部署，建议写进 Docker Compose，并把密钥放在 `.env` 或密钥管理系统中。

---

### 4. 多个 OpenAI 兼容地址

Open WebUI 支持多个 OpenAI base URL 和多个 key。

例如：

```yaml
environment:
  - OPENAI_API_BASE_URLS=https://api.openai.com/v1;https://api.deepseek.com
  - OPENAI_API_KEYS=sk-xxx;sk-yyy
```

注意：多个 key 的对应关系要谨慎管理，并尽量使用最小权限的 key。

---

## 十四、用户、权限与注册控制

### 1. 关闭注册

正式部署给自己或小团队使用时，建议关闭公开注册。

可以在管理界面中关闭：

```text
Admin Panel
  → Settings
  → Users / Authentication
```

也可以通过环境变量控制。常见做法是只允许管理员手动创建或审批用户。

---

### 2. 单用户模式

Open WebUI 支持关闭认证：

```bash
-e WEBUI_AUTH=False
```

例如：

```bash
docker run -d \
  -p 3000:8080 \
  -e WEBUI_AUTH=False \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

但要注意：

- 只适合本机个人试用
- 不适合多人或公网环境
- 已经有用户后不能随意切换单用户模式
- 暴露到网络时不建议关闭认证

---

### 3. 设置固定 WEBUI_SECRET_KEY

建议所有长期运行实例都设置：

```text
WEBUI_SECRET_KEY
```

生成：

```bash
openssl rand -hex 32
```

Docker Compose：

```yaml
environment:
  - WEBUI_SECRET_KEY=你的固定随机字符串
```

作用：

- 保持登录状态
- 避免重建容器后反复退出登录
- 避免某些加密信息无法解密
- 对 OAuth、API Key 等场景更稳定

---

## 十五、知识库与 RAG

Open WebUI 支持上传文档并基于文档问答。

### 1. 上传文档

进入：

```text
Workspace
  → Documents
```

上传文件，例如：

- PDF
- TXT
- Markdown
- DOCX
- CSV
- 其他支持格式

上传后，Open WebUI 会进行文档切分和向量化。

---

### 2. 在聊天中引用文档

在聊天输入框中使用：

```text
#
```

选择已上传文档或知识库。

例如：

```text
#我的文档 请总结这份文档的核心内容
```

也可以引用网页：

```text
#https://example.com 请总结这个页面
```

Open WebUI 会拉取页面内容后作为 RAG 上下文。

---

### 3. RAG 效果不好的常见原因

| 问题 | 可能原因 |
|---|---|
| 回答没有引用文档内容 | 没有正确选择文档 |
| 回答内容很泛 | 检索片段不相关 |
| 文档太长效果差 | 上下文长度不够 |
| Ollama 本地模型效果差 | 模型能力或上下文窗口不足 |
| 中文文档检索差 | Embedding 模型不适合中文 |
| PDF 表格识别差 | PDF 格式复杂或扫描版 |

如果使用 Ollama，本地模型默认上下文可能偏小。可以在 Ollama 或模型配置中提高：

```text
num_ctx
```

例如：

```text
8192
```

---

### 4. RAG 配置建议

进入：

```text
Admin Panel
  → Settings
  → Documents / RAG
```

可关注：

- Embedding 模型
- Chunk size
- Chunk overlap
- Top K
- Reranking
- 文档解析方式
- 向量数据库设置

建议：

| 场景 | 建议 |
|---|---|
| 中文文档 | 选择中文效果较好的 embedding |
| 长文档 | 增大上下文窗口，合理调 chunk |
| 技术文档 | chunk 不要太大，避免检索过宽 |
| 表格 PDF | 优先转成 Markdown / CSV 后上传 |
| 网页内容 | 优先使用干净页面或 raw 文本 |

---

## 十六、Prompts、Tools、Functions、Pipelines、MCP

Open WebUI 不只是聊天界面，也支持扩展能力。

| 能力 | 作用 |
|---|---|
| Prompts | 可复用提示词模板，类似 slash command |
| Tools / Functions | 在聊天中运行 Python 工具 |
| Pipelines | 独立插件框架，可处理消息过滤、路由、RAG、函数调用 |
| MCP | 接入 Model Context Protocol 工具 |
| OpenAPI Servers | 从 OpenAPI 端点自动发现工具 |
| Skills | Markdown 指令集，指导模型如何完成某类任务 |

简单理解：

```text
Prompts：复用常用提示词
Tools：给模型工具能力
Pipelines：对消息流做处理和扩展
MCP：接入外部工具生态
Skills：沉淀任务方法论
```

建议新手先掌握：

```text
Prompts
Documents / RAG
模型连接
用户管理
```

熟悉后再研究：

```text
Tools
Pipelines
MCP
OpenAPI
Skills
```

---

## 十七、Open WebUI API

Open WebUI 提供 API，可用于外部系统调用。

通常需要 API Key。

获取方式：

```text
Settings
  → Account
  → API Keys
```

调用时使用 Bearer Token：

```bash
curl http://localhost:3000/api/models \
  -H "Authorization: Bearer 你的_API_Key"
```

注意：

- API 需要鉴权
- 不要把 API Key 写进代码仓库
- 反向代理时注意 Authorization Header 是否被占用
- 正式环境建议走 HTTPS

---

## 十八、更新 Open WebUI

### 1. Docker Run 方式更新

备份后执行：

```bash
docker rm -f open-webui
docker pull ghcr.io/open-webui/open-webui:main
docker run -d \
  -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  -e WEBUI_SECRET_KEY="your-secret-key" \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

注意：只要 volume 没删，数据一般还在。

---

### 2. Docker Compose 方式更新

```bash
docker compose pull
docker compose up -d
```

查看日志：

```bash
docker compose logs -f
```

---

### 3. 是否使用 `:main`

`:main` 会跟随最新构建，方便但可能遇到破坏性变更。

更稳定的做法是固定版本，例如：

```yaml
image: ghcr.io/open-webui/open-webui:v0.9.5
```

升级前建议：

1. 备份数据
2. 查看 release notes
3. 固定版本号
4. 更新后清浏览器缓存
5. 验证登录、模型连接、知识库

---

## 十九、备份与恢复

Open WebUI 的关键数据在：

```text
/app/backend/data
```

Docker volume 示例：

```text
open-webui:/app/backend/data
```

其中可能包含：

```text
webui.db
uploads/
vector_db/
cache/
audit.log
```

---

### 1. 查看 volume 真实路径

```bash
docker volume inspect open-webui
```

---

### 2. 备份 Docker volume

```bash
mkdir -p ~/backup/open-webui

docker run --rm \
  -v open-webui:/data \
  -v ~/backup/open-webui:/backup \
  alpine \
  tar czf /backup/open-webui-$(date +%Y%m%d).tar.gz -C /data .
```

---

### 3. 恢复 Docker volume

先停止容器：

```bash
docker rm -f open-webui
```

恢复：

```bash
docker run --rm \
  -v open-webui:/data \
  -v ~/backup/open-webui:/backup \
  alpine \
  sh -c "cd /data && tar xzf /backup/open-webui-YYYYMMDD.tar.gz"
```

重新启动 Open WebUI。

---

### 4. 备份建议

建议至少备份：

- `webui.db`
- `uploads/`
- `vector_db/`
- 配置文件
- `docker-compose.yml`
- `.env`

如果你使用远程数据库，也要单独备份数据库。

---

## 二十、反向代理与 HTTPS

如果要在局域网或公网访问，建议使用反向代理和 HTTPS。

可选方案：

- Nginx
- Caddy
- Traefik
- Cloudflare Tunnel
- Cloudflare Access

### 1. Caddy 示例

```caddyfile
ai.example.com {
  reverse_proxy localhost:3000
}
```

### 2. Nginx 示例

```nginx
server {
    listen 80;
    server_name ai.example.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

注意：Open WebUI 需要 WebSocket 支持，所以反向代理要正确处理 `Upgrade` 头。

---

## 二十一、常见问题

### 1. Open WebUI 启动后访问不了

检查容器：

```bash
docker ps
docker logs -f open-webui
```

检查端口：

```bash
lsof -i :3000
```

确认访问地址：

```text
http://localhost:3000
```

---

### 2. Open WebUI 看不到 Ollama 模型

先确认 Ollama 有模型：

```bash
ollama list
```

确认 Ollama 服务可访问：

```bash
curl http://localhost:11434
```

容器内检查：

```bash
docker exec -it open-webui bash
curl http://host.docker.internal:11434
```

如果失败，检查：

- `OLLAMA_BASE_URL`
- Docker 网络
- Ollama 是否监听 `0.0.0.0:11434`
- 防火墙或代理

---

### 3. 更新后聊天记录没了

常见原因：

- 启动容器时没有挂载 `-v open-webui:/app/backend/data`
- 使用了新的 volume
- 误删了 volume
- 执行了 `docker compose down -v`

检查 volume：

```bash
docker volume ls
docker volume inspect open-webui
```

---

### 4. 更新或重启后总是重新登录

建议设置固定：

```text
WEBUI_SECRET_KEY
```

如果每次启动生成新的 secret，登录态和部分加密信息可能失效。

---

### 5. RAG 效果不好

排查：

- 是否正确选中了文档
- 文档是否成功解析
- Embedding 模型是否合适
- chunk 设置是否合理
- 模型上下文是否足够
- Ollama 模型是否能力不足

如果 Ollama 默认上下文太小，可以提高：

```text
num_ctx
```

---

### 6. Open WebUI 连接外部 API 失败

检查：

- API Key 是否正确
- Base URL 是否正确
- 是否是 OpenAI 兼容格式
- 容器是否能访问外网
- 公司代理 / 防火墙是否拦截
- 模型名称是否正确

进入容器测试网络：

```bash
docker exec -it open-webui bash
curl https://api.deepseek.com
```

---

### 7. 忘记管理员密码

如果第一个管理员账号密码忘记，新注册账号可能需要管理员激活。

建议优先查看官方 Reset Admin Password 文档，并在操作前备份数据。

---

### 8. Docker 镜像很大

可以考虑 slim 镜像：

```yaml
image: ghcr.io/open-webui/open-webui:main-slim
```

但 slim 镜像首次使用某些功能时可能需要下载额外模型或依赖。

---

## 二十二、推荐的日常维护命令

查看状态：

```bash
docker ps
docker logs --tail 100 open-webui
ollama ps
ollama list
```

重启：

```bash
docker restart open-webui
```

更新：

```bash
docker pull ghcr.io/open-webui/open-webui:main
docker rm -f open-webui
```

备份：

```bash
docker run --rm \
  -v open-webui:/data \
  -v ~/backup/open-webui:/backup \
  alpine \
  tar czf /backup/open-webui-$(date +%Y%m%d).tar.gz -C /data .
```

清理不用模型：

```bash
ollama list
ollama rm 模型名
```

---

## 二十三、适合你的推荐部署方式

如果是个人 Mac 本地使用，我建议：

```text
Ollama：直接安装在 macOS
Open WebUI：Docker / OrbStack 运行
模型：先用 qwen3、llama3.2、deepseek-r1 等
访问：localhost:3000
数据：使用 open-webui volume 持久化
```

推荐启动命令：

```bash
docker run -d \
  -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -e WEBUI_SECRET_KEY="$(openssl rand -hex 32)" \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

如果使用 Docker Compose，推荐保存好：

```text
docker-compose.yml
.env
```

以后换电脑、迁移环境、重装系统会方便很多。

---

## 二十四、命令速查汇总

### Docker

```bash
docker run -d -p 3000:8080 -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
docker logs -f open-webui
docker restart open-webui
docker rm -f open-webui
docker pull ghcr.io/open-webui/open-webui:main
docker volume inspect open-webui
```

### Docker Compose

```bash
docker compose up -d
docker compose ps
docker compose logs -f
docker compose pull
docker compose up -d
docker compose down
```

### Ollama

```bash
ollama list
ollama pull qwen3
ollama run qwen3
ollama ps
ollama stop qwen3
```

### 检查连接

```bash
curl http://localhost:3000
curl http://localhost:11434
docker exec -it open-webui bash
curl http://host.docker.internal:11434
```

### 备份

```bash
docker run --rm -v open-webui:/data -v ~/backup/open-webui:/backup alpine tar czf /backup/open-webui-$(date +%Y%m%d).tar.gz -C /data .
```

---

## 二十五、个人建议

Open WebUI 的价值不只是“给 Ollama 套一个网页”，它更像是一个本地 AI 工作台。

建议按这个顺序掌握：

```text
1. Docker 安装和访问
2. 连接 Ollama
3. 管理模型
4. 上传文档做 RAG
5. 接入 OpenAI 兼容 API
6. 配置用户和权限
7. 学会更新和备份
8. 再研究 Tools / Pipelines / MCP / Skills
```

最重要的三个注意事项：

```text
1. 一定要挂载 /app/backend/data，否则数据容易丢。
2. 长期运行要设置 WEBUI_SECRET_KEY。
3. 不要把 Ollama、Open WebUI、外部 API Key 直接暴露到公网。
```

---

## 参考资料

- Open WebUI 官网：https://openwebui.com/
- Open WebUI GitHub：https://github.com/open-webui/open-webui
- Open WebUI Quick Start：https://docs.openwebui.com/getting-started/quick-start/
- Environment Variable Configuration：https://docs.openwebui.com/reference/env-configuration/
- Updating Open WebUI：https://docs.openwebui.com/getting-started/updating/
- Backups：https://docs.openwebui.com/tutorials/maintenance/backups/
- RAG：https://docs.openwebui.com/features/chat-conversations/rag/
- API Endpoints：https://docs.openwebui.com/reference/api-endpoints/
- FAQ：https://docs.openwebui.com/faq/
