---
title: "第 29 讲：回溯与穷举搜索"
date: 2026-08-28
weight: 29
tags: ["数据结构与算法"]
draft: false
summary: "系统穷举的通用框架：状态-选择-撤销三要素、子集与排列的枚举与去重、N 皇后的位运算实现、剪枝的四种手段、分支限界与 A* 的关系，以及回溯、贪心与动态规划三者共同的底层结构。"
showToc: true
tocOpen: false
---

## 一、当没有多项式算法时

[第 28 讲]({{< ref "28-divide-and-conquer.md" >}})的分治、[第 30 讲]({{< ref "30-greedy-algorithms.md" >}})的贪心、[第 31 讲]({{< ref "31-dynamic-programming-1.md" >}})的动态规划，都要求问题有某种**结构**——子问题独立、贪心选择性质、或最优子结构。

**当这些结构都不存在时，剩下的办法只有一个：把所有可能都试一遍。**

⭐ 但"试一遍"不等于"笨"。**回溯（backtracking）是有组织的穷举**：它把解空间组织成一棵树，深度优先地走，并且在**确定某条分支不可能产生解时立刻掉头**。这个"立刻掉头"就是**剪枝**，它常常把 2ⁿ 的理论规模削减几个数量级。

**这一讲的位置很重要**。把三种范式放在一起看，会发现它们是同一件事的三个切面：

```
                    解空间树（所有可能的选择序列）
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
    回溯：走遍整棵树      贪心：只走一条枝      DP：走遍但记住重复的子树
    （+剪枝）            （靠交换论证保证对）   （靠重叠子问题省下指数）
```

⭐ **DP 就是"回溯 + 记忆化"**——[第 31 讲]({{< ref "31-dynamic-programming-1.md" >}})会看到，几乎每个 DP 都可以先写成回溯，再加一个 memo 表。**先写回溯往往是设计 DP 最可靠的路径。**

---

## 二、通用框架

**回溯的三要素**：

| 要素 | 含义 |
|---|---|
| **状态（path）** | 当前已经做出的选择序列 |
| **选择列表** | 当前状态下还能做哪些选择 |
| **撤销（undo）** | 返回上层前，把这一层的修改还原 |

```go
func backtrack(path []T, state *State) {
    if isSolution(path) {
        record(path) // ⚠️ 若要保存，必须拷贝（见下）
        return
    }
    for _, choice := range candidates(state) {
        if !isValid(choice, state) {
            continue // ⭐ 剪枝：不合法就根本不进入
        }
        apply(choice, &path, state)   // 做选择
        backtrack(path, state)        // 递归
        undo(choice, &path, state)    // ⭐ 撤销
    }
}
```

### ⚠️ Go 里最容易踩的坑：切片共享底层数组

```go
res = append(res, path)                          // ✗ path 是切片，后续修改会污染已保存的结果
res = append(res, slices.Clone(path))            // ✓ 必须深拷贝
res = append(res, append([]int(nil), path...))   // ✓ 等价写法
```

**这是回溯题里最高频的 bug**，而且症状极具迷惑性：结果数量正确，但内容全是最后一次的状态。根因是[第 5 讲]({{< ref "05-arrays-linked-lists.md" >}})讲过的切片共享底层数组——`path` 在撤销时被就地修改，而 `res` 里存的是指向同一块内存的切片头。

---

## 三、子集与排列：两种基本形态

### 子集（组合）：每个元素选或不选

```go
func Subsets(nums []int) [][]int {
    var res [][]int
    var path []int

    var dfs func(start int)
    dfs = func(start int) {
        res = append(res, slices.Clone(path)) // 每个节点都是一个解
        for i := start; i < len(nums); i++ {
            path = append(path, nums[i])
            dfs(i + 1) // ⭐ i+1：每个元素最多用一次，且不回头 ⟹ 天然去重
            path = path[:len(path)-1] // 撤销
        }
    }
    dfs(0)
    return res
}
```

⭐ **`start` 参数是组合类问题的核心**：它保证选出的下标严格递增，从而 `{1,2}` 和 `{2,1}` 只会产生一次。**组合不关心顺序，用 start 消除顺序；排列关心顺序，就不能用 start。**

### 排列：每个元素用一次，但顺序重要

```go
func Permutations(nums []int) [][]int {
    var res [][]int
    path := make([]int, 0, len(nums))
    used := make([]bool, len(nums))

    var dfs func()
    dfs = func() {
        if len(path) == len(nums) {
            res = append(res, slices.Clone(path))
            return
        }
        for i := range nums {
            if used[i] {
                continue // 排列没有 start，改用 used 标记
            }
            used[i] = true
            path = append(path, nums[i])
            dfs()
            path = path[:len(path)-1]
            used[i] = false // ⭐ 两个撤销都不能漏
        }
    }
    dfs()
    return res
}
```

### ⭐ 含重复元素时的去重

**这是回溯里最容易写错的一处。** 先排序，然后在**同一层**跳过重复值：

```go
func PermutationsUnique(nums []int) [][]int {
    slices.Sort(nums) // 前提：相同元素相邻
    var res [][]int
    var path []int
    used := make([]bool, len(nums))

    var dfs func()
    dfs = func() {
        if len(path) == len(nums) {
            res = append(res, slices.Clone(path))
            return
        }
        for i := range nums {
            if used[i] {
                continue
            }
            // ⭐ 关键：同一层里，若前一个相同元素还没被用，说明我们正处在
            //    "跳过前一个、直接用后一个" 的分支上 —— 它与之前的分支重复
            if i > 0 && nums[i] == nums[i-1] && !used[i-1] {
                continue
            }
            used[i] = true
            path = append(path, nums[i])
            dfs()
            path = path[:len(path)-1]
            used[i] = false
        }
    }
    dfs()
    return res
}
```

**为什么条件是 `!used[i-1]` 而不是 `used[i-1]`？**

考虑 `[1, 1']`（两个相同的 1）。我们希望**只允许按下标顺序使用相同元素**，即只有 `1` 已被用时才允许用 `1'`：

```
!used[i-1]  ⟹  前一个 1 没被用，当前却要用 1'  ⟹  这是"跳过 1 用 1'"的分支
                这与"用 1 跳过 1'"的分支产生完全相同的排列 ⟹ 剪掉  ✓

used[i-1]   ⟹  前一个 1 已在路径中，现在用 1' 是合法的"两个都用" ⟹ 保留
```

⚠️ 写成 `used[i-1]` 会剪掉合法分支，得到**偏少**的结果；不写这个判断会得到**重复**的结果。**两种错误都不会报错，只会给出错误答案**——所以必须理解它，而不是背它。

### 复杂度

| 形态 | 解的数量 | 复杂度 |
|---|---|---|
| 子集 | 2ⁿ | Θ(n·2ⁿ)（每个解要拷贝 O(n)） |
| 排列 | n! | Θ(n·n!) |
| 组合 C(n,k) | C(n,k) | Θ(k·C(n,k)) |

⭐ **输出规模本身就是指数级的，所以这个复杂度不可能改进**——除非题目只要求**计数**而非枚举，那往往可以用 DP 降到多项式。**"要枚举"和"要计数"是完全不同难度的两个问题**，看清楚题目问的是哪个。

---

## 四、N 皇后

> 在 n×n 棋盘上放 n 个皇后，使任意两个不在同一行、列或对角线上。

**关键建模**：每行恰好放一个皇后 ⟹ 解就是一个排列，状态只需记录"每列/每条对角线是否被占"。

```go
func SolveNQueens(n int) int {
    cols := make([]bool, n)
    diag1 := make([]bool, 2*n) // ↘ 方向：row - col + n 恒定
    diag2 := make([]bool, 2*n) // ↙ 方向：row + col 恒定
    count := 0

    var dfs func(row int)
    dfs = func(row int) {
        if row == n {
            count++
            return
        }
        for col := 0; col < n; col++ {
            d1, d2 := row-col+n, row+col
            if cols[col] || diag1[d1] || diag2[d2] {
                continue // ⭐ 剪枝：这一格被攻击
            }
            cols[col], diag1[d1], diag2[d2] = true, true, true
            dfs(row + 1)
            cols[col], diag1[d1], diag2[d2] = false, false, false // 撤销
        }
    }
    dfs(0)
    return count
}
```

⭐ **两条对角线的编号方式值得记住**：`↘` 上 `row - col` 恒定（加 n 避免负数），`↙` 上 `row + col` 恒定。**把二维约束降成一维数组查表，是把 O(n) 的冲突检测变成 O(1) 的标准手法。**

### 位运算版本

n ≤ 32 时，用三个整数代替三个数组，快一个数量级：

```go
func SolveNQueensBits(n int) int {
    count := 0
    full := (1 << n) - 1

    var dfs func(cols, d1, d2 int)
    dfs = func(cols, d1, d2 int) {
        if cols == full {
            count++
            return
        }
        // ⭐ 一次算出所有可放位置：取反后的空位
        avail := full &^ (cols | d1 | d2)
        for avail != 0 {
            p := avail & (-avail) // 取最低位的 1（第 20 讲的 lowbit）
            avail ^= p            // 用掉它
            dfs(cols|p, (d1|p)<<1&full, (d2|p)>>1)
            //          ↑ 对角线随行数下移而平移
        }
    }
    dfs(0, 0, 0)
    return count
}
```

**这段代码是位运算枚举的范本**：`avail & (-avail)` 取最低位的 1、`avail ^= p` 消掉它——[第 32 讲]({{< ref "32-dynamic-programming-2.md" >}})状压 DP 用的是同一套技巧。

**规模感**：n = 8 有 92 个解，n = 15 有 2 279 184 个，**n = 27 至今仍是被完整求解的最大规模**（2016 年，用了超算集群）。⭐ **这说明剪枝再好，指数增长仍然是指数增长——剪枝改变的是常数和可行规模，不是复杂度类。**

---

## 五、剪枝：把指数削小的四种手段

**剪枝是回溯的全部价值所在。** 没有剪枝，回溯就只是朴素穷举。

### ① 可行性剪枝（constraint propagation）

一旦发现当前部分解已经违反约束，立即返回。N 皇后里的 `cols[col] || diag1 || diag2` 就是。

**更强的版本是约束传播**：数独求解中，填入一个数后立即更新所有相关格子的候选集，若某格候选集为空则立刻回溯。⭐ **这比"填完再检查"能提前几十层剪掉整棵子树。**

### ② 最优性剪枝（bound pruning）

求最优解时，若"当前代价 + 剩余部分的**乐观估计**" 已经不优于已找到的最优解，剪掉。

```go
if curCost + optimisticBound(remaining) >= best {
    return // 这条分支不可能更优
}
```

⚠️ **`optimisticBound` 必须是真正的下界（不能高估）**，否则会剪掉最优解。这与 [A\* 的可采纳启发式]({{< ref "25-single-source-shortest-paths.md" >}})是**同一个条件**。

### ③ 搜索顺序启发（ordering heuristics）

⭐ **这一条常常是效果最好的，也最容易被忽略。**

```
最受约束变量优先（MRV）：先处理候选最少的位置 ⟹ 尽早触发冲突，尽早剪枝
最少约束值优先（LCV）：  优先尝试对其他变量限制最小的取值
```

**数独求解中，"总是先填候选数最少的格子"通常带来 10–100 倍加速**——比任何代码微优化都有效。直觉：**尽早失败比晚失败好**，因为失败得越早，剪掉的子树越大。

### ④ 对称性破除（symmetry breaking）

若解空间存在对称，只搜索其中一个代表。N 皇后中第一行只需搜索左半边（右半边的解由镜像得到），**直接减半**。

### 剪枝的效果

| 手段 | 典型收益 |
|---|---|
| 可行性剪枝 | 数量级 |
| 约束传播 | 数量级 |
| **搜索顺序启发** | **常常是最大的一项** |
| 最优性剪枝（界越紧越好） | 数量级 |
| 对称性破除 | 常数倍（2×、4×、8×） |

⚠️ **剪枝本身也有代价**。一个需要 O(n²) 计算的"更聪明的界"，可能不如一个 O(1) 的粗糙界跑得快。**必须实测，不能靠推理。**

---

## 六、分支限界

**分支限界（branch and bound）= 回溯 + 最优性剪枝 + 更聪明的搜索顺序。**

| | 回溯 | 分支限界 |
|---|---|---|
| 搜索顺序 | **深度优先**（栈） | **最优优先**（优先队列，按界排序） |
| 目标 | 找所有解 / 任一解 | **找最优解** |
| 内存 | O(深度) | 可能 O(指数) |

```go
// 0-1 背包的分支限界：优先展开"乐观估计最大"的节点
type node struct {
    level, value, weight int
    bound                float64 // 乐观上界：用分数背包松弛计算
}

func knapsackBB(items []Item, W int) int {
    // 按单位价值降序排列，使分数背包松弛成为有效上界
    slices.SortFunc(items, func(a, b Item) int {
        return cmp.Compare(b.Value*a.Weight, a.Value*b.Weight)
    })
    pq := &nodeHeap{} // 最大堆，按 bound 排序
    heap.Push(pq, &node{level: -1, bound: fracBound(items, W, -1, 0, 0)})
    best := 0

    for pq.Len() > 0 {
        u := heap.Pop(pq).(*node)
        if u.bound <= float64(best) {
            continue // ⭐ 上界已不优于现有解，整棵子树剪掉
        }
        i := u.level + 1
        if i >= len(items) {
            continue
        }
        // 分支 1：取第 i 件
        if w := u.weight + items[i].Weight; w <= W {
            v := u.value + items[i].Value
            best = max(best, v)
            if b := fracBound(items, W, i, v, w); b > float64(best) {
                heap.Push(pq, &node{i, v, w, b})
            }
        }
        // 分支 2：不取第 i 件
        if b := fracBound(items, W, i, u.value, u.weight); b > float64(best) {
            heap.Push(pq, &node{i, u.value, u.weight, b})
        }
    }
    return best
}
```

⭐ **这里的上界用[第 30 讲]({{< ref "30-greedy-algorithms.md" >}})的分数背包贪心计算**——分数背包是 0-1 背包的**松弛（relaxation）**，它的最优解必然 ≥ 0-1 背包的最优解，因此是一个合法的乐观界。

> **"松弛出一个界，用界来剪枝"是整个组合优化领域的核心套路。** 现代 ILP 求解器（Gurobi、CPLEX）的骨架就是**分支限界 + 线性规划松弛**，它们能求解百万变量的实例，靠的正是这个。这也回答了[第 34 讲]({{< ref "34-np-completeness.md" >}})的问题：为什么 NP-难问题在实践中常常可解。

### 与 A* 的关系

⭐ **A\***（[第 25 讲]({{< ref "25-single-source-shortest-paths.md" >}})）**就是分支限界在最短路问题上的特例**：

```
分支限界的 "界"          ≙  A* 的 f(v) = g(v) + h(v)
"界必须乐观（不高估）"    ≙  h 必须可采纳（admissible）
"按界排序展开"           ≙  优先队列按 f 排序
```

两者是同一个思想在不同问题上的化身。

---

## 七、三种范式的统一视角

回到开头那张图，现在可以说得更精确：

| | 回溯 | 贪心 | DP |
|---|---|---|---|
| 走解空间树的方式 | **全走，靠剪枝** | **只走一条枝** | **全走，靠记忆化** |
| 正确性靠什么 | 穷举的完备性 | **交换论证**（[第 30 讲]({{< ref "30-greedy-algorithms.md" >}})） | **最优子结构 + 重叠子问题** |
| 复杂度 | 指数（剪枝后常可用） | 通常 O(n log n) | 状态数 × 转移代价 |
| 失败的表现 | 太慢 | **给出错误答案** | 状态设计不出来 |

⭐ **注意最后一行**：**贪心失败时会静悄悄地给出错误答案，而回溯失败只是慢。** 这就是为什么没有证明的贪心是危险的，而回溯至少是**安全**的。

**实用的解题顺序**：

```
① 先写回溯（保证正确）
② 看子问题是否重叠 ──▶ 是：加 memo，变成 DP
                    └─▶ 否：找剪枝，或找贪心策略（但必须证明）
```

⭐ **这条路径在工程和面试中都极其有用**：先得到一个**正确但慢**的版本，再有依据地优化——而不是一上来猜一个贪心策略然后祈祷它对。

---

## 八、什么时候该用回溯

| 场景 | 说明 |
|---|---|
| **要枚举所有解** | 子集、排列、组合、划分 |
| **约束满足问题（CSP）** | 数独、图着色、八皇后、时间表排课 |
| **搜索空间小或剪枝强** | n ≤ 20 左右的精确求解 |
| **NP-难问题的精确解** | 配合分支限界，[第 34 讲]({{< ref "34-np-completeness.md" >}})的出路之一 |
| **没有更好的办法** | 诚实地承认这一点也是一种能力 |

⚠️ **不该用的场景**：子问题明显重叠（该用 DP）、有可证明的贪心策略、或规模大到剪枝也救不了（该转向近似或启发式）。

> **一个现实的提醒**：真正的工业级 CSP 求解不会手写回溯，而是把问题编码成 **SAT** 或 **ILP**，交给成熟求解器。手写回溯的价值在于**理解机制**，以及处理那些不方便编码成标准形式的问题。

---

## 随堂自测

1. 回溯的三要素是什么？为什么"撤销"这一步不能省略？
2. Go 中保存回溯结果时为什么必须 `slices.Clone(path)`？不拷贝会出现什么症状？
3. 子集枚举用 `start` 参数、排列枚举用 `used` 数组，为什么不能反过来？
4. 含重复元素的排列去重条件是 `!used[i-1]`，为什么不是 `used[i-1]`？分别会导致什么错误？
5. N 皇后中两条对角线如何编号成一维数组下标？这把什么复杂度降成了什么？
6. 位运算版 N 皇后中，`avail & (-avail)` 和 `(d1|p)<<1` 各是什么含义？
7. 剪枝的四种手段是什么？哪一种在实践中收益往往最大，为什么？
8. 最优性剪枝的界为什么必须是"乐观"的？这与 A* 的哪个条件对应？
9. 分支限界与回溯的两个区别是什么？0-1 背包的上界为什么可以用分数背包算？
10. 说明"DP 是回溯 + 记忆化"。给出一个先写回溯再转 DP 的例子。
11. 贪心失败和回溯失败的表现有什么本质不同？这对解题顺序有什么启示？

