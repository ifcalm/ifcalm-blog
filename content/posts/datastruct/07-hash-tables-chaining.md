---
title: "第 7 讲：散列表 I——散列函数、链地址法与全域散列"
date: 2026-08-28
weight: 7
tags: ["数据结构与算法"]
draft: false
summary: "从直接寻址到散列表：简单均匀散列假设下链地址法的期望代价推导、装填因子的作用、除法法与乘法法的取舍、全域散列的定义与碰撞概率证明，以及散列洪水攻击为什么迫使所有现代语言引入随机化。"
showToc: true
tocOpen: false
---

## 一、字典 ADT 与直接寻址

**字典（dictionary / map）ADT**：维护一组 (key, value) 对，支持 `Search`、`Insert`、`Delete`。

如果键的取值范围是很小的整数集合 U = {0, 1, …, m−1}，做法是平凡的——开一个长度 m 的数组，`T[k]` 直接存对应的值。这叫**直接寻址（direct addressing）**，三个操作都是 O(1)。

**问题**：实际的键空间 U 极其巨大：
- 64 位整数：|U| = 2⁶⁴
- 字符串：|U| = 无穷

而实际存储的键数 n 通常很小（几千到几百万）。**直接寻址的空间是 Θ(|U|)，不可行。**

**散列表的想法**：用一个函数 `h: U → {0, 1, …, m−1}` 把巨大的键空间压进 m 个槽，空间降到 Θ(m) = Θ(n)。

```
     键空间 U（巨大）                    散列表 T（m 个槽）
   ┌──────────────────┐                ┌────┐
   │  "alice"  ───────┼──── h ────────▶│ 0  │
   │  "bob"    ───────┼──── h ─────┐   ├────┤
   │  "carol"  ───────┼──── h ──┐  └──▶│ 1  │
   │  ...             │         │      ├────┤
   │  实际用到的只有 n 个│         └─────▶│ 2  │◀── 碰撞！
   └──────────────────┘                ├────┤
                                       │ 3  │
                                       └────┘
```

**代价是碰撞（collision）**：|U| > m 时，鸽笼原理保证一定存在 h(k₁) = h(k₂)。整个散列表理论就是在回答两个问题：**怎么让碰撞少，以及碰撞了怎么办。**

---

## 二、链地址法

**最直接的解决方案**：每个槽存一条链表，所有映射到该槽的元素挂在同一条链上。

```
T[0] ──▶ nil
T[1] ──▶ [k7,v7] ──▶ [k2,v2] ──▶ nil
T[2] ──▶ nil
T[3] ──▶ [k5,v5] ──▶ nil
T[4] ──▶ [k1,v1] ──▶ [k9,v9] ──▶ [k4,v4] ──▶ nil
```

```go
type entry[K comparable, V any] struct {
    key  K
    val  V
    next *entry[K, V]
}

type HashMap[K comparable, V any] struct {
    buckets []*entry[K, V]
    size    int
    seed    uint64 // 随机种子，见第六节
}

func (m *HashMap[K, V]) index(k K) int {
    return int(hash(k, m.seed) % uint64(len(m.buckets)))
}

func (m *HashMap[K, V]) Get(k K) (V, bool) {
    for e := m.buckets[m.index(k)]; e != nil; e = e.next {
        if e.key == k {
            return e.val, true
        }
    }
    var zero V
    return zero, false
}

func (m *HashMap[K, V]) Put(k K, v V) {
    i := m.index(k)
    for e := m.buckets[i]; e != nil; e = e.next {
        if e.key == k { // 已存在，覆盖
            e.val = v
            return
        }
    }
    m.buckets[i] = &entry[K, V]{key: k, val: v, next: m.buckets[i]} // 头插 O(1)
    m.size++
    if m.loadFactor() > 0.75 {
        m.rehash(2 * len(m.buckets))
    }
}

func (m *HashMap[K, V]) Delete(k K) bool {
    i := m.index(k)
    prev := (*entry[K, V])(nil)
    for e := m.buckets[i]; e != nil; prev, e = e, e.next {
        if e.key == k {
            if prev == nil {
                m.buckets[i] = e.next
            } else {
                prev.next = e.next
            }
            m.size--
            return true
        }
    }
    return false
}

func (m *HashMap[K, V]) loadFactor() float64 {
    return float64(m.size) / float64(len(m.buckets))
}
```

### 装填因子与期望代价

**装填因子（load factor）**：

```
α = n / m = 元素个数 / 槽数 = 每条链的平均长度
```

**简单均匀散列假设（Simple Uniform Hashing Assumption, SUHA）**：任意键等概率地被散列到 m 个槽中的任意一个，且与其他键的散列值独立。

**定理**：在 SUHA 下，链地址法的查找期望代价为 **Θ(1 + α)**（成功与不成功查找均如此）。

**证明（不成功查找）**：查找键 k 需遍历 T[h(k)] 整条链。链长的期望是

```
E[链长] = Σ_{i=1}^{n} Pr[第 i 个键落在槽 h(k)] = n · (1/m) = α
```

加上计算 h(k) 和寻址的 Θ(1)，总期望 = **Θ(1 + α)**。∎

**证明（成功查找）**：设查找的是第 i 个插入的键（头插法下，它之后插入的键排在它前面）。查找它需要检查的元素数为 `1 + (在它之后插入且落在同一槽的键数)`：

```
E = (1/n) Σ_{i=1}^{n} (1 + Σ_{j=i+1}^{n} 1/m)
  = 1 + (1/nm) Σ_{i=1}^{n} (n − i)
  = 1 + (1/nm) · n(n−1)/2
  = 1 + (n−1)/(2m)
  = 1 + α/2 − α/(2n)  =  Θ(1 + α)                  ∎
```

⭐ **推论**：只要维持 **α = O(1)**（即 m = Θ(n)），三个操作都是**期望 O(1)**。这就是为什么必须扩容。

### 再散列与摊还

当 α 超过阈值（Go map 是 6.5 个键/桶，Java HashMap 是 0.75）时，把槽数翻倍并重新插入所有元素：

```go
func (m *HashMap[K, V]) rehash(newSize int) {
    old := m.buckets
    m.buckets = make([]*entry[K, V], newSize)
    for _, head := range old {
        for e := head; e != nil; {
            next := e.next
            i := m.index(e.key)          // 用新的表长重算
            e.next = m.buckets[i]
            m.buckets[i] = e
            e = next
        }
    }
}
```

单次 rehash 是 Θ(n)，但由[第 4 讲]({{< ref "04-amortized-analysis.md" >}})的几何增长论证，**插入的摊还代价仍是 O(1)**。

> Go 的 runtime map 更进一步：它做**渐进式 rehash（incremental evacuation）**——扩容时不一次搬完，而是每次写操作顺带搬迁 1–2 个桶。这样避免了单次操作 Θ(n) 的尖峰，代价是实现复杂度和一段时间内的双表并存。

### ⚠️ 三个必须知道的限制

**（1）最坏情况仍是 Θ(n)。** 所有键都碰撞时，散列表退化成一条链表。

**（2）SUHA 是假设，不是事实。** 它对**固定的** h 永远不可能对**所有**输入成立——见第五节。

**（3）散列表不支持有序操作。** 没有 `Min`、`Predecessor`、范围查询、有序遍历。需要这些就得用平衡树（[第 15–18 讲]({{< ref "15-binary-search-trees.md" >}})）或跳表。Go 的 map 遍历顺序甚至是**故意随机化**的，就是为了防止程序依赖它。

---

## 三、什么是好的散列函数

一个好的散列函数需要满足：

| 性质 | 含义 | 违反的后果 |
|---|---|---|
| **确定性** | 相同键必须给出相同散列值 | 完全不能工作 |
| **均匀性** | 输出在 [0, m) 上近似均匀 | 长链、性能退化 |
| **雪崩效应** | 输入变 1 位，输出约一半位翻转 | 相似键聚簇 |
| **快** | 通常要求 O(键长) 且常数小 | 散列本身成为瓶颈 |

⚠️ **均匀性必须相对于"实际的键分布"而言**，而不是相对于均匀随机的键。实际的键从来不是随机的：连续的用户 ID、共同前缀的 URL、对齐到 8 字节的指针、`.com` 结尾的域名。**一个只对随机输入均匀的散列函数是没用的。**

### 除法法

```
h(k) = k mod m
```

**优点**：一条指令。**缺点**：对 m 极其敏感。

⚠️ **m 绝不能取 2 的幂**：`k mod 2^p` 只取了 k 的低 p 位，高位信息全部丢失。如果键是 8 字节对齐的指针，低 3 位恒为 0，直接损失 8 倍槽位。

**规则**：m 取**远离 2 的幂的素数**。

### 乘法法

```
h(k) = ⌊m · (k·A mod 1)⌋        0 < A < 1
```

取 A ≈ (√5−1)/2 ≈ 0.618（黄金比例，Knuth 的建议）。**优点**：对 m 不敏感，m 可以取 2 的幂（于是能用移位代替除法）。

64 位实现：

```go
// Fibonacci hashing：2^64 / φ ≈ 11400714819323198485
const phi64 = 11400714819323198485

func hashMul(k uint64, shift uint) uint64 {
    return (k * phi64) >> (64 - shift) // 取高 shift 位，表长 2^shift
}
```

⭐ **注意取的是高位而非低位**：乘法把低位的信息"搅拌"到高位，所以高位质量更好。这个技巧叫 **Fibonacci hashing**，被大量高性能哈希表采用。

### 字符串散列

FNV-1a（简单、够用、Go 标准库 `hash/fnv` 提供）：

```go
func fnv1a(s string) uint64 {
    const (
        offset64 = 14695981039346656037
        prime64  = 1099511628211
    )
    h := uint64(offset64)
    for i := 0; i < len(s); i++ {
        h ^= uint64(s[i])
        h *= prime64
    }
    return h
}
```

生产环境更常用 **xxHash**、**wyhash**（Go runtime 自己用的就是 AES 指令加速的变体）或 **SipHash**（抗攻击，见第五节）。

⚠️ 一个反面教材：`h(s) = Σ s[i]`。"abc"、"acb"、"bac" 全部相同，且值域只有 O(字符串长度 × 128)。**任何丢弃位置信息的散列都是错的。**

---

## 四、全域散列

SUHA 无法对固定的 h 成立。**全域散列（universal hashing）** 的解法是：**不用固定的 h，而是在运行时从一族函数中随机挑一个。**

> **定义**：函数族 **H = {h: U → {0,…,m−1}}** 称为**全域的（universal）**，如果对任意两个不同的键 k ≠ l：
> ```
> Pr_{h∈H}[h(k) = h(l)] ≤ 1/m
> ```
> （概率取自 h 的随机选择，而**不是**键的分布。）

这句话的力量在于：**它对任意输入都成立，因为随机性来自算法自己**——正如[第 4 讲]({{< ref "04-amortized-analysis.md" >}})区分的"期望"与"平均情况"。攻击者可以知道你用的是哪一族函数，但不知道你随机选中了哪一个。

### 定理：全域散列下期望链长仍是 O(1 + α)

**证明**：对键 k，定义指示随机变量 `X_{kl} = 1` 当且仅当 `h(k) = h(l)`。则 `E[X_{kl}] ≤ 1/m`。k 所在槽的其他元素数为

```
E[Nₖ] = E[Σ_{l≠k} X_{kl}] = Σ_{l≠k} E[X_{kl}] ≤ (n−1)/m < α        ∎
```

**注意这个证明没有对键的分布做任何假设。** 这就是全域散列相对 SUHA 的全部价值。

### 一个具体的全域族

取素数 p > |U|，随机选 a ∈ {1,…,p−1}、b ∈ {0,…,p−1}：

```
h_{a,b}(k) = ((a·k + b) mod p) mod m
```

**这族函数是全域的**（证明思路：对 k ≠ l，映射 `(k,l) ↦ ((ak+b) mod p, (al+b) mod p)` 是双射，于是 p(p−1) 对 (a,b) 中至多有 p(p−1)/m 对导致碰撞）。

```go
type UniversalHash struct{ a, b, p, m uint64 }

func NewUniversalHash(m uint64) UniversalHash {
    const p = (1 << 61) - 1 // 梅森素数
    return UniversalHash{
        a: 1 + rand.Uint64()%(p-1),
        b: rand.Uint64() % p,
        p: p, m: m,
    }
}

func (u UniversalHash) Hash(k uint64) uint64 {
    return ((u.a*k + u.b) % u.p) % u.m
}
```

---

## 五、散列洪水攻击

**2011 年，多个 Web 框架（PHP、Java、Python、Ruby、Node.js）同时被同一个漏洞击中。**

**攻击方式**：Web 服务器把 HTTP POST 参数放进散列表。攻击者离线计算出几万个**散列值相同**的参数名，一次请求发过去：

```
POST /  a=1&aa=1&aaa=1&...   ← 所有键的 h(k) 相同
```

散列表退化成链表，每次插入都要走完整条链：**n 次插入 = Θ(n²)。** 几百 KB 的请求就能让一台服务器 CPU 满载几分钟。这是拒绝服务（DoS），CVE-2011-4815 等一系列编号。

**根因**：散列函数是**固定且公开**的，攻击者可以离线构造最坏输入。

**修复**：全域散列的工程版本——**给散列函数加进程启动时的随机种子**。

| 语言/运行时 | 做法 |
|---|---|
| **Go** | runtime map 每个进程用随机 `hash0` 种子，且遍历顺序随机化 |
| **Python** | 3.3+ 默认 `PYTHONHASHSEED` 随机（可关闭） |
| **Rust** | `HashMap` 默认用带随机密钥的 SipHash 1-3 |
| **Java** | HashMap 在单桶超过 8 个元素时**转成红黑树**，把最坏从 O(n) 降到 O(log n) |

⭐ Java 的做法值得单独注意：它不消灭碰撞，而是**给碰撞兜底**。这是一个非常实用的防御思路——把最坏情况从线性降到对数，攻击的收益就不够了。

> **一句话总结**：**散列表的期望 O(1) 是一个概率论断言，它需要随机性作为前提。当随机性来自"假设输入是随机的"时，它可以被攻击；当随机性来自算法自己的种子时，它才是可靠的。**

---

## 六、Go map 的实现要点

作为工程参照，简单列出 Go runtime map 与教科书链地址法的差异：

| 维度 | 教科书 | Go runtime |
|---|---|---|
| 桶结构 | 链表节点，每节点 1 个键值 | 每桶存 **8 个键值** 的数组 + overflow 指针 |
| 快速比较 | 直接比较键 | 先比 **tophash**（散列高 8 位），不等直接跳过 |
| 内存布局 | key/value 交错 | **所有 key 连续，所有 value 连续**（省对齐填充） |
| 扩容 | 一次搬完 | **渐进式搬迁**，每次写搬 1–2 个桶 |
| 装填阈值 | α ≈ 0.75 | 6.5 个键/桶 |
| 迭代顺序 | 实现相关 | **故意随机**，防止依赖 |

⭐ "每桶 8 个键 + tophash 预筛" 是缓存友好性的直接体现：一个桶正好在少数几条缓存行内，8 次 tophash 比较是顺序内存访问，比追 8 次指针快一个数量级。**这正是[第 5 讲]({{< ref "05-arrays-linked-lists.md" >}})缓存局部性结论在真实系统里的应用。**

---

## 随堂自测

1. 为什么不能直接用直接寻址表处理 64 位整数键？散列表用什么代价换来了空间上的可行性？
2. 推导链地址法在 SUHA 下不成功查找的期望代价。为什么维持 α = O(1) 就能得到 O(1) 操作？
3. 除法法中 m 为什么不能取 2 的幂？如果键都是 16 的倍数、m = 64，会发生什么？
4. 全域散列的定义中，概率是对什么取的？为什么这一点使它能抵抗恶意输入而 SUHA 不能？
5. 证明：若 H 是全域族，则从 H 中随机选 h，任意键 k 所在链的期望长度小于 α + 1。
6. 散列洪水攻击的原理是什么？为什么"给散列加随机种子"能防住它，而"换一个更复杂的散列函数"不能？
7. Java 把长链转成红黑树，这个做法把最坏复杂度从什么降到了什么？它为什么比随机化种子更"兜底"？
8. Go map 的迭代顺序为什么被故意随机化？

---

> **上一讲**：[第 6 讲：栈、队列与双端队列]({{< ref "06-stacks-queues.md" >}})　**下一讲**：[第 8 讲：散列表 II——开放寻址、Cuckoo、一致性散列与布隆过滤器]({{< ref "08-hash-tables-open-addressing.md" >}})
