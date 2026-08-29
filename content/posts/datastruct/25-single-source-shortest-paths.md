---
title: "第 25 讲：单源最短路径——Dijkstra 与 Bellman-Ford"
date: 2026-08-28
weight: 25
tags: ["数据结构与算法"]
draft: false
summary: "松弛操作与最优子结构、Dijkstra 的贪心正确性证明与「为什么怕负权」、Bellman-Ford 的动态规划视角与负环检测、DAG 上的线性最短路，以及 A* 如何用启发式把 Dijkstra 加速几个数量级。"
showToc: true
tocOpen: false
---

## 一、问题与基本工具

> **单源最短路径（SSSP）**：给定加权有向图 G 和源点 s，求 s 到每个顶点 v 的最短路径权值 δ(s,v)。

**两条基础性质**：

**① 最优子结构**：最短路径的任意子路径也是最短路径。

**证明**：若 `s → … → u → … → v` 是最短路，而其中 `u → … → v` 段不是 u 到 v 的最短路，就可以用更短的替换它，得到更短的 s→v 路径，矛盾。∎

⭐ **这条性质是所有最短路算法的基石**，也是动态规划适用性的标志（[第 31 讲]({{< ref "31-dynamic-programming-1.md" >}})）。

**② 三角不等式**：`δ(s,v) ≤ δ(s,u) + w(u,v)`。

### 松弛（Relaxation）

**所有最短路算法都由同一个原子操作构成**：

```go
func relax(u, v int, w int, dist []int, parent []int) bool {
    if dist[u] != math.MaxInt && dist[u]+w < dist[v] {
        dist[v] = dist[u] + w
        parent[v] = u
        return true
    }
    return false
}
```

**语义**："如果经过 u 到 v 更近，就更新"。`dist[v]` 始终是**当前已知的最短路上界**，随着算法进行单调下降，最终收敛到 δ(s,v)。

⭐ **各个最短路算法的差别，只在于「按什么顺序松弛哪些边」**：

| 算法 | 松弛顺序 |
|---|---|
| **Dijkstra** | 按 dist 从小到大处理顶点，每条边松弛一次 |
| **Bellman-Ford** | 所有边松弛 V−1 轮 |
| **DAG 最短路** | 按拓扑序松弛 |
| **BFS** | 按层松弛（边权都为 1 的特例） |

---

## 二、Dijkstra 算法

**前提：所有边权非负。**

**贪心策略**：维护已确定最短路的集合 S。每次从 V−S 中取 `dist` 最小的顶点 u，**宣告 `dist[u]` 已是最终答案**，然后松弛 u 的所有出边。

```go
type pqItem struct {
    node, dist int
}

func Dijkstra(g *WGraph, s int) ([]int, []int) {
    dist := make([]int, g.n)
    parent := make([]int, g.n)
    for i := range dist {
        dist[i], parent[i] = math.MaxInt, -1
    }
    dist[s] = 0

    pq := &itemHeap{{node: s, dist: 0}}
    heap.Init(pq)

    for pq.Len() > 0 {
        it := heap.Pop(pq).(pqItem)
        u := it.node
        if it.dist > dist[u] { // ⭐ 惰性删除：这是过期条目
            continue
        }
        for _, e := range g.adj[u] {
            if nd := dist[u] + e.Weight; nd < dist[e.To] {
                dist[e.To] = nd
                parent[e.To] = u
                heap.Push(pq, pqItem{node: e.To, dist: nd})
            }
        }
    }
    return dist, parent
}
```

### ⭐ 正确性证明

> **定理**：当 u 被从优先队列取出时，`dist[u] = δ(s,u)`。

**反证**：设 u 是**第一个**被取出时 `dist[u] > δ(s,u)` 的顶点。考虑 s 到 u 的一条真实最短路 P。设 P 上第一个不在 S 中的顶点是 y，其前驱是 x ∈ S。

```
 s ────────▶ x ──▶ y ─ ─ ─ ▶ u
 └── 都在 S 中 ──┘  └ 都不在 S ┘
```

- 由于 x ∈ S 且 u 是第一个出错的，`dist[x] = δ(s,x)`。
- x 被取出时松弛了边 (x,y)，故 `dist[y] = δ(s,x) + w(x,y) = δ(s,y)`。
- **由于所有边权非负**，`δ(s,y) ≤ δ(s,u)`。
- u 被优先取出说明 `dist[u] ≤ dist[y] = δ(s,y) ≤ δ(s,u)`。
- 结合假设 `dist[u] > δ(s,u)`，矛盾。∎

⭐ **证明中"由于所有边权非负"这一步是唯一用到该前提的地方，也正是 Dijkstra 不能处理负权的原因**：负边会让"后面的路径更短"，从而使"已取出的顶点已确定"这个贪心断言失效。

### ⚠️ 负权的具体反例

```
        A
     1 ╱ ╲ 4
      B   C
       ╲ ╱
       -5  （B → C 权 −5）

Dijkstra 从 A 出发：
  取出 A，松弛得 dist[B]=1, dist[C]=4
  取出 B（dist 更小），松弛 B→C 得 dist[C] = 1 + (−5) = −4
  但 C 若已被取出并"确定"为 4，就永远错了
```

⚠️ **"给所有边权加一个大常数变成非负"是错的**——这会偏向边数少的路径，改变最优解。

### 复杂度

| 优先队列 | 复杂度 |
|---|---|
| 数组（线性扫描） | O(V²) —— **稠密图更优** |
| **二叉堆** | **O((V+E) log V)** |
| Fibonacci 堆 | O(E + V log V) —— 理论最优，实践中常输给二叉堆（[第 10 讲]({{< ref "10-heaps-priority-queues.md" >}})） |

**惰性删除的代价**：堆中最多 O(E) 个条目，复杂度 O(E log E) = O(E log V)，与标准版同阶。

---

## 三、Bellman-Ford 算法

**可以处理负权边，还能检测负环。**

**思想**：对所有边松弛 V−1 轮。

```go
func BellmanFord(n int, edges []Edge, s int) ([]int, bool) {
    dist := make([]int, n)
    for i := range dist {
        dist[i] = math.MaxInt
    }
    dist[s] = 0

    for i := 0; i < n-1; i++ { // V−1 轮
        changed := false
        for _, e := range edges {
            if dist[e.U] != math.MaxInt && dist[e.U]+e.W < dist[e.V] {
                dist[e.V] = dist[e.U] + e.W
                changed = true
            }
        }
        if !changed { // ⭐ 提前终止优化
            break
        }
    }

    for _, e := range edges { // 第 V 轮还能松弛 ⟹ 存在负环
        if dist[e.U] != math.MaxInt && dist[e.U]+e.W < dist[e.V] {
            return nil, false
        }
    }
    return dist, true
}
```

### 为什么是 V−1 轮

**关键不变式**：**第 i 轮结束后，`dist[v]` 已经不大于"最多经过 i 条边"的最短路径长度。**

**证明（对 i 归纳）**：i = 0 时 `dist[s] = 0` ✓。设第 i−1 轮后成立，任取一条 s→v 的、边数 ≤ i 的最短路 `s → … → u → v`，其中 s→u 段边数 ≤ i−1，由归纳假设第 i−1 轮后 `dist[u]` 已正确。第 i 轮松弛 (u,v) 时得到正确的 `dist[v]`。∎

**无负环时，最短路至多有 V−1 条边**（否则含环，而非负环可以去掉使路径不变长）。所以 **V−1 轮足够**。

**负环检测**：第 V 轮还能松弛，说明存在一条边数 ≥ V 的"更短"路径 ⟹ 必含负环。

⭐ **要找出负环上的顶点**：从最后一轮被松弛的顶点开始沿 parent 回溯 V 次，必然落入环内。

### 复杂度与优化

**Θ(V·E)**。这比 Dijkstra 慢得多，但它的能力也更强。

**SPFA（队列优化）**：只把"dist 被更新过"的顶点入队重新松弛。

```go
func SPFA(g *WGraph, s int) ([]int, bool) {
    dist := make([]int, g.n)
    inQueue := make([]bool, g.n)
    cnt := make([]int, g.n) // 每个点的入队次数
    for i := range dist { dist[i] = math.MaxInt }
    dist[s] = 0
    queue := []int{s}
    inQueue[s] = true

    for len(queue) > 0 {
        u := queue[0]
        queue = queue[1:]
        inQueue[u] = false
        for _, e := range g.adj[u] {
            if nd := dist[u] + e.Weight; dist[u] != math.MaxInt && nd < dist[e.To] {
                dist[e.To] = nd
                if !inQueue[e.To] {
                    cnt[e.To]++
                    if cnt[e.To] >= g.n { // ⭐ 入队 V 次 ⟹ 负环
                        return nil, false
                    }
                    queue = append(queue, e.To)
                    inQueue[e.To] = true
                }
            }
        }
    }
    return dist, true
}
```

⚠️ **SPFA 的平均表现很好（常常接近 O(E)），但最坏情况仍是 O(V·E)，且存在专门构造的反例图使它退化。** 竞赛中曾流行"SPFA 已死"的说法就来源于此。**有负权时用它，没有负权时永远用 Dijkstra。**

---

## 四、DAG 上的最短路：Θ(V+E)

**如果图是 DAG，可以按拓扑序松弛，一遍搞定。**

```go
func DAGShortestPath(g *WGraph, s int) []int {
    order, _ := TopoSortDFS(g) // 第 22 讲
    dist := make([]int, g.n)
    for i := range dist { dist[i] = math.MaxInt }
    dist[s] = 0

    for _, u := range order {
        if dist[u] == math.MaxInt {
            continue
        }
        for _, e := range g.adj[u] {
            if nd := dist[u] + e.Weight; nd < dist[e.To] {
                dist[e.To] = nd
            }
        }
    }
    return dist
}
```

**为什么一遍就够？** 按拓扑序处理时，轮到 u 时**所有能到达 u 的顶点都已处理完**，所以 `dist[u]` 已经是最终值。

⭐ **DAG 最短路的两个重要性质**：

1. **允许负权**（因为无环，不可能有负环）
2. **把边权取负即可求最长路**——这是**关键路径（CPM）** 和**项目调度**的算法基础。⚠️ 一般图的最长路是 NP-难的（[第 34 讲]({{< ref "34-np-completeness.md" >}})），但 DAG 上是线性的。

---

## 五、A*：带启发式的 Dijkstra

**Dijkstra 向所有方向均匀扩展**，像水波纹一样。如果我们知道目标在哪个方向，可以优先往那边搜。

**A\* 把优先队列的 key 从 `g(v)` 改成 `f(v) = g(v) + h(v)`**：

```
g(v) = 从 s 到 v 的已知代价
h(v) = 从 v 到目标 t 的代价的启发式估计
```

```
Dijkstra 的搜索区域:        A* 的搜索区域:
      ╭─────────╮                    ╱▔▔╲
     ╱     s     ╲                  │ s  ╲___
    │      ●      │                 ╰──▶   ● t
     ╲     ●t    ╱                    朝目标定向扩展
      ╰─────────╯
```

**两个条件**：

| 条件 | 定义 | 保证 |
|---|---|---|
| **可采纳（admissible）** | `h(v) ≤ δ(v,t)`——**从不高估** | 找到的路径**一定最优** |
| **一致（consistent）** | `h(u) ≤ w(u,v) + h(v)` | 每个顶点只需处理一次（无需重开） |

**一致 ⟹ 可采纳**。一致性本质上是"h 满足三角不等式"。

**常用启发式**：

| 场景 | h(v) |
|---|---|
| 网格四方向移动 | 曼哈顿距离 |
| 网格八方向移动 | 对角距离（Chebyshev） |
| 地图导航 | 欧几里得直线距离 |
| **h ≡ 0** | **退化为 Dijkstra** |

⭐ **h ≡ 0 时 A\* 就是 Dijkstra**——这说明 Dijkstra 是 A\* 的特例。而 h 越接近真实距离，搜索的顶点越少；若 h 恰好等于真实距离，A\* 只走最优路径上的顶点。

**应用**：游戏寻路、地图导航、机器人路径规划、拼图求解。

⚠️ **实际的地图导航还用更强的技术**：Contraction Hierarchies（预处理出"捷径"边，查询快几个数量级）、ALT（用地标做启发式）。Google Maps 在大陆级路网上做到毫秒级响应，靠的是预处理而不是纯 A\*。

---

## 六、算法选择

| 情况 | 算法 | 复杂度 |
|---|---|---|
| **无权图** | **BFS**（[第 21 讲]({{< ref "21-graphs-bfs.md" >}})） | Θ(V+E) |
| 边权 ∈ {0,1} | **0-1 BFS**（双端队列） | Θ(V+E) |
| 边权 ∈ [0,C] 小整数 | Dial 算法（桶） | O(E + VC) |
| **DAG（可含负权）** | **拓扑序松弛** | **Θ(V+E)** |
| **非负权，稀疏图** | **Dijkstra + 二叉堆** | O(E log V) |
| 非负权，稠密图 | Dijkstra + 数组 | O(V²) |
| **含负权** | **Bellman-Ford / SPFA** | O(V·E) |
| 需检测负环 | Bellman-Ford | O(V·E) |
| 已知目标点 + 有好的启发式 | **A\*** | 实践中远快于 Dijkstra |
| 全源最短路 | 见[第 26 讲]({{< ref "26-all-pairs-shortest-paths.md" >}}) | — |

⭐ **看到"最短路"三个字，第一件事是问：有负权吗？是 DAG 吗？边权都相等吗？** 这三个问题决定了复杂度能从 O(V·E) 一路降到 Θ(V+E)。

---

## 随堂自测

1. 什么是最优子结构？给出最短路径满足它的证明。
2. 松弛操作的语义是什么？为什么说所有最短路算法只是"松弛顺序不同"？
3. 完整证明 Dijkstra 的正确性，指出"边权非负"用在哪一步。
4. 给出一个具体的带负权图，说明 Dijkstra 会给出错误答案。
5. 为什么"给所有边权加常数变成非负"是错的？举例说明。
6. 证明 Bellman-Ford 的循环不变式："第 i 轮后 dist[v] ≤ 最多经过 i 条边的最短路"。
7. 为什么 V−1 轮就够了？第 V 轮还能松弛意味着什么？
8. SPFA 的平均表现好但最坏仍是 O(VE)，什么时候该用它、什么时候不该？
9. DAG 上的最短路为什么只需一遍拓扑序松弛？为什么它还能求最长路，而一般图不行？
10. A\* 的 h 满足什么条件才保证最优？h ≡ 0 时 A\* 退化成什么？
11. 边权全是 1 时用 Dijkstra 会有什么浪费？该用什么？

---

> **上一讲**：[第 24 讲：最小生成树]({{< ref "24-minimum-spanning-trees.md" >}})　**下一讲**：[第 26 讲：全源最短路径]({{< ref "26-all-pairs-shortest-paths.md" >}})
