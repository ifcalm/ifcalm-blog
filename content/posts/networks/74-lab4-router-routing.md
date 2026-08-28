---
title: "Lab 4：路由算法与转发表"
date: 2026-08-28
weight: 74
tags: ["计算机网络"]
draft: false
summary: "实现最长前缀匹配的转发表、Dijkstra 链路状态路由、分布式异步的距离向量路由（并亲眼看到无穷计数），以及一个简化的 BGP 策略选路引擎。占总成绩 10%。"
showToc: true
tocOpen: false
---

> 💻 **语言**：Python 3.9+ 或 C++17

---

## Part 1：最长前缀匹配转发表（25 分）

### 需求

```python
class ForwardingTable:
    def add_route(self, prefix: str, next_hop: str) -> None:
        """prefix 形如 '192.168.1.0/24'"""

    def remove_route(self, prefix: str) -> None: ...

    def lookup(self, ip: str) -> str | None:
        """⭐ 返回最长匹配前缀对应的下一跳；无匹配返回 None"""
```

### 必须支持

```
✅ IPv4 与 ⭐ IPv6（IPv6 为 +5 加分）
✅ 默认路由 0.0.0.0/0
✅ ⭐ 前缀重叠时正确选择最长的
✅ 动态增删路由
```

### 实现方式（决定分值上限）

| 方式 | 查找复杂度 | 分值上限 |
|---|---|---|
| 线性扫描所有前缀 | O(n) | 15/25 |
| 按前缀长度分桶 + 哈希 | O(32) | 20/25 |
| ⭐ **二叉 Trie（前缀树）** | O(32) 但常数小 | 23/25 |
| ⭐ **压缩 Trie / 多位 Trie** | O(1)–O(8) | 25/25 |

📌 **推荐做二叉 Trie**：每一位一层，最多 32 层；在下降过程中记录**沿途遇到的最后一个有效路由**——那就是最长匹配。

```python
class TrieNode:
    __slots__ = ('children', 'next_hop')
    def __init__(self):
        self.children = [None, None]   # 0 和 1
        self.next_hop = None           # ⭐ 非 None 表示此处有一条路由

def lookup(self, ip_int: int) -> str | None:
    node, best = self.root, None
    for i in range(31, -1, -1):
        if node.next_hop is not None:
            best = node.next_hop       # ⭐ 沿途记录，不要提前 return
        bit = (ip_int >> i) & 1
        node = node.children[bit]
        if node is None:
            break
    if node is not None and node.next_hop is not None:
        best = node.next_hop
    return best
```

### 性能要求（5 分）

```bash
python3 bench.py --routes 1000000 --lookups 1000000
```

⭐ **要求：100 万条路由下，100 万次查找在 10 秒内完成**（Python）或 **1 秒内**（C++）。

**报告中给出**：不同表规模（1K / 10K / 100K / 1M）下的**平均查找时间**与**内存占用**，并画图。

⭐ **讨论**：你的查找时间随表规模如何变化？这与第 17 讲说的 TCAM 的 O(1) 相比如何？为什么真实路由器要用硬件？

---

## Part 2：链路状态路由（Dijkstra）（20 分）

### 需求

```python
def dijkstra(graph: dict, source: str) -> tuple[dict, dict]:
    """
    graph: {node: {neighbor: cost}}
    返回 (distances, next_hops)
    ⭐ next_hops[dst] 是从 source 到 dst 的【第一跳】
    """
```

### 必须实现

```
✅ 用优先队列（heapq），复杂度 O(E log V)
✅ ⭐ 输出【每一步迭代】的 D() 与 p() 值表格（用于验证）
✅ 由前驱指针回溯出【第一跳】，生成转发表
✅ ⭐ 处理不连通的节点（距离为 ∞）
✅ ⭐ 等价多路径（ECMP）：存在多条同开销路径时全部返回
```

### 验证

```bash
python3 ls_routing.py --topo topologies/kr_figure5_3.json --source u --verbose
```

⭐ **输出的迭代表必须与第 20 讲的表格完全一致。**这是最直接的正确性验证。

### 报告要求

```
① 给出一张 6 节点网络的完整迭代表
② ⭐ 构造一个存在【两条等价最短路径】的拓扑，验证你的 ECMP 输出
③ ⭐ 讨论：如果链路开销是负数会怎样？Dijkstra 还正确吗？为什么？
```

---

## Part 3：距离向量路由（30 分）⭐ 核心

### 需求：真正的分布式异步实现

⚠️ **不允许写成一个中心化的循环。**每个节点必须是一个独立的对象/线程/进程，**只能与直接邻居交换消息**。

```python
class DVNode:
    def __init__(self, name, neighbors: dict[str, int]):
        self.name = name
        self.neighbors = neighbors        # {邻居: 直连开销}
        self.dv = {}                      # ⭐ 自己的距离向量
        self.neighbor_dvs = {}            # ⭐ 邻居报来的距离向量
        self.next_hop = {}

    def on_receive(self, sender: str, dv: dict) -> bool:
        """⭐ 用 Bellman-Ford 重算。若自己的 dv 变化则返回 True（需要通告邻居）"""

    def on_link_change(self, neighbor: str, new_cost: int) -> bool:
        """链路开销变化"""

    def compute_dv(self) -> dict:
        """d_x(y) = min over v { c(x,v) + d_v(y) }"""
```

### 3.1 基本收敛（10 分）

```bash
python3 dv_routing.py --topo topologies/simple.json --trace
```

⭐ **必须输出每一轮的距离向量表**，展示收敛过程。

**报告要求**：给出第 20 讲那个三节点例子（x-y-z）的完整收敛轨迹，与讲义对照。

### 3.2 ⭐ 复现「好消息传得快」（5 分）

```bash
python3 dv_routing.py --topo topologies/xyz.json \
        --change "y-x:4->1" --trace
```

**报告要求**：记录收敛所需的轮数，并解释为什么这么快。

### 3.3 ⭐⭐ 复现无穷计数问题（10 分）

```bash
python3 dv_routing.py --topo topologies/xyz.json \
        --change "y-x:4->60" --trace --max-rounds 100
```

**必须提交**：

```
① ⭐ 完整的轮次表，展示 d_y(x) 和 d_z(x) 交替 +1 的过程
② ⭐ 一张图：横轴轮次，纵轴 d_y(x) 与 d_z(x)，画出那条缓慢爬升的折线
③ 收敛需要多少轮？与第 20 讲的分析（44 轮）是否一致？
④ ⭐ 解释【根本原因】：为什么 y 会选择一条实际经过自己的路径？
```

📌 **这一小题是整个 Lab 4 的精华**。亲眼看到那条爬升的折线，比读十遍讲义都管用。

### 3.4 毒性逆转（5 分）⭐

```bash
python3 dv_routing.py --topo topologies/xyz.json \
        --change "y-x:4->60" --poisoned-reverse --trace
```

**报告要求**：

```
① 启用毒性逆转后收敛需要几轮？
② ⭐ 构造一个【三节点环路】的拓扑，证明毒性逆转【无法】消除其中的无穷计数
③ 说明 RIP 用什么办法兜底（第 20 讲）
```

⭐ **第 ② 问是本作业的最高难度点**，也是区分度最大的一题。

---

## Part 4：简化 BGP 选路（25 分）

### 需求

实现一个遵守 Gao-Rexford 规则的域间选路引擎。

```python
class ASNode:
    def __init__(self, asn: int):
        self.asn = asn
        self.relationships = {}      # {对端ASN: 'customer'|'peer'|'provider'}
        self.rib = {}                # {prefix: [候选路由列表]}

    def receive_announcement(self, from_asn: int, prefix: str,
                             as_path: list[int], attrs: dict) -> None:
        """⭐ 收到通告：① 环路检查 ② 计算 LOCAL_PREF ③ 选路 ④ 决定是否转发"""

    def select_best(self, prefix: str) -> dict | None:
        """⭐ 按 BGP 选路顺序选出最优路由"""
```

### 4.1 环路检测（5 分）

```
⭐ 若收到的 AS_PATH 中包含自己的 ASN → 立即丢弃
```

**验证**：构造一个环状 AS 拓扑，证明你的实现不会产生路由环路。

### 4.2 选路算法（8 分）

严格按第 21 讲的顺序：

```
① ⭐ LOCAL_PREF 最大者胜
② AS_PATH 最短者胜
③ ⭐ IGP 开销最小者胜（热土豆）
④ ASN 最小者胜（tie-break）
```

### 4.3 ⭐ Gao-Rexford 通告规则（8 分）

```
从【客户】学到的路由    → 通告给【所有邻居】
从【对等方】学到的路由  → ⭐ 只通告给【客户】
从【提供商】学到的路由  → ⭐ 只通告给【客户】
```

**并按关系设置 LOCAL_PREF**：

```
customer 路由: LOCAL_PREF = 300
peer 路由:     LOCAL_PREF = 200
provider 路由: LOCAL_PREF = 100
```

**验证**：用第 21 讲例题的五 AS 拓扑，验证你的输出与例题答案一致。

### 4.4 ⭐ 前缀劫持模拟（4 分）

```bash
python3 bgp.py --topo topologies/internet.json \
        --hijack "AS666 announces 198.51.100.0/25"
```

**报告要求**：

```
① ⭐ 有多少个 AS 的流量被劫持了？为什么 /25 能击败合法的 /24？
② ⭐ 实现一个简化的 RPKI 检查（给定 ROA 列表，验证起源 AS 与 maxLength），
   重新运行，说明劫持是否被阻止
③ ⭐ 构造一个 RPKI 【无法阻止】的劫持（伪造 AS_PATH 使起源看起来合法），
   说明为什么需要 BGPsec（第 21 讲）
```

📌 **第 ③ 问要求你真正理解 RPKI 的边界**——这是第 21 讲最重要的安全结论。

---

## ⚠️ 一票否决项

```
❌ Part 3 写成中心化的全局循环（节点直接读取其他节点的状态）
   → Part 3 上限 10/30
   ⭐ 判定标准：节点只能通过 on_receive 获知其他节点的信息
```

---

## 提示

📌 **Part 3 的异步性怎么实现？**不需要真的用线程。用一个**事件队列**即可：

```python
import heapq, random

events = []   # (触发时刻, 序号, 发送方, 接收方, 距离向量)

def send(frm, to, dv, now):
    # ⭐ 加一个随机时延，模拟异步
    delay = random.uniform(0.5, 2.0)
    heapq.heappush(events, (now + delay, next(counter), frm, to, dict(dv)))

while events:
    now, _, frm, to, dv = heapq.heappop(events)
    if nodes[to].on_receive(frm, dv):        # 返回 True 表示自己的 DV 变了
        for nb in nodes[to].neighbors:
            send(to, nb, nodes[to].dv, now)  # ⭐ 通告所有邻居
```

⭐ **随机时延是关键**——它保证了消息乱序到达，这才是真正的异步。**同步的实现可能掩盖掉某些 bug。**

📌 **Part 3.4 第 ② 问的思路**：构造 A、B、C 三个节点连成三角形，另有一个目的节点 D 只连在 A 上。断开 A–D，观察 B 和 C 如何互相"欺骗"——它们各自都没有经过对方（所以毒性逆转不触发），但它们的路径合起来构成了一个环。

---

## 为什么这个作业值得做

📌 你会在这个作业里**亲眼看到**两件教材上只能"告诉"你的事：

1. ⭐ **无穷计数不是一个理论上的可能性，而是一个必然会发生的、可以复现的现象。**
2. ⭐ **BGP 的路由选择是由商业关系而不是路径长度决定的**——你会看到自己的实现选了一条更长的路，仅仅因为它经过的是客户而非对等方。

这两件事，是理解真实互联网如何运转的关键。

