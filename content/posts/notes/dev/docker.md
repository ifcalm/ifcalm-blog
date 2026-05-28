---
title: "Docker 完整使用手册：从入门到日常开发实践"
date: 2026-04-18
tags: ["工具", "开发"]
draft: false
summary: "Docker 容器日常使用指南，覆盖镜像、容器、Dockerfile、Compose 等核心操作"
showToc: true
tocOpen: false
ShowShareButtons: false
---

## 一、Docker 是什么？

Docker 是一种容器化技术，它可以把应用程序以及运行应用所需的依赖、配置、运行环境一起打包，形成一个可以在不同机器上稳定运行的“容器”。

简单理解：

> Docker 解决的是“在我电脑上能跑，到了服务器就跑不起来”的问题。

传统部署方式通常需要在服务器上安装语言环境、依赖库、数据库客户端、运行时配置等，不同机器之间容易出现环境差异。Docker 则通过镜像和容器，把运行环境标准化，让应用可以更稳定地在开发、测试、生产环境中运行。

---

## 二、Docker 的核心概念

学习 Docker，先理解几个核心概念。

### 1. 镜像 Image

镜像可以理解为应用运行环境的“模板”。

例如：

```bash
nginx:latest
mysql:8.0
redis:7
ubuntu:22.04
golang:1.22
```

镜像本身是静态的，不能直接修改。我们通常基于镜像启动容器。

---

### 2. 容器 Container

容器是镜像运行起来之后的实例。

可以理解为：

```text
镜像 = 类
容器 = 对象
```

一个镜像可以启动多个容器。

例如，基于 `nginx` 镜像可以启动多个 Nginx 容器，每个容器都可以有不同的端口、配置和数据。

---

### 3. Dockerfile

Dockerfile 是用来构建镜像的脚本文件。

它描述了镜像应该如何生成，例如：

* 使用哪个基础镜像
* 拷贝哪些代码
* 安装哪些依赖
* 暴露哪些端口
* 容器启动后执行什么命令

---

### 4. Registry 镜像仓库

镜像仓库用于存储和分发 Docker 镜像。

常见仓库：

* Docker Hub
* GitHub Container Registry
* GitLab Container Registry
* 阿里云镜像仓库
* 华为云 SWR
* 腾讯云 TCR
* 私有 Harbor 仓库

---

### 5. Volume 数据卷

容器本身是临时的，如果删除容器，容器内部数据也可能丢失。

数据卷用于持久化数据，常用于：

* 数据库数据
* 上传文件
* 日志目录
* 配置文件

---

### 6. Network 网络

Docker 容器之间可以通过 Docker 网络互相访问。

常见网络模式：

* `bridge`：默认网络模式
* `host`：使用宿主机网络
* `none`：不使用网络
* 自定义网络：推荐用于多容器应用

---

### 7. Docker Compose

Docker Compose 用于管理多容器应用。

例如一个 Web 项目可能需要：

* Web 服务
* MySQL
* Redis
* Nginx

如果只使用 `docker run`，每个服务都需要手动启动，命令会很长。Docker Compose 可以通过一个 `compose.yaml` 文件统一描述这些服务，然后用一条命令启动全部服务。

---

## 三、Docker 的安装

### 1. macOS 安装 Docker

macOS 推荐安装 Docker Desktop。

安装方式一：官网下载 Docker Desktop。

安装方式二：使用 Homebrew 安装：

```bash
brew install --cask docker
```

安装完成后，打开 Docker Desktop，等待 Docker Engine 启动完成。

验证安装：

```bash
docker version
docker info
```

运行测试容器：

```bash
docker run hello-world
```

如果看到欢迎信息，说明 Docker 已经安装成功。

---

### 2. Windows 安装 Docker

Windows 推荐安装 Docker Desktop。

基本要求：

* Windows 10 或 Windows 11
* 建议开启 WSL2
* 安装 Docker Desktop for Windows

安装后可以在 PowerShell 中验证：

```powershell
docker version
docker run hello-world
```

---

### 3. Linux 安装 Docker

以 Ubuntu 为例：

```bash
sudo apt update
sudo apt install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker
```

验证：

```bash
docker version
docker run hello-world
```

如果不想每次都使用 `sudo`，可以把当前用户加入 `docker` 用户组：

```bash
sudo usermod -aG docker $USER
```

然后重新登录终端。

注意：把用户加入 `docker` 组相当于赋予较高权限，生产环境要谨慎处理。

---

## 四、Docker 基础命令

### 1. 查看 Docker 版本

```bash
docker version
```

### 2. 查看 Docker 系统信息

```bash
docker info
```

### 3. 查看帮助

```bash
docker --help
docker run --help
docker image --help
docker container --help
```

---

## 五、镜像管理

### 1. 搜索镜像

```bash
docker search nginx
```

### 2. 拉取镜像

```bash
docker pull nginx
docker pull redis:7
docker pull mysql:8.0
```

如果不指定版本，默认使用 `latest`：

```bash
docker pull nginx
```

但在生产环境中，不建议长期使用 `latest`，最好指定明确版本，例如：

```bash
docker pull nginx:1.26
```

---

### 3. 查看本地镜像

```bash
docker images
```

或者：

```bash
docker image ls
```

示例输出：

```text
REPOSITORY   TAG       IMAGE ID       CREATED        SIZE
nginx        latest    xxxxxxxx       2 weeks ago    190MB
redis        7         xxxxxxxx       1 month ago    117MB
```

---

### 4. 删除镜像

```bash
docker rmi nginx
```

按镜像 ID 删除：

```bash
docker rmi IMAGE_ID
```

强制删除：

```bash
docker rmi -f IMAGE_ID
```

---

### 5. 清理无用镜像

```bash
docker image prune
```

清理所有未使用镜像：

```bash
docker image prune -a
```

---

### 6. 镜像打标签

```bash
docker tag myapp:latest username/myapp:v1.0.0
```

---

### 7. 推送镜像到仓库

先登录：

```bash
docker login
```

推送：

```bash
docker push username/myapp:v1.0.0
```

---

## 六、容器管理

### 1. 启动一个 Nginx 容器

```bash
docker run nginx
```

这个命令会以前台方式启动 Nginx。

如果希望后台运行：

```bash
docker run -d nginx
```

---

### 2. 指定容器名称

```bash
docker run -d --name my-nginx nginx
```

---

### 3. 端口映射

容器内部 Nginx 默认监听 `80` 端口，如果想让宿主机通过 `8080` 访问：

```bash
docker run -d --name my-nginx -p 8080:80 nginx
```

访问：

```text
http://localhost:8080
```

端口格式：

```text
宿主机端口:容器端口
```

---

### 4. 查看运行中的容器

```bash
docker ps
```

查看所有容器，包括已停止的：

```bash
docker ps -a
```

---

### 5. 停止容器

```bash
docker stop my-nginx
```

或者使用容器 ID：

```bash
docker stop CONTAINER_ID
```

---

### 6. 启动已停止容器

```bash
docker start my-nginx
```

---

### 7. 重启容器

```bash
docker restart my-nginx
```

---

### 8. 删除容器

删除已停止容器：

```bash
docker rm my-nginx
```

强制删除运行中的容器：

```bash
docker rm -f my-nginx
```

---

### 9. 查看容器日志

```bash
docker logs my-nginx
```

实时查看日志：

```bash
docker logs -f my-nginx
```

查看最近 100 行：

```bash
docker logs --tail=100 my-nginx
```

---

### 10. 进入容器

```bash
docker exec -it my-nginx bash
```

如果容器中没有 bash，可以使用 sh：

```bash
docker exec -it my-nginx sh
```

---

### 11. 查看容器详细信息

```bash
docker inspect my-nginx
```

---

### 12. 查看容器资源占用

```bash
docker stats
```

---

### 13. 从容器复制文件到宿主机

```bash
docker cp my-nginx:/etc/nginx/nginx.conf ./nginx.conf
```

---

### 14. 从宿主机复制文件到容器

```bash
docker cp ./index.html my-nginx:/usr/share/nginx/html/index.html
```

---

## 七、docker run 常用参数

### 1. 后台运行

```bash
-d
```

示例：

```bash
docker run -d nginx
```

---

### 2. 指定容器名称

```bash
--name
```

示例：

```bash
docker run -d --name web nginx
```

---

### 3. 端口映射

```bash
-p
```

示例：

```bash
docker run -d -p 8080:80 nginx
```

---

### 4. 环境变量

```bash
-e
```

示例：

```bash
docker run -d \
  --name mysql \
  -e MYSQL_ROOT_PASSWORD=123456 \
  mysql:8.0
```

---

### 5. 数据卷挂载

```bash
-v
```

示例：

```bash
docker run -d \
  --name nginx \
  -v $(pwd)/html:/usr/share/nginx/html \
  -p 8080:80 \
  nginx
```

---

### 6. 自动重启策略

```bash
--restart
```

常见值：

```text
no
always
unless-stopped
on-failure
```

示例：

```bash
docker run -d \
  --name redis \
  --restart unless-stopped \
  redis:7
```

---

### 7. 容器退出后自动删除

```bash
--rm
```

示例：

```bash
docker run --rm ubuntu echo "hello docker"
```

适合临时任务。

---

### 8. 交互式终端

```bash
-it
```

示例：

```bash
docker run -it ubuntu bash
```

---

## 八、数据卷 Volume

### 1. 为什么需要数据卷？

容器删除后，容器内部的数据通常也会消失。

例如 MySQL 容器，如果不挂载数据卷，删除容器后数据库数据也可能丢失。

因此，数据库、上传文件、日志等需要持久化的内容，应该使用数据卷。

---

### 2. 创建数据卷

```bash
docker volume create mysql-data
```

---

### 3. 查看数据卷

```bash
docker volume ls
```

---

### 4. 查看数据卷详情

```bash
docker volume inspect mysql-data
```

---

### 5. 使用数据卷运行 MySQL

```bash
docker run -d \
  --name mysql \
  -e MYSQL_ROOT_PASSWORD=123456 \
  -v mysql-data:/var/lib/mysql \
  -p 3306:3306 \
  mysql:8.0
```

---

### 6. 删除数据卷

```bash
docker volume rm mysql-data
```

清理无用数据卷：

```bash
docker volume prune
```

---

### 7. 数据卷与目录挂载的区别

Docker 常见两种挂载方式：

#### 方式一：Volume

```bash
-v mysql-data:/var/lib/mysql
```

特点：

* 由 Docker 管理
* 适合数据库数据
* 跨平台表现更稳定

#### 方式二：Bind Mount

```bash
-v $(pwd)/html:/usr/share/nginx/html
```

特点：

* 直接挂载宿主机目录
* 适合开发调试
* 方便实时修改代码或配置

---

## 九、Docker 网络

### 1. 查看网络

```bash
docker network ls
```

---

### 2. 创建自定义网络

```bash
docker network create my-network
```

---

### 3. 容器加入网络

启动 Redis：

```bash
docker run -d \
  --name redis \
  --network my-network \
  redis:7
```

启动应用容器：

```bash
docker run -d \
  --name app \
  --network my-network \
  myapp:latest
```

在同一个自定义网络中，容器可以通过容器名访问对方。

例如应用可以通过下面地址访问 Redis：

```text
redis:6379
```

---

### 4. 删除网络

```bash
docker network rm my-network
```

清理无用网络：

```bash
docker network prune
```

---

## 十、Dockerfile 使用手册

### 1. Dockerfile 是什么？

Dockerfile 是构建镜像的配置文件。

一个简单的 Dockerfile：

```dockerfile
FROM nginx:1.26

COPY ./html /usr/share/nginx/html

EXPOSE 80
```

构建镜像：

```bash
docker build -t my-nginx:v1 .
```

运行镜像：

```bash
docker run -d -p 8080:80 my-nginx:v1
```

---

### 2. Dockerfile 常用指令

#### FROM

指定基础镜像。

```dockerfile
FROM ubuntu:22.04
```

---

#### WORKDIR

设置工作目录。

```dockerfile
WORKDIR /app
```

---

#### COPY

复制文件到镜像中。

```dockerfile
COPY . /app
```

---

#### ADD

也可以复制文件，但功能比 COPY 更多，例如自动解压压缩包。

一般情况下优先使用 `COPY`。

```dockerfile
ADD app.tar.gz /app
```

---

#### RUN

构建镜像时执行命令。

```dockerfile
RUN apt update && apt install -y curl
```

---

#### CMD

容器启动时默认执行的命令。

```dockerfile
CMD ["nginx", "-g", "daemon off;"]
```

---

#### ENTRYPOINT

容器入口命令。

```dockerfile
ENTRYPOINT ["java", "-jar", "app.jar"]
```

---

#### EXPOSE

声明容器内部服务端口。

```dockerfile
EXPOSE 8080
```

注意：`EXPOSE` 只是声明端口，不会自动映射到宿主机。真正映射端口需要使用 `-p`。

---

#### ENV

设置环境变量。

```dockerfile
ENV APP_ENV=prod
```

---

#### ARG

设置构建参数。

```dockerfile
ARG VERSION=1.0.0
```

构建时传参：

```bash
docker build --build-arg VERSION=1.0.1 -t myapp:v1 .
```

---

### 3. Go 项目 Dockerfile 示例

下面是一个 Go 项目的多阶段构建示例。

```dockerfile
FROM golang:1.22 AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o server ./cmd/server

FROM alpine:3.20

WORKDIR /app

COPY --from=builder /app/server /app/server

EXPOSE 8080

CMD ["/app/server"]
```

构建镜像：

```bash
docker build -t my-go-app:v1 .
```

运行容器：

```bash
docker run -d \
  --name my-go-app \
  -p 8080:8080 \
  my-go-app:v1
```

---

### 4. Node.js 项目 Dockerfile 示例

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "start"]
```

---

### 5. Java 项目 Dockerfile 示例

```dockerfile
FROM eclipse-temurin:21-jre

WORKDIR /app

COPY target/app.jar /app/app.jar

EXPOSE 8080

CMD ["java", "-jar", "/app/app.jar"]
```

---

### 6. .dockerignore 文件

`.dockerignore` 用于排除不需要复制到镜像中的文件，类似 `.gitignore`。

示例：

```text
.git
.idea
.vscode
node_modules
target
dist
logs
*.log
.DS_Store
.env
```

好处：

* 减少镜像构建上下文
* 加快构建速度
* 避免敏感文件进入镜像
* 降低镜像体积

---

## 十一、Docker Compose 使用手册

### 1. Docker Compose 是什么？

Docker Compose 用于定义和运行多容器应用。

它通过 `compose.yaml` 文件描述多个服务，例如：

* Web 应用
* MySQL
* Redis
* Nginx

然后通过一条命令启动：

```bash
docker compose up -d
```

---

### 2. Compose 文件示例

下面是一个 Web + MySQL + Redis 的示例：

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: my-app
    ports:
      - "8080:8080"
    environment:
      APP_ENV: dev
      MYSQL_HOST: mysql
      MYSQL_PORT: 3306
      MYSQL_USER: root
      MYSQL_PASSWORD: 123456
      REDIS_HOST: redis
      REDIS_PORT: 6379
    depends_on:
      - mysql
      - redis
    networks:
      - app-network

  mysql:
    image: mysql:8.0
    container_name: my-mysql
    environment:
      MYSQL_ROOT_PASSWORD: 123456
      MYSQL_DATABASE: app_db
    ports:
      - "3306:3306"
    volumes:
      - mysql-data:/var/lib/mysql
    networks:
      - app-network

  redis:
    image: redis:7
    container_name: my-redis
    ports:
      - "6379:6379"
    networks:
      - app-network

volumes:
  mysql-data:

networks:
  app-network:
    driver: bridge
```

---

### 3. 启动服务

```bash
docker compose up
```

后台启动：

```bash
docker compose up -d
```

---

### 4. 停止服务

```bash
docker compose down
```

如果同时删除数据卷：

```bash
docker compose down -v
```

注意：`-v` 会删除 volume，数据库数据可能会丢失，生产环境慎用。

---

### 5. 查看服务状态

```bash
docker compose ps
```

---

### 6. 查看日志

```bash
docker compose logs
```

实时查看日志：

```bash
docker compose logs -f
```

查看指定服务日志：

```bash
docker compose logs -f app
```

---

### 7. 重新构建镜像

```bash
docker compose build
```

构建并启动：

```bash
docker compose up -d --build
```

---

### 8. 进入某个服务容器

```bash
docker compose exec app sh
```

进入 MySQL 容器：

```bash
docker compose exec mysql bash
```

---

### 9. 执行一次性命令

```bash
docker compose run --rm app sh
```

---

### 10. 查看最终配置

```bash
docker compose config
```

这个命令可以检查 Compose 文件是否正确。

---

## 十二、Docker 常见实战场景

### 1. 快速启动 Nginx

```bash
docker run -d \
  --name nginx \
  -p 8080:80 \
  nginx:1.26
```

访问：

```text
http://localhost:8080
```

---

### 2. 挂载本地静态页面到 Nginx

目录结构：

```text
demo/
  html/
    index.html
```

启动：

```bash
docker run -d \
  --name nginx \
  -p 8080:80 \
  -v $(pwd)/html:/usr/share/nginx/html \
  nginx:1.26
```

---

### 3. 启动 Redis

```bash
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7
```

连接测试：

```bash
docker exec -it redis redis-cli
```

---

### 4. 启动 MySQL

```bash
docker run -d \
  --name mysql \
  -e MYSQL_ROOT_PASSWORD=123456 \
  -e MYSQL_DATABASE=test_db \
  -p 3306:3306 \
  -v mysql-data:/var/lib/mysql \
  mysql:8.0
```

进入 MySQL：

```bash
docker exec -it mysql mysql -uroot -p
```

---

### 5. 启动 PostgreSQL

```bash
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=123456 \
  -e POSTGRES_DB=test_db \
  -p 5432:5432 \
  -v postgres-data:/var/lib/postgresql/data \
  postgres:16
```

---

### 6. 启动 MongoDB

```bash
docker run -d \
  --name mongo \
  -p 27017:27017 \
  -v mongo-data:/data/db \
  mongo:7
```

---

## 十三、Docker 构建与发布流程

一个常见的应用发布流程如下：

```text
编写代码
  ↓
编写 Dockerfile
  ↓
构建镜像
  ↓
本地运行测试
  ↓
打标签
  ↓
推送到镜像仓库
  ↓
服务器拉取镜像
  ↓
启动容器
```

---

### 1. 构建镜像

```bash
docker build -t myapp:v1.0.0 .
```

---

### 2. 本地运行测试

```bash
docker run -d \
  --name myapp \
  -p 8080:8080 \
  myapp:v1.0.0
```

---

### 3. 打标签

```bash
docker tag myapp:v1.0.0 username/myapp:v1.0.0
```

---

### 4. 登录仓库

```bash
docker login
```

---

### 5. 推送镜像

```bash
docker push username/myapp:v1.0.0
```

---

### 6. 服务器拉取镜像

```bash
docker pull username/myapp:v1.0.0
```

---

### 7. 服务器运行容器

```bash
docker run -d \
  --name myapp \
  --restart unless-stopped \
  -p 8080:8080 \
  username/myapp:v1.0.0
```

---

## 十四、Docker 日常排查命令

### 1. 容器启动失败

查看容器状态：

```bash
docker ps -a
```

查看日志：

```bash
docker logs 容器名
```

查看详细信息：

```bash
docker inspect 容器名
```

---

### 2. 端口被占用

错误示例：

```text
Bind for 0.0.0.0:8080 failed: port is already allocated
```

查看端口占用：

macOS/Linux：

```bash
lsof -i :8080
```

或者：

```bash
netstat -an | grep 8080
```

解决方式：

* 停止占用端口的进程
* 换一个宿主机端口

例如：

```bash
docker run -d -p 8081:80 nginx
```

---

### 3. 容器内无法访问外部网络

排查步骤：

```bash
docker exec -it 容器名 sh
```

测试 DNS：

```bash
ping google.com
```

测试 IP：

```bash
ping 8.8.8.8
```

如果 IP 能通但域名不通，通常是 DNS 问题。

---

### 4. 容器之间无法访问

检查是否在同一个网络：

```bash
docker inspect 容器名
```

推荐创建自定义网络：

```bash
docker network create app-network
```

然后容器启动时加入同一个网络：

```bash
docker run -d --name redis --network app-network redis:7
docker run -d --name app --network app-network myapp:v1
```

应用访问 Redis 时使用：

```text
redis:6379
```

---

### 5. 镜像构建很慢

可以从以下几个方面优化：

* 使用 `.dockerignore`
* 减少不必要的文件复制
* 合理利用 Docker 构建缓存
* 把变化频率低的命令放前面
* 使用更小的基础镜像
* 使用多阶段构建

---

### 6. 磁盘空间不足

查看 Docker 占用：

```bash
docker system df
```

清理未使用资源：

```bash
docker system prune
```

清理所有未使用镜像、容器、网络：

```bash
docker system prune -a
```

同时清理数据卷：

```bash
docker system prune -a --volumes
```

注意：带 `--volumes` 可能删除数据库数据，使用前一定要确认。

---

## 十五、Docker 最佳实践

### 1. 生产环境不要随意使用 latest

不推荐：

```bash
docker run nginx:latest
```

推荐：

```bash
docker run nginx:1.26
```

原因是 `latest` 可能随着镜像更新发生变化，导致部署结果不可控。

---

### 2. 使用 .dockerignore

避免把无关文件复制进镜像。

例如：

```text
.git
node_modules
target
logs
.env
```

---

### 3. 使用多阶段构建

尤其是 Go、Java、Node.js 项目，多阶段构建可以明显减少镜像体积。

---

### 4. 一个容器只运行一个主要进程

不建议把 MySQL、Redis、Nginx、应用程序全部塞进一个容器。

推荐方式：

```text
app 一个容器
mysql 一个容器
redis 一个容器
nginx 一个容器
```

然后使用 Docker Compose 或 Kubernetes 管理它们。

---

### 5. 配置通过环境变量注入

不要把数据库密码、API Key 等敏感配置写死在镜像里。

推荐：

```bash
docker run -e DB_PASSWORD=xxx myapp:v1
```

或者使用 Compose：

```yaml
environment:
  DB_PASSWORD: ${DB_PASSWORD}
```

---

### 6. 数据必须持久化

数据库一定要挂载 volume：

```yaml
volumes:
  - mysql-data:/var/lib/mysql
```

否则删除容器后可能导致数据丢失。

---

### 7. 生产环境设置重启策略

推荐：

```bash
--restart unless-stopped
```

例如：

```bash
docker run -d \
  --name app \
  --restart unless-stopped \
  -p 8080:8080 \
  myapp:v1
```

---

### 8. 控制容器资源

限制内存：

```bash
docker run -d \
  --name app \
  --memory=512m \
  myapp:v1
```

限制 CPU：

```bash
docker run -d \
  --name app \
  --cpus=1.5 \
  myapp:v1
```

---

### 9. 不要在镜像中保存敏感信息

避免把这些文件复制进镜像：

```text
.env
id_rsa
secret.yaml
config-prod.yaml
```

可以把敏感信息放在：

* 环境变量
* Secret 管理系统
* CI/CD 变量
* 云平台密钥管理服务

---

### 10. 定期清理无用资源

开发机上 Docker 很容易占用大量磁盘空间。

常用清理命令：

```bash
docker system df
docker system prune
docker image prune -a
docker volume prune
```

---

## 十六、常用命令速查表

### 镜像命令

```bash
docker images
docker pull nginx
docker rmi nginx
docker build -t myapp:v1 .
docker tag myapp:v1 username/myapp:v1
docker push username/myapp:v1
```

---

### 容器命令

```bash
docker ps
docker ps -a
docker run -d --name web -p 8080:80 nginx
docker stop web
docker start web
docker restart web
docker rm web
docker logs -f web
docker exec -it web sh
```

---

### 数据卷命令

```bash
docker volume ls
docker volume create mysql-data
docker volume inspect mysql-data
docker volume rm mysql-data
docker volume prune
```

---

### 网络命令

```bash
docker network ls
docker network create app-network
docker network inspect app-network
docker network rm app-network
docker network prune
```

---

### Compose 命令

```bash
docker compose up
docker compose up -d
docker compose down
docker compose down -v
docker compose ps
docker compose logs -f
docker compose build
docker compose up -d --build
docker compose exec app sh
docker compose config
```

---

### 清理命令

```bash
docker system df
docker system prune
docker system prune -a
docker system prune -a --volumes
```

---

## 十七、Docker 与虚拟机的区别

Docker 容器和虚拟机都可以隔离环境，但它们的实现方式不同。

### 虚拟机

虚拟机会模拟完整的操作系统。

特点：

* 启动较慢
* 占用资源较多
* 隔离性强
* 每个虚拟机都有完整 OS

### Docker 容器

Docker 容器共享宿主机内核。

特点：

* 启动快
* 占用资源少
* 部署方便
* 更适合微服务和云原生应用

简单对比：

```text
虚拟机：像一台完整的电脑
容器：像一个隔离的应用运行环境
```

---

## 十八、Docker 适合哪些场景？

Docker 非常适合以下场景：

* 本地开发环境统一
* 后端服务部署
* 微服务架构
* CI/CD 自动化构建
* 数据库、中间件快速启动
* 测试环境快速搭建
* 云服务器应用部署
* 开源项目一键运行
* 多语言项目环境隔离

例如，一个项目需要同时依赖 Go、Node.js、MySQL、Redis、Nginx，如果手动安装和配置会比较麻烦。使用 Docker Compose 后，只需要维护一个配置文件，就可以快速启动完整环境。

---

## 十九、Docker 不适合哪些场景？

Docker 虽然强大，但也不是万能的。

以下场景需要谨慎：

* 强依赖图形界面的桌面应用
* 对宿主机内核有特殊要求的应用
* 极端高性能、低延迟场景
* 对安全隔离要求非常高的场景
* 不熟悉数据卷管理时直接运行数据库生产环境
* 把 Docker 当成完整虚拟机使用

Docker 更适合运行服务型应用，而不是当成一台完整的 Linux 机器来使用。

---

## 二十、推荐的学习路径

如果是刚开始学习 Docker，可以按下面路线学习：

```text
1. 理解镜像和容器
2. 掌握 docker run、ps、logs、exec、stop、rm
3. 学会端口映射和目录挂载
4. 学会使用数据卷
5. 学会编写 Dockerfile
6. 学会构建自己的镜像
7. 学会使用 Docker Compose
8. 学会部署一个完整项目
9. 学会日志查看和问题排查
10. 学会镜像优化和安全实践
```

---

## 二十一、一个完整项目示例

假设我们有一个 Go Web 项目，目录结构如下：

```text
myapp/
  cmd/
    server/
      main.go
  go.mod
  go.sum
  Dockerfile
  compose.yaml
```

### 1. Dockerfile

```dockerfile
FROM golang:1.22 AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o server ./cmd/server

FROM alpine:3.20

WORKDIR /app

COPY --from=builder /app/server /app/server

EXPOSE 8080

CMD ["/app/server"]
```

---

### 2. compose.yaml

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: go-app
    ports:
      - "8080:8080"
    environment:
      APP_ENV: dev
      MYSQL_HOST: mysql
      MYSQL_PORT: 3306
      MYSQL_USER: root
      MYSQL_PASSWORD: 123456
      MYSQL_DATABASE: app_db
      REDIS_HOST: redis
      REDIS_PORT: 6379
    depends_on:
      - mysql
      - redis
    networks:
      - app-network

  mysql:
    image: mysql:8.0
    container_name: go-mysql
    environment:
      MYSQL_ROOT_PASSWORD: 123456
      MYSQL_DATABASE: app_db
    ports:
      - "3306:3306"
    volumes:
      - mysql-data:/var/lib/mysql
    networks:
      - app-network

  redis:
    image: redis:7
    container_name: go-redis
    ports:
      - "6379:6379"
    networks:
      - app-network

volumes:
  mysql-data:

networks:
  app-network:
    driver: bridge
```

---

### 3. 启动项目

```bash
docker compose up -d --build
```

---

### 4. 查看状态

```bash
docker compose ps
```

---

### 5. 查看日志

```bash
docker compose logs -f app
```

---

### 6. 进入应用容器

```bash
docker compose exec app sh
```

---

### 7. 停止项目

```bash
docker compose down
```

---

### 8. 停止并删除数据

```bash
docker compose down -v
```

注意：这个命令会删除 MySQL 数据卷，数据库数据会丢失。

---

## 二十二、常见问题总结

### 1. docker: command not found

说明 Docker 没有安装成功，或者命令没有加入 PATH。

检查：

```bash
docker version
```

如果 macOS 使用 Docker Desktop，需要确认 Docker Desktop 已经启动。

---

### 2. Cannot connect to the Docker daemon

常见原因：

* Docker 服务没有启动
* 当前用户没有权限访问 Docker
* Docker Desktop 没有打开

Linux 上可以检查：

```bash
sudo systemctl status docker
```

启动：

```bash
sudo systemctl start docker
```

---

### 3. 端口冲突

错误示例：

```text
port is already allocated
```

解决：

```bash
lsof -i :端口号
```

换一个宿主机端口即可：

```bash
docker run -p 8081:80 nginx
```

---

### 4. 容器启动后马上退出

查看日志：

```bash
docker logs 容器名
```

常见原因：

* 启动命令执行完就退出
* 应用启动失败
* 配置文件错误
* 端口或依赖服务不可用
* 环境变量缺失

---

### 5. 修改代码后容器没有更新

如果代码已经构建进镜像，需要重新构建：

```bash
docker compose up -d --build
```

如果是 bind mount 挂载目录，需要确认挂载路径是否正确。

---

### 6. 数据库连接不上

排查点：

* 数据库容器是否启动
* 端口是否映射
* 用户名密码是否正确
* 应用和数据库是否在同一个 Docker 网络
* Compose 中是否使用服务名作为主机名

在 Compose 中，不要使用 `localhost` 访问 MySQL，应该使用服务名：

```text
mysql:3306
```

因为 `localhost` 指的是当前容器自身，不是 MySQL 容器。

---

## 二十三、总结

Docker 的核心价值是标准化应用运行环境。

它让我们可以把应用和依赖一起打包，做到：

* 本地开发更稳定
* 测试环境更容易搭建
* 部署流程更清晰
* 多服务管理更方便
* 应用迁移更简单

学习 Docker 不需要一开始就掌握所有复杂概念。最重要的是先掌握以下内容：

```text
镜像
容器
端口映射
数据卷
网络
Dockerfile
Docker Compose
```

当这些内容熟悉之后，就可以把 Docker 用到真实项目中，例如：

* 本地启动 MySQL、Redis
* 部署 Go、Java、Node.js 服务
* 使用 Compose 管理完整开发环境
* 配合 CI/CD 自动构建和发布镜像

Docker 是现代后端开发、云原生和 DevOps 工作流中非常重要的基础工具，值得系统学习和长期使用。
