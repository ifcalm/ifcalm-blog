---
title: "第 23 讲：并查集与不相交集合"
date: 2026-08-28
weight: 23
tags: ["数据结构与算法"]
draft: false
summary: "不相交集合 ADT、按秩合并与路径压缩两种优化各自的界、组合后 O(α(n)) 的含义与反 Ackermann 函数、带权并查集与可撤销并查集，以及为什么它在 Kruskal 和连通性问题中不可替代。"
showToc: true
tocOpen: false
---

## 一、不相交集合 ADT

维护一组**互不相交**的集合，支持：

| 操作 | 语义 |
|---|---|
| `MakeSet(x)` | 创建只含 x 的集合 |
| `Find(x)` | 返回 x 所属集合的**代表元** |
| `Union(x, y)` | 合并 x 和 y 所在的两个集合 |

**判断 x 与 y 是否同组**：`Find(x) == Find(y)`。

⚠️ **注意这个 ADT 不支持什么：分裂（split）、删除元素、枚举某个集合的所有成员**（除非额外维护）。**它只回答"是否在一起"。** 正是这种极度的受限，让它能做到近乎 O(1)。

**典型问题**：

- 动态连通性："加了这条边之后，A 和 B 连通了吗"
- Kruskal 求最小生成树（[第 24 讲]({{< ref "24-minimum-spanning-trees.md" >}})）：判断加边是否成环
- 图像连通区域标记
- 编译器的类型统一（unification）
- 网络中的等价类合并、账号合并

---

## 二、朴素实现与两个优化

### 森林表示

每个集合是一棵树，根是代表元。`parent[x]` 指向父节点，根的 `parent` 指向自己。

```
   集合 {1,2,3,4}          集合 {5,6}

        1                      5
      ╱   ╲                     ╲
     2     3                     6
     │
     4
```

```go
type DSU struct {
    parent []int
    rank   []int // 秩：树高的上界
    count  int   // 当前集合数
}

func NewDSU(n int) *DSU {
    d := &DSU{parent: make([]int, n), rank: make([]int, n), count: n}
    for i := range d.parent {
        d.parent[i] = i // 每个元素自成一集
    }
    return d
}
```

**朴素版**的问题：树可能退化成链，`Find` 退化为 O(n)。

### 优化一：按秩合并（Union by Rank）

**总是把矮树挂到高树下**，避免树变高。

```go
func (d *DSU) Union(x, y int) bool {
    rx, ry := d.Find(x), d.Find(y)
    if rx == ry {
        return false // 已在同一集合
    }
    if d.rank[rx] < d.rank[ry] { // ⭐ 矮的挂到高的下面
        rx, ry = ry, rx
    }
    d.parent[ry] = rx
    if d.rank[rx] == d.rank[ry] {
        d.rank[rx]++ // 只有等高合并才会让高度加 1
    }
    d.count--
    return true
}
```

> **定理**：只用按秩合并，树高为 **O(log n)**。

**证明**：秩为 k 的树至少有 2^k 个节点（对 k 归纳：秩 k 的树由两棵秩 k−1 的树合并而来，节点数 ≥ 2·2^{k−1} = 2^k）。故 `n ≥ 2^k ⟹ k ≤ log₂ n`。∎

**变体：按大小合并（Union by Size）**——把小集合挂到大集合下。界同样是 O(log n)，且 `size` 数组本身常常有用（如"求所在连通块的大小"），实践中更常用。

### 优化二：路径压缩（Path Compression）

**Find 的路上，把所有节点直接挂到根上。**

```go
func (d *DSU) Find(x int) int {
    if d.parent[x] != x {
        d.parent[x] = d.Find(d.parent[x]) // 递归返回时改指向根
    }
    return d.parent[x]
}
```

```
压缩前：      1              压缩后（Find(4) 之后）：
            ╱                        1
           2                       ╱ │ ╲
           │                      2  3  4
           3
           │
           4
```

**迭代版**（避免深递归）：

```go
func (d *DSU) Find(x int) int {
    root := x
    for d.parent[root] != root {
        root = d.parent[root]
    }
    for d.parent[x] != root { // 第二趟：全部改指向根
        d.parent[x], x = root, d.parent[x]
    }
    return root
}
```

**路径分裂（path splitting）/ 路径减半（path halving）** 是单趟的变体，常数更小：

```go
func (d *DSU) Find(x int) int { // 路径减半：每隔一个节点指向祖父
    for d.parent[x] != x {
        d.parent[x] = d.parent[d.parent[x]]
        x = d.parent[x]
    }
    return x
}
```

⭐ **路径减半只需一趟循环，无递归，实测通常最快**，是工程实现的推荐写法。

---

## 三、复杂度：O(α(n))

| 优化组合 | 每操作摊还代价 |
|---|---|
| 都不用 | O(n) |
| 仅按秩合并 | O(log n) |
| 仅路径压缩 | O(log n)（摊还） |
| **两者结合** | **O(α(n))** |

> **Tarjan 定理（1975）**：同时使用按秩合并与路径压缩，m 次操作在 n 个元素上的总代价是 **Θ(m · α(n))**，其中 α 是**反 Ackermann 函数**。

### α(n) 有多小

Ackermann 函数 A(k, j) 增长得快到荒谬，它的反函数因此增长得慢到荒谬：

```
α(n) ≤ 4    对所有  n < 2^2^2^2^16  ≈ 10^{10^{19728}}
```

⭐ **宇宙中的原子数约 10⁸⁰。** 所以在任何真实场景中，**α(n) ≤ 4，并查集操作实质上是常数时间**。

⚠️ 但要精确：**它不是 O(1)**。已经证明（Fredman & Saks 1989）**Ω(α(n)) 是这个问题在 cell-probe 模型下的下界**——不存在真正 O(1) 的并查集。这是理论计算机科学中少见的"下界恰好等于上界，且这个界如此古怪"的结果。

### 为什么两个优化必须一起用

- **只有按秩合并**：树高 O(log n)，但每次 Find 都要重新走完整条路径。
- **只有路径压缩**：单次可能很贵（第一次 Find 要走 O(n)），但压缩后便宜；摊还是 O(log n)。
- **两者结合**：按秩合并保证树本来就矮，路径压缩再把走过的路径全部拍平——**每条路径最多被完整走一次**。

这是[第 4 讲]({{< ref "04-amortized-analysis.md" >}})摊还分析的一个高级应用：完整证明用**分层（ranking by levels）** 的记账法，把节点按秩分成若干组，证明每个节点跨组的次数有限。

---

## 四、两个重要变体

### 带权并查集

在 `parent` 之外维护**到父节点的相对权值**，用于回答"x 与 y 的关系是什么"而不只是"是否相关"。

```go
type WeightedDSU struct {
    parent []int
    diff   []int // diff[x] = value[x] - value[parent[x]]
}

func (d *WeightedDSU) Find(x int) (root int, w int) {
    if d.parent[x] == x {
        return x, 0
    }
    root, pw := d.Find(d.parent[x])
    d.diff[x] += pw       // ⭐ 路径压缩时累加权值
    d.parent[x] = root
    return root, d.diff[x]
}

// 声明 value[y] - value[x] = w
func (d *WeightedDSU) Union(x, y, w int) bool {
    rx, wx := d.Find(x)
    ry, wy := d.Find(y)
    if rx == ry {
        return wy-wx == w // 校验一致性：矛盾则返回 false
    }
    d.parent[ry] = rx
    d.diff[ry] = wx + w - wy
    return true
}
```

**应用**：食物链问题、差分约束的一致性检查、"A 比 B 高 3 厘米"这类关系推理、以及**判断一组等式约束是否自相矛盾**（编译器的类型统一就是这个问题）。

### 可撤销并查集

⚠️ **路径压缩与"撤销"不兼容**——压缩改动了大量指针，无法回滚。

需要撤销时（如"离线动态连通性"、回溯搜索）：**只用按秩合并，放弃路径压缩**，用一个栈记录每次合并改动的指针：

```go
type RollbackDSU struct {
    parent, size []int
    history      []int // 记录每次 Union 时被挂上去的根
}

func (d *RollbackDSU) Union(x, y int) bool {
    rx, ry := d.Find(x), d.Find(y) // Find 无压缩，O(log n)
    if rx == ry {
        d.history = append(d.history, -1)
        return false
    }
    if d.size[rx] < d.size[ry] { rx, ry = ry, rx }
    d.parent[ry] = rx
    d.size[rx] += d.size[ry]
    d.history = append(d.history, ry)
    return true
}

func (d *RollbackDSU) Rollback() {
    ry := d.history[len(d.history)-1]
    d.history = d.history[:len(d.history)-1]
    if ry == -1 { return }
    d.size[d.parent[ry]] -= d.size[ry]
    d.parent[ry] = ry
}
```

**代价**：每操作 O(log n) 而非 O(α(n))。

⭐ **这是一个很好的取舍案例：路径压缩带来了性能，但破坏了"结构的历史可逆性"。当需求变成"可撤销"时，就必须把它换掉。**

---

## 五、应用

### Kruskal 最小生成树

```go
func Kruskal(n int, edges []WeightedEdge) []WeightedEdge {
    slices.SortFunc(edges, func(a, b WeightedEdge) int { return a.W - b.W })
    d := NewDSU(n)
    var mst []WeightedEdge
    for _, e := range edges {
        if d.Union(e.U, e.V) { // 不成环才加入
            mst = append(mst, e)
            if len(mst) == n-1 {
                break
            }
        }
    }
    return mst
}
```

**总代价 O(E log E)**，其中排序 O(E log E) 支配，并查集部分只有 O(E α(V))。详见[第 24 讲]({{< ref "24-minimum-spanning-trees.md" >}})。

### 动态连通性

```
"加边"型的连通性问题：并查集，每操作 O(α(n))          ✓ 完美
"删边"型的连通性问题：并查集做不到                     ✗
```

⭐ **并查集是一个"只增不减"的结构**。删边需要完全不同的技术：**离线**可以用"时间分治 + 可撤销并查集"，**在线**要用 Link-Cut Tree 或 Euler Tour Tree（O(log²n)）。

**这个非对称性值得记住**：遇到"删边后询问连通性"，先想想能不能把问题**离线倒过来处理**——把删边变成加边，问题立刻变简单。

### 其他

| 应用 | 做法 |
|---|---|
| 图像连通区域标记 | 逐行扫描，相邻同色像素 Union |
| 账号合并（同一人的多个邮箱） | 每个邮箱一个元素，同账号内 Union |
| 网格渗流（percolation） | 加虚拟源点和汇点，判断二者是否连通 |
| 判断等式约束是否矛盾 | `a == b` 用 Union，`a != b` 最后校验 |
| 最近公共祖先（Tarjan 离线 LCA） | DFS + 并查集，O((n+q)α(n)) |

---

## 六、完整实现

```go
type DSU struct {
    parent []int
    size   []int
    count  int
}

func NewDSU(n int) *DSU {
    d := &DSU{parent: make([]int, n), size: make([]int, n), count: n}
    for i := range d.parent {
        d.parent[i], d.size[i] = i, 1
    }
    return d
}

func (d *DSU) Find(x int) int { // 路径减半
    for d.parent[x] != x {
        d.parent[x] = d.parent[d.parent[x]]
        x = d.parent[x]
    }
    return x
}

func (d *DSU) Union(x, y int) bool { // 按大小合并
    rx, ry := d.Find(x), d.Find(y)
    if rx == ry {
        return false
    }
    if d.size[rx] < d.size[ry] {
        rx, ry = ry, rx
    }
    d.parent[ry] = rx
    d.size[rx] += d.size[ry]
    d.count--
    return true
}

func (d *DSU) Connected(x, y int) bool { return d.Find(x) == d.Find(y) }
func (d *DSU) Size(x int) int          { return d.size[d.Find(x)] }
func (d *DSU) Count() int              { return d.count } // 连通分量个数
```

**30 行，每操作近乎 O(1)。** ⭐ 这是整门课程里"性价比"最高的数据结构：实现最简单，威力却极大。

---

## 随堂自测

1. 并查集**不支持**哪三类操作？这些限制换来了什么？
2. 证明：只用按秩合并时，树高是 O(log n)。
3. 路径压缩的递归版与路径减半版有什么区别？为什么后者在工程上更受欢迎？
4. 为什么按秩合并和路径压缩必须一起用？各自单独用能达到什么界？
5. α(n) 在实际中是多少？为什么说并查集"实质上是常数时间"但严格说不是 O(1)？
6. 带权并查集在路径压缩时如何维护权值？写出 Find 的代码。
7. 为什么可撤销并查集必须放弃路径压缩？它的复杂度变成多少？
8. 并查集能处理"加边后询问连通性"，为什么处理不了"删边"？有哪些应对办法？
9. 给定一批形如 `a==b` 和 `a!=b` 的约束，如何用并查集判断是否矛盾？
10. 在 Kruskal 中，并查集的总代价是多少？它是瓶颈吗？

---

> **上一讲**：[第 22 讲：深度优先搜索、拓扑排序与强连通分量]({{< ref "22-dfs-topological-scc.md" >}})　**下一讲**：[第 24 讲：最小生成树]({{< ref "24-minimum-spanning-trees.md" >}})
