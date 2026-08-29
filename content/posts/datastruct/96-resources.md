---
title: "复杂度速查表与参考资料"
date: 2026-08-28
weight: 96
tags: ["数据结构与算法"]
draft: false
summary: "一页纸的复杂度对照表（数据结构、排序、图算法）、选型决策树、Go 标准库对应关系，以及教材、公开课、经典论文与在线资源清单。"
showToc: true
tocOpen: true
---

## 一、数据结构复杂度速查

### 字典 / 集合

| 结构 | 查找 | 插入 | 删除 | 有序操作 | 空间 | 备注 |
|---|---|---|---|---|---|---|
| 无序数组 | O(n) | O(1) | O(n) | ✗ | O(n) | |
| **有序数组 + 二分** | **O(log n)** | O(n) | O(n) | **✓** | O(n) | ⭐ 读多写少时常打败平衡树：零指针开销、缓存最优、可 mmap（第 14 讲） |
| **散列表（链地址）** | **期望 O(1)** | 期望 O(1) | 期望 O(1) | ✗ | O(n) | 最坏 O(n) |
| **散列表（开放寻址）** | 期望 1/(1−α) | 期望 | 期望 + 墓碑 | ✗ | O(n) | 缓存最优 |
| Cuckoo 散列 | **最坏 O(1)** | 期望 O(1) | **最坏 O(1)** | ✗ | O(n) | α ≤ 0.5 |
| BST（无平衡） | O(h) | O(h) | O(h) | ✓ | O(n) | h 最坏 n |
| **AVL 树** | **O(log n)** | O(log n) | O(log n) | ✓ | O(n) | h ≤ 1.44 log n |
| **红黑树** | **O(log n)** | O(log n) | O(log n) | ✓ | O(n) | 删除旋转 ≤ 3 |
| **B / B+ 树** | O(log_t n) | O(log_t n) | O(log_t n) | **✓** | O(n) | **磁盘与缓存友好** |
| **跳表** | 期望 O(log n) | 期望 O(log n) | 期望 O(log n) | ✓ | O(n) | 实现简单、并发友好 |
| Treap | 期望 O(log n) | 期望 O(log n) | 期望 O(log n) | ✓ | O(n) | 有 split/merge |
| 伸展树 | 摊还 O(log n) | 摊还 | 摊还 | ✓ | O(n) | 工作集性质 |
| **Trie** | O(L) | O(L) | O(L) | **前缀 ✓** | O(总字符×Σ) | L = 串长 |
| 布隆过滤器 | O(k) | O(k) | ✗ | ✗ | **1.2 B/元素** | 有假阳性 |

### 序列

| 结构 | 按下标访问 | 头部插删 | 尾部插删 | 中间插删（已知位置） | 空间开销 |
|---|---|---|---|---|---|
| 静态数组 | **Θ(1)** | Θ(n) | Θ(1) | Θ(n) | 0 |
| **动态数组** | **Θ(1)** | Θ(n) | **Θ(1) 摊还** | Θ(n) | ≤ n |
| 单链表 | Θ(n) | Θ(1) | Θ(1) | Θ(1)* | n 指针 |
| **双链表** | Θ(n) | **Θ(1)** | **Θ(1)** | **Θ(1)** | 2n 指针 |
| 环形缓冲 | Θ(1) | **Θ(1)** | **Θ(1)** | Θ(n) | ≤ n |
| 分块链表 | Θ(√n) | Θ(√n) | Θ(√n) | Θ(√n) | O(n) |
| **平衡树序列（rope）** | **Θ(log n)** | Θ(log n) | Θ(log n) | **Θ(log n)** | O(n) |

\* 需持有前驱节点指针

### 优先队列

| 结构 | Push | Pop-min | Peek | DecreaseKey | Meld |
|---|---|---|---|---|---|
| 无序数组 | O(1) | O(n) | O(n) | O(1) | O(1) |
| **二叉堆** | **O(log n)** | **O(log n)** | **O(1)** | O(log n) | O(n) |
| d 叉堆（d=4） | O(log_d n) | O(d log_d n) | O(1) | O(log_d n) | O(n) |
| 配对堆 | O(1) | O(log n)* | O(1) | o(log n)* | **O(1)** |
| Fibonacci 堆 | **O(1)*** | O(log n)* | O(1) | **O(1)*** | **O(1)*** |

\* 摊还。⚠️ Fibonacci 堆常数极大，实测常输给 4 叉堆。

---

## 二、排序算法速查

| 算法 | 最好 | 平均 | 最坏 | 空间 | 稳定 | 备注 |
|---|---|---|---|---|---|---|
| 插入排序 | **Θ(n)** | Θ(n²) | Θ(n²) | O(1) | ✓ | Θ(n+I)，小数组最快 |
| 选择排序 | Θ(n²) | Θ(n²) | Θ(n²) | O(1) | ✗ | 交换次数最少（n−1） |
| 冒泡排序 | Θ(n) | Θ(n²) | Θ(n²) | O(1) | ✓ | 无实用价值 |
| **归并排序** | Θ(n log n) | **Θ(n log n)** | **Θ(n log n)** | Θ(n) | **✓** | 外排序、并行首选 |
| **快速排序** | Θ(n log n) | **Θ(n log n)** | Θ(n²) | O(log n) | ✗ | **常数最小，缓存最优** |
| **堆排序** | Θ(n log n) | Θ(n log n) | **Θ(n log n)** | **O(1)** | ✗ | 唯一"原地+最坏 n log n" |
| Timsort | **Θ(n)** | Θ(n log n) | Θ(n log n) | Θ(n) | **✓** | 真实数据上极快 |
| introsort | Θ(n log n) | Θ(n log n) | **Θ(n log n)** | O(log n) | ✗ | 快排 + 堆排兜底 |
| 计数排序 | Θ(n+k) | Θ(n+k) | Θ(n+k) | Θ(n+k) | ✓ | 键须是小整数 |
| **基数排序** | Θ(d(n+r)) | Θ(d(n+r)) | Θ(d(n+r)) | Θ(n+r) | ✓ | 定长键，实测快 2–4 倍 |
| 桶排序 | Θ(n) | **Θ(n)** | Θ(n²) | Θ(n) | 取决于 | 依赖均匀分布 |

**下界**：比较排序最坏 **Ω(n log n)**（决策树 + Stirling）。

---

## 三、图算法速查

| 问题 | 算法 | 复杂度 | 条件 |
|---|---|---|---|
| 遍历 | BFS / DFS | Θ(V+E) | — |
| **无权最短路** | BFS | **Θ(V+E)** | 边权相等 |
| 边权 ∈{0,1} 最短路 | 0-1 BFS | **Θ(V+E)** | — |
| **DAG 最短/最长路** | 拓扑序松弛 | **Θ(V+E)** | DAG，可负权 |
| **非负权最短路** | Dijkstra + 二叉堆 | O(E log V) | 非负权 |
| 非负权最短路（稠密） | Dijkstra + 数组 | **O(V²)** | 非负权 |
| **负权最短路 / 负环检测** | Bellman-Ford | O(V·E) | — |
| 有目标点 + 好启发式 | A\* | 实践远快 | h 可采纳 |
| **全源（稠密）** | Floyd-Warshall | **Θ(V³)** | 可负权 |
| **全源（稀疏）** | Johnson | O(V·E log V) | 可负权 |
| 传递闭包 | Warshall + bitset | Θ(V³/64) | — |
| **MST（稀疏）** | Kruskal | O(E log E) | — |
| MST（稠密） | Prim + 数组 | **O(V²)** | — |
| MST（并行/分布式） | Borůvka | O(E log V) | — |
| 拓扑排序 | DFS / Kahn | Θ(V+E) | DAG |
| **强连通分量** | Tarjan | **Θ(V+E)** | — |
| 割点 / 桥 | Tarjan 变体 | Θ(V+E) | — |
| 动态连通性（只加边） | 并查集 | O(α(V)) / 操作 | — |
| **最大流** | Dinic | O(V²E) | — |
| **二分匹配** | Dinic / Hopcroft-Karp | **O(E√V)** | 二分图 |
| 一般图最大匹配 | 带花树（Blossom） | O(V³) | — |
| 最小费用最大流 | SPFA 增广 | O(V·E·f) | — |

---

## 三·五、搜索与枚举速查

| 问题 | 方法 | 复杂度 |
|---|---|---|
| 有序序列定位 | 二分查找 / `slices.BinarySearch` | Θ(log n) |
| 前驱 / 后继 / 计数 / 范围 | `LowerBound` + `UpperBound` | Θ(log n) |
| **最小化最大值 / 最大化最小值** | **二分答案 + 线性判定** | Θ(n·log 值域) |
| 旋转有序数组查找 | 变体二分（判断哪半有序） | Θ(log n)，有重复时最坏 Θ(n) |
| 寻找峰值（无序） | 二分（靠"能排除一半"而非有序） | Θ(log n) |
| 实数域最优值 | 固定迭代 100 次的实数二分 | Θ(100·判定代价) |
| 枚举所有子集 | 回溯 + `start` | Θ(n·2ⁿ) |
| 枚举所有排列 | 回溯 + `used` | Θ(n·n!) |
| 约束满足（数独、N 皇后） | 回溯 + 剪枝（MRV 启发） | 指数，剪枝后常可用 |
| **NP-难问题求精确最优解** | **分支限界 + 松弛界** | 指数，实践常可解 |
| 状态空间最短路 | BFS / A\* | Θ(V+E) |

⭐ **二分的真正前提是"能安全排除一半"，不是"有序"**；**回溯的价值全在剪枝**，没有剪枝它只是朴素穷举。

---

## 四、选型决策树

### 我需要一个"存 key-value"的结构

```
需要按 key 顺序遍历、范围查询、前驱后继吗？
├─ 否 ──▶ 散列表（Go: map）
│         └─ 需要最坏 O(1) 查找？ ──▶ Cuckoo 散列
│         └─ 只需要"存不存在"且能容忍误判？ ──▶ 布隆过滤器
└─ 是 ──▶ 数据在磁盘/SSD 上吗？
          ├─ 是 ──▶ 写多？ ──▶ LSM 树      读多？ ──▶ B+ 树
          └─ 否 ──▶ 需要并发？ ──▶ 跳表
                    需要 split/merge 或区间操作？ ──▶ Treap
                    追求最快查找？ ──▶ B 树（缓存友好）或 AVL
                    只是要个能用的？ ──▶ 有序切片 + 二分（读多写少）
```

### 我需要"最短路"

```
边权都相等？ ──▶ BFS（Θ(V+E)）
边权 ∈{0,1}？ ──▶ 0-1 BFS（Θ(V+E)）
图是 DAG？ ──▶ 拓扑序松弛（Θ(V+E)，还能求最长路）
有负权？ ──▶ Bellman-Ford / SPFA（O(V·E)）
知道目标点且有好的距离估计？ ──▶ A*
否则 ──▶ Dijkstra（稀疏用堆，稠密用数组）
```

### 我要在一堆可能里"找最优"

```
能写出"给定候选值 v，判断 v 可行吗"且可行性单调？ ──▶ 二分答案（Θ(n log 值域)）
子问题重叠？ ──▶ 动态规划
有可证明的贪心策略（写得出交换论证）？ ──▶ 贪心
以上都不行，规模又不大（n ≲ 20–40）？ ──▶ 回溯 + 剪枝 / 分支限界
规模大且是 NP-难？ ──▶ 近似算法 / 启发式 / 编码成 SAT 或 ILP 交给求解器
```

### 我要"排序"

```
需要稳定？ ──▶ slices.SortStableFunc（Timsort/归并）
键是小整数或定长？ ──▶ 计数 / 基数排序（快 2–4 倍）
数据放不进内存？ ──▶ 外部归并排序
只要前 k 个？ ──▶ 流式用堆（Θ(n log k)），内存中用快速选择（期望 Θ(n)）
否则 ──▶ slices.Sort（pdqsort）
```

---

## 五、Go 标准库对应关系

| 概念 | Go 中的对应 | 备注 |
|---|---|---|
| 动态数组 | `[]T` + `append` | 内建倍增策略 |
| 散列表 | `map[K]V` | 渐进式 rehash、随机种子、**遍历顺序随机** |
| 有序 map | ⚠️ **无内建** | 用 `github.com/google/btree`、`tidwall/btree` 或自己实现跳表 |
| 双链表 | `container/list` | 实践中多用 slice |
| 堆 / 优先队列 | `container/heap` | 接口 + 算法；⚠️ 用 `heap.Push` 而非 `h.Push` |
| 排序（不稳定） | `slices.Sort` / `sort.Slice` | pdqsort |
| **排序（稳定）** | `slices.SortStableFunc` / `sort.SliceStable` | 插入 + 原地归并 |
| **二分查找** | `slices.BinarySearch` / `sort.Search` | `slices.BinarySearch` 返回的就是 lower_bound；`sort.Search` 找第一个使谓词为 true 的下标，⚠️ **谓词必须单调**（第 14 讲） |
| 字符串查找 | `strings.Index` / `Contains` | 已高度优化，别自己写 |
| 大整数 | `math/big` | 自动在朴素/Karatsuba/Toom-Cook 间切换 |
| 位运算 | `math/bits` | `OnesCount`（POPCNT）、`TrailingZeros`、`Len`；`x & (-x)` 取 lowbit，用于状压 DP 与位运算 N 皇后 |
| 队列（跨 goroutine） | `chan T` | 本质是环形缓冲 + 锁；单线程算法别用它 |
| 散列函数 | `hash/fnv`、`hash/maphash` | `maphash` 带随机种子，抗碰撞攻击 |

---

## 六、教材

**主教材**

- **Cormen, Leiserson, Rivest & Stein.** *Introduction to Algorithms*, 4th Edition (2022). MIT Press. —— 通称 **CLRS**，最标准的参考，证明完整，适合查阅甚于通读。
- **Sedgewick & Wayne.** *Algorithms*, 4th Edition (2011). —— 实现视角，代码清晰，红黑树（LLRB）和图算法讲得特别好。配套网站有大量可视化。

**进阶与补充**

- **Kleinberg & Tardos.** *Algorithm Design* (2005). —— **算法设计思路**讲得最好的一本，尤其是贪心的交换论证和网络流建模。
- **Erickson, Jeff.** *Algorithms* (2019). —— **免费开放**（jeffe.cs.illinois.edu/teaching/algorithms/），写作风格幽默，递归和 DP 部分极佳。
- **Dasgupta, Papadimitriou & Vazirani.** *Algorithms*. —— 薄，适合快速通读。
- **Skiena.** *The Algorithm Design Manual*, 3rd Edition. —— 第二部分是一本"问题→算法"的字典，工程实用性最强。
- **Knuth.** *The Art of Computer Programming*, Vol. 1–4. —— 不是用来读完的，是用来查的。
- **Tarjan.** *Data Structures and Network Algorithms* (1983). —— 摊还分析的经典论述。

**理论方向**

- **Arora & Barak.** *Computational Complexity: A Modern Approach*. —— 复杂性理论标准教材。
- **Garey & Johnson.** *Computers and Intractability* (1979). —— NP-完全问题的经典目录，附录列了几百个 NPC 问题。
- **Williamson & Shmoys.** *The Design of Approximation Algorithms*. —— **免费**，近似算法标准教材。
- **Motwani & Raghavan.** *Randomized Algorithms*. —— 随机化算法。

---

## 七、公开课

| 课程 | 说明 |
|---|---|
| **MIT 6.006** Introduction to Algorithms | 本科入门，OCW 有全部视频与讲义 |
| **MIT 6.046J** Design and Analysis of Algorithms | 进阶，Erik Demaine 主讲，分治/随机化/近似 |
| **MIT 6.851** Advanced Data Structures | 高级数据结构（可持久化、缓存无关、位技巧） |
| **Princeton COS 226** Algorithms | Sedgewick 主讲，Coursera 上有，实现导向 |
| **Stanford CS161** Design and Analysis of Algorithms | Tim Roughgarden 的版本讲得极清楚 |
| **Berkeley CS170** Efficient Algorithms | 讲义质量高 |
| **CMU 15-451/651** Algorithm Design and Analysis | 讲义深度好 |

---

## 八、经典论文

| 主题 | 论文 |
|---|---|
| 摊还分析 | Tarjan, *Amortized Computational Complexity* (1985) |
| 并查集 | Tarjan, *Efficiency of a Good But Not Linear Set Union Algorithm* (1975) |
| 并查集下界 | Fredman & Saks, *The Cell Probe Complexity of Dynamic Data Structures* (1989) |
| 红黑树 | Guibas & Sedgewick, *A Dichromatic Framework for Balanced Trees* (1978) |
| 左倾红黑树 | Sedgewick, *Left-Leaning Red-Black Trees* (2008) |
| B 树 | Bayer & McCreight (1972) |
| 跳表 | Pugh, *Skip Lists: A Probabilistic Alternative to Balanced Trees* (1990) |
| Treap | Seidel & Aragon, *Randomized Search Trees* (1996) |
| 伸展树 | Sleator & Tarjan, *Self-Adjusting Binary Search Trees* (1985) |
| Fibonacci 堆 | Fredman & Tarjan (1987) |
| 线性时间选择 | Blum, Floyd, Pratt, Rivest & Tarjan (1973) |
| 全域散列 | Carter & Wegman, *Universal Classes of Hash Functions* (1979) |
| Cuckoo 散列 | Pagh & Rodler (2004) |
| 一致性散列 | Karger et al. (1997) |
| 布隆过滤器 | Bloom (1970) |
| Strassen | Strassen, *Gaussian Elimination is not Optimal* (1969) |
| Karatsuba | Karatsuba & Ofman (1962) |
| 最大流最小割 | Ford & Fulkerson (1956) |
| Dinic | Dinitz (1970) |
| SCC | Tarjan, *Depth-First Search and Linear Graph Algorithms* (1972) |
| **NP 完全性** | Cook (1971); Karp, *Reducibility Among Combinatorial Problems* (1972) |
| 缓存无关 | Frigo, Leiserson, Prokop & Ramachandran (1999) |
| 整数乘法 O(n log n) | Harvey & van der Hoeven (2019) |

---

## 九、在线资源

| 资源 | 用途 |
|---|---|
| **VisuAlgo**（visualgo.net） | 数据结构与算法的交互式可视化，AVL/红黑树/图算法尤其好 |
| **Algorithm Visualizer** | 逐步执行动画 |
| **cp-algorithms.com** | 竞赛算法的完整实现与推导，中英文都有 |
| **OI Wiki**（oi-wiki.org） | 中文，覆盖极广，从基础到高级数据结构 |
| **Big-O Cheat Sheet**（bigocheatsheet.com） | 一页纸复杂度对照 |
| **LeetCode / Codeforces** | 练习；LeetCode 偏面试，Codeforces 偏算法深度 |
| **Go 标准库源码** | `src/sort/`、`src/runtime/map.go`、`src/container/` 都值得读 |

---

## 十、如何继续

**如果你想深入数据结构**：MIT 6.851（高级数据结构）——可持久化、缓存无关、字大小技巧、动态最优性猜想。

**如果你想深入算法理论**：近似算法（Williamson & Shmoys）、随机化算法（Motwani & Raghavan）、参数化复杂性（Cygan et al.）。

**如果你想往工程方向**：读真实系统的实现——Go runtime 的 map 和 scheduler、Redis 的 dict/ziplist/skiplist、LevelDB 的 skiplist 和 SSTable、Linux 内核的 rbtree 和 radix tree。**这些代码里的每一个决策都能在本课程中找到对应的理论依据**，反过来也会让你看到理论在哪里被现实修正。

**如果你只是想不忘掉**：每隔几个月回来扫一遍[术语表]({{< ref "95-glossary.md" >}})和本页的速查表，遇到不确定的就回去读对应讲次。

---

> 回到[课程首页]({{< ref "_index.md" >}})
