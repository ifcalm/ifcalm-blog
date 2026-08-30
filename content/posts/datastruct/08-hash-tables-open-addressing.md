---
title: "第 8 讲：散列表 II——开放寻址、Cuckoo、一致性散列与布隆过滤器"
date: 2026-08-28
weight: 8
tags: ["数据结构与算法"]
draft: false
summary: "开放寻址的三种探查方式与聚簇现象、探查次数 1/(1−α) 的推导、墓碑删除的代价、Robin Hood 与 Cuckoo 散列的最坏保证、一致性散列如何把再平衡代价降到 K/n，以及布隆过滤器的误判率公式与最优参数。"
showToc: true
tocOpen: false
---

## 一、开放寻址：不要链表

**链地址法的问题**：每个元素都是一次独立的堆分配，指针追逐，缓存不友好（[第 5 讲]({{< ref "05-arrays-linked-lists.md" >}})）。

**开放寻址（open addressing）** 的想法：**所有元素都存在表内**。槽被占了就按某个规则去探查下一个槽。

散列函数变成两个参数：`h(k, i)` 表示键 k 的第 i 次探查位置，探查序列 `⟨h(k,0), h(k,1), …, h(k,m−1)⟩` 应当是 {0,…,m−1} 的一个排列。

⚠️ **必然结果：n ≤ m**。开放寻址装不下比槽还多的元素，α ≤ 1。

### 三种探查方式

```
线性探查   h(k,i) = (h'(k) + i) mod m
二次探查   h(k,i) = (h'(k) + c₁i + c₂i²) mod m
双重散列   h(k,i) = (h₁(k) + i·h₂(k)) mod m
```

```
线性探查（步长 1）：      二次探查（步长 1,4,9…）：   双重散列（步长依键而定）：
 ┌─┬─┬─┬─┬─┬─┬─┬─┐        ┌─┬─┬─┬─┬─┬─┬─┬─┐        ┌─┬─┬─┬─┬─┬─┬─┬─┐
 │ │▓│▓│▓│▓│●│ │ │        │ │▓│ │ │▓│ │ │ │        │ │▓│ │ │ │▓│ │ │
 └─┴─┴─┴─┴─┴─┴─┴─┘        └─┴─┴─┴─┴─┴─┴─┴─┘        └─┴─┴─┴─┴─┴─┴─┴─┘
  一次聚簇：连成一片          二次聚簇：同起点同序列       各键探查序列不同
  缓存最好                   缓存中等                    缓存最差，分布最好
```

| 方式 | 不同探查序列数 | 聚簇 | 缓存 |
|---|---|---|---|
| 线性探查 | m | **一次聚簇（primary clustering）**：连续占用块会互相吞并，越长越容易变长 | **最好**（纯顺序访问） |
| 二次探查 | m | **二次聚簇**：h′ 相同的键走完全相同的序列 | 中等 |
| 双重散列 | **m²** | 基本没有 | 差 |

⚠️ 二次探查要保证能遍历全表：m 取 2 的幂时 `c₁ = c₂ = 1/2` 可行；否则需要挑选参数。这是它实践中不如另两者流行的原因。

⚠️ 双重散列要求 `h₂(k)` 与 m 互素，否则探查序列覆盖不到全表。常见做法：m 取 2 的幂，`h₂` 强制取奇数。

### 期望探查次数

**均匀散列假设**下（每个键的探查序列等概率是 m! 个排列之一）：

```
不成功查找 / 插入：   E[探查次数] ≤ 1/(1−α)
成功查找：            E[探查次数] ≤ (1/α)·ln(1/(1−α))
```

**不成功查找的证明**：每次探查命中空槽的概率约为 (1−α)，几何分布的期望是 `1/(1−α)`。∎

**这个公式必须刻在脑子里**：

| α | 1/(1−α) | 含义 |
|---|---|---|
| 0.5 | 2 | 表半满，平均探查 2 次 |
| 0.75 | 4 | |
| 0.9 | **10** | |
| 0.95 | **20** | |
| 0.99 | **100** | 性能已经崩溃 |

⭐ **代价随 α 不是线性增长，而是在 α → 1 时爆炸。** 这就是所有开放寻址实现都在 α ≈ 0.5–0.75 就扩容的原因。链地址法的 Θ(1+α) 是线性的，所以能容忍更高的装填因子——这是两种方案最本质的性能差异。

---

## 二、开放寻址的实现与墓碑

```go
type slotState uint8

const (
    empty slotState = iota
    occupied
    deleted // 墓碑
)

type OpenMap[K comparable, V any] struct {
    keys   []K
    vals   []V
    states []slotState
    size   int // occupied 数
    used   int // occupied + deleted 数
}

func (m *OpenMap[K, V]) probe(k K, i int) int {
    n := uint64(len(m.keys))
    h1 := hash1(k) % n
    h2 := hash2(k)%(n-1) + 1 // 与 n 互素（n 取 2 的幂时强制取奇数）
    return int((h1 + uint64(i)*h2) % n)
}

func (m *OpenMap[K, V]) Get(k K) (V, bool) {
    for i := 0; i < len(m.keys); i++ {
        j := m.probe(k, i)
        switch m.states[j] {
        case empty:
            var zero V
            return zero, false // 遇到真正的空槽才能断定不存在
        case occupied:
            if m.keys[j] == k {
                return m.vals[j], true
            }
        }
        // deleted：必须继续往后探查
    }
    var zero V
    return zero, false
}

func (m *OpenMap[K, V]) Delete(k K) bool {
    for i := 0; i < len(m.keys); i++ {
        j := m.probe(k, i)
        if m.states[j] == empty {
            return false
        }
        if m.states[j] == occupied && m.keys[j] == k {
            m.states[j] = deleted // ⚠️ 不能置为 empty
            m.size--
            return true
        }
    }
    return false
}
```

### ⚠️ 为什么删除必须留墓碑

```
插入 k₁（探查到槽 3）、k₂（槽 3 被占，探查到槽 4）

 ┌─┬─┬─┬────┬────┬─┐
 │ │ │ │ k₁ │ k₂ │ │
 └─┴─┴─┴────┴────┴─┘

删除 k₁ 并把槽 3 置空：

 ┌─┬─┬─┬────┬────┬─┐
 │ │ │ │空  │ k₂ │ │
 └─┴─┴─┴────┴────┴─┘

现在查找 k₂：探查槽 3 发现是空 → 断定"不存在" → ✗ 但 k₂ 明明在表里！
```

**墓碑（tombstone）** 标记"这里曾有元素，查找请继续走"。

**墓碑的代价**：它们仍然占据探查路径。删除频繁的表，即使 `size` 很小，`used` 也可能接近 m，探查次数照样爆炸。**因此扩容判断必须用 `used`（含墓碑）而不是 `size`**，并在墓碑过多时做一次原地重建。

⭐ **这是开放寻址相对链地址法最大的工程劣势：删除操作会污染结构。** 如果 workload 是"高频删除 + 高频查找"，链地址法通常是更省心的选择。

---

## 三、Robin Hood 与 Cuckoo：给最坏情况上界

### Robin Hood 散列

在线性探查中，记录每个元素的**探查距离（probe sequence length, PSL）**——它离自己理想位置有多远。插入时：

> **如果当前元素的 PSL 小于待插入元素的 PSL，就把两者交换，让"富人"（离家近的）让位给"穷人"。**

```go
func (m *RobinHood[K, V]) Put(k K, v V) {
    j, dist := int(hash(k)%uint64(len(m.slots))), 0
    for {
        if !m.slots[j].occupied {
            m.slots[j] = slot[K, V]{k, v, dist, true}
            m.size++
            return
        }
        if m.slots[j].key == k {
            m.slots[j].val = v
            return
        }
        if m.slots[j].dist < dist { // 劫富济贫：交换后继续为被踢出者找位置
            m.slots[j], k, v, dist = slot[K, V]{k, v, dist, true}, m.slots[j].key, m.slots[j].val, m.slots[j].dist
        }
        j = (j + 1) % len(m.slots)
        dist++
    }
}
```

**效果**：PSL 的**方差**大幅下降。最长探查距离从 O(log n) 降到 O(log log n)。而且查找可以**提前终止**——探查到某个位置时，如果那里元素的 PSL 比当前 dist 还小，说明目标键不可能在更后面。

**这是现代高性能哈希表（Rust 的 hashbrown、Swiss Tables）的核心思路之一**：不追求平均更快，而是**削掉长尾**。P99 延迟往往比平均延迟更重要。

### Cuckoo 散列

用**两个**散列函数和两张表。每个键只可能在两个位置之一：`T₁[h₁(k)]` 或 `T₂[h₂(k)]`。

```
查找：至多看 2 个槽 ⟹ 最坏 O(1)！
删除：至多看 2 个槽 ⟹ 最坏 O(1)！
插入：放进 T₁[h₁(k)]；若被占，踢走原住户，让它去自己的另一个位置；
      被踢者再踢走那里的住户……直到找到空位，或循环次数超阈值 → 全表重建
```

```
插入 x：
  T₁[h₁(x)] 被 a 占  →  踢走 a，x 就位
  a 去 T₂[h₂(a)]，被 b 占  →  踢走 b，a 就位
  b 去 T₁[h₁(b)]，空  →  b 就位，结束
```

| 操作 | Cuckoo 散列 |
|---|---|
| 查找 | **最坏 O(1)**（至多 2 次探查） |
| 删除 | **最坏 O(1)** |
| 插入 | 期望 O(1)，但 α > 0.5 时失败率上升，需重建 |

⭐ **Cuckoo 是唯一给出查找最坏 O(1) 保证的实用散列方案。** 代价是插入可能触发长链踢出甚至全表重建，且装填因子受限（两函数版约 0.5，四路桶版可到 0.95）。在**读远多于写**的场景（路由表、只读索引）非常合适。

---

## 四、一致性散列

**场景**：n 台服务器缓存数据，用 `server = hash(key) % n` 分配。

**问题**：加一台机器（n → n+1），`hash(key) % n` 与 `hash(key) % (n+1)` 几乎全都不同——**几乎所有键都要迁移**。对缓存集群这意味着瞬间全部未命中，请求全打到后端数据库，直接雪崩。

**一致性散列（consistent hashing）** 的解法：把散列值空间看成一个环。

```
                    0 / 2³²
                       │
          节点C ◀──────┼──────▶ 节点A
             ╱         │         ╲
            ╱     key1 ●          ╲       规则：每个 key 顺时针
           │          ╱            │      找到的第一个节点，
           │         ╱             │      就是它的归属节点
            ╲   key2 ●            ╱
             ╲       │           ╱
               ──────┼──────────
                  节点B
```

**加入节点 D 时**：只有"从 D 逆时针到前一个节点"这一段的键需要迁移到 D，**其余键完全不动**。

**定理**：K 个键、n 个节点，增删一个节点平均只迁移 **K/n** 个键。

### 虚拟节点

**问题**：节点在环上的位置是随机的，可能分布很不均匀；且节点少时方差很大。

**解法**：每个物理节点在环上放 **V 个虚拟节点**（如 `hash("nodeA#0")`, `hash("nodeA#1")`, …）。V 取 100–200 时负载偏差可控制在几个百分点内。

```go
type ConsistentHash struct {
    ring     []uint64          // 有序的虚拟节点散列值
    nodes    map[uint64]string // 散列值 → 物理节点
    replicas int
}

func (c *ConsistentHash) Add(node string) {
    for i := 0; i < c.replicas; i++ {
        h := hash64(fmt.Sprintf("%s#%d", node, i))
        c.ring = append(c.ring, h)
        c.nodes[h] = node
    }
    slices.Sort(c.ring)
}

func (c *ConsistentHash) Get(key string) string {
    if len(c.ring) == 0 { return "" }
    h := hash64(key)
    // 二分找第一个 ≥ h 的虚拟节点，找不到就绕回环首
    i := sort.Search(len(c.ring), func(i int) bool { return c.ring[i] >= h })
    if i == len(c.ring) { i = 0 }
    return c.nodes[c.ring[i]]
}
```

查找是环上的二分，**O(log(nV))**。

**实际用途**：Memcached 客户端分片、Cassandra/DynamoDB 的分区、CDN 节点选择、Nginx 上游负载均衡（`hash ... consistent`）。

> 现代替代方案 **Rendezvous hashing（HRW）** 更简单：`node = argmax_n hash(key, n)`。它天然均匀、无需虚拟节点，代价是每次查找 O(n) 而非 O(log n)。节点数不多时通常更优。

---

## 五、布隆过滤器

**场景**：判断一个元素**可能**在集合中，且能接受一定误判，但要求空间极省。

**结构**：一个 m 位的位数组 + k 个独立散列函数。

```
插入 x：把 h₁(x), h₂(x), …, hₖ(x) 这 k 个位置都置 1
查询 y：这 k 个位置全为 1 ⟹ "可能存在"
        任一位为 0        ⟹ "一定不存在"
```

```
位数组（m=16, k=3）：
 索引  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
      ┌──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┐
      │0 │1 │0 │0 │1 │0 │0 │1 │0 │1 │0 │0 │1 │0 │0 │0 │
      └──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘
        插入"cat" → 位 1,4,9      插入"dog" → 位 7,9,12
        查询"fox" → 位 1,7,12 全为 1 → 误判为"可能存在"！
```

```go
type BloomFilter struct {
    bits []uint64
    m, k uint64
}

func NewBloom(n uint64, fpRate float64) *BloomFilter {
    m := uint64(math.Ceil(-float64(n) * math.Log(fpRate) / (math.Ln2 * math.Ln2)))
    k := uint64(math.Round(float64(m) / float64(n) * math.Ln2))
    return &BloomFilter{bits: make([]uint64, (m+63)/64), m: m, k: max(k, 1)}
}

// 双散列技巧：用两个散列函数模拟 k 个（Kirsch-Mitzenmacher）
func (b *BloomFilter) positions(data []byte) func(func(uint64) bool) {
    h1, h2 := hash1(data), hash2(data)|1
    return func(yield func(uint64) bool) {
        for i := uint64(0); i < b.k; i++ {
            if !yield((h1 + i*h2) % b.m) { return }
        }
    }
}

func (b *BloomFilter) Add(data []byte) {
    for p := range b.positions(data) {
        b.bits[p/64] |= 1 << (p % 64)
    }
}

func (b *BloomFilter) MayContain(data []byte) bool {
    for p := range b.positions(data) {
        if b.bits[p/64]&(1<<(p%64)) == 0 {
            return false // 确定不存在
        }
    }
    return true // 可能存在
}
```

### 误判率与最优参数

插入 n 个元素后，某一位仍为 0 的概率是 `(1 − 1/m)^{kn} ≈ e^{−kn/m}`。因此误判率

```
FP ≈ (1 − e^{−kn/m})^k
```

对 k 求导取极值，得**最优散列函数个数**：

```
k* = (m/n)·ln 2 ≈ 0.693 · (m/n)
```

代入得**最优误判率**：

```
FP = (0.6185)^{m/n}
```

反解出**给定误判率所需的位数**：

```
m/n = −log₂(FP) / ln 2 ≈ 1.44 · log₂(1/FP)
```

| 目标误判率 | 每元素位数 m/n | 最优 k |
|---|---|---|
| 10% | 4.8 | 3 |
| 1% | **9.6**（约 1.2 字节） | 7 |
| 0.1% | 14.4 | 10 |
| 0.01% | 19.2 | 13 |

⭐ **1% 误判率下每个元素只要 1.2 字节**——与元素本身多大完全无关。这就是布隆过滤器的价值：存 10 亿个 URL 只需 1.2 GB，而存 URL 本身要几百 GB。

### 性质与变体

| 性质 | 说明 |
|---|---|
| **无假阴性** | 说"不存在"就一定不存在 |
| **有假阳性** | 说"可能存在"可能是错的 |
| **不能删除** | 清零某位会影响共享该位的其他元素 |
| **不能取出元素** | 只存位，不存数据 |
| **可以求并** | 两个同参数过滤器按位或 = 并集 |

**变体**：**计数布隆过滤器**（每位改成 4 位计数器，支持删除，空间 ×4）、**Cuckoo filter**（支持删除且空间更省）、**商过滤器**（缓存友好）。

**真实用途**：

- **LSM 树 / RocksDB / LevelDB**：查询前先问布隆过滤器，避免无谓的磁盘读——这是 LSM 读性能的关键。
- **Chrome 恶意网址检查**：本地过滤器先筛，可能命中才查服务器。
- **比特币 SPV 轻钱包**：BIP 37 用它筛选相关交易。
- **CDN 边缘节点**："这个对象只被请求过一次吗"——避免为一次性请求缓存。

---

## 六、方案对比与选型

| 方案 | 查找 | 删除 | 空间 | 最坏保证 | 适用 |
|---|---|---|---|---|---|
| 链地址法 | 期望 Θ(1+α) | 简单 | n 个指针 | O(n) | 通用，删除频繁 |
| 线性探查 | 期望 1/(1−α) | 墓碑 | 表内 | O(n) | **缓存最优**，读多写少 |
| 双重散列 | 期望 1/(1−α) | 墓碑 | 表内 | O(n) | 分布最好 |
| Robin Hood | 期望 O(1)，尾部短 | 回填/墓碑 | 表内 + PSL | O(log log n) 长度 | **削长尾**，低延迟系统 |
| Cuckoo | **最坏 O(1)** | **最坏 O(1)** | 表内，α ≤ 0.5 | 插入可能重建 | 读密集、要求确定延迟 |
| 一致性散列 | O(log n) | — | O(nV) | — | 分布式分片 |
| 布隆过滤器 | O(k) | 不支持 | **1.2 字节/元素** | 有误判 | 存在性预筛 |

---

## 随堂自测

1. 推导开放寻址不成功查找的期望探查次数 1/(1−α)。为什么 α = 0.99 时性能崩溃而链地址法不会？
2. 为什么开放寻址删除元素时必须留墓碑？画出一个"直接置空导致查找失败"的具体例子。
3. 一张开放寻址表反复插入删除，`size` 一直很小但查找越来越慢。原因是什么？怎么修？
4. 线性探查缓存最优但有一次聚簇，双重散列没有聚簇但缓存最差。什么样的 workload 该选哪个？
5. Robin Hood 散列为什么能让查找提前终止？写出终止条件。
6. Cuckoo 散列查找为什么是最坏 O(1)？它付出的代价是什么？
7. 用 `hash(key) % n` 分片，从 4 台机器扩到 5 台，大约多少比例的键要迁移？一致性散列是多少？
8. 布隆过滤器要达到 1% 误判率，每个元素需要多少位？如果内存只够 5 位/元素，最优 k 是多少，误判率约为多少？
9. 为什么布隆过滤器不能直接支持删除？计数布隆过滤器付出了什么代价？

