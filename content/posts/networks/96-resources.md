---
title: "参考资料与延伸阅读"
date: 2026-08-28
weight: 96
tags: ["计算机网络"]
draft: false
summary: "教材与免费开放教科书、按讲次编排的 RFC 阅读清单、值得读的经典论文、公开课与实验平台、以及一份「学完这门课之后往哪走」的路线图。"
showToc: true
tocOpen: true
---

## 一、教材

### 主教材

> **Kurose, J. F., & Ross, K. W.** *Computer Networking: A Top-Down Approach*, 8th Edition. Pearson, 2021.

本课程 29 讲的章节对应关系见每讲开头的「课前阅读」。这本书的优点是**自顶向下的组织**和**大量可计算的例题**；缺点是对实现细节较浅。

### 强烈推荐的补充

| 书 | 特点 | 什么时候读它 |
|---|---|---|
| ⭐ **Peterson & Davie**, *Computer Networks: A Systems Approach* | **免费开源**（systemsapproach.org），系统实现视角 | 想知道"这东西到底怎么实现"时 |
| ⭐ **Stevens**, *TCP/IP Illustrated, Vol. 1* (2nd ed.) | 逐字节讲协议，配大量抓包 | 需要精确到字段时；做 Lab 1、Lab 3 时 |
| **Bonaventure**, *Computer Networking: Principles, Protocols and Practice* | **免费开放教材**，讲解清晰 | 想换一个角度看同一个主题时 |
| **Comer**, *Internetworking with TCP/IP, Vol. 1* | 经典，网络层讲得深 | 复习网络层时 |
| ⭐ **Aumasson**, *Serious Cryptography* | 现代密码学，工程视角 | 第 27–28 讲之后想深入安全 |
| **Beej's Guide to Network Programming** | **免费**，socket 编程入门 | 做 Lab 2 之前 |

---

## 二、RFC 阅读清单

⭐ **读 RFC 的能力本身就是这门课的目标之一。**RFC 不是教科书，它是**规范**——它告诉你"必须"（MUST）、"应当"（SHOULD）、"可以"（MAY）各是什么。

### 怎么读 RFC

```
① 先看 Abstract 和 Introduction —— 判断这份 RFC 解决什么问题
② ⭐ 跳到 "Security Considerations" —— 这一节往往最有信息量，
   它诚实地写出了作者知道的弱点
③ 需要细节时再回头精读对应章节
④ ⭐ 注意 RFC 会被 obsolete/update —— 在 rfc-editor.org 上查它的状态，
   不要读一份已经被取代的规范
```

### 按讲次编排

| 讲次 | RFC | 主题 | 建议 |
|---|---|---|---|
| 4 | RFC 1122/1123 | 主机需求 | 选读 |
| 5 | ⭐ **RFC 9110** | HTTP 语义（方法、状态码） | **精读方法与状态码部分** |
| 5 | RFC 9111 | HTTP 缓存 | 精读 `Cache-Control` |
| 6 | RFC 9113 | HTTP/2 | 读多路复用与 HPACK 概念 |
| 6 | ⭐ **RFC 9000** | **QUIC** | 读 Introduction 与连接迁移 |
| 6 | RFC 9114 | HTTP/3 | 选读 |
| 7 | ⭐ **RFC 1034/1035** | **DNS 概念与实现** | 经典，值得精读 |
| 7 | RFC 8484 | DNS over HTTPS | 读 Security Considerations |
| 8 | RFC 5321/5322 | SMTP 与邮件格式 | 选读 |
| 8 | RFC 7208 / 6376 / 7489 | SPF / DKIM / DMARC | 了解即可 |
| 10 | RFC 768 | **UDP**（只有 3 页！） | ⭐ **完整读一遍**，感受早期 RFC 的简洁 |
| 13–14 | ⭐ **RFC 9293** | **TCP 现行规范** | 精读状态机与序号部分 |
| 13 | RFC 2018 | SACK | 读机制部分 |
| 13 | RFC 6298 | RTO 计算 | ⭐ 短，值得精读 |
| 14 | RFC 7323 | 窗口缩放与时间戳 | 精读窗口缩放 |
| 14 | RFC 896 | Nagle 算法 | ⭐ 极短，读它体会问题的来源 |
| 15–16 | ⭐ **RFC 5681** | **TCP 拥塞控制** | **精读**，公式与状态机 |
| 16 | RFC 8312 | CUBIC | 选读 |
| 16 | RFC 3168 | ECN | 读原理 |
| 16 | RFC 8289 | CoDel | ⭐ 读它对 bufferbloat 的分析 |
| 18 | RFC 791 | **IPv4** | 精读头部字段 |
| 18 | ⭐ **RFC 1918** | **私有地址** | 极短 |
| 18 | RFC 2131 | DHCP | 读 DORA 流程 |
| 18 | RFC 3022 | NAT | 读它对局限的坦率讨论 |
| 19 | ⭐ **RFC 8200** | **IPv6** | 精读，与 RFC 791 对比着读 |
| 19 | RFC 4861 | NDP | 选读 |
| 21 | ⭐ **RFC 4271** | **BGP-4** | 读选路决策部分 |
| 21 | RFC 6480 | RPKI 架构 | 了解 |
| 22 | RFC 792 / 4443 | ICMP / ICMPv6 | ⭐ 读类型代码表 |
| 22 | RFC 6241 | NETCONF | 选读 |
| 27–28 | ⭐ **RFC 8446** | **TLS 1.3** | **精读握手部分**；对比 RFC 5246 (TLS 1.2) |
| 28 | RFC 4301/4303 | IPsec / ESP | 选读 |
| 28 | ⭐ **BCP 38 (RFC 2827)** | **入口过滤** | 极短，⭐ **必读**——理解为什么它没被部署 |

📌 **如果只读五份**：RFC 768（UDP）、RFC 896（Nagle）、RFC 2827（BCP 38）、RFC 5681（拥塞控制）、RFC 8446（TLS 1.3）。

---

## 三、值得读的经典论文

⭐ **网络是一个论文可读性很高的领域**——很多奠基性论文只有十几页且几乎没有数学门槛。

| 论文 | 年份 | 为什么读它 | 对应讲次 |
|---|---|---|---|
| ⭐ **Cerf & Kahn**, *A Protocol for Packet Network Intercommunication* | 1974 | ⭐ **互联网的出生证明。**看 TCP/IP 最初的样子 | 1, 4 |
| ⭐ **Saltzer, Reed & Clark**, *End-to-End Arguments in System Design* | 1984 | ⭐ **本课程最重要的一篇。**端到端原则的原始论证 | 4 |
| ⭐ **Jacobson**, *Congestion Avoidance and Control* | 1988 | ⭐ 拥塞崩溃之后的救火之作，慢启动与 AIMD 的来源 | 15, 16 |
| **Chiu & Jain**, *Analysis of the Increase and Decrease Algorithms* | 1989 | ⭐ AIMD 收敛性的相图证明 | 15 |
| **Clark**, *The Design Philosophy of the DARPA Internet Protocols* | 1988 | ⭐ 互联网设计目标的优先级排序（会让你重新理解很多决定） | 4 |
| **Karol et al.**, *Input Versus Output Queueing* | 1987 | 58.6% 那个数字的来源 | 17 |
| **Appenzeller et al.**, *Sizing Router Buffers* | 2004 | `RTT×C/√N` 的推导 | 17 |
| **Gao & Rexford**, *Stable Internet Routing Without Global Coordination* | 2001 | ⭐ BGP 收敛性的条件 | 21 |
| **McKeown et al.**, *OpenFlow* | 2008 | SDN 的起点 | 19, 22 |
| ⭐ **Cardwell et al.**, *BBR: Congestion-Based Congestion Control* | 2016 | ⭐ 对"丢包=拥塞"假设的根本质疑 | 16 |
| **Langley et al.**, *The QUIC Transport Protocol* | 2017 | 大规模部署的一手经验与数据 | 6, 26 |
| **Gettys & Nichols**, *Bufferbloat: Dark Buffers in the Internet* | 2011 | 一个"人人都在用却没人注意"的问题被发现的过程 | 16 |

📌 **读论文的建议顺序**：先读 Saltzer 的端到端原则，再读 Clark 的设计哲学，最后读 Jacobson 的拥塞控制。**这三篇读完，你对互联网的理解会和读之前不一样。**

---

## 四、公开课与实验平台

### 公开课

| 课程 | 学校 | 特点 |
|---|---|---|
| ⭐ **CS 144: Introduction to Computer Networking** | Stanford | ⭐ **实验极强**——你会从零实现一个可用的 TCP。**强烈推荐做完** |
| **CS 168: Introduction to the Internet** | UC Berkeley | 讲义质量高，路由部分尤其好 |
| **6.829: Computer Networks** | MIT | 研究生课，直接读论文 |
| **15-441: Computer Networks** | CMU | 项目导向，实现完整协议栈 |
| **Wireshark Labs** | UMass (Kurose) | ⭐ 与教材配套，免费，本课程 Lab 1 参考了它 |

### 实验平台与工具

| 工具 | 用途 |
|---|---|
| ⭐ **Wireshark** | 抓包分析。本课程 Lab 1 的核心工具 |
| ⭐ **Mininet** | 在一台机器上模拟完整的网络拓扑，可跑真实协议栈 |
| **GNS3 / EVE-NG** | 模拟真实路由器/交换机镜像，适合练 OSPF/BGP 配置 |
| **containerlab** | 用容器搭网络实验室，比虚拟机轻量得多 |
| ⭐ **netem / tc** | Linux 内核的网络损伤模拟（丢包、时延、乱序）——Lab 3 可用它替代模拟器 |
| **iperf3** | 吞吐量测试 |
| ⭐ **flent** | Bufferbloat 与 AQM 的标准测试工具 |
| **BIRD / FRRouting** | 开源路由协议栈，可以真的跑 BGP |
| **RIPE Atlas / RIPE stat** | 全球分布的测量探针，可查真实的 BGP 路由与可达性 |
| **bgp.tools / bgpview** | 查任意 AS 的对等关系与前缀 |

---

## 五、持续跟踪

### 会议（论文都公开）

```
SIGCOMM   —— 网络领域顶会，偏架构与测量
NSDI      —— 系统与实现
CoNEXT    —— 新兴主题
IMC       —— 互联网测量
```

### 值得订阅的

```
IETF 邮件列表：想看协议是怎么被吵出来的，订 tls@ 或 quic@
APNIC / RIPE Labs 博客：高质量的路由与测量分析
Cloudflare / Fastly 技术博客：⭐ 大规模部署的一手数据
```

---

## 六、学完之后往哪走

### 路线 A：系统与内核方向

```
① 读 Linux 网络栈：从 net/ipv4/tcp_input.c 开始（这是拥塞控制的实现）
② 学 eBPF / XDP —— 在内核里编程处理分组
③ 读 TCP/IP Illustrated Vol. 2（源码级）
④ 目标能力：能读懂并修改内核网络栈
```

### 路线 B：协议实现方向

```
① ⭐ 完整做一遍 Stanford CS144（自己实现 TCP）
② 读一个开源 QUIC 实现（quiche / msquic / quic-go）
③ 参与 IETF 的某个工作组，看规范怎么形成
④ 目标能力：能实现一个符合规范的协议栈
```

### 路线 C：数据中心与云网络

```
① Clos / Fat-tree 拓扑，ECMP
② VXLAN、EVPN、SRv6
③ RDMA / RoCE、DCTCP、DCQCN
④ ⭐ 可编程交换机（P4、Tofino）
⑤ 目标能力：能设计与运维大规模数据中心网络
```

### 路线 D：网络安全

```
① 《Serious Cryptography》
② 做 CTF 的 network / pwn 方向
③ 读 TLS 1.3 规范并自己实现一个握手
④ 学威胁建模：先问"攻击者能做什么"，再问"我怎么防"
⑤ 目标能力：能做协议级的安全分析
```

### 路线 E：性能与可观测性

```
① RFC 6349（TCP 吞吐量测试方法）
② eBPF 网络追踪（bpftrace、Cilium）
③ 分布式追踪与网络指标（RED/USE 方法）
④ 目标能力：能定位"到底慢在哪一层"
```

---

## 七、⭐ 一个建议

📌 **不要停在"读"上。**

这门课教的每一个机制，你都可以在自己的机器上跑一遍：

```
想理解拥塞控制  → 用 netem 加丢包，看 ss -i 里的 cwnd 怎么变
想理解 BGP     → 用 containerlab 搭三个 AS，跑 FRRouting，自己配策略
想理解 TLS     → 用 openssl s_client -debug 看完整握手
想理解队列     → 用 tc 换不同的 qdisc，用 flent 测 bufferbloat
```

⭐ **网络是可以被完全观测的。**这是它相比很多学科的巨大优势——**没有什么是必须靠相信的。**

---

*返回：[课程主页]({{< ref "_index.md" >}}) · [复习指南]({{< ref "90-exam-guide.md" >}}) · [术语表]({{< ref "95-glossary.md" >}})*
