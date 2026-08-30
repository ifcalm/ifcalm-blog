---
title: "第 21 讲：图的表示与广度优先搜索"
date: 2026-08-28
weight: 21
tags: ["数据结构与算法"]
draft: false
summary: "图的术语与两种表示的完整取舍（邻接表 vs 邻接矩阵）、稀疏与稠密的分界、BFS 的三色不变式与正确性证明、最短路径树、二分图判定，以及双向 BFS 与 0-1 BFS 这两个实用变体。"
showToc: true
tocOpen: false
---

## 一、为什么图是最通用的模型

数组是线性的，树是层次的，**图是任意的**——因此几乎所有关系型问题都能建模成图：

| 问题 | 顶点 | 边 |
|---|---|---|
| 社交网络 | 用户 | 好友关系 |
| 网页排名 | 网页 | 超链接 |
| 编译依赖 | 源文件 | include / import |
| 路由 | 路由器 | 链路（权重 = 时延） |
| 任务调度 | 任务 | 先后约束 |
| 状态搜索（八数码、迷宫） | 状态 | 一步操作 |
| 类型推导 | 类型变量 | 约束 |

⭐ **算法竞赛与工程中最有价值的能力，往往不是"会写 Dijkstra"，而是"看出这个问题是图问题"。** 最后两行尤其值得注意：**很多看起来不像图的搜索问题，本质是隐式图上的 BFS**——顶点是状态，边是转移，图从不显式建出来。

### 术语速查

| 术语 | 含义 |
|---|---|
| 有向 / 无向 | 边是否有方向 |
| 加权 / 无权 | 边是否带数值 |
| **度（degree）** | 无向图中顶点关联的边数；有向图分**入度**、**出度** |
| 路径 / 简单路径 | 顶点序列 / 不重复顶点的路径 |
| 环（cycle） | 起点终点相同的路径；**DAG** = 有向无环图 |
| 连通 / 强连通 | 无向图任意两点可达 / 有向图任意两点互相可达 |
| **稀疏 / 稠密** | E = O(V) / E = Θ(V²) |

**握手引理**：无向图中 `Σ deg(v) = 2E`。这条简单的等式是很多复杂度分析的基础——它保证了"遍历所有顶点的所有邻居"总代价是 Θ(V + E) 而不是 Θ(V·E)。

---

## 二、两种表示

### 邻接表

```go
type Graph struct {
    n   int
    adj [][]int // adj[u] 是 u 的所有邻居
}

func NewGraph(n int) *Graph { return &Graph{n: n, adj: make([][]int, n)} }

func (g *Graph) AddEdge(u, v int) {
    g.adj[u] = append(g.adj[u], v)
    g.adj[v] = append(g.adj[v], u) // 无向图，有向图去掉这行
}
```

加权图：

```go
type Edge struct {
    To     int
    Weight int
}

type WGraph struct {
    n   int
    adj [][]Edge
}
```

### 邻接矩阵

```go
type MatrixGraph struct {
    n   int
    mat [][]bool // mat[u][v] = 是否有边
}
```

### ⭐ 取舍

| | 邻接表 | 邻接矩阵 |
|---|---|---|
| **空间** | **Θ(V + E)** | Θ(V²) |
| 判断 (u,v) 是否有边 | O(deg(u)) | **Θ(1)** |
| 遍历 u 的所有邻居 | **Θ(deg(u))** | Θ(V) |
| 遍历所有边 | **Θ(V + E)** | Θ(V²) |
| 加边 | **Θ(1)** | Θ(1) |
| 删边 | O(deg(u)) | **Θ(1)** |
| 适合 | **稀疏图（绝大多数）** | 稠密图、需频繁查边 |

**分界点在哪？** E ≈ V²/64 左右（因为矩阵可以用位压缩到 1 bit/边）。

⚠️ **真实世界的图几乎全是稀疏的**：
- Facebook：30 亿用户，平均好友 200 ⟹ E ≈ 300V，而 V² = 9×10¹⁸
- 万维网：平均出链约 10 条
- 道路网：每个路口平均 3–4 条路

**所以默认用邻接表**。用矩阵的场景很少：Floyd-Warshall（[第 26 讲]({{< ref "26-all-pairs-shortest-paths.md" >}}))、图的邻接矩阵幂运算、V < 1000 的稠密图。

⚠️ **复杂度必须写成 O(V + E)**，不能省略任一项（[第 2 讲]({{< ref "02-asymptotic-analysis.md" >}})）：稀疏图中 E = Θ(V)，稠密图中 E = Θ(V²)，两者天差地别。

---

## 三、广度优先搜索

**BFS 逐层扩展**：先访问所有距离为 1 的顶点，再访问距离为 2 的……

```
    起点 s
      │
   ┌──┴──┐        距离 1
   a     b
  ╱ ╲   ╱ ╲
 c   d e   f      距离 2
     │
     g            距离 3
```

```go
// 返回 s 到各点的最短距离（-1 表示不可达）和最短路径树的父指针
func BFS(g *Graph, s int) (dist []int, parent []int) {
    dist = make([]int, g.n)
    parent = make([]int, g.n)
    for i := range dist {
        dist[i], parent[i] = -1, -1
    }

    dist[s] = 0
    queue := []int{s}
    for len(queue) > 0 {
        u := queue[0]
        queue = queue[1:] // 实际代码请用环形缓冲，见第 6 讲
        for _, v := range g.adj[u] {
            if dist[v] == -1 { // 未访问
                dist[v] = dist[u] + 1
                parent[v] = u
                queue = append(queue, v)
            }
        }
    }
    return dist, parent
}
```

⚠️ **必须在入队时标记，而不是出队时。** 否则同一个顶点可能被多次入队，队列规模爆炸到 O(E)，复杂度退化。

### 复杂度

```
每个顶点入队、出队各一次：           Θ(V)
每条边被检查一次（无向图两次）：       Θ(E)
                                 ───────────
                            总计   Θ(V + E)
```

⭐ 这是**摊还思想**（[第 4 讲]({{< ref "04-amortized-analysis.md" >}})）：单个顶点的邻居可能很多，但所有顶点的邻居总数由握手引理约束为 2E。

### 正确性：三色不变式

把顶点分成三色：

```
⚪ 白：未发现        🔘 灰：已发现，在队列中（边界）      ⚫ 黑：已处理完
```

**不变式**：队列中的顶点距离值只有两种，且非递减：

```
队列 = [d, d, d, …, d, d+1, d+1, …, d+1]
```

**定理**：BFS 计算出的 `dist[v]` 等于 s 到 v 的最短路径长度 δ(s,v)。

**证明梗概**（对 δ 归纳）：
- **上界** `dist[v] ≥ δ(s,v)`：dist 是沿某条实际路径累加的，不可能小于最短路。
- **下界** `dist[v] ≤ δ(s,v)`：设 δ(s,v) = k，取一条最短路 `s → … → u → v`，则 δ(s,u) = k−1。由归纳假设 `dist[u] = k−1`，u 出队时会检查 v。此时若 v 已被发现，则 `dist[v] ≤ k`（由队列的单调性）；否则 v 被赋值 `dist[u]+1 = k`。∎

⭐ **BFS 求最短路的前提是「所有边权相等」。** 一旦边权不同，逐层扩展就不再对应距离递增——这时需要 Dijkstra（[第 25 讲]({{< ref "25-single-source-shortest-paths.md" >}})）。**Dijkstra 本质就是"把 BFS 的队列换成优先队列"。**

### 最短路径树

`parent` 数组构成一棵以 s 为根的树，其中 s 到任意 v 的树上路径就是一条最短路：

```go
func Path(parent []int, s, t int) []int {
    if parent[t] == -1 && t != s {
        return nil // 不可达
    }
    var path []int
    for v := t; v != -1; v = parent[v] {
        path = append(path, v)
    }
    slices.Reverse(path)
    return path
}
```

---

## 四、BFS 的应用

### 应用 1：连通分量

```go
func ConnectedComponents(g *Graph) []int {
    comp := make([]int, g.n)
    for i := range comp { comp[i] = -1 }
    c := 0
    for s := 0; s < g.n; s++ {
        if comp[s] != -1 { continue }
        queue := []int{s}
        comp[s] = c
        for len(queue) > 0 {
            u := queue[0]
            queue = queue[1:]
            for _, v := range g.adj[u] {
                if comp[v] == -1 {
                    comp[v] = c
                    queue = append(queue, v)
                }
            }
        }
        c++
    }
    return comp
}
```

**总代价仍是 Θ(V + E)**——所有 BFS 加起来每个顶点每条边各处理一次。

### 应用 2：二分图判定

**二分图**：顶点能分成两组，使每条边的两个端点在不同组。**等价于：不含奇数长度的环。**

```go
func IsBipartite(g *Graph) ([]int, bool) {
    color := make([]int, g.n)
    for i := range color { color[i] = -1 }
    for s := 0; s < g.n; s++ {
        if color[s] != -1 { continue }
        color[s] = 0
        queue := []int{s}
        for len(queue) > 0 {
            u := queue[0]
            queue = queue[1:]
            for _, v := range g.adj[u] {
                if color[v] == -1 {
                    color[v] = 1 - color[u] // 染成相反的颜色
                    queue = append(queue, v)
                } else if color[v] == color[u] {
                    return nil, false // ⭐ 同色相邻 ⟹ 存在奇环
                }
            }
        }
    }
    return color, true
}
```

**为什么"同色相邻"就说明有奇环？** 若 u 与 v 同色，说明 `dist[u]` 与 `dist[v]` 同奇偶。加上边 (u,v)，从它们的最近公共祖先绕一圈的环长为 `dist[u] + dist[v] − 2·dist[lca] + 1`，是奇数。∎

**应用**：任务分配（二分匹配，[第 27 讲]({{< ref "27-network-flow.md" >}})）、冲突检测、2-染色问题。

### 应用 3：隐式图上的 BFS

**很多搜索问题不需要建图**。以"最少几步把 x 变成 y"这类问题为例：

```go
// 每步可以 +1、-1 或 ×2，求 s 到 t 的最少步数
func MinSteps(s, t, limit int) int {
    dist := map[int]int{s: 0}
    queue := []int{s}
    for len(queue) > 0 {
        u := queue[0]
        queue = queue[1:]
        if u == t {
            return dist[u]
        }
        for _, v := range []int{u + 1, u - 1, u * 2} { // 邻居按需生成
            if v < 0 || v > limit {
                continue
            }
            if _, seen := dist[v]; !seen {
                dist[v] = dist[u] + 1
                queue = append(queue, v)
            }
        }
    }
    return -1
}
```

⭐ **顶点是状态，边是操作，图从不显式存在。** 华容道、八数码、魔方、单词接龙、迷宫、编辑距离的最少操作数——全都是这个模式。

---

## 五、两个实用变体

### 双向 BFS

从起点和终点**同时**做 BFS，在中间相遇时停止。

```
单向 BFS 搜索的顶点数：  b^d          （b 是分支因子，d 是距离）
双向 BFS：              2 · b^(d/2)
```

**d = 10、b = 10 时：10¹⁰ vs 2×10⁵——快 5 万倍。**

⚠️ 前提：必须能从终点反向扩展（反图可得），且知道终点。

### 0-1 BFS

**当边权只有 0 和 1 时**，可以用**双端队列**代替优先队列，在 Θ(V+E) 内求最短路（而不是 Dijkstra 的 O(E log V)）：

```go
func ZeroOneBFS(g *WGraph, s int) []int {
    dist := make([]int, g.n)
    for i := range dist { dist[i] = math.MaxInt }
    dist[s] = 0
    dq := []int{s}
    for len(dq) > 0 {
        u := dq[0]
        dq = dq[1:]
        for _, e := range g.adj[u] {
            if nd := dist[u] + e.Weight; nd < dist[e.To] {
                dist[e.To] = nd
                if e.Weight == 0 {
                    dq = append([]int{e.To}, dq...) // 权 0 → push 到队首
                } else {
                    dq = append(dq, e.To) // 权 1 → push 到队尾
                }
            }
        }
    }
    return dist
}
```

⭐ **双端队列在这里扮演了"只有两档优先级的优先队列"**。这个技巧的推广是 **Dial 算法**：边权都在 [0, C] 内时，用 C+1 个桶代替堆，得到 O(E + VC)。

**典型应用**：网格中"走直线免费、转弯花费 1"、"打通墙壁花费 1"这类问题。

---

## 六、复杂度汇总

| 操作 | 邻接表 | 邻接矩阵 |
|---|---|---|
| BFS / DFS | **Θ(V + E)** | Θ(V²) |
| 连通分量 | **Θ(V + E)** | Θ(V²) |
| 二分图判定 | **Θ(V + E)** | Θ(V²) |
| 空间 | Θ(V + E) | Θ(V²) |

---

## 随堂自测

1. 握手引理是什么？它为什么保证"遍历所有顶点的所有邻居"是 Θ(V+E) 而非 Θ(V·E)？
2. 邻接表和邻接矩阵在哪五个操作上有差别？稀疏图为什么必须用邻接表？
3. 为什么图算法的复杂度必须写 O(V+E) 而不能只写 O(E)？
4. BFS 为什么必须在**入队**时标记已访问？出队时标记会怎样？
5. 陈述并证明 BFS 求出的 dist 就是最短距离（分上界和下界两部分）。
6. BFS 求最短路的前提是什么？边权不同时该用什么算法？两者的关系是什么？
7. 二分图判定中，"发现同色相邻"为什么等价于"存在奇环"？
8. 举一个"隐式图 BFS"的例子，说明顶点和边分别是什么。
9. 双向 BFS 为什么能把 b^d 降到 2b^(d/2)？它需要什么前提？
10. 0-1 BFS 为什么用双端队列就够了，不需要堆？如果边权是 {0,1,2} 呢？

