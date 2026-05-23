---
title: "Docker：从装好到用熟"
date: 2026-04-18
tags: ["工具", "开发"]
draft: false
summary: "Docker 容器日常使用指南，覆盖镜像、容器、Dockerfile、Compose 等核心操作"
showToc: true
tocOpen: true
ShowShareButtons: false
---

## 它能干嘛

Docker 把应用和环境打包在一起，让它跑到哪都一样。你在本地跑的容器，丢到服务器上行为一致，不会出现"我电脑上能跑啊"的尴尬。

## 安装

```bash
# macOS
brew install docker

# 或者用 OrbStack（轻量替代 Docker Desktop）
brew install orbstack

# Linux
curl -fsSL https://get.docker.com | sh
```

## 核心概念

Docker 就三个东西来回转：

- **镜像（Image）** — 一个只读模板，比如 `nginx:latest`、`python:3.12`
- **容器（Container）** — 镜像跑起来之后的实例，可读可写
- **仓库（Registry）** — 存镜像的地方，Docker Hub 是默认的公共仓库

再加两个配角：
- **卷（Volume）** — 容器删了数据还在，持久化存储
- **网络（Network）** — 容器之间怎么通信

## 镜像操作

```bash
# 拉镜像
docker pull nginx:latest
docker pull python:3.12-slim    # slim 版本体积小，生产常用

# 看本地有哪些镜像
docker images
docker image ls

# 看镜像的分层历史
docker history nginx:latest

# 给镜像打标签
docker tag nginx:latest my-nginx:v1

# 删镜像
docker rmi nginx:latest
docker image rm nginx:latest

# 清理没用的镜像
docker image prune
```

## 容器操作

### 跑起来

```bash
# 最基本的
docker run nginx:latest

# 后台跑，给个名字
docker run -d --name my-nginx nginx:latest

# 映射端口（本机8080 → 容器80）
docker run -d -p 8080:80 --name my-nginx nginx:latest

# 挂载目录（本地目录 → 容器目录）
docker run -d -v $(pwd)/html:/usr/share/nginx/html -p 8080:80 nginx:latest

# 用完即删
docker run --rm nginx:latest

# 交互式进去
docker run -it ubuntu:latest /bin/bash
```

### 日常管理

```bash
# 看运行中的
docker ps

# 看所有（包括停掉的）
docker ps -a

# 看最近创建的 N 个
docker ps -n 5

# 进去正在运行的容器
docker exec -it my-nginx /bin/bash
docker exec my-nginx cat /etc/nginx/nginx.conf

# 查看日志
docker logs my-nginx
docker logs -f my-nginx       # 实时跟踪
docker logs --tail 50 my-nginx # 最后50行

# 看容器详情
docker inspect my-nginx

# 复制文件
docker cp my-nginx:/etc/nginx/nginx.conf ./nginx.conf   # 容器→本机
docker cp ./index.html my-nginx:/usr/share/nginx/html/   # 本机→容器

# 启停
docker stop my-nginx
docker start my-nginx
docker restart my-nginx
docker pause my-nginx          # 暂停进程但不停止容器
docker unpause my-nginx

# 删容器
docker rm my-nginx
docker rm -f my-nginx           # 强制删，不管停没停
docker container prune          # 清掉所有已停止的容器
```

### `docker run` 常用参数

| 参数 | 说明 | 例 |
|------|------|-----|
| `-d` | 后台跑 | `-d` |
| `--name` | 给容器起名 | `--name my-app` |
| `-p` | 端口映射 | `-p 8080:80` |
| `-v` | 挂载目录/卷 | `-v ./data:/data` |
| `-e` | 环境变量 | `-e MYSQL_ROOT_PASSWORD=123` |
| `--rm` | 停了自动删 | `--rm` |
| `--restart` | 重启策略 | `--restart always` |
| `--network` | 加入网络 | `--network my-net` |
| `-it` | 交互式 | `-it` |

## Dockerfile 写镜像

一个简单的例子，把 Go 项目打包成镜像：

```dockerfile
# 构建阶段
FROM golang:1.24-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o server .

# 运行阶段
FROM alpine:latest
RUN apk --no-cache add ca-certificates
COPY --from=builder /app/server /server
EXPOSE 8080
CMD ["/server"]
```

多阶段构建的好处：构建依赖留在第一阶段，最终镜像只包含运行需要的文件，体积小很多。

### 常用指令

| 指令 | 干嘛的 |
|------|--------|
| `FROM` | 基于哪个镜像 |
| `WORKDIR` | 设工作目录 |
| `COPY` | 从本机复制文件到镜像 |
| `ADD` | 类似 COPY，但支持自动解压 tar 和远程 URL |
| `RUN` | 构建时执行命令 |
| `ENV` | 设环境变量 |
| `ARG` | 构建参数（`--build-arg` 传入） |
| `EXPOSE` | 声明容器监听的端口（文档性质，实际靠 -p 映射） |
| `CMD` | 容器启动时默认执行的命令 |
| `ENTRYPOINT` | 容器入口，CMD 可作为它的默认参数 |
| `VOLUME` | 声明匿名卷 |
| `USER` | 以哪个用户运行 |

### 构建和推送

```bash
# 构建
docker build -t my-app:v1 .

# 指定 Dockerfile
docker build -f Dockerfile.prod -t my-app:v1 .

# 加构建参数
docker build --build-arg VERSION=1.0 -t my-app:v1 .

# 不看缓存重新构建
docker build --no-cache -t my-app:v1 .

# 推送到仓库
docker tag my-app:v1 username/my-app:v1
docker push username/my-app:v1

# 登录
docker login
docker login registry.example.com
```

## 卷（Volume）

容器删了，卷里的数据还在：

```bash
# 创建卷
docker volume create my-data

# 挂载卷
docker run -d -v my-data:/data --name db mysql:8

# 挂载本地目录
docker run -d -v $(pwd)/data:/data --name db mysql:8

# 列出卷
docker volume ls

# 删卷
docker volume rm my-data
docker volume prune     # 清掉没在用的卷
```

卷 vs 绑定挂载：卷由 Docker 管理，绑定挂载（`-v /本地路径:/容器路径`）直接指向宿主机目录。开发时用绑定挂载方便热更新，生产环境用卷。

## 网络（Network）

```bash
# 创建网络
docker network create my-net

# 在指定网络中跑容器
docker run -d --network my-net --name app1 my-app
docker run -d --network my-net --name app2 my-app

# 同一网络内的容器可以用容器名互相访问
# 比如 app1 里可以 ping app2

# 把已有容器连到网络
docker network connect my-net existing-container

# 查看
docker network ls
docker network inspect my-net

# 删
docker network rm my-net
docker network prune
```

默认情况下 Docker 会创建 `bridge` 网络，容器之间只能用 IP 互通。自己建网络后，容器可以用名字互相访问。

## Docker Compose

多个容器一起管，写一个 `docker-compose.yml`：

```yaml
services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DB_HOST=db
      - DB_PASSWORD=secret
    depends_on:
      - db
    restart: always

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_PASSWORD=secret
      - POSTGRES_DB=myapp
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: always

volumes:
  pgdata:
```

常用命令：

```bash
# 启动所有服务
docker compose up -d

# 重新构建并启动
docker compose up -d --build

# 看状态
docker compose ps

# 看日志
docker compose logs -f

# 在某个服务里执行命令
docker compose exec app /bin/sh

# 停止并清理
docker compose down

# 停止并连卷一起删
docker compose down -v
```

## 清理与空间

```bash
# 看磁盘占用
docker system df

# 一键清理（停止的容器、未使用的网络、悬空镜像、构建缓存）
docker system prune

# 更狠，连未使用的镜像和卷也清
docker system prune -a --volumes

# 分别清理
docker container prune   # 停止的容器
docker image prune       # 未使用的镜像
docker volume prune      # 未使用的卷
docker network prune     # 未使用的网络
docker builder prune     # 构建缓存
```

磁盘告急时 `docker system prune -a` 能回收不少空间。

## 常用模式

### 开发时热更新

把源码目录挂进去，改代码不用重新构建镜像：

```bash
docker run -d -v $(pwd):/app -p 3000:3000 node:20-alpine sh -c "cd /app && npm start"
```

### 一次性任务

```bash
# 用 alpine 跑个命令就走
docker run --rm alpine echo "hello"

# MySQL 客户端连另一个容器里的数据库
docker run --rm -it mysql:8 mysql -h db-container -u root -p
```

### 查看容器资源占用

```bash
docker stats
docker stats my-container
```

### 把容器保存为镜像

```bash
docker commit my-container my-custom-image:v1
```

### 导出导入镜像

```bash
docker save -o my-image.tar my-app:v1
docker load -i my-image.tar
```

适合没有 registry 或者离线环境的场景。

---

没了。Docker 上手不难，`run`、`ps`、`exec`、`logs`、`stop` 五个命令熟悉了基本就够日常用了。
