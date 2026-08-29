---
title: "第 24 讲：最小生成树——Kruskal 与 Prim"
date: 2026-08-28
weight: 24
tags: ["数据结构与算法"]
draft: false
summary: "割性质与环性质这两条定理如何一次性证明所有 MST 算法的正确性、Kruskal 与 Prim 的实现与复杂度对比、边权唯一时 MST 唯一的证明，以及 MST 与最短路径树的本质区别。"
showToc: true
tocOpen: false
---

## 一、问题

> **最小生成树（MST）**
> **输入**：连通、无向、加权图 G = (V, E, w)
> **输出**：一棵包含所有顶点的树 T ⊆ E，使 `Σ_{e∈T} w(e)` 最小

**性质**：生成树恰有 **V−1 条边**（树的定义：连通且无环 ⟹ 边数 = 顶点数 − 1）。

**应用**：网络布线成本最小化、电路板走线、聚类（去掉 MST 中最长的 k−1 条边得到 k 个簇）、图像分割、近似算法（TSP 的 2-近似，见[第 34 讲]({{< ref "34-np-completeness.md" >}})）。

---

## 二、两条定理决定一切

MST 有多个算法，但它们的正确性都建立在同两条定理上。理解了这两条，所有算法都是显然的。

### ⭐ 割性质（Cut Property）

> **定义**：图的一个**割（cut）** 是顶点集的一个划分 (S, V−S)。**横跨边（crossing edge）** 是一端在 S、另一端在 V−S 的边。
>
> **割性质**：对**任意**割，其**权值最小的横跨边**必定属于某棵 MST。（若该边唯一最小，则它属于**所有** MST。）

```
        S 区域          │        V−S 区域
    ┌──────────────┐   │   ┌──────────────┐
    │   a ──── b   │   │   │   d ──── e   │
    │       ╲      │───┼───│      ╱       │
    │        c ────┼─5─┼───┼── f          │   ← 权 5 是最小横跨边
    └──────────────┘   │   └──────────────┘      ⟹ 它必在某棵 MST 中
                       │
              还有一条横跨边权 9
```

**证明（交换论证）**：设 e 是最小横跨边，假设某棵 MST T 不含 e。把 e 加入 T 会形成一个环 C。C 必然还包含另一条横跨边 e′（因为环从 S 出去必须回来）。由 e 的最小性 `w(e) ≤ w(e′)`。令 `T′ = T − {e′} + {e}`，则 T′ 仍是生成树，且 `w(T′) ≤ w(T)`。所以 T′ 也是 MST，且含 e。∎

⭐ **这个"加一条边形成环，再删掉环上另一条边"的手法叫交换论证（exchange argument），是[第 30 讲]({{< ref "30-greedy-algorithms.md" >}})证明贪心算法正确性的核心工具。**

### 环性质（Cycle Property）

> 对任意环，其**权值最大的边**（若唯一）**不属于任何 MST**。

**证明**：若某 MST 含这条最大边 e，删掉它，树分成两个连通块。环上必有另一条边 e′ 连接这两块，且 `w(e′) < w(e)`。替换后得到更小的生成树，矛盾。∎

### 通用 MST 算法

```
维护一个边集 A（始终是某棵 MST 的子集，称为"安全"的）
重复 V−1 次：
    找一条对 A "安全"的边加入 A
```

**割性质保证了如何找安全边**：取任意一个"不横跨 A 中已有边"的割，取其最小横跨边即可。

⭐ **Kruskal 与 Prim 的唯一区别，就是选择哪个割。**

| 算法 | 选择的割 |
|---|---|
| **Prim** | (已加入的顶点集, 其余顶点)——**割固定，逐步长大** |
| **Kruskal** | 对当前最小边 (u,v)，取"u 所在连通块 vs 其余"——**每次的割不同** |

---

## 三、Kruskal 算法

**贪心策略**：按边权从小到大考虑每条边，**不构成环就加入**。

```
边排序：  (a,b,1) (c,d,2) (b,c,3) (a,c,4) (d,e,5) …

加 (a,b,1) ✓        a─b   c  d  e
加 (c,d,2) ✓        a─b   c─d  e
加 (b,c,3) ✓        a─b─c─d    e
加 (a,c,4) ✗ 成环   （a 和 c 已连通）
加 (d,e,5) ✓        a─b─c─d─e   ← 完成，V−1=4 条边
```

```go
type Edge struct{ U, V, W int }

func Kruskal(n int, edges []Edge) ([]Edge, int) {
    slices.SortFunc(edges, func(a, b Edge) int { return cmp.Compare(a.W, b.W) })

    d := NewDSU(n) // 第 23 讲的并查集
    mst := make([]Edge, 0, n-1)
    total := 0
    for _, e := range edges {
        if d.Union(e.U, e.V) { // Union 返回 false 表示已连通（会成环）
            mst = append(mst, e)
            total += e.W
            if len(mst) == n-1 {
                break
            }
        }
    }
    return mst, total
}
```

**"不构成环"的判定就是并查集**（[第 23 讲]({{< ref "23-disjoint-sets.md" >}})）——这是并查集最经典的应用。

### 复杂度

```
排序：            O(E log E) = O(E log V)      ← 因为 E ≤ V²，log E ≤ 2 log V
并查集操作：       O(E · α(V))
                 ──────────────
          总计    O(E log E)   ← 排序是瓶颈
```

⭐ **如果边已经排好序**（或边权是小整数可用基数排序，[第 12 讲]({{< ref "12-sorting-lower-bound-linear-sorts.md" >}})），Kruskal 降到 **O(E α(V))**，几乎线性。

**正确性**：每次加入的边 (u,v) 是"u 所在连通块与其余部分"这个割的最小横跨边（因为所有更小的边要么已被加入，要么两端已在同一块内）。由割性质，它是安全的。∎

---

## 四、Prim 算法

**贪心策略**：从一个顶点开始，**每次把"离当前树最近的顶点"拉进来**。

```
起点 a：
  树 = {a}              最近的边 (a,b,1)  ⟹  加入 b
  树 = {a,b}            最近的边 (b,c,3)  ⟹  加入 c
  树 = {a,b,c}          最近的边 (c,d,2)  ⟹  加入 d
  …
```

⭐ **Prim 与 Dijkstra 的结构几乎一模一样**（[第 25 讲]({{< ref "25-single-source-shortest-paths.md" >}})），差别只在 key 的定义：

```
Prim：      key[v] = min 边权(u, v)，u ∈ 树        ← "到树的距离"
Dijkstra：  key[v] = min (dist[u] + 边权(u,v))     ← "到起点的距离"
```

```go
func Prim(g *WGraph, start int) ([]Edge, int) {
    inMST := make([]bool, g.n)
    key := make([]int, g.n)
    parent := make([]int, g.n)
    for i := range key {
        key[i], parent[i] = math.MaxInt, -1
    }
    key[start] = 0

    pq := &edgeHeap{{node: start, weight: 0}}
    heap.Init(pq)
    total := 0
    var mst []Edge

    for pq.Len() > 0 {
        item := heap.Pop(pq).(pqItem)
        u := item.node
        if inMST[u] { // ⭐ 惰性删除：跳过过期条目
            continue
        }
        inMST[u] = true
        total += key[u]
        if parent[u] != -1 {
            mst = append(mst, Edge{parent[u], u, key[u]})
        }

        for _, e := range g.adj[u] {
            if !inMST[e.To] && e.Weight < key[e.To] {
                key[e.To] = e.Weight
                parent[e.To] = u
                heap.Push(pq, pqItem{node: e.To, weight: e.Weight})
            }
        }
    }
    return mst, total
}
```

⚠️ **惰性删除（lazy deletion）**：Go 的 `container/heap` 不支持 `DecreaseKey`，所以我们**每次更新就 push 一个新条目**，弹出时用 `inMST` 跳过过期的。代价是堆里最多有 E 个元素而不是 V 个，但复杂度不变：O(E log E) = O(E log V)。这是工程实现中最常用的写法。

### 复杂度取决于优先队列

| 优先队列实现 | Prim 复杂度 |
|---|---|
| 数组（线性扫描找最小） | O(V²) |
| **二叉堆** | **O(E log V)** |
| Fibonacci 堆 | **O(E + V log V)** |

⭐ **稠密图（E = Θ(V²)）用数组版更好**：O(V²) 优于 O(V² log V)。这是[第 10 讲]({{< ref "10-heaps-priority-queues.md" >}})"数据结构选择取决于操作混合比例"的又一实例。

---

## 五、Kruskal vs Prim

| | Kruskal | Prim（二叉堆） | Prim（数组） |
|---|---|---|---|
| 复杂度 | O(E log E) | O(E log V) | O(V²) |
| 依赖的数据结构 | **并查集** + 排序 | **优先队列** | 数组 |
| 适合 | **稀疏图** | 稀疏图 | **稠密图** |
| 中间状态 | 森林（多个连通块） | **单棵树**（连通） |
| 边已排序时 | **O(E α(V))** ⭐ | 无优势 |
| 并行化 | 较好（Borůvka 更好） | 较差（本质串行） |
| 适合分布式 | ✓ | ✗ |

⭐ **选型规则**：
- **稀疏图**（E ≈ V）→ Kruskal 或堆版 Prim
- **稠密图**（E ≈ V²）→ 数组版 Prim（O(V²)）
- **边权已排序或是小整数** → Kruskal（近线性）
- **图太大需要分布式** → **Borůvka 算法**（每轮让每个连通块选自己的最小出边，O(log V) 轮，天然并行）

---

## 六、MST 的性质

### 唯一性

> **定理**：若所有边权**互不相同**，则 MST 唯一。

**证明（反证）**：设有两棵不同的 MST：T₁、T₂。取 `e = T₁ △ T₂` 中权值最小的边，不妨设 `e ∈ T₁ \ T₂`。把 e 加入 T₂ 形成环 C，C 中必有边 `e′ ∉ T₁`（否则 T₁ 含环）。由 e 的选取 `w(e) < w(e′)`，故 `T₂ − e′ + e` 比 T₂ 更小，矛盾。∎

**推论**：边权有重复时 MST 可能不唯一，但**MST 的总权值唯一**。

**实用技巧**：想要唯一 MST 时，给相同权值的边加一个基于编号的微小扰动（tie-breaking）即可。

### ⭐ MST ≠ 最短路径树

这是最常见的混淆之一。

```
        A
      2/ \2
      B───C
        3

MST（总权 4）：      A-B(2), A-C(2)
从 B 出发的最短路树：B-A(2), B-C(3)   ← B 到 C 走 MST 要 2+2=4，走直连只要 3
```

| | MST | 最短路径树 |
|---|---|---|
| 优化目标 | **所有边权之和最小** | **从源点到各点的距离分别最小** |
| 与起点有关 | ✗ | ✓ |
| 全局 vs 局部 | 全局总和 | 每个点单独 |

⚠️ **MST 上两点间的路径，不一定是图中两点间的最短路。** 这是两个完全不同的优化问题。

### 其他有用性质

| 性质 | 说明 |
|---|---|
| **最小瓶颈路** | MST 上 u→v 的路径，**最大边权最小**（minimax path）。这是 MST 一个非常有用但常被忽略的性质 |
| 边权全部 +c | MST 不变（每棵生成树都恰好有 V−1 条边） |
| 边权全部 ×c（c>0） | MST 不变 |
| 最大生成树 | 把权取负后求 MST |
| 次小生成树 | 枚举每条非树边，替换掉它在树上路径的最大边 |

⭐ **"最小瓶颈路"性质的应用**：在一个网络里找一条 u 到 v 的路径，使**路径上最脆弱的那条链路尽可能强**（如带宽最大、故障率最低）。答案就是 MST 上的路径，不需要专门的算法。

---

## 随堂自测

1. 陈述割性质并给出交换论证的完整证明。
2. 环性质说了什么？它和割性质是什么关系？
3. 通用 MST 算法的框架是什么？Kruskal 和 Prim 分别选择了哪个割？
4. Kruskal 中"判断是否成环"为什么用并查集？总复杂度的瓶颈在哪一步？
5. 若边权都是 1 到 100 的整数，Kruskal 能做到多快？为什么？
6. Prim 与 Dijkstra 的算法结构几乎相同，唯一的差别在哪一行？
7. 为什么稠密图上数组版 Prim（O(V²)）优于堆版（O(E log V)）？
8. 为什么 Go 实现 Prim 常用"惰性删除"而不是 DecreaseKey？代价是什么？
9. 证明：边权互不相同时 MST 唯一。边权有重复时什么仍然唯一？
10. 给出一个具体的图，说明 MST 上两点的路径不是最短路。
11. 什么是最小瓶颈路？为什么 MST 上的路径就是它？

---

> **上一讲**：[第 23 讲：并查集与不相交集合]({{< ref "23-disjoint-sets.md" >}})　**下一讲**：[第 25 讲：单源最短路径]({{< ref "25-single-source-shortest-paths.md" >}})
