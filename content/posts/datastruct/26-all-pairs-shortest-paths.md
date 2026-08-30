---
title: "第 26 讲：全源最短路径——Floyd-Warshall 与 Johnson"
date: 2026-08-28
weight: 26
tags: ["数据结构与算法"]
draft: false
summary: "Floyd-Warshall 的动态规划推导与「为什么 k 必须是最外层循环」、路径重构、传递闭包与 Warshall 算法、Johnson 用重赋权把负权图转成非负权图的完整技巧，以及三种全源方案的选型。"
showToc: true
tocOpen: false
---

## 一、问题

> **全源最短路径（APSP）**：求图中**每一对**顶点 (u,v) 之间的最短路径。

**朴素做法**：对每个顶点跑一次单源最短路。

| 做法 | 复杂度 | 限制 |
|---|---|---|
| V 次 Dijkstra（二叉堆） | O(V·E log V) | 边权非负 |
| V 次 Bellman-Ford | O(V²·E) | 可含负权 |
| **Floyd-Warshall** | **Θ(V³)** | 可含负权 |
| **Johnson** | **O(V·E log V)** | 可含负权 |

⭐ 稠密图 E = Θ(V²) 时：V 次 Dijkstra 是 O(V³ log V)，**Floyd-Warshall 的 Θ(V³) 反而更快**，而且代码只有五行。

---

## 二、Floyd-Warshall

### 动态规划的推导

**定义子问题**：

```
d[k][i][j] = 从 i 到 j 的最短路径长度，
             且路径的中间顶点只允许来自 {1, 2, …, k}
```

⭐ **"中间顶点"这个刻画是全部的关键**：起点 i 和终点 j 不受限制，只限制路径经过哪些中间点。

**递推关系**：考虑顶点 k 用不用：

```
d[k][i][j] = min( d[k−1][i][j],              不经过 k
                  d[k−1][i][k] + d[k−1][k][j] )  经过 k
```

```
             ┌──── 不经过 k ────┐
        i ───┴──────────────────┴──▶ j
         ╲                        ╱
          ╲──▶ k ────────────────╱
           经过 k：拆成 i→k 和 k→j 两段
           而这两段都不经过 k（简单路径不重复顶点）
```

**基础情形**：`d[0][i][j] = w(i,j)`（无边则为 ∞，`d[0][i][i] = 0`）。

**答案**：`d[V][i][j]`（允许所有顶点作为中间点）。

### 空间优化：去掉一维

第 k 层只依赖第 k−1 层，且**可以证明就地更新是安全的**（因为 `d[k][i][k] = d[k−1][i][k]`——从 i 到 k 的最短路不会把 k 用作中间点）。

```go
func FloydWarshall(n int, w [][]int) ([][]int, [][]int) {
    const inf = math.MaxInt / 4 // 留余量避免相加溢出
    dist := make([][]int, n)
    next := make([][]int, n) // 路径重构
    for i := range dist {
        dist[i] = slices.Clone(w[i])
        next[i] = make([]int, n)
        for j := range next[i] {
            if w[i][j] < inf && i != j {
                next[i][j] = j
            } else {
                next[i][j] = -1
            }
        }
        dist[i][i] = 0
    }

    for k := 0; k < n; k++ { // ⭐ k 必须是最外层
        for i := 0; i < n; i++ {
            for j := 0; j < n; j++ {
                if dist[i][k]+dist[k][j] < dist[i][j] {
                    dist[i][j] = dist[i][k] + dist[k][j]
                    next[i][j] = next[i][k]
                }
            }
        }
    }
    return dist, next
}

func Path(next [][]int, u, v int) []int {
    if next[u][v] == -1 {
        return nil
    }
    path := []int{u}
    for u != v {
        u = next[u][v]
        path = append(path, u)
    }
    return path
}
```

### ⚠️ 为什么 k 必须是最外层循环

**这是 Floyd-Warshall 最经典的错误。** 如果写成 `for i { for j { for k {…} } }`，语义就完全变了。

**正确的语义**：外层的每一轮 k，完成的是"允许把 k 加入中间点集合"这一次**全局**的更新。所有 (i,j) 对必须在同一个 k 的允许集合下同步演进。

**如果 k 在内层**：`d[i][j]` 会在 `d[i][k]` 和 `d[k][j]` 还没算好的时候就被使用，结果是错的（且错得很隐蔽——很多情况下仍然给出正确答案，只在某些图上出错）。

⭐ **记忆方法**：**k 代表"DP 的阶段"，i、j 代表"状态"。DP 必须按阶段推进。**

### 负环检测

```go
for i := 0; i < n; i++ {
    if dist[i][i] < 0 { // 自己到自己的距离为负 ⟹ 存在负环
        return nil, false
    }
}
```

⚠️ 有负环时，`dist` 的其余值无意义（可以无限小）。

---

## 三、传递闭包

**问题**：只关心"i 能否到达 j"，不关心距离。

把 Floyd-Warshall 的 `min/+` 换成 `or/and`：

```go
func TransitiveClosure(n int, adj [][]bool) [][]bool {
    reach := make([][]bool, n)
    for i := range reach {
        reach[i] = slices.Clone(adj[i])
        reach[i][i] = true
    }
    for k := 0; k < n; k++ {
        for i := 0; i < n; i++ {
            if !reach[i][k] { // 小优化：i 到不了 k 就跳过整行
                continue
            }
            for j := 0; j < n; j++ {
                reach[i][j] = reach[i][j] || reach[k][j]
            }
        }
    }
    return reach
}
```

这叫 **Warshall 算法**，Θ(V³)。

⭐ **用位集（bitset）优化**：把 `reach[i]` 存成 `[]uint64`，内层循环变成整字的按位或：

```go
for w := range reach[i] {
    reach[i][w] |= reach[k][w]
}
```

**复杂度降到 Θ(V³/64)**——常数改善 64 倍。这是[第 2 讲]({{< ref "02-asymptotic-analysis.md" >}})"常数因子有时很重要"的典型例子：V = 5000 时，1.25×10¹¹ 次操作降到 2×10⁹ 次，从几分钟变成几秒。

**应用**：类型系统的子类型关系、数据库依赖分析、程序切片、可达性查询。

---

## 四、Johnson 算法

**动机**：稀疏图上，V 次 Dijkstra（O(V·E log V)）远优于 Floyd-Warshall（Θ(V³)）。**但 Dijkstra 不能处理负权。**

**Johnson 的想法**：**给边权做一次变换，把负权变成非负权，同时保持最短路径不变。**

### 重赋权（reweighting）

给每个顶点 v 一个"势能" h(v)，定义新边权：

```
ŵ(u,v) = w(u,v) + h(u) − h(v)
```

**关键性质：路径的新权值只与端点有关（望远镜求和）**：

```
ŵ(路径 v₀→v₁→…→vₖ) = Σ [w(vᵢ,vᵢ₊₁) + h(vᵢ) − h(vᵢ₊₁)]
                     = w(路径) + h(v₀) − h(vₖ)
```

⭐ **中间的所有 h 全部消掉了。** 因此**同样两点之间，所有路径的权值都改变了相同的量 `h(v₀) − h(vₖ)`，最短路径的「身份」完全不变。**

### 怎么找 h 使 ŵ ≥ 0

要求 `w(u,v) + h(u) − h(v) ≥ 0`，即 `h(v) ≤ h(u) + w(u,v)`。

**这恰好是三角不等式！** 所以取 **h(v) = 从某个新加虚拟源点 q 到 v 的最短距离** 即可：

```
① 添加虚拟顶点 q，向所有顶点连一条权 0 的边
② 用 Bellman-Ford 从 q 求出 h(v) = δ(q, v)     ← 顺带检测负环
③ 重赋权 ŵ(u,v) = w(u,v) + h(u) − h(v) ≥ 0
④ 对每个顶点跑 Dijkstra（用 ŵ）
⑤ 还原真实距离：δ(u,v) = δ̂(u,v) − h(u) + h(v)
```

```go
func Johnson(n int, edges []Edge) ([][]int, bool) {
    // ① ② 加虚拟源点 n，跑 Bellman-Ford
    aug := slices.Clone(edges)
    for v := 0; v < n; v++ {
        aug = append(aug, Edge{U: n, V: v, W: 0})
    }
    h, ok := BellmanFord(n+1, aug, n)
    if !ok {
        return nil, false // 存在负环
    }

    // ③ 重赋权
    g := NewWGraph(n)
    for _, e := range edges {
        g.AddEdge(e.U, e.V, e.W+h[e.U]-h[e.V]) // 保证 ≥ 0
    }

    // ④ ⑤ 对每个顶点跑 Dijkstra 并还原
    dist := make([][]int, n)
    for u := 0; u < n; u++ {
        d, _ := Dijkstra(g, u)
        dist[u] = d
        for v := range d {
            if d[v] != math.MaxInt {
                dist[u][v] = d[v] - h[u] + h[v]
            }
        }
    }
    return dist, true
}
```

**复杂度**：`O(V·E)`（一次 Bellman-Ford）`+ V · O(E log V)`（V 次 Dijkstra）= **O(V·E log V)**。

⭐ **稀疏图 E = Θ(V) 时：O(V² log V) 远优于 Floyd-Warshall 的 Θ(V³)。**

⚠️ **重赋权技巧的价值超出本讲**：它是"用势能函数变换问题"的通用手法，在最小费用流（每轮用势能保持非负权以便用 Dijkstra）、以及[第 4 讲]({{< ref "04-amortized-analysis.md" >}})的摊还分析中都是同一个思想。

---

## 五、选型

| 情况 | 算法 | 复杂度 |
|---|---|---|
| **稠密图**（E ≈ V²） | **Floyd-Warshall** | Θ(V³)，代码 5 行 |
| **稀疏图 + 非负权** | V 次 Dijkstra | O(V·E log V) |
| **稀疏图 + 有负权** | **Johnson** | O(V·E log V) |
| 只要可达性 | Warshall + bitset | Θ(V³/64) |
| 只要部分点对 | 直接跑相应的单源 | — |
| V > 5000 且稠密 | ⚠️ Θ(V³) = 10¹¹，重新考虑问题建模 | — |

⭐ **实用提醒**：Floyd-Warshall 的 Θ(V³) 空间也是 Θ(V²)。V = 10⁴ 时距离矩阵就是 10⁸ 个 int，800 MB。**全源最短路在大图上根本不可行**——这时应该考虑的是"我真的需要所有点对吗"，通常答案是不需要。

---

## 六、Floyd-Warshall 的其他变体

同一个三重循环框架，换掉 `min` 和 `+`，可以解一系列问题（这个抽象叫**半环上的路径代数**）：

| 问题 | 替换 |
|---|---|
| 最短路 | `min`, `+` |
| 传递闭包 | `or`, `and` |
| **最大瓶颈路**（路径最小边权最大） | `max`, `min` |
| **最小瓶颈路**（路径最大边权最小） | `min`, `max` |
| 路径数量计数 | `+`, `×` |
| 最可靠路径（概率乘积最大） | `max`, `×` |

⭐ **只要运算构成一个半环（结合律 + 分配律），Floyd-Warshall 的框架就成立。** 这是把一个具体算法抽象成代数结构的漂亮例子。

---

## 随堂自测

1. 写出 Floyd-Warshall 的 DP 状态定义和递推式，说明"中间顶点"这个限定为什么关键。
2. 为什么 k 必须是最外层循环？如果放在最内层，语义变成什么？
3. 为什么可以去掉 DP 的第一维就地更新？关键性质是什么？
4. Floyd-Warshall 如何检测负环？检测到之后其余结果还有效吗？
5. 稠密图上为什么 Floyd-Warshall 优于 V 次 Dijkstra？稀疏图上呢？
6. 传递闭包用 bitset 优化后复杂度是多少？为什么这个常数改进值得做？
7. 证明重赋权 `ŵ(u,v) = w(u,v) + h(u) − h(v)` 不改变最短路径的选择。
8. Johnson 算法中 h(v) 取什么？为什么这样取能保证 ŵ ≥ 0？
9. 为什么要引入一个连向所有顶点的虚拟源点，而不是随便选一个已有顶点？
10. 把 Floyd-Warshall 的 (min, +) 换成 (max, min) 得到什么问题的解？换成 (min, max) 呢？⚠️ 这两个答案是相反的，别搞混。

