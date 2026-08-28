---
title: "Lab 2：用 Socket 实现并发 HTTP 服务器"
date: 2026-08-28
weight: 72
tags: ["计算机网络"]
draft: false
summary: "从零实现一个能被真实浏览器访问的 HTTP/1.1 服务器：请求解析、持续连接、并发处理、条件 GET 与缓存。不许用任何 HTTP 库。占总成绩 10%。"
showToc: true
tocOpen: false
---

> 💻 **语言**：Python 3.9+（仅允许标准库中的 `socket`、`selectors`、`threading`、`os`、`hashlib` 等）

---

## ⚠️ 禁止使用的库

```
❌ http.server / socketserver / BaseHTTPRequestHandler
❌ flask / django / fastapi / tornado / aiohttp / requests
❌ 任何第三方 HTTP 解析库

✅ socket, selectors, threading, asyncio, os, sys, time, hashlib,
   mimetypes, urllib.parse（仅用于 URL 解码）
```

📌 **本作业的全部意义在于亲手实现协议。**用了 HTTP 库 = 0 分。

---

## Part 1：基础 HTTP 服务器（30 分）

### 需求

```
python3 server.py --port 8080 --root ./www
```

启动后，浏览器访问 `http://localhost:8080/index.html` 应当能看到 `./www/index.html` 的内容。

### 必须实现

| 功能 | 要求 |
|---|---|
| **GET 方法** | 返回文件内容 |
| **HEAD 方法** | ⭐ 只返回首部，不返回实体体 |
| **200 OK** | 文件存在且可读 |
| **404 Not Found** | 文件不存在 |
| **403 Forbidden** | 文件存在但无读权限 |
| **400 Bad Request** | 请求行格式错误 |
| **405 Method Not Allowed** | 不支持的方法（须带 `Allow:` 首部） |
| **Content-Type** | ⭐ 根据扩展名正确设置（用 `mimetypes`） |
| **Content-Length** | 必须准确 |
| **Date** | RFC 7231 格式的 GMT 时间 |

### ⭐ 安全要求：路径穿越防护（必做，5 分）

```
攻击请求:  GET /../../etc/passwd HTTP/1.1

⭐ 你的服务器【绝不能】返回 www 目录之外的任何文件。
```

**正确做法**：

```python
import os

def safe_path(root: str, url_path: str) -> str | None:
    # 1. URL 解码
    # 2. 拼接并规范化
    full = os.path.realpath(os.path.join(root, url_path.lstrip('/')))
    root_real = os.path.realpath(root)
    # 3. ⭐ 检查规范化后的路径仍在 root 之内
    if not full.startswith(root_real + os.sep) and full != root_real:
        return None
    return full
```

⚠️ **注意必须用 `realpath` 而非 `abspath`**——前者会解析符号链接，后者不会。**只做字符串检查 `if '..' in path` 是不够的**（URL 编码 `%2e%2e` 可以绕过）。

### ⭐ 关键难点：读取完整的请求

```python
def read_request_head(conn) -> bytes:
    """读取直到 \r\n\r\n。⭐ 不能假设一次 recv 就能读到完整请求。"""
    buf = b''
    while b'\r\n\r\n' not in buf:
        chunk = conn.recv(4096)
        if not chunk:                       # 对端关闭
            raise ConnectionError('peer closed before request complete')
        buf += chunk
        if len(buf) > 8192:                 # ⭐ 防止内存耗尽攻击
            raise ValueError('request head too large')
    return buf
```

📌 **这正是第 9 讲「坑 1：TCP 没有报文边界」的实战。**HTTP 用 `\r\n\r\n` 作为首部结束的分隔符——这是第 9 讲说的三种定界方式中的「分隔符」方案。

---

## Part 2：持续连接（20 分）

### 需求

实现 HTTP/1.1 的默认持续连接：

```
① 处理完一个请求后【不关闭连接】，继续等待下一个请求
② 遇到 Connection: close 首部 → 处理完后关闭
③ ⭐ 设置空闲超时（建议 5 秒），超时后主动关闭
④ 响应中正确设置 Connection 首部
```

### ⭐ 关键难点：如何知道一个请求结束了

```
对 GET/HEAD：  首部结束（\r\n\r\n）即请求结束
对 POST/PUT：  ⭐ 还要按 Content-Length 精确读取指定字节的请求体
              （多读一个字节，下一个请求就解析错了）
```

**验证你的实现**：

```bash
# 在一条连接上连发两个请求
printf 'GET /a.html HTTP/1.1\r\nHost: x\r\n\r\nGET /b.html HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n' \
  | nc localhost 8080
```

⭐ **应当收到两个完整的响应。**如果只收到一个，说明你的请求边界处理有问题。

---

## Part 3：并发处理（25 分）

### 需求

⭐ **一个慢客户端不能阻塞其他客户端。**

**任选一种实现**（在报告中说明你选了哪种及理由）：

| 方案 | 分值上限 | 说明 |
|---|---|---|
| **每连接一线程** | 20/25 | 最简单，需正确处理线程清理 |
| ⭐ **I/O 多路复用（selectors）** | 25/25 | 单线程 epoll/kqueue |
| ⭐ **asyncio** | 25/25 | 异步版本 |
| 线程池 | 23/25 | 需说明池大小的选择依据 |

### 验证

```bash
# 客户端 A：请求一个会让服务器慢的资源（可自行加一个 /slow 端点 sleep 5 秒）
curl http://localhost:8080/slow &

# 客户端 B：立刻请求普通资源
time curl http://localhost:8080/index.html

# ⭐ B 应当【立即】返回，而不是等 5 秒
```

⚠️ **如果你用 selectors 或 asyncio，注意不要在事件循环里做阻塞操作**（第 9 讲）——`time.sleep()`、同步文件读取大文件都会卡死整个服务器。

---

## Part 4：缓存与条件 GET（15 分）

### 需求

```
① 响应中包含 Last-Modified（文件的 mtime，GMT 格式）
② 响应中包含 ETag（⭐ 建议用文件内容的 SHA-256 前 16 位，或 mtime+size 的哈希）
③ ⭐ 收到 If-Modified-Since：文件未修改则返回 304，【不带实体体】
④ ⭐ 收到 If-None-Match：ETag 匹配则返回 304
⑤ 响应中包含合理的 Cache-Control
```

⚠️ **304 响应的三条规则**（RFC 9110）：

```
⭐ 不能有实体体
⭐ 不能有 Content-Length（或必须为 0）
⭐ 必须包含 ETag（如果 200 响应会包含的话）
```

### 验证

```bash
ETAG=$(curl -sI http://localhost:8080/index.html | grep -i etag | cut -d' ' -f2 | tr -d '\r')
curl -v -H "If-None-Match: $ETAG" http://localhost:8080/index.html
# ⭐ 应当返回 304，且响应体为空
```

---

## Part 5：并发客户端（10 分）

实现 `client.py`，用**多线程或异步**同时发起 N 个请求并统计性能：

```bash
python3 client.py --url http://localhost:8080/index.html --n 100 --concurrency 10
```

**输出要求**：

```
Requests:     100
Concurrency:  10
Success:      100
Failed:       0
Total time:   1.234 s
Throughput:   81.0 req/s
Latency (ms): min=2.1  p50=8.4  p95=24.7  p99=41.2  max=52.0
```

⚠️ **必须自己用 socket 实现 HTTP 请求，不能用 `requests` 或 `urllib`。**

---

## 报告要求（含在评分中）

`report.md` 需回答：

1. ⭐ **你如何处理"TCP 没有报文边界"？**给出你的代码片段并解释
2. ⭐ **你选择了哪种并发模型？为什么？**在什么场景下另一种更好？
3. ⭐ **你如何防止路径穿越？**为什么字符串检查 `'..' in path` 不够？
4. ⭐ **测量数据**：用 Part 5 的客户端测试，给出并发度 1 / 10 / 100 时的吞吐量与 p99 时延，**并解释你观察到的趋势**
5. **你遇到的最难的 bug 是什么？怎么定位的？**（真诚回答有分）

---

## 提示

📌 **从最小可用版本开始**：先做一个只能处理 GET 并返回 200 的单线程服务器，用浏览器验证能打开。**先跑通再加功能。**

📌 **调试利器**：一边跑服务器一边用 Wireshark 抓 `tcp.port == 8080`。你会立刻看到自己发出的报文哪里格式不对。

📌 **最常见的三个 bug**：
1. 用 `\n` 而不是 `\r\n`（浏览器可能容忍，但严格的客户端不会）
2. `Content-Length` 算错（尤其是 UTF-8 中文，**字节数 ≠ 字符数**）
3. 假设一次 `recv` 就能读到完整请求

