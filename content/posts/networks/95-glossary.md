---
title: "术语表：英中对照与速查"
date: 2026-08-28
weight: 95
tags: ["计算机网络"]
draft: false
summary: "按主题组织的计算机网络术语表，中英对照，每条附一句话精确定义与所在讲次。用于查漏、反查和考前速览。"
showToc: true
tocOpen: true
---

> 📌 **怎么用这一页**：① 忘了某个词是什么意思时反查；② 考前从头扫一遍，看到不确定的就回去读对应讲次；③ 读英文文献时对照。
> ⭐ 标记的是**本课程最核心的 40 个概念**。

---

## 一、体系结构与基本概念

| 中文 | 英文 | 一句话定义 | 讲次 |
|---|---|---|---|
| ⭐ 端系统 / 主机 | end system / host | 运行网络应用程序的设备，位于网络边缘 | 1 |
| 分组交换机 | packet switch | 收到分组并向输出链路转发的设备（路由器、交换机） | 1 |
| ⭐ 协议 | protocol | 定义报文的**格式、次序**与收发时采取的**动作** | 1 |
| ⭐ 分组交换 | packet switching | 数据切块独立传输，不预留资源 | 2 |
| 电路交换 | circuit switching | 通信前预留端到端专用通路 | 2 |
| ⭐ 统计复用 | statistical multiplexing | 不为每个用户预留，赌"不会同时用" | 2 |
| ⭐ 存储转发 | store-and-forward | 路由器必须收完整个分组才能开始转发 | 2 |
| ⭐ 转发 | forwarding | 单台路由器内把分组从输入端口移到输出端口（纳秒级） | 2, 17 |
| ⭐ 路由 | routing | 全网范围决定分组走哪条端到端路径（秒级） | 2, 20 |
| ⭐ 端到端原则 | end-to-end principle | 只有在端点才能正确实现的功能，不应放在网络内部 | 4 |
| ⭐ 沙漏模型 / 窄腰 | hourglass / narrow waist | IP 是唯一的收腰，使万物互通，也使 IP 极难改变 | 4 |
| ⭐ 封装 | encapsulation | 每层把上层数据整体当作载荷，加上自己的头部 | 4 |
| ⭐ 协议僵化 | ossification | 中间设备对协议做了假设，导致协议无法演进 | 6, 19 |

---

## 二、性能

| 中文 | 英文 | 一句话定义 | 讲次 |
|---|---|---|---|
| ⭐ 传输时延 | transmission delay | 把分组所有比特推到链路上的时间 `L/R` | 3 |
| ⭐ 传播时延 | propagation delay | 一个比特从链路一端走到另一端的时间 `d/s` | 3 |
| 处理时延 | processing delay | 检查头部、决定输出端口的时间 | 3 |
| ⭐ 排队时延 | queuing delay | 在输出队列中等待的时间，**唯一随负载变化的一项** | 3 |
| ⭐ 流量强度 | traffic intensity | `La/R`，逼近 1 时排队时延爆炸 | 3 |
| ⭐ 瓶颈链路 | bottleneck link | 端到端路径上速率最小的那条链路 | 3 |
| ⭐ 带宽时延积 | bandwidth-delay product (BDP) | `R × RTT`，管道能容纳的比特数 | 3, 11 |
| 长肥管道 | long fat network (LFN) | 高带宽 + 高时延的链路，对协议提出特殊要求 | 11, 14 |
| 抖动 | jitter | 时延的变动幅度 | 3, 8 |
| 有效吞吐量 | goodput | 接收方收到的**有用数据**速率（不含重传） | 15 |

---

## 三、应用层

| 中文 | 英文 | 一句话定义 | 讲次 |
|---|---|---|---|
| 客户机–服务器 | client-server | 服务能力受服务器资源限制的架构 | 5 |
| ⭐ 对等 / 自扩展 | P2P / self-scalability | 每个新用户既是负担也是资源，分发时间趋于常数 | 5, 8 |
| ⭐ 套接字 | socket | 应用层与传输层之间的 API 边界 | 5, 9 |
| ⭐ 无状态 | stateless | 服务器不保存客户端过去请求的信息 | 5 |
| ⭐ 持续连接 | persistent connection | 一条 TCP 连接上串行多个请求，省 RTT 与拥塞窗口 | 5 |
| ⭐ 幂等 | idempotent | 执行一次与 N 次效果相同，因而可安全重试 | 5, 28 |
| Cookie | cookie | 给无状态协议外挂状态的机制，也是追踪的基础 | 5 |
| ⭐ 条件 GET | conditional GET | 用 If-Modified-Since / If-None-Match 换取 304，省实体体不省 RTT | 5 |
| ⭐ Web 缓存 | web cache / proxy | 同时降低时延、带宽成本；改变接入链路的流量强度 | 6 |
| ⭐ CDN | content delivery network | 把内容搬到用户附近；**用 DNS 做节点选择** | 6 |
| ⭐ 队头阻塞 | head-of-line blocking | 队首受阻导致后面本可处理的元素也等待 | 6, 17 |
| 多路复用（HTTP/2） | multiplexing | 一条连接上并发多个流，消除应用层队头阻塞 | 6 |
| ⭐ QUIC | QUIC | 建在 UDP 之上的用户态传输协议，流级独立、支持连接迁移 | 6, 26 |
| ⭐ 权威 DNS 服务器 | authoritative DNS server | 存放某个域真正记录的服务器 | 7 |
| ⭐ 本地 DNS / 解析器 | local DNS / resolver | 代理你去查询层次结构并缓存结果，不属于层次结构本身 | 7 |
| ⭐ 递归查询 | recursive query | "帮我问到底" | 7 |
| ⭐ 迭代查询 | iterative query | "告诉我下一步该问谁" | 7 |
| TTL（DNS） | time to live | 记录可被缓存的秒数，切换速度与查询量的权衡 | 7 |
| 任播 | anycast | 多个节点通告同一地址，路由到最近的一个 | 7, 19 |
| DNSSEC | DNS Security Extensions | 给 DNS 记录签名，**管真伪不管隐私** | 7 |
| DoH / DoT | DNS over HTTPS / TLS | 加密 DNS 查询，**管隐私不管真伪** | 7 |
| 一报还一报 | tit-for-tat | BitTorrent 的激励机制：你给我发得快，我才给你发 | 8 |
| 乐观疏通 | optimistic unchoking | 随机给一个邻居机会，防止新 peer 被饿死 | 8 |
| ⭐ DASH | Dynamic Adaptive Streaming over HTTP | 客户端按带宽自选码率，智能全在端上 | 8 |

---

## 四、传输层

| 中文 | 英文 | 一句话定义 | 讲次 |
|---|---|---|---|
| ⭐ 多路复用/分解 | multiplexing / demultiplexing | 发送端汇集、接收端分发到正确的 socket | 10 |
| ⭐ 二元组 / 四元组 | 2-tuple / 4-tuple | UDP socket 用（目的IP,端口）；TCP 用（源IP,源端口,目的IP,目的端口） | 10 |
| 反码校验和 | Internet checksum | 16 位求和（进位回卷）后取反；漏检率约 2⁻¹⁶ | 10 |
| 伪首部 | pseudo-header | 校验和覆盖的 IP 地址等字段，**破坏分层，逼 NAT 重算校验和** | 10 |
| ⭐ ARQ | automatic repeat request | 校验和 + 确认 + 重传的统称 | 11 |
| ⭐ 停等协议 | stop-and-wait | 发一个等一个，利用率 `(L/R)/(RTT+L/R)` | 11 |
| ⭐ 流水线 | pipelining | 允许多个分组同时在途，利用率提升 N 倍 | 12 |
| ⭐ 滑动窗口 | sliding window | 限制在途未确认数据量；TCP 控速的着力点 | 12 |
| ⭐ 回退 N 步 | Go-Back-N (GBN) | 累积确认 + 单定时器 + 超时重传整个窗口 | 12 |
| ⭐ 选择重传 | Selective Repeat (SR) | 逐个确认 + 每包定时器 + 只重传丢失的那个 | 12 |
| ⭐ 累积确认 | cumulative ACK | ACK(n) 表示 n 之前全部收到；对 ACK 丢失鲁棒 | 12, 13 |
| MSS | maximum segment size | TCP 报文段最大载荷，握手时协商 | 13 |
| ⭐ EWMA | exponentially weighted moving average | RTT 估计的平滑方法，近期样本权重更大 | 13 |
| ⭐ Karn 算法 | Karn's algorithm | 不对重传过的报文段测 RTT，改用指数退避 | 13 |
| ⭐ 快速重传 | fast retransmit | 收到 3 个重复 ACK 立即重传，不等超时 | 13 |
| ⭐ SACK | selective acknowledgment | 明确告知已收到的不连续块，一个 RTT 修复所有空洞 | 13 |
| ⭐ 三次握手 | three-way handshake | 双方各自宣告 ISN 并各自得到确认 | 14 |
| ⭐ TIME_WAIT | TIME_WAIT | 主动关闭方等待 2MSL：保最后 ACK 送达 + 让旧报文消亡 | 14 |
| SYN Cookie | SYN cookie | 把连接状态编码进 ISN，无状态因而无法被耗尽 | 14 |
| ⭐ 流量控制 | flow control | 保护**接收方缓冲区**，靠 rwnd 显式告知 | 14 |
| 零窗口探测 | window probe | 打破零窗口死锁；责任在发送方 | 14 |
| ⭐ 窗口缩放 | window scaling | 把 16 位 rwnd 扩到最大 1 GB，长肥管道必需 | 14 |
| ⭐ Nagle 算法 | Nagle's algorithm | 有未确认数据时攒小包；与延迟确认交互产生 200 ms 延迟 | 14 |
| ⭐ 拥塞控制 | congestion control | 保护**网络**，靠丢包/时延间接推断 | 15 |
| ⭐ 拥塞崩溃 | congestion collapse | 重传的正反馈导致吞吐量趋于 0（1986 年真实发生） | 15 |
| ⭐ AIMD | additive increase, multiplicative decrease | 加性增平行公平线，乘性减按比例缩小差距 → 收敛到公平 | 15 |
| 最大最小公平 | max-min fairness | 不减少更小的流就无法增加任何流 | 15 |
| ⭐ 慢启动 | slow start | cwnd 每 RTT 翻倍（名字有误导，实为指数增长） | 16 |
| ⭐ 拥塞避免 | congestion avoidance | cwnd 每 RTT 加 1 MSS | 16 |
| 快速恢复 | fast recovery | 3 个重复 ACK 后 cwnd = ssthresh+3，不退回 1 | 16 |
| ⭐ CUBIC | CUBIC | cwnd 是距上次丢包的**绝对时间**的三次函数；RTT 公平 | 16 |
| ⭐ BBR | BBR | 测 BtlBw 与 RTprop，工作在 BDP 点：跑满带宽不填缓冲 | 16 |
| ⭐ 缓冲区膨胀 | bufferbloat | 大缓冲区 + 基于丢包的 TCP = 巨大排队时延 | 16 |
| ECN | explicit congestion notification | 路由器在丢包前标记分组，无损传递拥塞信号 | 16 |
| AQM / CoDel | active queue management | 看**驻留时间**而非队列长度来丢包 | 16, 17 |

---

## 五、网络层

| 中文 | 英文 | 一句话定义 | 讲次 |
|---|---|---|---|
| ⭐ 数据平面 | data plane | 单台路由器的转发行为（纳秒、硬件） | 17 |
| ⭐ 控制平面 | control plane | 全网的路由计算（秒、软件） | 17, 20 |
| ⭐ 尽最大努力 | best-effort | 不保证交付、时延、带宽、顺序——**弱正是它可扩展的原因** | 17 |
| ⭐ 最长前缀匹配 | longest prefix matching | 多条前缀匹配时选最长的那条 | 17 |
| TCAM | ternary content-addressable memory | 支持通配的硬件查找表，O(1) 但昂贵、容量有限 | 17 |
| 虚拟输出队列 | virtual output queue (VOQ) | 每个输出端口一个独立队列，消除队头阻塞 | 17 |
| WFQ | weighted fair queuing | 按比特加权分配带宽，与分组大小无关 | 17 |
| ⭐ 子网 | subnet | 一组不经过路由器就能互相通信的接口 | 18 |
| ⭐ CIDR | classless interdomain routing | 前缀长度任意，支持按需分配与**地址聚合** | 18 |
| ⭐ 地址聚合 | route aggregation | 用一条粗前缀代替多条细前缀，抑制路由表膨胀 | 18 |
| MTU | maximum transmission unit | 链路能承载的最大帧载荷（以太网 1500 字节） | 18 |
| ⭐ 分片 | fragmentation | 路由器切分、**目的主机重组**；IPv6 已取消 | 18 |
| ⭐ PMTUD | path MTU discovery | 源主机探测路径最小 MTU；**屏蔽 ICMP 会造成黑洞** | 18, 22 |
| ⭐ DHCP | dynamic host configuration protocol | 四步 DORA，给出 IP + 掩码 + **网关** + **DNS** | 18 |
| ⭐ NAT | network address translation | 用端口号当地址位；救了 IPv4，破坏了可寻址性 | 18 |
| 打洞 | hole punching | 双方同时外发建立映射，实现 NAT 后直连 | 18 |
| CGNAT | carrier-grade NAT | 运营商级 NAT，造成双层 NAT，打洞成功率骤降 | 18 |
| ⭐ SLAAC | stateless address autoconfiguration | IPv6 主机无需 DHCP 自动配址 | 19 |
| NDP | neighbor discovery protocol | IPv6 中取代 ARP，**跑在 ICMPv6 上** | 19 |
| 双栈 / 隧道 | dual stack / tunneling | IPv6 过渡的两种方案 | 19 |
| ⭐ 泛化转发 | generalized forwarding | 「匹配（跨层字段）+ 动作」，统一路由器/交换机/防火墙/LB | 19 |
| 中间盒 | middlebox | NAT、防火墙、LB 等违反端到端原则的设备；**僵化的直接原因** | 19 |
| ⭐ 链路状态 | link-state (LS) | 每个节点知道完整拓扑，各自跑 Dijkstra；**健壮** | 20 |
| ⭐ 距离向量 | distance-vector (DV) | 只与邻居交换距离；**错误会全网扩散** | 20 |
| ⭐ 无穷计数 | count-to-infinity | DV 只传距离、丢失路径，导致缓慢的路由环路 | 20 |
| ⭐ 毒性逆转 | poisoned reverse | 向路径上的下一跳谎报 ∞；**只能消除两节点环路** | 20 |
| ⭐ 自治系统 | autonomous system (AS) | 处于同一管理控制下的一组路由器 | 21 |
| ⭐ OSPF | open shortest path first | 域内链路状态协议，用**区域**限制泛洪范围 | 21 |
| ⭐ BGP | border gateway protocol | 互联网**唯一**的域间路由协议，跑在 TCP 179 | 21 |
| ⭐ AS_PATH | AS_PATH | 路由经过的 AS 序列；**防环 + 策略依据** | 21 |
| ⭐ 路径向量 | path vector | 携带完整路径的 DV 变体，从根本上消除环路 | 21 |
| ⭐ LOCAL_PREF | local preference | 本 AS 的策略偏好，**排在选路第一位** | 21 |
| ⭐ 热土豆路由 | hot potato routing | 尽快把流量甩出本 AS；导致**路径不对称** | 21 |
| ⭐ Gao-Rexford | Gao-Rexford rules | 只通告能带来收入的路由；客户 > 对等 > 提供商 | 21 |
| ⭐ BGP 劫持 | BGP hijacking | 通告不属于自己的（更具体的）前缀吸引流量 | 21 |
| ⭐ RPKI | resource PKI | 验证前缀的**起源 AS**；**不验证 AS_PATH** | 21 |
| ⭐ SDN | software-defined networking | 控制平面从设备剥离，逻辑集中、物理分布 | 22 |
| OpenFlow / P4 | OpenFlow / P4 | 南向接口；P4 更进一步实现**协议无关**的可编程解析 | 19, 22 |
| ⭐ ICMP | internet control message protocol | 网络层的差错与控制报文，携带出错报文的**前 8 字节** | 22 |
| SNMP / NETCONF | SNMP / NETCONF+YANG | 前者擅长监控；后者带来**事务与回滚** | 22 |
| MPLS | multiprotocol label switching | "2.5 层"标签交换，用于**流量工程**与 L3VPN | 22 |

---

## 六、链路层与无线

| 中文 | 英文 | 一句话定义 | 讲次 |
|---|---|---|---|
| ⭐ 成帧 | framing | 把数据报封装成帧并标记边界 | 23 |
| ⭐ 字节填充 | byte stuffing | 用转义字节让数据中可出现定界符（同 SMTP 点填充） | 23 |
| 前向纠错 | forward error correction (FEC) | 不重传即可纠错，用于高 RTT 或单向场景 | 23 |
| ⭐ CRC | cyclic redundancy check | 模 2 除法；**r 位保证检出所有 ≤ r 的突发错误** | 23 |
| ⭐ 时隙 ALOHA | slotted ALOHA | 最大效率 **1/e ≈ 37%** | 24 |
| ⭐ CSMA/CD | carrier sense multiple access with collision detection | 边发边听，检测到碰撞立即停止；有线专用 | 24 |
| ⭐ 二进制指数退避 | binary exponential backoff | 第 m 次碰撞后从 2^m 个值中随机选（与 TCP 退避同构） | 24 |
| ⭐ 最小帧长 | minimum frame size | 64 字节 = `2τ × R`，为保证能检测到碰撞 | 24 |
| ⭐ MAC 地址 | MAC address | 48 位扁平地址，与设备绑定；**逐跳更换** | 24 |
| ⭐ ARP | address resolution protocol | 广播查询 IP 对应的 MAC；**不跨越路由器** | 24 |
| ⭐ 自学习 | self-learning | 交换机从帧的**源地址**学习端口，无需配置 | 24 |
| ⭐ 生成树协议 | spanning tree protocol (STP) | 阻断链路消除环路；因为**以太网帧没有 TTL** | 24 |
| VLAN | virtual LAN | 在一台交换机上划分多个逻辑广播域（802.1Q） | 24 |
| ⭐ 隐藏终端 | hidden terminal | 两站互相听不到但在接收方处碰撞 | 25 |
| ⭐ CSMA/CA | collision avoidance | 无线只能避免不能检测；退避计数器**冻结不重置** | 25 |
| SIFS / DIFS | short/DCF interframe space | SIFS 更短，使 ACK 总能抢先 | 25 |
| RTS/CTS | request/clear to send | 用 AP 广播的 CTS 让隐藏终端静默；默认关闭 | 25 |
| NAV | network allocation vector | 虚拟载波侦听：看 Duration 字段而非真的听 | 25 |
| 性能异常 | performance anomaly | 一个慢站点拖慢整个 BSS | 25 |
| eNodeB / gNB | eNodeB / gNB | 4G / 5G 基站 | 26 |
| ⭐ P-GW / UPF | packet gateway / user plane function | 为终端**分配并锚定 IP**，因而移动时 IP 不变 | 26 |
| ⭐ 网络切片 | network slicing | 在同一物理网上划分逻辑独立的端到端网络 | 26 |
| ⭐ 间接路由 | indirect routing | 经归属代理转发；透明但有**三角路由** | 26 |
| 切换 / 漫游 | handover / roaming | 前者同运营商内换基站，后者跨运营商 | 26 |
| ⭐ 连接迁移 | connection migration | QUIC 用与 IP 无关的 Connection ID 标识连接 | 26 |

---

## 七、安全

| 中文 | 英文 | 一句话定义 | 讲次 |
|---|---|---|---|
| ⭐ 机密性/完整性/认证 | confidentiality / integrity / authentication | 四属性中的三项（另一项是可用性）；**互相独立** | 27 |
| AEAD | authenticated encryption with associated data | 同时提供机密性与完整性（AES-GCM） | 27 |
| ⭐ 混合加密 | hybrid encryption | 公钥加密会话密钥，对称密钥加密数据 | 27 |
| ⭐ MAC | message authentication code | 用**共享秘密**保证完整性；**无不可否认性** | 27 |
| HMAC | HMAC | 双层嵌套哈希，抵抗长度扩展攻击 | 27 |
| ⭐ 数字签名 | digital signature | 用**私钥**签摘要；提供**不可否认性** | 27 |
| ⭐ 证书 / CA | certificate / certificate authority | CA 签名的「公钥属于某主体」的声明 | 27 |
| ⭐ 证书透明度 | certificate transparency (CT) | 所有签发记入公开日志，使误签发可被检测 | 27 |
| ⭐ 现时数 | nonce | 一生只用一次的随机数；**防重放** | 27 |
| ⭐ 重放攻击 | replay attack | 录下密文原样重发；**加密不能防它** | 27 |
| ⭐ 中间人攻击 | man-in-the-middle | 插入通信路径读取或篡改双向流量 | 27 |
| ⭐ 前向保密 | forward secrecy | 长期私钥泄露也无法解密历史会话（靠临时 DH） | 28 |
| 降级攻击 | downgrade attack | 迫使双方使用弱算法；TLS 的 Finished 防它 | 28 |
| 0-RTT | zero round-trip time | 首个分组即携带数据；**无重放保护，只能用于幂等请求** | 28 |
| ⭐ IPsec ESP | encapsulating security payload | 提供加密的 IPsec 协议；AH 因无法穿 NAT 被淘汰 | 28 |
| ⭐ 隧道模式 | tunnel mode | 加密整个原始数据报，**隐藏内部地址**；VPN 的实现方式 | 28 |
| ⭐ 有状态防火墙 | stateful firewall | 维护连接跟踪表，只放行已建立连接的入站分组 | 28 |
| 零信任 | zero trust | 不因来自内网就信任；每次访问都认证授权 | 28 |
| ⭐ BCP 38 | ingress filtering | ISP 丢弃源地址伪造的分组；**根本解法，卡在激励** | 28 |

---

## 八、服务质量、实时多媒体与数据中心

| 中文 | English | 一句话定义 | 讲次 |
|---|---|---|---|
| ⭐ 令牌桶 | token bucket | 用 `(r, b)` 同时刻画长期速率与允许突发；任意区间 `t` 内流量 ≤ `r·t + b` | 17 |
| 漏桶 | leaky bucket | 桶里装**数据**、输出速率严格恒定，完全抹平突发（令牌桶装的是**许可**） | 17 |
| ⭐ 流量监管 | policing | 超出约定就丢弃或降级，**不缓存**——不增时延但丢包 | 17 |
| ⭐ 流量整形 | shaping | 超出约定先缓存、延后发出，**不丢包但增时延** | 17 |
| 综合服务 | IntServ | 逐流预留（RSVP），路由器为每条流维护状态；死于状态爆炸 | 17 |
| ⭐ 区分服务 | DiffServ | 边缘分类打 DSCP 标记，核心只按类别转发；复杂性放在边缘 | 17 |
| 逐跳行为 | PHB | DiffServ 中单跳的转发行为（EF 加速转发、AF 确保转发），**不是端到端保证** | 17 |
| ⭐ 播放缓冲 | playout buffer | 接收方故意延后播放，把**可变的网络时延**换成**恒定的播放时延** | 8 |
| ⭐ 时延抖动 | jitter | 同一条流中不同分组经历的时延之差；播放缓冲要抵消的就是它 | 8 |
| RTP | Real-time Transport Protocol | 在 UDP 上补充**序号**（检丢包乱序）与**时间戳**（重建节奏）；⭐ 不提供任何 QoS 保证 | 8 |
| RTCP | RTP Control Protocol | 接收方周期回报丢包率、抖动与 RTT，发送方据此调码率 | 8 |
| SIP | Session Initiation Protocol | 负责**建立/修改/结束会话**（找人、协商编解码），传语音的是 RTP | 8 |
| 交织 | interleaving | 把相邻采样打散到不同包，丢包变成多处小间隙；⭐ 增加时延，不适合交互式 | 8 |
| ⭐ 全等分带宽 | full bisection bandwidth | 主机任意分成两半，两半间带宽等于接入带宽之和，即无超额订购 | 24 |
| 超额订购 | oversubscription | 上联带宽小于下联总和的比例（传统树形常达 12:1） | 24 |
| ⭐ Clos / Fat-Tree | Clos / fat-tree | `k` 端口交换机搭出 `k³/4` 台主机、`(k/2)²` 台核心交换机的多路径拓扑 | 24 |
| ⭐ ECMP | equal-cost multi-path | 按五元组哈希把不同流散到等价路径；**同流同路**以避免乱序 | 24 |
| ⭐ TCP incast | TCP incast | 多对一同步汇聚 → 浅缓冲溢出 → 整窗丢失 → 只能等超时 → 吞吐崩塌 | 24 |
| ⭐ DCTCP | Data Center TCP | 用 ECN 标记比例 `α` 按比例降窗 `cwnd×(1−α/2)`；问「拥塞多严重」而非「拥塞了吗」 | 24 |

---

## 九、常用端口号速查

| 端口 | 服务 | | 端口 | 服务 |
|---|---|---|---|---|
| 20/21 | FTP | | 179 | **BGP** |
| 22 | SSH | | 443 | HTTPS / QUIC |
| 23 | Telnet | | 465/587 | SMTP 提交 |
| 25 | SMTP | | 514 | Syslog |
| 53 | **DNS** | | 853 | DNS-over-TLS |
| 67/68 | **DHCP** | | 993 | IMAPS |
| 69 | TFTP | | 995 | POP3S |
| 80 | HTTP | | 3306 | MySQL |
| 110 | POP3 | | 5432 | PostgreSQL |
| 123 | NTP | | 6379 | Redis |
| 143 | IMAP | | 6653 | OpenFlow |
| 161/162 | SNMP | | 8080 | HTTP 备用 |

---

## 十、常用 ICMP 类型/代码

| 类型 | 代码 | 含义 | 用途 |
|---|---|---|---|
| **0** | 0 | Echo Reply | ping 的回复 |
| 3 | 0 | 网络不可达 | |
| 3 | 1 | 主机不可达 | |
| **3** | **3** | **端口不可达** | ⭐ traceroute 判断终点 |
| **3** | **4** | **需要分片但设了 DF** | ⭐ PMTUD 依赖它 |
| **8** | 0 | Echo Request | ping |
| **11** | 0 | **TTL 超时** | ⭐ traceroute 逐跳发现 |
| 12 | 0 | 参数错误 | |

