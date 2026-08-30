---
title: "第 32 讲：动态规划 II——进阶模型与优化"
date: 2026-08-28
weight: 32
tags: ["数据结构与算法"]
draft: false
summary: "区间 DP（矩阵链乘、最优 BST）、树形 DP、状态压缩 DP（TSP 与集合覆盖）、数位 DP，以及三类经典优化：单调队列优化、前缀和/差分优化、四边形不等式与决策单调性。"
showToc: true
tocOpen: false
---

## 一、区间 DP

**特征**：状态定义为一个**区间** `dp[i][j]`，转移时枚举区间内的**分割点**。

⭐ **区间 DP 的循环顺序必须按「区间长度」从小到大**，因为长区间依赖短区间。

### 矩阵链乘法

> **问题**：矩阵链 `A₁A₂…Aₙ`，Aᵢ 的维度是 `pᵢ₋₁ × pᵢ`。加括号使标量乘法次数最少。

**为什么有差别？** 矩阵乘法满足结合律，但代价差别巨大：

```
A₁(10×100)  A₂(100×5)  A₃(5×50)

((A₁A₂)A₃):  10·100·5 + 10·5·50  = 5000 + 2500  = 7500
(A₁(A₂A₃)):  100·5·50 + 10·100·50 = 25000 + 50000 = 75000

差 10 倍！
```

**状态**：`dp[i][j]` = 计算 `Aᵢ…Aⱼ` 的最小标量乘法次数。

**转移**：枚举最后一次乘法的分割点 k：

```
dp[i][j] = min_{i ≤ k < j} ( dp[i][k] + dp[k+1][j] + p_{i−1}·p_k·p_j )
```

```go
func MatrixChainOrder(p []int) (int, [][]int) {
    n := len(p) - 1 // n 个矩阵
    dp := make([][]int, n+1)
    split := make([][]int, n+1)
    for i := range dp {
        dp[i] = make([]int, n+1)
        split[i] = make([]int, n+1)
    }

    for length := 2; length <= n; length++ { // ⭐ 按区间长度递增
        for i := 1; i+length-1 <= n; i++ {
            j := i + length - 1
            dp[i][j] = math.MaxInt
            for k := i; k < j; k++ {
                cost := dp[i][k] + dp[k+1][j] + p[i-1]*p[k]*p[j]
                if cost < dp[i][j] {
                    dp[i][j] = cost
                    split[i][j] = k
                }
            }
        }
    }
    return dp[1][n], split
}
```

**复杂度**：状态 Θ(n²)，每个转移 Θ(n) ⟹ **Θ(n³)**，空间 Θ(n²)。

### 区间 DP 家族

| 问题 | 状态与转移要点 |
|---|---|
| 矩阵链乘 | 枚举最后一次乘法的位置 |
| **最优二叉搜索树** | 枚举根，`dp[i][j] = min(dp[i][k−1] + dp[k+1][j]) + Σ权重` |
| 石子合并 | 枚举最后合并的分界 |
| 最长回文子序列 | `dp[i][j] = dp[i+1][j−1] + 2`（两端相同） |
| 括号匹配 / 表达式加括号 | 枚举分割点 |
| 戳气球 | ⭐ 逆向思维：枚举**最后**戳破的气球 |

⭐ **"戳气球"这类问题的技巧值得单独记**：正向思考（枚举第一个戳的）会破坏区间的独立性，而**枚举最后一个操作的对象**能让左右两边真正独立。**区间 DP 遇到困难时，试试倒过来想。**

### 最优二叉搜索树

⭐ 这个问题把[第 15 讲]({{< ref "15-binary-search-trees.md" >}})和 DP 连了起来：给定每个键的**查询频率**，构造使**期望查找代价最小**的 BST。

**注意它与平衡树的区别**：平衡树最小化**最坏高度**，最优 BST 最小化**期望深度**——高频键应该更靠近根，哪怕树不平衡。

```
dp[i][j] = min_{i ≤ r ≤ j} ( dp[i][r−1] + dp[r+1][j] ) + Σ_{k=i}^{j} freq[k]
```

**那个 `Σ freq` 项**是因为把子树接到根下面，子树中每个节点的深度都 +1。

**Θ(n³)**，可用四边形不等式优化到 Θ(n²)（见第五节）。

---

## 二、树形 DP

**特征**：状态定义在**子树**上，转移沿着树的结构（通常用 DFS 后序）。

### 树上最大独立集

> **问题**：选出最多的节点，使任意两个被选节点不相邻。

**状态**：`dp[u][0]` = 不选 u 时 u 子树的最大独立集；`dp[u][1]` = 选 u 时。

```
dp[u][0] = Σ_{v ∈ children(u)} max(dp[v][0], dp[v][1])    u 不选，孩子随意
dp[u][1] = 1 + Σ_{v ∈ children(u)} dp[v][0]              u 选了，孩子都不能选
```

```go
func TreeMaxIndependentSet(tree [][]int, root int) int {
    dp := make([][2]int, len(tree))
    var dfs func(u, parent int)
    dfs = func(u, parent int) {
        dp[u][0], dp[u][1] = 0, 1
        for _, v := range tree[u] {
            if v == parent {
                continue
            }
            dfs(v, u)
            dp[u][0] += max(dp[v][0], dp[v][1])
            dp[u][1] += dp[v][0]
        }
    }
    dfs(root, -1)
    return max(dp[root][0], dp[root][1])
}
```

**Θ(n)**——每个节点处理一次。

⚠️ **对比一般图**：最大独立集是 NP-完全的（[第 34 讲]({{< ref "34-np-completeness.md" >}})），二分图上可用匹配求解（[第 27 讲]({{< ref "27-network-flow.md" >}})），**树上则是线性的**。**图的结构越受限，问题越容易——这是一条贯穿全课的规律。**

### 换根 DP（二次扫描）

**问题**：对**每个**节点求"以它为根时的某个量"（如到所有点的距离和）。

朴素做法：对每个节点做一次 DFS，Θ(n²)。

**换根 DP**：两遍 DFS，Θ(n)。

```
① 第一遍（自底向上）：求出以 root 为根时每个子树的信息
② 第二遍（自顶向下）：由父节点的答案 O(1) 推出孩子的答案
```

```go
// 求每个节点到所有其他节点的距离之和
func SumOfDistances(n int, tree [][]int) []int {
    size := make([]int, n) // 子树大小
    ans := make([]int, n)

    var dfs1 func(u, p int) // ① 求 size 和 ans[root]
    dfs1 = func(u, p int) {
        size[u] = 1
        for _, v := range tree[u] {
            if v == p { continue }
            dfs1(v, u)
            size[u] += size[v]
            ans[0] += size[v] // 累加子树贡献（这里以 0 为根）
        }
    }

    var dfs2 func(u, p int) // ② 换根：从父节点推孩子
    dfs2 = func(u, p int) {
        for _, v := range tree[u] {
            if v == p { continue }
            // ⭐ 根从 u 移到 v：v 子树内的点各近 1，子树外的点各远 1
            ans[v] = ans[u] - size[v] + (n - size[v])
            dfs2(v, u)
        }
    }

    dfs1(0, -1)
    dfs2(0, -1)
    return ans
}
```

⭐ **换根 DP 的核心是那一行转移**：想清楚"根从 u 移到 v 时，哪些点的距离变了、变了多少"。这是一个很有代表性的**增量思维**。

---

## 三、状态压缩 DP

**特征**：状态包含一个**集合**，用二进制位表示。适用于 **n ≤ 20** 左右。

### 旅行商问题（TSP）

> **问题**：从起点出发，经过所有城市各一次，回到起点，求最短路径。

**状态**：`dp[mask][i]` = 已访问集合为 mask、当前在城市 i 的最短路径长度。

```go
func TSP(dist [][]int) int {
    n := len(dist)
    full := 1 << n
    const inf = math.MaxInt / 2
    dp := make([][]int, full)
    for i := range dp {
        dp[i] = make([]int, n)
        for j := range dp[i] { dp[i][j] = inf }
    }
    dp[1][0] = 0 // 从城市 0 出发，已访问 {0}

    for mask := 1; mask < full; mask++ {
        for i := 0; i < n; i++ {
            if dp[mask][i] == inf || mask&(1<<i) == 0 {
                continue
            }
            for j := 0; j < n; j++ {
                if mask&(1<<j) != 0 { // j 已访问
                    continue
                }
                next := mask | (1 << j)
                dp[next][j] = min(dp[next][j], dp[mask][i]+dist[i][j])
            }
        }
    }

    best := inf
    for i := 1; i < n; i++ { // 回到起点
        best = min(best, dp[full-1][i]+dist[i][0])
    }
    return best
}
```

**复杂度**：状态 Θ(2ⁿ·n)，转移 Θ(n) ⟹ **Θ(2ⁿ·n²)**，空间 Θ(2ⁿ·n)。

⭐ **这是 Held-Karp 算法（1962）**。与朴素枚举全排列的 **Θ(n!)** 相比是巨大的改进：

| n | n! | 2ⁿ·n² |
|---|---|---|
| 10 | 3.6×10⁶ | 10⁵ |
| 15 | 1.3×10¹² | **7×10⁶** |
| 20 | 2.4×10¹⁸ | **4×10⁸** |
| 25 | 1.6×10²⁵ | 2×10¹⁰（内存爆炸：2²⁵×25×8B = 6.7 GB） |

**但它仍然是指数级的**——TSP 是 NP-难的（[第 34 讲]({{< ref "34-np-completeness.md" >}})），n = 25 就是实用上限。更大规模需要近似算法或分支限界。

### 常用位运算技巧

```go
mask & (1 << i)        // 判断第 i 位是否为 1
mask | (1 << i)        // 置 1
mask &^ (1 << i)       // 清 0（Go 的 AND NOT 运算符）
mask & (mask - 1)      // ⭐ 清掉最低位的 1
mask & (-mask)         // ⭐ 取出最低位的 1（lowbit，见第 20 讲）
bits.OnesCount(uint(mask))     // 1 的个数（编译为 POPCNT 指令）
bits.TrailingZeros(uint(mask)) // 最低位 1 的下标

// ⭐ 枚举 mask 的所有子集
for sub := mask; sub > 0; sub = (sub - 1) & mask {
    // sub 是 mask 的一个非空子集
}
```

⭐ **"枚举所有子集的所有子集"的总复杂度是 Θ(3ⁿ)** 而不是 Θ(4ⁿ)——因为每个元素有三种状态（不在 mask、在 mask 不在 sub、在 sub）。这个结论在集合划分类 DP 中经常用到。

---

## 四、数位 DP

**特征**：统计 `[L, R]` 内满足某种**数位性质**的数的个数。

**核心技巧**：
1. **转化为前缀**：`f(R) − f(L−1)`
2. **按位从高到低填**，状态记录"是否顶着上界"（tight）和"是否已有前导非零"

```go
// 统计 [0, n] 中不含数字 4 的数的个数
func countNoFour(n int) int {
    digits := []byte(strconv.Itoa(n))
    memo := make(map[[2]int]int)

    var dfs func(pos int, tight bool) int
    dfs = func(pos int, tight bool) int {
        if pos == len(digits) {
            return 1
        }
        t := 0
        if tight {
            t = 1
        }
        key := [2]int{pos, t}
        if !tight { // ⭐ 只有非 tight 状态才能缓存（tight 依赖具体的上界前缀）
            if v, ok := memo[key]; ok {
                return v
            }
        }
        limit := 9
        if tight {
            limit = int(digits[pos] - '0')
        }
        res := 0
        for d := 0; d <= limit; d++ {
            if d == 4 {
                continue
            }
            res += dfs(pos+1, tight && d == limit)
        }
        if !tight {
            memo[key] = res
        }
        return res
    }
    return dfs(0, true)
}
```

**复杂度 O(位数 × 状态数 × 10)**——与 n 的**大小**无关，只与它的**位数**有关。所以能处理 n 达 10¹⁸ 的问题。

⚠️ **tight 状态不能被缓存**（除非把上界也编进 key），这是数位 DP 最常见的错误。

---

## 五、三类优化

### 优化 1：单调队列优化

**适用形式**：`dp[i] = min_{j ∈ [i−k, i−1]} ( dp[j] + w(i) )`——转移来源是一个**滑动窗口**。

朴素 Θ(nk) ⟹ 用[第 6 讲]({{< ref "06-stacks-queues.md" >}})的单调队列降到 **Θ(n)**。

```go
// 每次最多跳 k 步，求到达终点的最大得分
func maxResult(nums []int, k int) int {
    n := len(nums)
    dp := make([]int, n)
    dp[0] = nums[0]
    dq := []int{0} // 存下标，dp 值单调递减

    for i := 1; i < n; i++ {
        for len(dq) > 0 && dq[0] < i-k { // 队首过期
            dq = dq[1:]
        }
        dp[i] = dp[dq[0]] + nums[i]
        for len(dq) > 0 && dp[dq[len(dq)-1]] <= dp[i] { // 队尾被支配
            dq = dq[:len(dq)-1]
        }
        dq = append(dq, i)
    }
    return dp[n-1]
}
```

### 优化 2：前缀和 / 差分

**适用**：转移是对一段连续状态求和，或对一段状态统一加值。

```
dp[i][j] = Σ_{k=j−m}^{j} dp[i−1][k]     ⟹  预处理 dp[i−1] 的前缀和，转移 O(1)
```

⭐ 把 Θ(n) 的转移变成 Θ(1)，整体降一个量级。这是最简单也最常用的 DP 优化。

### 优化 3：四边形不等式与决策单调性

**适用**：`dp[i][j] = min_{i≤k<j} ( dp[i][k] + dp[k+1][j] ) + w(i,j)`。

> **四边形不等式**：若代价函数 w 满足 `w(a,c) + w(b,d) ≤ w(a,d) + w(b,c)`（对 a ≤ b ≤ c ≤ d），则**最优决策点单调**：
> ```
> opt[i][j−1] ≤ opt[i][j] ≤ opt[i+1][j]
> ```

**利用这个单调性收缩枚举范围**，可以把 Θ(n³) 降到 **Θ(n²)**：

```go
for length := 2; length <= n; length++ {
    for i := 1; i+length-1 <= n; i++ {
        j := i + length - 1
        // ⭐ k 只在 [opt[i][j-1], opt[i+1][j]] 内枚举
        for k := opt[i][j-1]; k <= opt[i+1][j]; k++ {
            if cost := dp[i][k] + dp[k+1][j] + w(i, j); cost < dp[i][j] {
                dp[i][j] = cost
                opt[i][j] = k
            }
        }
    }
}
```

**为什么总代价是 Θ(n²)？** 对固定的区间长度，所有 k 的枚举范围加起来是**望远镜求和**，总量 O(n)。

⭐ **最优 BST 用这个优化后从 Θ(n³) 降到 Θ(n²)**（Knuth 优化，1971）。

**其他优化**：斜率优化 / 凸包技巧（转移含 `i×j` 乘积项）、Divide & Conquer 优化（决策单调但无四边形不等式）、矩阵快速幂优化线性递推（[第 28 讲]({{< ref "28-divide-and-conquer.md" >}})）。

---

## 六、DP 优化速查

| 转移形式 | 优化 | 复杂度 |
|---|---|---|
| `min` 来自滑动窗口 | 单调队列 | Θ(nk) → Θ(n) |
| 来自一段区间的和 | 前缀和 | Θ(n²) → Θ(n) |
| 区间 DP + 四边形不等式 | 决策单调性 | Θ(n³) → Θ(n²) |
| 转移含 `i·j` 项 | 斜率优化 / 凸包 | Θ(n²) → Θ(n) |
| 线性递推、n 极大 | 矩阵快速幂 | Θ(n) → Θ(log n) |
| 只依赖上一层 | 滚动数组 | 空间 Θ(n²) → Θ(n) |
| 只有部分状态可达 | 记忆化搜索 | 避免无效状态 |

---

## 随堂自测

1. 区间 DP 的循环为什么必须按区间长度递增？
2. 矩阵链乘的状态与转移是什么？为什么加括号方式能差 10 倍？
3. "戳气球"为什么要枚举最后戳破的而不是第一个？
4. 最优 BST 与平衡树的优化目标有什么不同？
5. 写出树上最大独立集的两个状态和转移方程。为什么树上是线性的而一般图是 NP-完全的？
6. 换根 DP 的两遍 DFS 各做什么？写出"根从 u 移到 v"的转移。
7. TSP 的状压 DP 复杂度是多少？相比枚举排列改进了多少？n 能做到多大？
8. `mask & (mask-1)` 和 `mask & (-mask)` 分别是什么？枚举所有子集的循环怎么写？
9. 为什么"枚举所有子集的子集"总复杂度是 Θ(3ⁿ)？
10. 数位 DP 中为什么 tight 状态不能缓存？
11. 四边形不等式给出什么结论？为什么利用它能把 Θ(n³) 降到 Θ(n²)？

