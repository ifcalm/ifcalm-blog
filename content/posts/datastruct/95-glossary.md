---
title: "术语表：英中对照与速查"
date: 2026-08-28
weight: 95
tags: ["数据结构与算法"]
draft: false
summary: "按主题组织的数据结构与算法术语表，中英对照，每条附一句话精确定义与所在讲次。用于查漏、反查和考前速览。"
showToc: true
tocOpen: true
---

> 📌 **怎么用这一页**：① 忘了某个词的意思时反查；② 考前从头扫一遍，看到不确定的就回去读对应讲次；③ 读英文教材和论文时对照。
> ⭐ 标记的是**本课程最核心的 40 个概念**。

---

## 一、分析工具

| 中文 | 英文 | 一句话定义 | 讲次 |
|---|---|---|---|
| ⭐ RAM 模型 | Random-Access Machine | 假设任意内存访问都是常数时间的计算模型 | 1 |
| ⭐ 循环不变式 | loop invariant | 每次迭代前后都成立的断言；用初始化/保持/终止三步证明正确性 | 1 |
| 变界函数 | variant | 每次迭代严格减小且有下界的量，用于证明停机 | 1 |
| ⭐ 抽象数据类型 | abstract data type (ADT) | 一组操作的**规范**（能做什么），与实现无关 | 1 |
| ⭐ 数据结构 | data structure | ADT 的一种**实现**（数据在内存里怎么摆） | 1 |
| ⭐ 大 O | big-O | 渐近**上界**：∃c,n₀，n≥n₀ 时 f(n) ≤ c·g(n) | 2 |
| ⭐ 大 Ω | big-Omega | 渐近**下界** | 2 |
| ⭐ 大 Θ | big-Theta | 渐近**紧确界**（同时是 O 和 Ω） | 2 |
| 小 o / 小 ω | little-o / little-omega | 严格上界 / 严格下界（lim f/g = 0 或 ∞） | 2 |
| 最坏情况 | worst case | 规模 n 的所有输入中的最大代价；本课程默认口径 | 1, 2 |
| 平均情况 | average case | 对**输入分布**求期望；假设不成立就失效 | 1, 11 |
| ⭐ 期望运行时间 | expected running time | 随机性来自**算法自己**，对任意输入成立 | 1, 11 |
| ⭐ 主定理 | Master Theorem | 求解 T(n)=aT(n/b)+f(n) 的三情形判据 | 3 |
| 递归树 | recursion tree | 画出各层代价来**猜**递归式的解 | 3 |
| 代换法 | substitution method | 猜一个界，再用数学归纳法证明 | 3 |
| ⭐ 摊还分析 | amortized analysis | 保证 n 个操作的**总**代价，不含任何概率 | 4 |
| 聚合法 | aggregate method | 直接算总代价再除以 n | 4 |
| 记账法 | accounting method | 给操作指定摊还代价，多收的存为信用 | 4 |
| ⭐ 势能法 | potential method | 用势能函数 Φ 度量"积攒的债"，ĉ = c + ΔΦ | 4 |
| ⭐ 滞后区 | hysteresis | 伸缩阈值留出余量以避免抖动（如收缩阈值取 capacity/4） | 4 |
| ⭐ 伪多项式时间 | pseudo-polynomial | 关于**数值**是多项式、关于**输入长度**是指数（如背包的 Θ(nW)） | 1, 31, 34 |

---

## 二、线性结构与散列

| 中文 | 英文 | 一句话定义 | 讲次 |
|---|---|---|---|
| ⭐ 动态数组 | dynamic array | 容量满时**几何增长**扩容，append 摊还 O(1) | 5 |
| ⭐ 哨兵节点 | sentinel | 不存数据的边界节点，用于消灭所有 if 分支 | 5 |
| ⭐ 缓存局部性 | cache locality | 连续内存访问远快于指针追逐；渐近分析看不见它 | 5, 18 |
| 指针追逐 | pointer chasing | 沿指针跳转访问，无法被硬件预取器预测 | 5 |
| ⭐ 环形缓冲 | circular buffer | 用取模实现两端 O(1) 的队列；⚠️ `s = s[1:]` 是错的 | 6 |
| ⭐ 单调栈 | monotonic stack | 维护单调性的栈，把"下一个更大元素"从 O(n²) 降到 O(n) | 6 |
| ⭐ 单调队列 | monotonic deque | 滑动窗口最值，Θ(n) | 6 |
| ⭐ 装填因子 | load factor (α) | n/m = 元素数 / 槽数 = 平均链长 | 7 |
| 链地址法 | chaining | 每槽挂一条链表，期望 Θ(1+α) | 7 |
| ⭐ 简单均匀散列假设 | SUHA | 每个键等概率落入任一槽；这是**假设**不是事实 | 7 |
| ⭐ 全域散列 | universal hashing | 从函数族中**随机**选 h，Pr[碰撞] ≤ 1/m；对任意输入成立 | 7 |
| ⭐ 散列洪水攻击 | hash flooding | 构造大量同散列值的键使表退化成链表（DoS） | 7 |
| 再散列 | rehash | 装填因子超阈值时扩容重插；摊还 O(1) | 7 |
| 开放寻址 | open addressing | 元素全存表内，槽被占就探查下一个；期望 1/(1−α) | 8 |
| 线性/二次/双重探查 | linear/quadratic/double probing | 三种探查序列，聚簇程度与缓存表现各异 | 8 |
| 一次聚簇 | primary clustering | 线性探查中连续占用块互相吞并 | 8 |
| ⭐ 墓碑 | tombstone | 开放寻址删除时的标记；不留会导致查找失败 | 8 |
| Robin Hood 散列 | Robin Hood hashing | 让 PSL 小的元素让位，削掉探查长尾 | 8 |
| ⭐ Cuckoo 散列 | cuckoo hashing | 两个位置二选一，查找/删除**最坏 O(1)** | 8 |
| ⭐ 一致性散列 | consistent hashing | 环状散列空间，增删节点只迁移 K/n 个键 | 8 |
| 虚拟节点 | virtual node | 每个物理节点在环上放 V 个副本以均衡负载 | 8 |
| ⭐ 布隆过滤器 | Bloom filter | 位数组 + k 个散列；无假阴性、有假阳性；1% 误判仅需 9.6 位/元素 | 8 |

---

## 三、排序与选择

| 中文 | 英文 | 一句话定义 | 讲次 |
|---|---|---|---|
| ⭐ 稳定排序 | stable sort | 相等元素的相对顺序保持；多关键字排序的基础 | 9 |
| 原地排序 | in-place | 额外空间 O(1) | 9 |
| 自适应 | adaptive | 输入近乎有序时更快（如插入排序 Θ(n+I)） | 9 |
| ⭐ 逆序对 | inversion | i<j 但 A[i]>A[j] 的下标对；插入排序的移动次数恰好等于它 | 9 |
| Timsort | Timsort | 扫出天然升序 run 再按栈规则合并；Python/Java 对象排序用它 | 9 |
| ⭐ 堆序性质 | heap property | 父节点 ≤（或 ≥）所有子节点；**不是全序** | 10 |
| 完全二叉树 | complete binary tree | 除最后一层外填满、最后一层左对齐；可无指针地压进数组 | 10 |
| ⭐ 下沉 / 上浮 | sift-down / sift-up | 堆的两个修复原语，各 O(log n) | 10 |
| ⭐ 建堆 | build-heap | 自底向上 siftDown，**Θ(n)** 而非 Θ(n log n) | 10 |
| 对顶堆 | two-heap | 最大堆 + 最小堆维护流式中位数 | 10 |
| Lomuto / Hoare 划分 | partition scheme | 两种快排划分；Lomuto 在全相等输入上退化 | 11 |
| ⭐ 随机化快排 | randomized quicksort | 随机选主元，期望 1.39 n log₂n，与输入无关 | 11 |
| ⭐ 三路划分 | 3-way partition | 荷兰国旗划分，k 个不同值时 Θ(n log k) | 11 |
| introsort | introsort | 快排 + 递归过深时切堆排序，最坏 Θ(n log n) | 11 |
| pdqsort | pattern-defeating quicksort | Go `slices.Sort` 用的快排加固版 | 11 |
| ⭐ 决策树模型 | decision tree model | 把比较排序画成二叉树，叶子 ≥ n! ⟹ 高 ≥ log(n!) | 12 |
| ⭐ 比较排序下界 | comparison sort lower bound | **Ω(n log n)**；只对"仅用比较"的算法成立 | 12 |
| 计数排序 | counting sort | Θ(n+k)，键须是 [0,k) 的整数；倒序遍历保证稳定 | 12 |
| ⭐ 基数排序 | radix sort | 按位分组，LSD 必须配稳定子排序 | 12 |
| 桶排序 | bucket sort | 期望 Θ(n)，依赖**均匀分布**假设 | 12 |
| ⭐ 顺序统计量 | order statistic | 第 k 小的元素 | 13 |
| ⭐ 快速选择 | quickselect | 只递归一侧的快排，期望 Θ(n) | 13 |
| ⭐ BFPRT / 中位数的中位数 | median of medians | 每 5 个一组取中位数，最坏 Θ(n)；组大小 5 使 1/5+7/10 < 1 | 13 |
| introselect | introselect | 快速选择 + BFPRT 兜底；`std::nth_element` 用它 | 13 |

---

## 四、二分与搜索树

| 中文 | 英文 | 一句话定义 | 讲次 |
|---|---|---|---|
| ⭐ 二分查找 | binary search | 有序序列上 O(log n) 定位；正确性依赖「区间开闭 + 循环条件 + 收缩方式」三者一致 | 14 |
| ⭐ lower_bound | lower_bound | 第一个 ≥ x 的下标；只记这一个模板即可派生前驱/后继/计数/范围 | 14 |
| ⭐ 二分答案 | binary search on the answer | 把最优化问题转成单调的判定问题再二分；⚠️ 必须论证单调性 | 14 |
| 单调谓词 | monotone predicate | `F…F T…T` 形式的判定序列；二分的真正前提（不是"有序"） | 14 |
| ⭐ 有序字典 | ordered dictionary | 在字典基础上支持 Min/Max/前驱/后继/范围查询 | 15 |
| ⭐ BST 性质 | BST property | 左子树**所有**键 ≤ 根 ≤ 右子树所有键；是**全局**条件 | 15 |
| 中序遍历 | in-order traversal | 左-根-右；在 BST 上给出升序序列 | 15 |
| 中序后继 | in-order successor | 大于 x 的最小键；删除两孩子节点时用它替换 | 15 |
| ⭐ 随机 BST | random BST | 随机插入序列建成的 BST，期望高度 4.311·ln n ≈ 2.99 log₂n | 15 |
| ⭐ 旋转 | rotation | O(1) 改变树形而**保持中序序列**，故保持 BST 性质 | 16 |
| ⭐ 平衡因子 | balance factor | AVL 中左右子树高度差，必须 ∈ {−1,0,+1} | 16 |
| ⭐ AVL 高度界 | — | h ≤ **1.44 log₂ n**，由斐波那契递推推出 | 16 |
| LL/LR/RL/RR | — | 插入失衡的四种情形；LR、RL 需双旋 | 16 |
| ⭐ 2-3-4 树 | 2-3-4 tree | 每节点 1–3 个键，**所有叶子同深度**；红黑树的原型 | 17 |
| ⭐ 黑高 | black-height | 到叶子路径上的黑节点数；红黑树规则 ⑤ 的核心 | 17 |
| ⭐ 红黑树高度界 | — | h ≤ **2 log₂(n+1)**；比 AVL 松但删除只需 ≤ 3 次旋转 | 17 |
| 左倾红黑树 | LLRB | 限定红链接只能左倾，插入修复只需三个 if | 17 |
| ⭐ 外存模型 | external memory / DAM model | 以块（大小 B）为传输单位，代价 = I/O 次数 | 18 |
| ⭐ B 树 | B-tree | 每节点 t−1 到 2t−1 个键，高 log_t n；10⁹ 条记录只需 4 次 I/O | 18 |
| 半满约束 | half-full constraint | 除根外每节点至少 t−1 个键，保证树高是 log_t n | 18 |
| ⭐ B+ 树 | B+ tree | 数据只在叶子 + 叶子链表相连 ⟹ 范围查询是顺序 I/O | 18 |
| 聚簇索引 / 回表 | clustered index / lookup | 主键索引叶子存整行；二级索引查完要再查主键索引 | 18 |
| 覆盖索引 | covering index | 查询列全在二级索引中，无需回表 | 18 |
| ⭐ LSM 树 | log-structured merge tree | 顺序写 + 后台 compaction，写多读少时优于 B+ 树 | 18 |
| 缓存无关 | cache-oblivious | 不知道 B 和 M 仍达到最优 I/O（van Emde Boas 布局） | 18 |
| ⭐ 跳表 | skip list | 随机层数的多级索引链表，期望 Θ(log n)；Redis、LevelDB 用它 | 19 |
| ⭐ Treap | treap | key 满足 BST 序、随机 priority 满足堆序；形状唯一 | 19 |
| ⭐ split / merge | — | Treap 的两个原语，可 O(log n) 摘出整个区间 | 19 |
| 伸展树 | splay tree | 每次访问把节点旋到根；摊还 O(log n)，有**工作集性质** | 19 |
| 工作集性质 | working-set property | 最近访问过的元素下次访问更快 | 19 |
| ⭐ 增强 | augmentation | 在树节点上存额外信息；要求它能由孩子 O(1) 推出 | 20 |
| ⭐ 顺序统计树 | order-statistic tree | 存子树大小，支持 Rank 和 Select | 20 |
| 区间树 | interval tree | 存子树最大右端点，O(log n) 查重叠区间 | 20 |
| ⭐ 树状数组 | Fenwick tree / BIT | `i&(-i)` 分块的前缀和结构，10 行代码，常数极小 | 20 |
| ⭐ 线段树 | segment tree | 每节点存区间聚合值；支持任意结合律运算与懒标记 | 20 |
| 懒标记 | lazy propagation | 区间修改时先打标记、访问子节点时才下推 | 20 |

---

## 五、图算法

| 中文 | 英文 | 一句话定义 | 讲次 |
|---|---|---|---|
| ⭐ 握手引理 | handshaking lemma | Σ deg(v) = 2E；保证遍历所有邻居是 Θ(V+E) | 21 |
| ⭐ 邻接表 | adjacency list | Θ(V+E) 空间；真实图几乎全是稀疏的，默认用它 | 21 |
| 邻接矩阵 | adjacency matrix | Θ(V²) 空间，查边 Θ(1)；稠密图或 Floyd-Warshall 用 | 21 |
| ⭐ BFS | breadth-first search | 队列逐层扩展，求**无权最短路**；必须入队时标记 | 21 |
| 最短路径树 | shortest path tree | BFS/Dijkstra 的 parent 数组构成的树 | 21 |
| 二分图 | bipartite graph | 可 2-染色 ⟺ 不含奇环 | 21 |
| 隐式图 | implicit graph | 顶点是状态、边是操作，图从不显式建出 | 21 |
| 0-1 BFS | — | 边权 ∈{0,1} 时用双端队列，Θ(V+E) | 21 |
| ⭐ DFS | depth-first search | 栈/递归一路到底再回溯；求**结构**信息 | 22 |
| ⭐ 括号定理 | parenthesis theorem | 两个顶点的 [disc,fin] 区间要么不交要么包含 | 22 |
| ⭐ 后向边 | back edge | 指向**灰色**（递归栈上）顶点的边 ⟺ 存在环 | 22 |
| ⭐ 拓扑序 | topological order | DAG 的线性排列，每条边都从前指向后 | 22 |
| Kahn 算法 | Kahn's algorithm | 反复取入度 0 的顶点；也是并行调度器的骨架 | 22 |
| ⭐ 强连通分量 | strongly connected component (SCC) | 互相可达的极大顶点集 | 22 |
| ⭐ 凝聚图 | condensation graph | 把每个 SCC 缩成一点，**结果一定是 DAG** | 22 |
| Kosaraju | Kosaraju's algorithm | 两遍 DFS + 反图 | 22 |
| ⭐ Tarjan (SCC) | Tarjan's algorithm | 一遍 DFS + low-link；⚠️ 后向边用 disc 而非 low | 22 |
| ⭐ 并查集 | disjoint-set / union-find | 只回答"是否在一起"；按秩合并 + 路径压缩 ⟹ O(α(n)) | 23 |
| 按秩/按大小合并 | union by rank/size | 矮树挂到高树下，树高 O(log n) | 23 |
| ⭐ 路径压缩 | path compression | Find 时把路径上所有点直接挂到根 | 23 |
| 反 Ackermann 函数 | inverse Ackermann α(n) | 对一切实际的 n 都 ≤ 4；但不是 O(1)（有下界） | 23 |
| ⭐ 割性质 | cut property | 任意割的最小横跨边属于某棵 MST | 24 |
| 环性质 | cycle property | 任意环的最大边不属于任何 MST | 24 |
| ⭐ 交换论证 | exchange argument | 把最优解逐步改造成贪心解而不变差；贪心正确性的主力工具 | 24, 30 |
| Kruskal | Kruskal's algorithm | 按边权排序 + 并查集判环；O(E log E) | 24 |
| Prim | Prim's algorithm | 每次拉入离树最近的顶点；与 Dijkstra 结构相同 | 24 |
| Borůvka | Borůvka's algorithm | 每轮每个连通块选最小出边，O(log V) 轮，天然并行 | 24 |
| 最小瓶颈路 | minimum bottleneck path | 路径最大边权最小；就是 MST 上的路径 | 24 |
| ⭐ 松弛 | relaxation | "经过 u 更近就更新"；所有最短路算法的原子操作 | 25 |
| ⭐ 最优子结构 | optimal substructure | 最优解的子路径也是最优的 | 25, 30, 31 |
| ⭐ Dijkstra | Dijkstra's algorithm | 按 dist 递增确定顶点；**必须非负权** | 25 |
| ⭐ Bellman-Ford | Bellman-Ford | 所有边松弛 V−1 轮；可负权、可测负环，O(V·E) | 25 |
| SPFA | SPFA | Bellman-Ford 的队列优化；平均快但最坏仍 O(V·E) | 25 |
| A\* | A-star | key = g(v) + h(v)；h 可采纳则最优，h≡0 时退化为 Dijkstra | 25 |
| 可采纳 / 一致 | admissible / consistent | h 从不高估 / h 满足三角不等式 | 25 |
| ⭐ Floyd-Warshall | Floyd-Warshall | `d[k][i][j]` 中间点只用 {1..k}；⚠️ **k 必须最外层** | 26 |
| 传递闭包 | transitive closure | 可达性矩阵；bitset 优化到 Θ(V³/64) | 26 |
| ⭐ 重赋权 | reweighting | `ŵ = w + h(u) − h(v)`，望远镜求和使最短路不变 | 26 |
| Johnson | Johnson's algorithm | Bellman-Ford 求势能 + V 次 Dijkstra；稀疏图最优 | 26 |
| ⭐ 残量网络 | residual network | 含**反向边**，让算法能"后悔" | 27 |
| 增广路 | augmenting path | 残量网络中 s→t 的路径 | 27 |
| ⭐ 最大流最小割定理 | max-flow min-cut theorem | 最大流值 = 最小割容量；线性规划对偶的图论化身 | 27 |
| Edmonds-Karp | Edmonds-Karp | BFS 找最短增广路，O(V·E²)，与容量无关 | 27 |
| ⭐ Dinic | Dinic's algorithm | 分层图 + 阻塞流；单位容量图上 O(E√V)，实践首选 | 27 |
| ⭐ König 定理 | König's theorem | 二分图中最大匹配 = 最小顶点覆盖 | 27 |
| 拆点 | vertex splitting | v → v_in/v_out，用于给顶点加容量限制 | 27 |

---

## 六、算法设计范式与复杂性

| 中文 | 英文 | 一句话定义 | 讲次 |
|---|---|---|---|
| ⭐ 分治 | divide and conquer | 分解-解决-合并；要求子问题**不重叠** | 28 |
| Karatsuba | Karatsuba algorithm | 用加减省一次乘法，Θ(n^1.585) | 28 |
| ⭐ Strassen | Strassen algorithm | 7 次乘法代替 8 次，Θ(n^2.807) | 28 |
| 快速幂 | fast exponentiation | 反复平方，Θ(log n)；矩阵版可加速任意线性递推 | 28 |
| FFT | fast Fourier transform | 系数↔点值的 Θ(n log n) 转换，用于多项式/大整数乘法 | 28 |
| ⭐ 回溯 | backtracking | 有组织的穷举：状态-选择-撤销三要素 + 剪枝 | 29 |
| ⭐ 剪枝 | pruning | 可行性/最优性/搜索顺序/对称性四类；搜索顺序启发常收益最大 | 29 |
| 最受约束变量优先 | MRV heuristic | 先处理候选最少的位置，尽早失败尽早剪枝 | 29 |
| ⭐ 分支限界 | branch and bound | 回溯 + 乐观界剪枝 + 最优优先展开；ILP 求解器的骨架 | 29 |
| 松弛 | relaxation | 放宽约束得到乐观界（如用分数背包界剪 0-1 背包） | 29 |
| ⭐ 贪心选择性质 | greedy-choice property | 存在一个最优解包含贪心的选择 | 30 |
| 贪心保持领先 | greedy stays ahead | 归纳证明贪心的进度始终不劣于任何解 | 30 |
| ⭐ Huffman 编码 | Huffman coding | 反复合并最小两个频率；最优**前缀码** | 30 |
| 前缀码 | prefix code | 无码字是另一码字的前缀，可无歧义解码 | 30 |
| ⭐ 拟阵 | matroid | 满足遗传性 + 交换性质的集合系统；贪心在其上必然最优 | 30 |
| ⭐ 重叠子问题 | overlapping subproblems | 递归会反复求解同一子问题；DP 的第二个前提 | 31 |
| 记忆化 | memoization | 自顶向下缓存递归结果 | 31 |
| ⭐ 滚动数组 | rolling array | 只保留最近几层，把空间从 Θ(n²) 降到 Θ(n) | 31 |
| Hirschberg 算法 | Hirschberg's algorithm | 线性空间 LCS 且能回溯序列；`diff` 用它 | 31 |
| ⭐ 0-1 背包 / 完全背包 | 0-1 / unbounded knapsack | 一维写法容量**倒序** / **正序**，一个方向之差 | 31 |
| ⭐ LIS | longest increasing subsequence | 状态定义为"以 a[i] 结尾"；贪心+二分做到 O(n log n) | 31 |
| 区间 DP | interval DP | `dp[i][j]` 枚举分割点；**循环按区间长度递增** | 32 |
| 树形 DP | tree DP | 状态定义在子树上，DFS 后序转移 | 32 |
| 换根 DP | rerooting DP | 两遍 DFS 求出"以每个点为根"的答案，Θ(n) | 32 |
| ⭐ 状压 DP | bitmask DP | 状态含一个集合（二进制位）；Held-Karp 解 TSP 为 Θ(2ⁿn²) | 32 |
| 数位 DP | digit DP | 按位填数 + tight 标志；⚠️ tight 状态不能缓存 | 32 |
| 四边形不等式 | quadrangle inequality | 保证决策单调，把区间 DP 从 Θ(n³) 降到 Θ(n²) | 32 |
| ⭐ 失配函数 π | prefix function | `P[0..i]` 的最长 border 长度；KMP 的核心 | 33 |
| KMP | Knuth-Morris-Pratt | 文本指针永不回退，Θ(n+m)；用势能法证明 | 33 |
| 滚动哈希 | rolling hash | O(1) 更新窗口哈希；Rabin-Karp 的基础 | 33 |
| ⭐ Trie | trie / prefix tree | 前缀树；查找 Θ(L)，与集合大小无关 | 33 |
| Aho-Corasick | Aho-Corasick automaton | Trie + fail 指针，一遍扫出所有模式的所有出现 | 33 |
| 后缀数组 | suffix array | 所有后缀的字典序排名；配 height 数组威力极大 | 33 |
| ⭐ P | class P | 存在多项式时间**求解**算法的判定问题 | 34 |
| ⭐ NP | class NP | 存在多项式时间**验证**算法；N = Nondeterministic | 34 |
| ⭐ 多项式归约 | polynomial reduction | A ≤_p B 意为"能解 B 就能解 A"，故 B 至少和 A 一样难 | 34 |
| ⭐ NP-完全 | NP-complete | 在 NP 中且是 NP-难的 | 34 |
| NP-难 | NP-hard | 所有 NP 问题都能归约到它；未必在 NP 中 | 34 |
| ⭐ Cook-Levin 定理 | Cook-Levin theorem | SAT 是 NP-完全的；整棵归约树的根 | 34 |
| ⭐ 近似比 | approximation ratio | 算法解与最优解之比的上界（如顶点覆盖的 2） | 34 |
| FPTAS | fully polynomial-time approximation scheme | 对任意 ε 给出 1+ε 近似且时间关于 1/ε 多项式 | 34 |
| 固定参数可解 | fixed-parameter tractable (FPT) | `f(k)·poly(n)`，把指数隔离在小参数 k 上 | 34 |

---

> 回到[课程首页]({{< ref "_index.md" >}})，或查看[复杂度速查表与参考资料]({{< ref "96-resources.md" >}})。
