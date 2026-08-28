---
title: "Lab 0：网络工具热身"
date: 2026-08-28
weight: 70
tags: ["计算机网络"]
draft: false
summary: "用 curl、dig、traceroute、netcat、ss 亲手观察真实网络。第一周的入门作业：不写一行代码，但要能解释你看到的每一个数字。占总成绩 2%。"
showToc: true
tocOpen: false
---

> 📅 **发布**：第 1 周 · **截止**：第 2 周周五 23:59
> 💯 **占比**：总成绩 **2%**（20 分）
> 🔧 **环境**：Linux / macOS 终端；Windows 用户使用 WSL2

---

## 作业目标

这个作业不写代码，目的只有一个：**让你相信这门课讲的东西是真的。**

完成后你应当能够：

1. 用 `dig` 观察 DNS 的层次结构与缓存效果
2. 用 `traceroute` 观察真实的路径与逐跳时延
3. 用 `curl -v` 读懂一次完整的 HTTP/TLS 交互
4. 用 `netcat` 手工"说" HTTP 协议
5. 用 `ss` 观察本机的 TCP 连接状态

---

## 环境准备

```bash
# macOS
brew install bind netcat iproute2mac

# Ubuntu / Debian / WSL2
sudo apt update && sudo apt install -y dnsutils traceroute netcat-openbsd iproute2 curl
```

**验证安装**：

```bash
dig -v && curl --version && traceroute --version
```

---

## Part A：DNS（5 分）

### A1. 基本解析（1 分）

```bash
dig www.wikipedia.org
```

**要回答的问题**：

1. `ANSWER SECTION` 中返回了几条记录？分别是什么类型？
2. 如果出现了 CNAME，说明了什么？（提示：第 6、7 讲）
3. 各条记录的 TTL 分别是多少？为什么它们可能不同？

### A2. 观察缓存效果（1 分）

```bash
dig www.wikipedia.org | grep "Query time"
# 立刻再执行一次
dig www.wikipedia.org | grep "Query time"
```

**要回答**：两次的 `Query time` 差多少？解释原因（第 7 讲）。

### A3. 追踪完整的层次结构（2 分）⭐

```bash
dig +trace www.wikipedia.org
```

**要回答**：

1. 一共经过了几级服务器？分别是什么角色？
2. 找出输出中根服务器、TLD 服务器、权威服务器各自的回答
3. 这是**迭代查询**还是**递归查询**？为什么？

### A4. 查询不同的记录类型（1 分）

```bash
dig wikipedia.org MX          # 邮件服务器
dig wikipedia.org NS          # 权威服务器
dig wikipedia.org AAAA        # IPv6 地址
dig -x 8.8.8.8                # 反向解析
```

**要回答**：`-x` 做的是什么类型的查询？它的 `Name` 字段长什么样，为什么？

---

## Part B：路径与时延（5 分）

### B1. traceroute（2 分）

```bash
traceroute www.wikipedia.org
traceroute 1.1.1.1
```

**要回答**：

1. 到这两个目标各经过几跳？
2. ⭐ 是否出现 `* * *`？这说明该跳故障了吗？（第 3、22 讲）
3. ⭐ 是否出现某一跳的时延**大于**它后面的跳？给出至少两种解释。

### B2. ping 与时延分布（2 分）

```bash
ping -c 20 1.1.1.1
```

**要回答**：

1. 记录 min / avg / max / mdev 四个值
2. ⭐ max 与 min 的差距说明了什么？（提示：第 3 讲的排队时延）
3. 估算你到该服务器的**物理距离下界**（用 `d = 传播速度 × 单向时延`，传播速度取 2×10⁸ m/s）

### B3. Bufferbloat 实测（1 分）⭐

```bash
# 终端 1：持续 ping
ping 1.1.1.1

# 终端 2：同时开始一个大文件下载（或在浏览器里下载任意大文件）
curl -o /dev/null https://speed.cloudflare.com/__down?bytes=200000000
```

**要回答**：下载开始后 ping 值变化了多少？这是什么现象？（第 16 讲）

---

## Part C：HTTP（6 分）

### C1. 读懂 curl -v（2 分）

```bash
curl -v https://example.com -o /dev/null
```

**在输出中找出并标注**：

1. DNS 解析结果
2. TCP 连接建立
3. ⭐ TLS 握手：协议版本、密码套件
4. ⭐ 服务器证书的颁发者与有效期
5. 发出的 HTTP 请求首部
6. 收到的 HTTP 响应状态码与首部

### C2. 各阶段耗时（2 分）⭐

```bash
curl -w "\nDNS:      %{time_namelookup}\nTCP:      %{time_connect}\nTLS:      %{time_appconnect}\n首字节:   %{time_starttransfer}\n总计:     %{time_total}\n" \
     -o /dev/null -s https://www.wikipedia.org
```

**要回答**：

1. 哪个阶段最耗时？
2. ⭐ 用同样的命令再跑一次，哪些时间变小了？为什么？
3. 把每个阶段与第 29 讲的时间线对应起来

### C3. 条件 GET（1 分）

```bash
curl -v https://example.com -o /dev/null 2>&1 | grep -i "last-modified\|etag"

# 用上一步得到的 ETag 值：
curl -v -H 'If-None-Match: "你得到的ETag"' https://example.com -o /dev/null
```

**要回答**：第二次请求的状态码是什么？响应体有多大？省下了什么、没省下什么？（第 5 讲）

### C4. 手工说 HTTP（1 分）⭐

```bash
printf 'GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n' | nc example.com 80
```

**要回答**：

1. ⭐ 为什么必须有 `Host:` 首部？去掉它试试会怎样（第 5 讲）
2. ⭐ 为什么行尾必须是 `\r\n` 而不是 `\n`？
3. 为什么这里用 80 端口而不是 443？换成 443 会怎样？

---

## Part D：本机连接状态（4 分）

### D1. 查看连接（2 分）

```bash
ss -tan               # 所有 TCP 连接及状态
ss -tlnp              # 正在监听的端口
```

**要回答**：

1. 找出至少三种不同的 TCP 状态，说明各自的含义（第 14 讲）
2. ⭐ 找出处于 `TIME_WAIT` 的连接。它为什么存在？会持续多久？
3. 你的机器上有哪些进程在监听端口？其中有没有你不认识的？

### D2. 观察四元组（2 分）⭐

```bash
# 终端 1
nc -l 9999

# 终端 2
nc localhost 9999

# 终端 3
ss -tan | grep 9999
```

**要回答**：

1. 你看到了几条连接记录？为什么（第 9、10 讲）
2. ⭐ 写出这条连接的完整四元组
3. 再开一个 `nc localhost 9999`，四元组的哪一项变了？

---

## 提交要求

提交一个 **PDF 或 Markdown 文件**，命名为 `lab0_<你的学号>.pdf`，包含：

1. 每一小题的**命令输出截图或粘贴**（可截取关键部分）
2. 每一小题的**文字回答**
3. 文件末尾附 `AI_USAGE.md` 声明（见 [Syllabus]({{< ref "00-syllabus.md" >}}) 的 AI 工具政策）

⚠️ **只贴输出不作答不得分。**本作业考察的是**解释能力**，不是执行命令的能力。

---

## 评分标准（Rubric）

| 项目 | 分值 | 满分标准 |
|---|---|---|
| Part A：DNS | 5 | 正确识别层次结构与缓存效应，能解释 CNAME 与 TTL 差异 |
| Part B：路径与时延 | 5 | 正确解释 `* * *` 与时延倒挂，bufferbloat 观察有数据支撑 |
| Part C：HTTP | 6 | 能逐段读懂 curl 输出，正确解释 Host 与 CRLF 的必要性 |
| Part D：连接状态 | 4 | 正确写出四元组，正确解释 TIME_WAIT |
| **合计** | **20** | |

**扣分项**：

- 只贴输出、无解释：该小题 **0 分**
- 解释明显来自复制粘贴而与自己的实际输出不符：该 Part **0 分**
- 未提交 `AI_USAGE.md`：**扣 2 分**

---

## 常见问题

**Q：`traceroute` 全是 `* * *` 怎么办？**
A：某些网络（尤其是企业网、部分校园网）会屏蔽 ICMP 或 UDP 探测。试试 `traceroute -I`（用 ICMP）或 `traceroute -T -p 443`（用 TCP SYN）。在报告中说明你用了哪种方式，这本身就是一个好的观察。

**Q：`dig +trace` 报错？**
A：某些网络强制所有 DNS 走本地解析器，无法直接查询根服务器。可以改用在线工具（如 `dig` 的 Web 版本）完成 A3，并在报告中说明原因。

**Q：Bufferbloat 测试看不出变化？**
A：说明你的路由器可能已经启用了 AQM（现代路由器越来越多默认开启 FQ-CoDel），或者你的带宽远大于测试流量。试试同时开多个下载。**观察到"没有 bufferbloat"也是一个有效结论**，但要说明你的测试条件。

---

## 提示

📌 **这个作业最大的价值不在于分数，而在于建立一个习惯**：当你对网络有疑问时，**你可以直接去看**。这门课后面所有的抽象概念，都能在这些工具里找到对应的观察。

📌 **建议把这些命令加进你的日常工具箱**。`curl -w` 的计时输出在排查线上问题时极其有用。

---

*相关讲次：[第 3 讲（时延）]({{< ref "03-delay-loss-throughput.md" >}}) · [第 5 讲（HTTP）]({{< ref "05-application-layer-http.md" >}}) · [第 7 讲（DNS）]({{< ref "07-dns.md" >}}) · [第 14 讲（TCP 状态）]({{< ref "14-tcp-connection-flow-control.md" >}})*
*下一个实验：[Lab 1：Wireshark 抓包分析]({{< ref "71-lab1-wireshark.md" >}})*
