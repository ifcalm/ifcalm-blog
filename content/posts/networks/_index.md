---
title: "CS 450：计算机网络"
description: "一门完整的美式大学计算机网络课程：自顶向下，从 HTTP 讲到以太网，配 29 讲课堂笔记、5 个编程实验、4 套习题与考试复习指南。"
summary: "按美国研究型大学一学期 15 周的教学计划完整开设：Syllabus、29 讲 Lecture Notes、5 个 Programming Assignment、4 套 Problem Set（含参考答案）、期中期末复习指南与术语表。教材对应 Kurose & Ross《Computer Networking: A Top-Down Approach》第 8 版。"
layout: "list"
---

这是一门**完整开设**的计算机网络课程，不是读书笔记，也不是知识点罗列。

它按美国研究型大学一个学期（15 周）的实际教学计划组织：有 Syllabus，有周计划，有编程作业，有习题和完整参考答案，有期中期末的复习范围。你可以把它当成一门可以自学完成的课来上。

## 课程信息

| 项目 | 内容 |
|---|---|
| **课程编号** | CS 450 — Computer Networks |
| **学分** | 4 credits（3 小时 Lecture + 1 小时 Discussion Section） |
| **学期** | 15 周 · 每周 2 次课（每次 75 分钟） |
| **教材** | Kurose & Ross, *Computer Networking: A Top-Down Approach*, 8th Edition |
| **先修** | 数据结构与算法、C 或 Python 编程、基础概率论；建议已学操作系统 |
| **课程层次** | 本科高年级（Upper-division undergraduate），研究生可选修 |
| **授课方式** | 自顶向下（Top-Down）：应用层 → 传输层 → 网络层 → 链路层 → 无线 → 安全 |

📄 **[先读教学大纲 Syllabus]({{< ref "00-syllabus.md" >}})** —— 包含课程定位、学习目标、先修要求、教材，以及标明每讲对应教材章节的 15 周日程表。

## 为什么是「自顶向下」

传统教材从物理层开始讲电压和编码，学生要到第十周才第一次看到一个真实的网络应用。自顶向下反过来：第一周就打开浏览器抓包，看 HTTP 请求长什么样，然后不断追问「它下面靠什么支撑」。

这是 Kurose & Ross 从 1999 年起推动、如今被美国绝大多数计算机系采用的顺序。它的好处很实际：**每一层的存在理由，都由上一层提出的需求来解释。**你不会学到一个不知道为什么存在的机制。

## 课程结构

课程分为七个单元，共 29 讲。

### Unit 1 · 计算机网络与互联网（第 1–4 讲）
互联网的组成、分组交换的核心思想、时延与吞吐量的定量分析、协议分层。

- [第 1 讲：互联网是什么——网络边缘与接入网]({{< ref "01-what-is-the-internet.md" >}})
- [第 2 讲：网络核心——分组交换与电路交换]({{< ref "02-network-core.md" >}})
- [第 3 讲：时延、丢包与吞吐量]({{< ref "03-delay-loss-throughput.md" >}})
- [第 4 讲：协议分层、封装与安全威胁概览]({{< ref "04-protocol-layers.md" >}})

### Unit 2 · 应用层（第 5–9 讲）
从 HTTP 开始，理解应用如何使用网络，以及网络对应用提出了什么要求。

- [第 5 讲：应用层原理与 HTTP]({{< ref "05-application-layer-http.md" >}})
- [第 6 讲：Web 缓存、CDN 与 HTTP/2、HTTP/3]({{< ref "06-web-caching-cdn-http2-http3.md" >}})
- [第 7 讲：DNS——互联网的目录服务]({{< ref "07-dns.md" >}})
- [第 8 讲：电子邮件、P2P、流媒体与实时多媒体]({{< ref "08-email-p2p-streaming.md" >}})
- [第 9 讲：Socket 编程]({{< ref "09-socket-programming.md" >}})

### Unit 3 · 传输层（第 10–16 讲）
课程最难也最重要的部分：如何在不可靠的网络上造出可靠的管道，以及如何让所有人共享带宽而不崩溃。

- [第 10 讲：传输层服务、多路复用与 UDP]({{< ref "10-transport-layer-udp.md" >}})
- [第 11 讲：可靠数据传输原理]({{< ref "11-reliable-data-transfer.md" >}})
- [第 12 讲：流水线协议——GBN 与 Selective Repeat]({{< ref "12-pipelined-protocols.md" >}})
- [第 13 讲：TCP——报文段结构、RTT 估计与可靠传输]({{< ref "13-tcp-basics.md" >}})
- [第 14 讲：TCP 连接管理与流量控制]({{< ref "14-tcp-connection-flow-control.md" >}})
- [第 15 讲：拥塞控制原理]({{< ref "15-congestion-control-principles.md" >}})
- [第 16 讲：TCP 拥塞控制——Reno、CUBIC、BBR 与 ECN]({{< ref "16-tcp-congestion-control.md" >}})

### Unit 4 · 网络层：数据平面（第 17–19 讲）
路由器内部如何在纳秒级别转发分组、调度与流量监管如何给出时延保证，以及 IP 地址体系为什么长成今天这样。

- [第 17 讲：网络层数据平面、调度与流量监管]({{< ref "17-network-layer-data-plane.md" >}})
- [第 18 讲：IPv4 编址、子网划分、CIDR、DHCP 与 NAT]({{< ref "18-ipv4-addressing-nat.md" >}})
- [第 19 讲：IPv6、隧道与泛化转发（SDN 数据平面）]({{< ref "19-ipv6-and-generalized-forwarding.md" >}})

### Unit 5 · 网络层：控制平面（第 20–22 讲）
路由表是怎么算出来的，以及全球六万多个自治系统如何达成一致。

- [第 20 讲：路由算法——链路状态与距离向量]({{< ref "20-routing-algorithms.md" >}})
- [第 21 讲：域内路由 OSPF 与域间路由 BGP]({{< ref "21-ospf-bgp.md" >}})
- [第 22 讲：SDN 控制平面、ICMP 与网络管理]({{< ref "22-sdn-icmp-management.md" >}})

### Unit 6 · 链路层、局域网与数据中心（第 23–24 讲）
- [第 23 讲：链路层服务与差错检测]({{< ref "23-link-layer-error-detection.md" >}})
- [第 24 讲：多路访问协议、以太网、交换机与数据中心网络]({{< ref "24-multiple-access-ethernet-switches.md" >}})

### Unit 7 · 无线、移动与安全（第 25–29 讲）
- [第 25 讲：无线链路与 802.11 WiFi]({{< ref "25-wireless-wifi.md" >}})
- [第 26 讲：蜂窝网络 4G/5G 与移动性管理]({{< ref "26-cellular-mobility.md" >}})
- [第 27 讲：网络安全——密码学、完整性与认证]({{< ref "27-security-cryptography.md" >}})
- [第 28 讲：TLS、IPsec、防火墙与 DDoS 防御]({{< ref "28-tls-ipsec-firewalls.md" >}})
- [第 29 讲：综合——一个网页请求的一生]({{< ref "29-day-in-the-life.md" >}})

## 编程作业（Programming Assignments）

五个动手作业，难度递增。风格参考 Stanford CS144 与 UMass Wireshark Labs。

| 作业 | 内容 | 语言 | 对应讲次 |
|---|---|---|---|
| [Lab 0]({{< ref "70-lab0-warmup.md" >}}) | 网络工具热身：curl、dig、traceroute、netcat | Shell | 3、5、7、14 |
| [Lab 1]({{< ref "71-lab1-wireshark.md" >}}) | Wireshark 抓包分析（HTTP / DNS / TCP / IP / 802.11） | — | 5、7、13、16、24、25 |
| [Lab 2]({{< ref "72-lab2-web-server.md" >}}) | 用 Socket 实现并发 HTTP 服务器与客户端 | Python | 5、6、9 |
| [Lab 3]({{< ref "73-lab3-reliable-transport.md" >}}) | 在 UDP 之上实现可靠传输协议（含拥塞控制） | Python/C++ | 11、12、13、15、16 |
| [Lab 4]({{< ref "74-lab4-router-routing.md" >}}) | 实现距离向量路由与最长前缀匹配转发表 | Python/C++ | 17、18、20、21 |

## 习题与考试

- [Problem Set 1]({{< ref "80-problem-set-1.md" >}})：引论与应用层（第 1–9 讲）
- [Problem Set 2]({{< ref "81-problem-set-2.md" >}})：传输层（第 10–16 讲）
- [Problem Set 3]({{< ref "82-problem-set-3.md" >}})：网络层与链路层（第 17–24 讲）
- [Problem Set 4]({{< ref "83-problem-set-4.md" >}})：无线、移动性与网络安全（第 25–29 讲）
- [期中与期末复习指南]({{< ref "90-exam-guide.md" >}})：必背公式卡、高频考点清单与两份模拟题

## 工具书

- [术语表：英中对照与速查]({{< ref "95-glossary.md" >}})
- [参考资料与延伸阅读]({{< ref "96-resources.md" >}})：RFC 清单、公开课、经典论文

## 怎么用这门课

**如果你是在自学：** 按 Syllabus 的 15 周日程走。每讲读完正文先做「随堂自测」，一周结束时做对应的 Problem Set。不要跳过实验——网络这门课，不抓一次包、不写一次 socket，理解永远停留在名词层面。

**如果你在准备面试：** 第 5、7、13、14、16、18、24、29 讲是被问得最多的部分。第 29 讲（一个网页请求的一生）几乎是所有网络面试的终极题。

**如果你只想搞懂某个具体问题：** 用[术语表]({{< ref "95-glossary.md" >}})反查。

> 本课程内容基于公开教材、RFC 文档与公开课程材料整理，用于学习与普及。文中的课程编号、评分比例和日程为教学设计示例，不对应任何真实院校的具体开课记录。协议细节以对应 RFC 的最新版本为准。
