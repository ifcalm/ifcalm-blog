---
title: "第 9 讲：Socket 编程"
date: 2026-08-25
weight: 9
tags: ["计算机网络"]
draft: false
summary: "用 Python 从零写 UDP 与 TCP 的客户端和服务器；欢迎套接字与连接套接字的区别；并发模型的三种选择；以及每个人第一次写网络程序都会踩的五个坑：粘包、部分读写、字节序、TIME_WAIT 与阻塞。"
showToc: true
tocOpen: false
---

## 一、Socket 是什么

回顾第 5 讲：**Socket 是应用层与传输层之间的 API 边界**。

```
  你的代码
     │
     ▼
 ┌────────┐  ← socket()、bind()、send()、recv() ...
 │ Socket │
 └────────┘
     │
     ▼
 操作系统内核：TCP/UDP 实现、IP 栈、网卡驱动
```

**你控制**：用 TCP 还是 UDP、发什么数据、什么时候发、少量参数（超时、缓冲区大小、Nagle 开关）。
**你不控制**：分组怎么走、重传的时机、拥塞窗口怎么变。

---

## 二、UDP 编程

### 2.1 UDP 的模型

**没有连接。**每次发送都必须显式指定目的地址；每次接收都会告诉你来自谁。

```
客户端                              服务器
  │                                   │
  │                             socket() 创建
  │                             bind() 绑定端口 12000
  │                                   │
socket() 创建                    recvfrom() 阻塞等待
  │                                   │
sendto(数据, (服务器IP, 12000)) ───→  收到，得到 (数据, 客户端地址)
  │                                   │
recvfrom() ←──────────────────  sendto(响应, 客户端地址)
  │                                   │
close()                          回到 recvfrom()
```

⭐ **注意**：服务器**不需要**为每个客户端创建新 socket。一个 socket 处理所有人，靠 `recvfrom` 返回的地址来区分。

### 2.2 UDP 服务器代码

```python
# udp_server.py —— 把收到的内容转成大写返回
from socket import socket, AF_INET, SOCK_DGRAM

SERVER_PORT = 12000

server_socket = socket(AF_INET, SOCK_DGRAM)   # AF_INET=IPv4, SOCK_DGRAM=UDP
server_socket.bind(('', SERVER_PORT))          # '' 表示监听所有网卡
print(f"UDP server ready on port {SERVER_PORT}")

while True:
    message, client_address = server_socket.recvfrom(2048)
    #                          ↑ 一次调用同时拿到数据和对方地址
    modified = message.decode().upper()
    server_socket.sendto(modified.encode(), client_address)
```

### 2.3 UDP 客户端代码

```python
# udp_client.py
from socket import socket, AF_INET, SOCK_DGRAM

SERVER_NAME = 'localhost'
SERVER_PORT = 12000

client_socket = socket(AF_INET, SOCK_DGRAM)
client_socket.settimeout(2.0)        # ⚠️ 必须设超时，UDP 不保证有回应

message = input('Input lowercase sentence: ')
client_socket.sendto(message.encode(), (SERVER_NAME, SERVER_PORT))

try:
    modified, server_address = client_socket.recvfrom(2048)
    print(modified.decode())
except TimeoutError:
    print('No response — packet may have been lost.')   # ← UDP 的现实

client_socket.close()
```

📌 **注意客户端没有 `bind()`**。操作系统会自动分配一个**临时端口**（ephemeral port，通常 49152–65535）。服务器必须 bind 是因为客户端要知道去哪找它；客户端不必，因为服务器从收到的包里就能得到它的地址。

⚠️ **那个 `try/except` 不是可选的。**UDP 下丢包是正常状态，没有超时处理的 UDP 客户端会永久挂起。

---

## 三、TCP 编程

### 3.1 两种 socket：欢迎与连接 ⭐

这是 TCP 编程最容易搞混、也是考试必考的一点。

```
服务器：
  ┌──────────────────┐
  │  欢迎套接字        │  ← 只做一件事：接受新连接
  │ (listening socket)│     一直存在，绑定在端口 12000
  └────────┬─────────┘
           │ accept() 返回
     ┌─────┴──────┬────────────┐
     ▼            ▼            ▼
 ┌────────┐  ┌────────┐  ┌────────┐
 │连接套接字│  │连接套接字│  │连接套接字│  ← 每个客户端一个
 │ 客户A   │  │ 客户B   │  │ 客户C   │     用来真正收发数据
 └────────┘  └────────┘  └────────┘
```

> **欢迎套接字负责「接待」，连接套接字负责「服务」。**
> 就像餐厅门口的迎宾员和每张桌子的服务员。

**这些连接套接字都绑在同一个端口 12000 上，怎么区分？**答案是**四元组**：

```
(源IP, 源端口, 目的IP, 目的端口)
```

三个客户端的源 IP 或源端口不同，因此四元组不同，内核能准确分发。**这就是第 10 讲要讲的「面向连接的多路分解」。**

### 3.2 TCP 服务器代码

```python
# tcp_server.py —— 单线程版本
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR

SERVER_PORT = 12000

welcome_socket = socket(AF_INET, SOCK_STREAM)          # SOCK_STREAM = TCP
welcome_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1) # ⭐ 见第五节「坑 4」
welcome_socket.bind(('', SERVER_PORT))
welcome_socket.listen(5)                                # 5 = 未完成连接队列长度
print(f"TCP server ready on port {SERVER_PORT}")

while True:
    conn_socket, addr = welcome_socket.accept()   # ⭐ 阻塞，直到有连接进来
    print(f"connection from {addr}")

    sentence = conn_socket.recv(1024).decode()
    conn_socket.send(sentence.upper().encode())

    conn_socket.close()      # 只关连接套接字
    # 欢迎套接字继续存在，等下一个客户
```

### 3.3 TCP 客户端代码

```python
# tcp_client.py
from socket import socket, AF_INET, SOCK_STREAM

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect(('localhost', 12000))   # ⭐ 这里触发三次握手

sentence = input('Input lowercase sentence: ')
client_socket.send(sentence.encode())          # 不需要指定地址，连接已建立

response = client_socket.recv(1024)
print(response.decode())

client_socket.close()
```

### 3.4 UDP 与 TCP 编程对比

| | UDP | TCP |
|---|---|---|
| 服务器 socket 数 | **1 个** | 1 个欢迎 + 每客户 1 个连接 |
| 客户端要 connect | ❌ | ✅（触发握手） |
| 发送 API | `sendto(data, addr)` | `send(data)` |
| 接收 API | `recvfrom()` 返回数据+地址 | `recv()` 只返回数据 |
| 报文边界 | ⭐ **保留**（一个 sendto = 一个 recvfrom） | ⭐ **不保留**（字节流） |
| 丢包 | 应用自己处理 | 内核自动重传 |

---

## 四、并发服务器

上面的 TCP 服务器有一个致命问题：**处理客户 A 时，客户 B 只能干等。**如果 A 的请求要 10 秒，所有人都被堵住。

### 4.1 方案一：每连接一线程

```python
import threading
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR

def handle_client(conn_socket, addr):
    try:
        while True:
            data = conn_socket.recv(4096)
            if not data:              # ⭐ 对端关闭连接时 recv 返回 b''
                break
            conn_socket.sendall(data.upper())
    finally:
        conn_socket.close()

welcome = socket(AF_INET, SOCK_STREAM)
welcome.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
welcome.bind(('', 12000))
welcome.listen(128)

while True:
    conn, addr = welcome.accept()
    t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
    t.start()
```

- ✅ 代码直观
- ❌ 每线程约 1–8 MB 栈空间；上下文切换开销；**几千连接就撑不住**（C10K 问题）

### 4.2 方案二：I/O 多路复用（select / poll / epoll）

**一个线程同时监视成千上万个 socket，谁就绪处理谁。**

```python
import selectors, socket

sel = selectors.DefaultSelector()      # Linux 上自动使用 epoll

def accept(sock):
    conn, addr = sock.accept()
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn):
    data = conn.recv(4096)
    if data:
        conn.sendall(data.upper())
    else:
        sel.unregister(conn)
        conn.close()

server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('', 12000))
server.listen(128)
server.setblocking(False)
sel.register(server, selectors.EVENT_READ, accept)

while True:
    for key, _ in sel.select():        # ⭐ 阻塞直到任意 socket 就绪
        callback = key.data
        callback(key.fileobj)
```

- ✅ **单线程处理十万连接**，内存占用极低
- ❌ 回调风格代码难写难读；**任何一个回调里做阻塞操作，整个服务器卡死**

📌 nginx、Redis、Node.js 全部基于这个模型。

### 4.3 方案三：异步（async / await）

```python
import asyncio

async def handle(reader, writer):
    while True:
        data = await reader.read(4096)
        if not data:
            break
        writer.write(data.upper())
        await writer.drain()
    writer.close()

async def main():
    server = await asyncio.start_server(handle, '', 12000)
    async with server:
        await server.serve_forever()

asyncio.run(main())
```

本质仍是 I/O 多路复用，但语法上恢复了顺序代码的可读性。**这是今天的主流选择。**

### 4.4 三种模型对比

| | 多线程 | I/O 多路复用 | 异步 |
|---|---|---|---|
| 可读性 | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ |
| 连接规模 | 千级 | **十万级** | **十万级** |
| 内存占用 | 高 | 低 | 低 |
| CPU 密集任务 | 可（配合多进程） | ❌ 会阻塞全局 | ❌ 会阻塞全局 |
| 代表 | Apache (prefork) | nginx, Redis | Node.js, FastAPI |

---

## 五、五个必踩的坑

### 坑 1：TCP 没有报文边界 ⭐⭐⭐

**这是网络编程第一大坑，Lab 2 和 Lab 3 都会考。**

```python
# 客户端连续发两条
sock.send(b"HELLO")
sock.send(b"WORLD")

# 服务器可能收到：
data = sock.recv(1024)
# 结果可能是 b"HELLOWORLD"  ← 粘在一起了
# 也可能是 b"HEL"           ← 被拆开了
# 也可能是 b"HELLO"         ← 恰好正确（你的测试通过了，生产环境炸了）
```

**根本原因**：**TCP 提供的是一条无结构的字节流。**它从不承诺「你 send 一次，对方 recv 一次」。发送端的 Nagle 算法（第 14 讲）会合并小包，网络会分片，接收端缓冲区会拼接。

**解决办法：应用层必须自己定界。**三种标准做法：

```
① 定长消息          ：每条消息固定 N 字节
② 长度前缀（最常用） ：先发 4 字节长度，再发内容
③ 分隔符           ：用 \r\n\r\n 等标记结束（HTTP 就是这么做的）
```

**长度前缀的正确实现**：

```python
import struct

def send_msg(sock, payload: bytes):
    sock.sendall(struct.pack('>I', len(payload)) + payload)   # 4 字节大端长度

def recv_exactly(sock, n: int) -> bytes:
    """⭐ 必须循环读，recv 不保证一次给够 n 字节"""
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError('peer closed')
        buf += chunk
    return buf

def recv_msg(sock) -> bytes:
    length = struct.unpack('>I', recv_exactly(sock, 4))[0]
    return recv_exactly(sock, length)
```

### 坑 2：`send()` 不保证发完，`recv()` 不保证收满

`send()` 返回**实际发送的字节数**，可能小于你给的长度（内核发送缓冲区满了）。

```python
sock.send(big_data)          # ❌ 可能只发了一部分，剩下的静默丢失
sock.sendall(big_data)       # ✅ 循环直到全部发完
```

`recv(n)` 返回的是「**至多** n 字节」，可能只有 1 字节。必须像上面 `recv_exactly` 那样循环。

### 坑 3：字节序（Endianness）

不同 CPU 的多字节整数存储顺序不同。**网络字节序统一为大端（big-endian）。**

```python
struct.pack('>I', 1024)   # '>' = 大端（网络序）✅
struct.pack('<I', 1024)   # '<' = 小端 ❌ 换台机器就错
struct.pack('I',  1024)   # 跟随本机 ❌ 更糟，错得不明显
```

C 语言里对应的是 `htons()` / `htonl()` / `ntohs()` / `ntohl()`。

### 坑 4：`Address already in use`

服务器关闭后立刻重启，报这个错。原因是 TCP 的 **TIME_WAIT** 状态（第 14 讲会详细讲为什么必须有它）——旧连接还占着那个端口 2×MSL 时间（通常 30–120 秒）。

```python
sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)   # ⭐ bind 之前设置
```

⚠️ 这不是「绕过一个 bug」，而是明确告诉内核：「我知道有 TIME_WAIT 连接，允许我复用这个地址」。

### 坑 5：阻塞与超时

默认所有 socket 操作都是**阻塞**的。没有超时的网络程序，迟早会挂在某次 `recv` 上永不返回。

```python
sock.settimeout(5.0)         # 所有操作 5 秒超时
sock.setblocking(False)      # 完全非阻塞（配合 selectors 使用）
```

📌 **工程原则**：**每一个网络调用都应当有超时。**这条规则没有例外。

---

## 六、例题（Worked Example）

**题目**：一个 TCP 服务器监听 8080 端口，同时有三个客户端连接：

- 客户 A：192.168.1.5:51000
- 客户 B：192.168.1.5:51001（与 A 是同一台机器！）
- 客户 C：203.0.113.9:51000（与 A 端口号相同！）

服务器 IP 为 198.51.100.2。

(a) 服务器上一共有几个 socket？
(b) 内核如何区分这三个连接？写出各自的四元组。
(c) 如果 A 又开了一个新连接，源端口会是什么？

**解答**：

(a) **4 个**：1 个欢迎套接字（绑定 `*:8080`）+ 3 个连接套接字。

(b) 靠**四元组**（源IP, 源端口, 目的IP, 目的端口）：

```
A: (192.168.1.5, 51000, 198.51.100.2, 8080)
B: (192.168.1.5, 51001, 198.51.100.2, 8080)   ← 与 A 只有源端口不同
C: (203.0.113.9, 51000, 198.51.100.2, 8080)   ← 与 A 只有源 IP 不同
```

三者各不相同，因此内核可以准确地把每个到达的报文段交给正确的连接套接字。

⭐ **这解释了为什么一台服务器可以在 80 端口上服务几十万个并发连接**——端口号不是稀缺资源，四元组才是。

(c) 由**客户机操作系统自动分配的另一个临时端口**，例如 51002。客户端不能重复使用 51000，因为那会与已有连接的四元组冲突。

📌 **推论**：**单台客户机对同一个服务器 IP:端口，最多能建约 64K 条连接**（受临时端口范围限制）。这是压力测试工具经常撞到的天花板，解法是给客户机配多个 IP。

---

## 七、随堂自测

1. UDP 服务器为什么只需要一个 socket，而 TCP 服务器需要多个？
2. 欢迎套接字和连接套接字各自的职责是什么？accept() 返回的是哪一个？
3. 客户端为什么通常不需要 bind()？
4. 「我 send 了 3 次，为什么对方 recv 一次就全收到了？」请解释，并给出正确做法。
5. `send()` 和 `sendall()` 的区别是什么？什么时候会出问题？
6. 为什么要 `SO_REUSEADDR`？它绕过的是什么机制？
7. 三种并发模型分别适合什么场景？为什么 nginx 选了 I/O 多路复用？

---

## 八、本讲要点回顾

- **Socket 是应用与传输层的 API 边界。**
- UDP：无连接，`sendto`/`recvfrom`，**保留报文边界**，服务器**一个 socket 走天下**。
- TCP：**欢迎套接字接客，连接套接字服务**；靠**四元组**区分连接。
- ⭐ **TCP 是字节流，没有报文边界。应用必须自己定界**——长度前缀是最稳妥的做法。
- `send` 可能只发一部分，`recv` 可能只收一部分：**都要循环**。
- 多字节整数必须转成**网络字节序（大端）**。
- 并发三选一：**多线程（好写、千级）、I/O 多路复用（十万级、难写）、异步（十万级、好写）**。
- **每一个网络调用都要有超时。**

---

## 九、自测答案

**1.** 因为 UDP 无连接：服务器不维护任何连接状态，每个到达的数据报都自带源地址，`recvfrom` 一次就能同时拿到数据和「这是谁发的」。TCP 是面向连接的，每条连接有独立的序号、窗口、缓冲区等状态，必须用独立的 socket 承载。

**2.** 欢迎套接字（listening socket）只负责**接受新连接**，它绑定在服务端口上并长期存在；连接套接字负责与**某一个特定客户端**收发数据。`accept()` **返回的是新建的连接套接字**（以及对端地址），欢迎套接字本身继续监听。

**3.** 因为客户端不需要一个**可预知的**端口——服务器是从收到的报文里得知客户端地址的。操作系统会自动分配一个临时端口。（需要 bind 的情况：要固定源端口以穿过特定防火墙规则，或要指定从哪块网卡发出。）

**4.** 因为 **TCP 是字节流，不保留报文边界**。发送端的 Nagle 算法可能把三次 send 合并成一个段，接收端缓冲区把到达的数据拼接起来，一次 `recv` 就全拿走了。正确做法是在应用层自己定界：**长度前缀**（先发 4 字节长度再发内容）、定长消息、或分隔符。

**5.** `send()` 返回实际写入内核发送缓冲区的字节数，**可能小于请求长度**，剩余部分需要你自己再发；`sendall()` 内部循环直到全部发完（或抛异常）。当数据量大于内核发送缓冲区、或对端接收慢导致流量控制生效（第 14 讲）时，`send()` 就会只发一部分——这时用 `send` 而不检查返回值会造成**静默的数据截断**。

**6.** 因为主动关闭连接的一方会进入 **TIME_WAIT** 状态并持续 2×MSL，期间该 (IP, 端口) 组合被占用，重新 bind 会失败。`SO_REUSEADDR` 告诉内核允许在存在 TIME_WAIT 连接的情况下绑定该地址。它不是绕过 bug，而是显式接受 TIME_WAIT 所防范的风险（旧连接的迟到报文被误认，第 14 讲）。

**7.** 多线程适合**连接数不多但每个连接需要复杂/阻塞处理**的场景，代码好写；I/O 多路复用适合**海量并发、每连接处理很轻**的场景（反向代理、缓存），内存和切换开销极低；异步在保持多路复用性能的同时恢复了可读性，适合新写的高并发服务。nginx 选多路复用，是因为它的典型负载正是「十万级并发连接 + 每连接只做转发这种极轻的工作」——多线程模型在这个负载下会被上下文切换和内存耗尽。

