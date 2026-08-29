---
title: "第 22 讲：深度优先搜索、拓扑排序与强连通分量"
date: 2026-08-28
weight: 22
tags: ["数据结构与算法"]
draft: false
summary: "DFS 的时间戳与括号定理、四类边与环检测、拓扑排序的两种实现及其正确性、Kosaraju 与 Tarjan 求强连通分量的完整推导，以及缩点后的凝聚图为什么一定是 DAG。"
showToc: true
tocOpen: false
---

## 一、DFS 与时间戳

BFS 用队列逐层扩展，**DFS 用栈（或递归）一路走到底再回溯**。

```go
type DFS struct {
    g              *Graph
    color          []int // 0=白 1=灰 2=黑
    disc, fin      []int // 发现时间、完成时间
    parent         []int
    time           int
}

func (d *DFS) Run() {
    for u := 0; u < d.g.n; u++ {
        if d.color[u] == 0 {
            d.visit(u)
        }
    }
}

func (d *DFS) visit(u int) {
    d.color[u] = 1 // 灰：正在处理
    d.time++
    d.disc[u] = d.time

    for _, v := range d.g.adj[u] {
        if d.color[v] == 0 {
            d.parent[v] = u
            d.visit(v)
        }
    }

    d.color[u] = 2 // 黑：处理完毕
    d.time++
    d.fin[u] = d.time
}
```

**复杂度 Θ(V + E)**，与 BFS 相同。

### ⭐ 括号定理

> 对任意两个顶点 u、v，区间 `[disc[u], fin[u]]` 与 `[disc[v], fin[v]]` 要么**完全不相交**，要么**一个完全包含另一个**。绝不会部分重叠。

```
时间轴：
u:  (─────────────)                 不相交
v:                    (──────)

u:  (──────────────────────)        v 是 u 的后代
v:      (─────────)
```

**推论**：`v 是 u 在 DFS 森林中的后代  ⟺  disc[u] < disc[v] < fin[v] < fin[u]`。

⭐ **这两个时间戳几乎是 DFS 全部威力的来源**。下面的每一个应用都建立在它们之上。

### 四类边

对有向图，DFS 把每条边 (u,v) 分成四类：

| 类型 | 判据（发现 (u,v) 时 v 的颜色） | 含义 |
|---|---|---|
| **树边（tree）** | 白 | v 是被 u 首次发现的 |
| **后向边（back）** | **灰** | v 是 u 的祖先 ⟹ ⭐ **存在环** |
| 前向边（forward） | 黑，且 `disc[u] < disc[v]` | v 是 u 的后代但非直接子 |
| 横叉边（cross） | 黑，且 `disc[u] > disc[v]` | 跨子树 |

**无向图只有树边和后向边**（前向边和横叉边在无向图中会被看成后向边）。

### 环检测

> **定理**：有向图有环 ⟺ DFS 中存在后向边。

```go
func HasCycle(g *Graph) bool {
    color := make([]int, g.n)
    var visit func(int) bool
    visit = func(u int) bool {
        color[u] = 1
        for _, v := range g.adj[u] {
            if color[v] == 1 { // ⭐ 遇到灰色 = 后向边 = 有环
                return true
            }
            if color[v] == 0 && visit(v) {
                return true
            }
        }
        color[u] = 2
        return false
    }
    for u := 0; u < g.n; u++ {
        if color[u] == 0 && visit(u) {
            return true
        }
    }
    return false
}
```

⚠️ **必须用三色，不能用二色（访问过/未访问）**。二色会把"已完成的顶点被再次指向"（前向边、横叉边）误判为环。**灰色的含义是"在当前递归栈上"**——只有指向递归栈上的顶点才是环。

⚠️ **无向图的环检测要排除父边**：`if v != parent[u] && visited[v]`。

---

## 二、拓扑排序

> **拓扑序**：DAG 顶点的一个线性排列，使得对每条边 (u,v)，u 排在 v 之前。

**存在性定理**：有向图存在拓扑序 ⟺ 它是 DAG。

**用途**：编译依赖、任务调度、课程先修、Makefile、Excel 公式求值顺序、包管理器解析依赖、Go 的 `init()` 执行顺序。

### 方法一：DFS 按完成时间逆序

```go
func TopoSortDFS(g *Graph) ([]int, bool) {
    color := make([]int, g.n)
    order := make([]int, 0, g.n)

    var visit func(int) bool
    visit = func(u int) bool {
        color[u] = 1
        for _, v := range g.adj[u] {
            if color[v] == 1 {
                return false // 有环，无拓扑序
            }
            if color[v] == 0 && !visit(v) {
                return false
            }
        }
        color[u] = 2
        order = append(order, u) // ⭐ 完成时压入
        return true
    }
    for u := 0; u < g.n; u++ {
        if color[u] == 0 && !visit(u) {
            return nil, false
        }
    }
    slices.Reverse(order) // 完成时间的逆序就是拓扑序
    return order, true
}
```

**正确性证明**：设 (u,v) 是一条边。DFS 访问 u 时：
- v 是白色 ⟹ v 成为 u 的后代 ⟹ `fin[v] < fin[u]` ✓
- v 是黑色 ⟹ v 已完成 ⟹ `fin[v] < fin[u]` ✓
- v 是灰色 ⟹ 后向边 ⟹ 有环，与 DAG 矛盾

**三种情形都有 `fin[v] < fin[u]`，所以按 fin 降序排列即为拓扑序。** ∎

### 方法二：Kahn 算法（BFS 风格）

```go
func TopoSortKahn(g *Graph) ([]int, bool) {
    indeg := make([]int, g.n)
    for u := 0; u < g.n; u++ {
        for _, v := range g.adj[u] {
            indeg[v]++
        }
    }

    queue := make([]int, 0, g.n)
    for u := 0; u < g.n; u++ {
        if indeg[u] == 0 {
            queue = append(queue, u)
        }
    }

    order := make([]int, 0, g.n)
    for len(queue) > 0 {
        u := queue[0]
        queue = queue[1:]
        order = append(order, u)
        for _, v := range g.adj[u] {
            indeg[v]--
            if indeg[v] == 0 { // 所有前驱都排好了
                queue = append(queue, v)
            }
        }
    }
    if len(order) < g.n {
        return nil, false // ⭐ 有顶点入度永不为 0 ⟹ 存在环
    }
    return order, true
}
```

| | DFS 版 | Kahn 版 |
|---|---|---|
| 环检测 | 灰色顶点 | 输出顶点数 < V |
| 可求字典序最小拓扑序 | ✗ | **✓**（把队列换成最小堆） |
| 可求关键路径/最长路 | ✓ | **✓**（更自然） |
| 递归深度 | O(V)，深图可能爆栈 | 无递归 |
| 天然支持增量 | ✗ | **✓**（适合动态任务调度器） |

⭐ **Kahn 算法的另一个价值**：它就是**并行任务调度器**的核心——入度为 0 的顶点集合就是"当前可以并行执行的任务集合"。

---

## 三、强连通分量

> **强连通分量（SCC）**：有向图顶点的极大子集，其中任意两点互相可达。

```
    ┌───────────┐        ┌──────┐
    │  a ──▶ b  │  ───▶  │  d   │
    │  ▲     │  │        │  ▲│  │
    │  └─ c ◀┘  │        │  │▼  │
    └───────────┘        │  e   │
      SCC 1 {a,b,c}      └──────┘
                          SCC 2 {d,e}
```

**关键性质**：把每个 SCC 缩成一个点，得到的**凝聚图（condensation graph）一定是 DAG**。

**证明**：若凝聚图有环，环上所有 SCC 中的顶点就互相可达，它们应该属于同一个 SCC，与"极大"矛盾。∎

⭐ **这个性质极其有用**：它把任意有向图的分析化归为"SCC 内部" + "DAG 上的处理"两部分。2-SAT、依赖循环检测、编译器的循环优化都靠它。

### Kosaraju 算法：两遍 DFS

```
① 在原图 G 上做 DFS，记录完成时间，得到顶点的逆序 order
② 构造反图 Gᵀ（所有边反向）
③ 按 order 的顺序在 Gᵀ 上做 DFS，每棵 DFS 树就是一个 SCC
```

```go
func Kosaraju(g *Graph) [][]int {
    // ① 第一遍 DFS，按完成时间入栈
    visited := make([]bool, g.n)
    order := make([]int, 0, g.n)
    var dfs1 func(int)
    dfs1 = func(u int) {
        visited[u] = true
        for _, v := range g.adj[u] {
            if !visited[v] { dfs1(v) }
        }
        order = append(order, u)
    }
    for u := 0; u < g.n; u++ {
        if !visited[u] { dfs1(u) }
    }

    // ② 构造反图
    rev := NewGraph(g.n)
    for u := 0; u < g.n; u++ {
        for _, v := range g.adj[u] {
            rev.adj[v] = append(rev.adj[v], u)
        }
    }

    // ③ 按完成时间逆序在反图上 DFS
    for i := range visited { visited[i] = false }
    var sccs [][]int
    var dfs2 func(int, *[]int)
    dfs2 = func(u int, comp *[]int) {
        visited[u] = true
        *comp = append(*comp, u)
        for _, v := range rev.adj[u] {
            if !visited[v] { dfs2(v, comp) }
        }
    }
    for i := len(order) - 1; i >= 0; i-- {
        if u := order[i]; !visited[u] {
            comp := []int{}
            dfs2(u, &comp)
            sccs = append(sccs, comp)
        }
    }
    return sccs
}
```

**为什么正确？** 核心引理：

> 设 C 和 C′ 是两个不同的 SCC，且原图中存在从 C 到 C′ 的边，则 `max fin(C) > max fin(C′)`。

即：**按完成时间降序处理，第一个被处理的 SCC 一定是凝聚 DAG 的"源"**。在反图上从它出发，只能到达它自己内部的顶点（因为反图中它的出边全部指向"已处理完的 SCC"）。∎

⭐ **直觉**：第一遍 DFS 求出的完成时间逆序，正是凝聚 DAG 的拓扑序；反图让"源"变成"汇"，从而每次 DFS 都被困在一个 SCC 内。

**复杂度 Θ(V + E)**（两遍 DFS + 建反图）。

### Tarjan 算法：一遍 DFS

Tarjan 用 **low-link 值** 在一次 DFS 中完成，不需要建反图：

```go
func Tarjan(g *Graph) [][]int {
    const unvisited = -1
    disc := make([]int, g.n)
    low := make([]int, g.n)
    onStack := make([]bool, g.n)
    for i := range disc { disc[i] = unvisited }
    var stack []int
    timer := 0
    var sccs [][]int

    var dfs func(int)
    dfs = func(u int) {
        disc[u], low[u] = timer, timer
        timer++
        stack = append(stack, u)
        onStack[u] = true

        for _, v := range g.adj[u] {
            switch {
            case disc[v] == unvisited:
                dfs(v)
                low[u] = min(low[u], low[v]) // 树边：继承孩子的 low
            case onStack[v]:
                low[u] = min(low[u], disc[v]) // ⚠️ 后向边：用 disc 而非 low
            }
            // v 已访问且不在栈上：跨到别的已完成 SCC，忽略
        }

        if low[u] == disc[u] { // ⭐ u 是 SCC 的根
            comp := []int{}
            for {
                v := stack[len(stack)-1]
                stack = stack[:len(stack)-1]
                onStack[v] = false
                comp = append(comp, v)
                if v == u { break }
            }
            sccs = append(sccs, comp)
        }
    }

    for u := 0; u < g.n; u++ {
        if disc[u] == unvisited { dfs(u) }
    }
    return sccs
}
```

**low[u] 的含义**：从 u 的子树出发，通过至多一条后向边能到达的**最小 disc 值**。

**`low[u] == disc[u]` 意味着**：u 的子树无法"逃出"到更早的顶点 ⟹ u 是这个 SCC 在 DFS 树中的根 ⟹ 栈中 u 之上的所有顶点构成一个 SCC。

⚠️ **`case onStack[v]` 里必须用 `disc[v]` 而不是 `low[v]`**。这是 Tarjan 最经典的实现错误：用 low 会把不同 SCC 错误地合并。（用 `low[v]` 在求**割点/桥**的变体中才是对的，两个算法的形似导致这个错误极常见。）

| | Kosaraju | Tarjan |
|---|---|---|
| DFS 遍数 | 2 | **1** |
| 需要反图 | **是**（额外 Θ(V+E) 空间） | 否 |
| 常数 | 较大 | **较小** |
| 易理解 | **✓** | 较难 |
| 输出顺序 | 凝聚 DAG 的拓扑序 | 拓扑**逆**序 |

⭐ **实践中用 Tarjan**（一遍、省空间）；**教学和推理时想 Kosaraju**（更容易说清为什么对）。

---

## 四、DFS 的其他应用

| 应用 | 关键量 |
|---|---|
| 拓扑排序 | 完成时间逆序 |
| 环检测 | 后向边 / 灰色顶点 |
| SCC | low-link / 反图 |
| **割点（articulation point）** | `low[child] >= disc[u]` |
| **桥（bridge）** | `low[child] > disc[u]` |
| **双连通分量** | 边栈 + low |
| 欧拉回路（Hierholzer） | 每条边用一次 |
| 迷宫生成、回溯搜索 | 递归 + 撤销 |

⚠️ **递归深度问题**：链状图上 DFS 深度是 Θ(V)。Go 的 goroutine 栈可增长（最大默认 1 GB），比 C 安全得多，但 V = 10⁷ 的深图仍会造成大量栈拷贝开销。**关键路径上建议改写成显式栈**（[第 6 讲]({{< ref "06-stacks-queues.md" >}})）。

---

## 五、BFS vs DFS

| | BFS | DFS |
|---|---|---|
| 数据结构 | 队列 | 栈 / 递归 |
| 复杂度 | Θ(V+E) | Θ(V+E) |
| 空间（最坏） | O(V)（一层的宽度） | O(V)（最长路径深度） |
| 求无权最短路 | **✓** | ✗ |
| 拓扑排序 | ✓（Kahn） | **✓**（更自然） |
| 环检测 | ✓ | **✓**（更自然） |
| SCC | ✗ | **✓** |
| 连通分量 | ✓ | ✓ |
| 适合的图形状 | 浅而宽 | 深而窄 |

⭐ **一句话**：**要"距离"用 BFS，要"结构"（环、次序、连通性）用 DFS。** 因为距离是逐层的概念，而结构信息藏在 DFS 的时间戳里。

---

## 随堂自测

1. 陈述括号定理，并用它给出"v 是 u 的后代"的时间戳判据。
2. 有向图 DFS 的四类边分别如何判定？哪一类的存在等价于有环？
3. 为什么环检测必须用三色而不能用二色？给出一个二色会误判的例子。
4. 无向图环检测为什么要排除父边？
5. 证明"按完成时间降序排列即为拓扑序"，分三种颜色情形讨论。
6. Kahn 算法如何检测环？如何修改它以得到字典序最小的拓扑序？
7. 证明凝聚图一定是 DAG。这个性质有什么用？
8. Kosaraju 为什么第二遍要在反图上做？用"凝聚 DAG 的源"来解释。
9. Tarjan 中 `low[u] = min(low[u], disc[v])` 为什么不能写成 `low[v]`？
10. `low[u] == disc[u]` 的含义是什么？为什么它标志着 SCC 的根？

---

> **上一讲**：[第 21 讲：图的表示与广度优先搜索]({{< ref "21-graphs-bfs.md" >}})　**下一讲**：[第 23 讲：并查集与不相交集合]({{< ref "23-disjoint-sets.md" >}})
