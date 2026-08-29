---
title: "第 20 讲：数据结构的增强——顺序统计树与区间树"
date: 2026-08-28
weight: 20
tags: ["数据结构与算法"]
draft: false
summary: "增强方法论的四个步骤与「可维护性定理」、顺序统计树（Rank/Select）、区间树的重叠查询与正确性证明、前缀和结构（树状数组与线段树）的对比，以及按大小 split 的平衡树序列。"
showToc: true
tocOpen: false
---

## 一、增强的方法论

很多问题不需要发明新数据结构，只需要在已有结构上**存一点额外信息**。

> **增强（augmentation）的四个步骤**（CLRS）：
> 1. 选择一个基础数据结构（通常是红黑树等平衡 BST）
> 2. 确定要维护的额外信息
> 3. 验证**这些信息可以在 O(1) 时间内由子节点的信息推出**
> 4. 实现新操作

⭐ **第 3 步是全部的关键**，它对应一条定理：

> **可维护性定理**：设增强信息 f 满足——**节点 x 的 f(x) 只依赖 x 本身、x.left 和 x.right 的信息**，则插入、删除和旋转后都能在 O(log n) 内维护 f，不改变原有操作的渐近复杂度。

**为什么？** 因为插入/删除只改变一条根到叶路径上的节点，沿路径向上重算即可（每个 O(1)，共 O(log n)）；旋转只改变常数个节点的子树结构，就地重算即可。

⚠️ **反例（不满足条件的信息）**：在每个节点存"子树中所有键的中位数"。中位数**无法**由左右子树的中位数 O(1) 推出，所以这个增强不可行。同样，"子树中不同值的个数"也不行。

⚠️ **旋转时的更新顺序**：必须**先更新变成孩子的节点，再更新变成父亲的节点**（[第 16 讲]({{< ref "16-avl-trees.md" >}})）。这是增强结构最常见的 bug。

---

## 二、顺序统计树

**增强信息**：每个节点存 **`size` = 以它为根的子树的节点数**。

```
                (26, size=13)
              ╱               ╲
      (17, size=7)         (41, size=5)
      ╱          ╲          ╱         ╲
 (14,size=3)  (21,size=3) (30,size=1) (47,size=3)
```

**可维护性验证**：`size(x) = size(x.left) + size(x.right) + 1` ✓ 只依赖孩子。

```go
type Node struct {
    Key         int
    Left, Right *Node
    Size        int
}

func size(x *Node) int {
    if x == nil { return 0 }
    return x.Size
}

func update(x *Node) { x.Size = 1 + size(x.Left) + size(x.Right) }
```

### Select：第 i 小的元素

```go
func Select(x *Node, i int) *Node { // i 从 1 开始，O(log n)
    for x != nil {
        r := size(x.Left) + 1 // x 在其子树中的排名
        switch {
        case i == r:
            return x
        case i < r:
            x = x.Left
        default:
            i -= r // ⭐ 进入右子树时要减去左子树和自己
            x = x.Right
        }
    }
    return nil
}
```

### Rank：某个键的排名

```go
func Rank(root *Node, key int) int { // 有多少个键 ≤ key
    r := 0
    for x := root; x != nil; {
        switch {
        case key < x.Key:
            x = x.Left
        case key > x.Key:
            r += size(x.Left) + 1 // 左子树全部 + x 自己
            x = x.Right
        default:
            return r + size(x.Left) + 1
        }
    }
    return r
}
```

**两者都是 O(log n)。**

### 应用

| 场景 | 用法 |
|---|---|
| **游戏排行榜** | "我排第几名"= Rank；"第 100 名是谁"= Select |
| **数据库 `LIMIT n OFFSET m`** | Select(m) 定位后顺序取 n 个 |
| **中位数维护** | `Select(size/2)` |
| **统计逆序对**（[第 9 讲]({{< ref "09-insertion-merge-sort.md" >}})） | 从右往左插入，每次查询"已插入元素中比当前小的个数" |
| **区间计数** | `Rank(hi) − Rank(lo)` |

⭐ 顺带解决了一个[第 5 讲]({{< ref "05-arrays-linked-lists.md" >}})的遗留问题：**如果把 BST 的"键"换成"位置"，按 size 而不是按 key 来定位，就得到一个支持 O(log n) 随机访问 + O(log n) 任意位置插入删除的序列结构。** 这就是文本编辑器用的 **rope**——数组做不到（插入 O(n)），链表也做不到（访问 O(n)）。

---

## 三、区间树

**问题**：维护一组区间 [low, high]，查询"有没有区间与给定区间 [a, b] 重叠"。

**增强设计**：
- **BST 的 key** = 区间的**左端点** low
- **增强信息** `max` = 以该节点为根的子树中，所有区间**右端点的最大值**

```
                [16, 21] max=30
               ╱              ╲
      [8, 9] max=23        [25, 30] max=30
      ╱         ╲                    ╲
 [5,8] max=10  [15,23] max=23      [26,26] max=26
```

**可维护性**：`max(x) = max(x.high, max(x.left), max(x.right))` ✓

```go
type IntervalNode struct {
    Low, High   int
    Max         int
    Left, Right *IntervalNode
}

func (x *IntervalNode) update() {
    x.Max = x.High
    if x.Left != nil && x.Left.Max > x.Max { x.Max = x.Left.Max }
    if x.Right != nil && x.Right.Max > x.Max { x.Max = x.Right.Max }
}

// 找任意一个与 [lo, hi] 重叠的区间
func Search(x *IntervalNode, lo, hi int) *IntervalNode {
    for x != nil {
        if x.Low <= hi && lo <= x.High { // 重叠
            return x
        }
        // ⭐ 关键的分支决策
        if x.Left != nil && x.Left.Max >= lo {
            x = x.Left
        } else {
            x = x.Right
        }
    }
    return nil
}
```

### ⭐ 正确性证明

查找的每一步只走一个方向，凭什么保证不会漏掉答案？

**情形 A：走向左子树**（因为 `x.Left.Max >= lo`）。
需证：若左子树中没有重叠区间，则右子树中也没有。
设左子树中右端点最大的区间是 j，即 `j.high = x.Left.Max >= lo`。若 j 与 [lo,hi] 不重叠，由 `j.high >= lo` 必有 **`j.low > hi`**。而 BST 性质保证右子树中所有区间的 low ≥ x.low > j.low（右子树的 low 都比 x 大，而 j 在左子树 ⟹ j.low ≤ x.low）……于是右子树中每个区间的 low 都 > hi，**全部不可能重叠**。✓

**情形 B：走向右子树**（因为左子树为空或 `x.Left.Max < lo`）。
左子树中所有区间的 high ≤ `x.Left.Max` < lo，即全部结束于 lo 之前，**不可能重叠**。✓ ∎

⭐ **这个证明是"增强信息如何指导剪枝"的范本**：max 这一个数就让我们在每个节点上排除掉整整一棵子树。

**查询代价 O(log n)。** 若要报告**所有**重叠区间，代价是 O(k log n)（k 是答案数量）。

**应用**：日程冲突检测、基因组区间注释、网络防火墙规则匹配（IP 段重叠）、编译器的寄存器活跃区间分析。

---

## 四、前缀和结构：树状数组与线段树

有一类增强问题特别常见：**在数组上做「区间查询 + 单点/区间修改」**。

朴素做法的困境：

| 方案 | 单点修改 | 区间求和 |
|---|---|---|
| 原数组 | O(1) | **O(n)** |
| 预计算前缀和 | **O(n)** | O(1) |

**两个专用结构都做到 O(log n) + O(log n)。**

### 树状数组（Fenwick Tree）

**核心思想**：`tree[i]` 存储的是"以 i 结尾、长度为 `lowbit(i)` 的区间和"，其中 `lowbit(i) = i & (-i)`（i 的最低位 1）。

```
下标:      1    2    3    4    5    6    7    8
覆盖范围: [1]  [1,2] [3] [1..4] [5] [5,6] [7] [1..8]

         ┌───────────────────────────────┐ 8
         ┌───────────────┐ 4             ┌───┐ 6      ┌─┐ 7
         ┌───┐ 2         ┌─┐ 3           ┌─┐ 5
         ┌─┐ 1
```

```go
type Fenwick struct{ tree []int } // 1-indexed

func NewFenwick(n int) *Fenwick { return &Fenwick{tree: make([]int, n+1)} }

func (f *Fenwick) Add(i, delta int) { // 单点加，O(log n)
    for ; i < len(f.tree); i += i & (-i) { // 向上跳到所有覆盖 i 的节点
        f.tree[i] += delta
    }
}

func (f *Fenwick) Sum(i int) int { // 前缀和 [1, i]，O(log n)
    s := 0
    for ; i > 0; i -= i & (-i) { // 不断剥掉最低位的 1
        s += f.tree[i]
    }
    return s
}

func (f *Fenwick) RangeSum(l, r int) int { return f.Sum(r) - f.Sum(l-1) }
```

⭐ **树状数组的代码只有几行，常数极小，是竞赛和工程中处理前缀和的首选。** 缺点是只支持有逆元的运算（加法可以，取 max 不行——因为 `RangeSum` 依赖减法）。

### 线段树

每个节点表示一个区间，存该区间的聚合值（和、最值、gcd……）。

```
                    [0,7] sum=36
              ╱                    ╲
       [0,3] sum=6            [4,7] sum=30
       ╱        ╲              ╱        ╲
   [0,1]      [2,3]        [4,5]      [6,7]
   sum=1      sum=5        sum=9      sum=21
```

```go
type SegTree struct {
    n    int
    tree []int
}

func (s *SegTree) Update(node, l, r, i, val int) { // 单点赋值
    if l == r {
        s.tree[node] = val
        return
    }
    mid := (l + r) / 2
    if i <= mid {
        s.Update(2*node, l, mid, i, val)
    } else {
        s.Update(2*node+1, mid+1, r, i, val)
    }
    s.tree[node] = s.tree[2*node] + s.tree[2*node+1] // 合并
}

func (s *SegTree) Query(node, l, r, ql, qr int) int { // 区间查询
    if qr < l || r < ql {
        return 0 // 完全不相交：返回幺元
    }
    if ql <= l && r <= qr {
        return s.tree[node] // 完全包含：直接返回
    }
    mid := (l + r) / 2
    return s.Query(2*node, l, mid, ql, qr) + s.Query(2*node+1, mid+1, r, ql, qr)
}
```

**查询 O(log n)**：因为任意查询区间最多被拆成 O(log n) 个节点区间。

**懒标记（lazy propagation）**：支持**区间修改**——修改时不下推到叶子，而是在节点上打一个标记，等到必须访问子节点时才下推。这把区间修改也降到 O(log n)。

### 对比

| | 树状数组 | 线段树 |
|---|---|---|
| 代码量 | **~10 行** | ~80 行 |
| 常数 | **极小** | 中等 |
| 空间 | **n** | 4n |
| 支持的运算 | 需**可逆**（和、异或） | **任意满足结合律**（max、min、gcd、矩阵乘） |
| 区间修改 | 需要技巧（差分） | **懒标记，自然支持** |
| 可持久化 | 难 | **容易** |

⭐ **选型规则**：**只需要区间和 → 树状数组；需要区间最值、区间修改或更复杂的合并 → 线段树。**

---

## 五、增强的三个经典练习

| 目标操作 | 增强信息 | 可维护性 |
|---|---|---|
| 第 i 小 / 排名 | 子树大小 | `1 + size(l) + size(r)` ✓ |
| 区间重叠查询 | 子树最大右端点 | `max(high, max(l), max(r))` ✓ |
| 子树键的和 | 子树和 | `key + sum(l) + sum(r)` ✓ |
| **子树的黑高** | 黑高 | ✓（红黑树本身就是增强） |
| 子树深度/高度 | 高度 | `1 + max(h(l), h(r))` ✓（AVL 本身） |
| ❌ 子树的中位数 | — | **✗ 无法由孩子 O(1) 推出** |
| ❌ 子树中不同值的个数 | — | **✗** |

⭐ **注意最后两行**：中位数和 distinct count 都不满足可维护性条件。它们需要完全不同的技术（如可持久化线段树 / 归并树），复杂度也更高。**遇到一个增强需求，第一件事就是检查第 3 步是否成立。**

---

## 随堂自测

1. 写出增强方法论的四个步骤，说明为什么第 3 步是关键。
2. 为什么"子树的中位数"不能作为增强信息？"子树键的和"为什么可以？
3. 旋转时更新增强信息的顺序为什么不能颠倒？举一个出错的例子。
4. 实现 `Select(i)` 时，进入右子树为什么要执行 `i -= size(left) + 1`？
5. 用顺序统计树在 O(n log n) 内统计逆序对，说明具体做法。
6. 区间树的查找每步只走一个方向，证明它不会漏掉重叠的区间（分两种情形）。
7. 如果要报告**所有**与 [a,b] 重叠的区间，复杂度是多少？
8. 树状数组的 `i & (-i)` 是什么？为什么 `Sum` 循环执行 O(log n) 次？
9. 为什么树状数组不能直接求区间最大值，而线段树可以？
10. 用平衡树按"子树大小"而非"键"来定位，能得到什么结构？它解决了数组和链表各自的什么缺陷？

---

> **上一讲**：[第 19 讲：随机化平衡——跳表与 Treap]({{< ref "19-skip-lists-treaps.md" >}})　**下一讲**：[第 21 讲：图的表示与广度优先搜索]({{< ref "21-graphs-bfs.md" >}})
