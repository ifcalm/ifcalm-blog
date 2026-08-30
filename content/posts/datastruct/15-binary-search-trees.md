---
title: "第 15 讲：二叉搜索树"
date: 2026-08-28
weight: 15
tags: ["数据结构与算法"]
draft: false
summary: "有序字典 ADT 与 BST 性质、四种遍历、查找/前驱/后继/最值的实现、删除的三种情形与「两个孩子」的标准处理、随机构建 BST 期望高度 O(log n) 的证明，以及为什么真实工作负载下必须平衡。"
showToc: true
tocOpen: false
---

## 一、为什么散列表不够

[第 7–8 讲]({{< ref "07-hash-tables-chaining.md" >}})的散列表已经给出期望 O(1) 的查找、插入、删除。但它有一个根本性的缺失：**散列破坏了顺序**。

**有序字典（ordered dictionary / sorted map）ADT** 在字典的基础上增加：

| 操作 | 语义 | 散列表能做吗 |
|---|---|---|
| `Min()` / `Max()` | 最小 / 最大的键 | ✗ Θ(n) |
| `Predecessor(k)` / `Successor(k)` | 小于 k 的最大键 / 大于 k 的最小键 | ✗ Θ(n) |
| `RangeQuery(lo, hi)` | 所有落在 [lo,hi] 的键 | ✗ Θ(n) |
| `InOrder()` | 按序遍历全部 | ✗ 需排序 Θ(n log n) |
| `Rank(k)` / `Select(i)` | k 的排名 / 第 i 小 | ✗ |

**真实场景中这些操作无处不在**：数据库的 `ORDER BY` 与 `BETWEEN`、时间序列的区间查询、排行榜的名次、调度器的"下一个到期任务"、自动补全的前缀范围。

⭐ **一句话选型**：**只按键取值 → 散列表；需要顺序 → 搜索树。** Go 里 `map` 对应前者，`container/list` 之外没有内建的后者，通常用有序切片 + 二分（读多写少）或第三方 B 树/跳表库。

---

## 二、BST 性质

> **二叉搜索树性质**：对树中每个节点 x，
> - 左子树中**所有**键 ≤ x.key
> - 右子树中**所有**键 ≥ x.key

```
                8
              ╱   ╲
            3      10
          ╱   ╲       ╲
         1     6       14
             ╱   ╲     ╱
            4     7   13
```

⚠️ **这是一个递归的、全局的条件，不是局部条件**。下面这棵树满足"每个节点比左孩子大、比右孩子小"，但**不是 BST**：

```
                8
              ╱   ╲
            3      10
              ╲
               12       ← 12 在 8 的左子树里，却大于 8
```

**验证 BST 必须传递上下界**，而不是只比较父子：

```go
func IsBST(root *Node) bool {
    return check(root, math.MinInt, math.MaxInt)
}

func check(x *Node, lo, hi int) bool {
    if x == nil {
        return true
    }
    if x.Key <= lo || x.Key >= hi {
        return false
    }
    return check(x.Left, lo, x.Key) && check(x.Right, x.Key, hi)
}
```

### 中序遍历给出有序序列

```go
type Node struct {
    Key         int
    Val         any
    Left, Right *Node
}

func InOrder(x *Node, visit func(*Node)) { // 左 → 根 → 右
    if x == nil { return }
    InOrder(x.Left, visit)
    visit(x)
    InOrder(x.Right, visit)
}
```

**Θ(n)**，输出恰好是键的升序。这是 BST 性质最直接的推论，也是"BST = 有序结构"的形式化表达。

四种遍历的用途：

| 遍历 | 顺序 | 典型用途 |
|---|---|---|
| **中序** | 左-根-右 | **有序输出**、验证 BST |
| 前序 | 根-左-右 | **序列化/复制树**（先建根） |
| 后序 | 左-右-根 | **释放/计算子树聚合**（先处理孩子） |
| 层序（BFS） | 逐层 | 打印树形、按深度处理 |

---

## 三、查找与相关操作

### 查找

```go
func (t *BST) Get(k int) (any, bool) { // 迭代版，O(h)
    x := t.root
    for x != nil {
        switch {
        case k < x.Key:
            x = x.Left
        case k > x.Key:
            x = x.Right
        default:
            return x.Val, true
        }
    }
    return nil, false
}
```

**代价 O(h)**，h 是树高。⭐ **本讲所有操作都是 O(h)，因此整门搜索树的故事就是「如何保证 h = O(log n)」**——这是[第 16–19 讲]({{< ref "16-avl-trees.md" >}})的全部内容。

### 最值、前驱与后继

```go
func minimum(x *Node) *Node { // 一路向左
    for x != nil && x.Left != nil { x = x.Left }
    return x
}

// 后继：大于 x.Key 的最小键
func successor(x *Node) *Node {
    if x.Right != nil {
        return minimum(x.Right) // 情形 ①：右子树的最小值
    }
    // 情形 ②：向上找，直到某个祖先的左子树包含 x
    p := x.Parent
    for p != nil && x == p.Right {
        x, p = p, p.Parent
    }
    return p
}
```

```
情形 ①：x 有右子树              情形 ②：x 无右子树
        x                            p ← 后继
       ╱ ╲                          ╱
      …   R                        …
         ╱                          ╲
        后继（R 的最左）               x
```

**情形 ② 的直觉**：中序遍历中，访问完 x 及其整棵子树后，下一个访问的是"x 所在的最近一个左子树的父节点"。

---

## 四、插入与删除

### 插入：总是插在叶子位置

```go
func (t *BST) Put(k int, v any) {
    var parent *Node
    x := t.root
    for x != nil {
        parent = x
        switch {
        case k < x.Key:
            x = x.Left
        case k > x.Key:
            x = x.Right
        default:
            x.Val = v // 键已存在，更新
            return
        }
    }
    n := &Node{Key: k, Val: v, Parent: parent}
    switch {
    case parent == nil:
        t.root = n
    case k < parent.Key:
        parent.Left = n
    default:
        parent.Right = n
    }
    t.size++
}
```

### ⭐ 删除：三种情形

```go
func (t *BST) Delete(k int) bool {
    z := t.find(k)
    if z == nil { return false }

    switch {
    case z.Left == nil: // 情形 ① / ②：至多一个孩子
        t.transplant(z, z.Right)
    case z.Right == nil:
        t.transplant(z, z.Left)
    default: // 情形 ③：两个孩子
        y := minimum(z.Right) // 后继，它必然没有左孩子
        if y.Parent != z {
            t.transplant(y, y.Right) // 把 y 从原位置摘下
            y.Right = z.Right
            y.Right.Parent = y
        }
        t.transplant(z, y)
        y.Left = z.Left
        y.Left.Parent = y
    }
    t.size--
    return true
}

// 用子树 v 替换子树 u 的位置
func (t *BST) transplant(u, v *Node) {
    switch {
    case u.Parent == nil:
        t.root = v
    case u == u.Parent.Left:
        u.Parent.Left = v
    default:
        u.Parent.Right = v
    }
    if v != nil {
        v.Parent = u.Parent
    }
}
```

```
情形 ①：无孩子        情形 ②：一个孩子        情形 ③：两个孩子
    p                     p                      p
    │                     │                      │
    z          ⟹  删       z         ⟹  提升子树     z          ⟹ 用后继替换
                          │                    ╱   ╲
                          c                   L     R
                                                   ╱
                                                  y = 后继（无左孩子）
```

⭐ **情形 ③ 的关键**：用 z 的**中序后继** y 顶替 z。y = `minimum(z.Right)`，它**必然没有左孩子**（否则左孩子更小），所以摘除 y 只是情形 ②。

**为什么用后继就对了？** 因为 y 是"右子树中最小的"，替换后：左子树全部 ≤ y（它们都 ≤ z ≤ y），右子树剩余部分全部 ≥ y（y 是其中最小）。BST 性质得以保持。

⚠️ 用**前驱**（左子树的最大值）同样正确。总是选后继会导致树逐渐向左倾斜，有些实现会随机选择前驱或后继来缓解——这是"Hibbard 删除"的已知问题：反复随机插入删除后，树高会从 √n 级恶化。

---

## 五、高度：最好、最坏与随机

**所有操作都是 O(h)。h 是多少？**

```
最好（完全平衡）：h = ⌊log₂ n⌋       ⟹ O(log n)
最坏（一条链）：  h = n − 1          ⟹ O(n)
```

**最坏情况何时发生？** **按升序插入**：

```
insert 1,2,3,4,5  ⟹    1
                         ╲
                          2
                           ╲
                            3
                             ╲
                              4
                               ╲
                                5
```

⚠️ **这是灾难性的，因为"按顺序插入"在真实系统里极其常见**：按时间戳插入日志、按自增 ID 导入数据、从已排序文件建索引。**朴素 BST 恰好在最常见的输入模式下退化成链表。**

### ⭐ 随机构建 BST 的期望高度

> **定理**：把 n 个互异键的一个**均匀随机排列**依次插入空 BST，得到的树的期望高度是 **O(log n)**（精确地，约 **4.311·ln n ≈ 2.99 log₂ n**）。

**证明思路**（期望深度的简化版）：设 X_n 为随机 BST 的高度，Y_n = 2^{X_n}。第一个插入的键等概率是第 i 小的（i = 1..n），它成为根，左右子树分别是规模 i−1 和 n−i 的随机 BST：

```
Y_n = 2 · max(Y_{i−1}, Y_{n−i})
E[Y_n] ≤ (2/n) Σ_{i=0}^{n-1} (E[Y_i] + E[Y_{n−1−i}])
```

用归纳法可证 `E[Y_n] = O(n³)`，再由 Jensen 不等式 `2^{E[X_n]} ≤ E[2^{X_n}] = E[Y_n]` 得

```
E[X_n] ≤ log₂ E[Y_n] = O(log n)                          ∎
```

**更简单的相关结论**：随机 BST 中一个节点的**期望深度**是 `2 ln n ≈ 1.39 log₂ n`。⭐ **这与[第 11 讲]({{< ref "11-quicksort.md" >}})快排的 1.39 n log₂ n 是同一个常数**——绝非巧合：**随机 BST 的构建过程与随机化快排的划分过程是同构的**（根 = 主元，左右子树 = 两侧递归）。

### ⚠️ 但期望 O(log n) 救不了你

三个理由：

1. **真实输入不是随机排列。** 有序、近乎有序、周期性的输入是常态。
2. **删除会破坏随机性。** 即使插入序列随机，Hibbard 删除后的树不再是随机 BST，高度会退化到 Θ(√n)。
3. **期望是对输入分布的假设**（[第 4 讲]({{< ref "04-amortized-analysis.md" >}})的区分），不是算法自带的保证。

**因此必须主动平衡。** 两条路线：

| 路线 | 做法 | 代表 |
|---|---|---|
| **确定性平衡** | 维护额外的结构不变式，插入删除后旋转修复 | AVL（[第 16 讲]({{< ref "16-avl-trees.md" >}})）、红黑树（[第 17 讲]({{< ref "17-red-black-trees.md" >}})）、B 树（[第 18 讲]({{< ref "18-b-trees.md" >}})） |
| **随机化平衡** | 把随机性注入算法自身，与输入顺序无关 | 跳表、Treap（[第 19 讲]({{< ref "19-skip-lists-treaps.md" >}})） |

⭐ 第二条路线正是[第 7 讲]({{< ref "07-hash-tables-chaining.md" >}})全域散列和[第 11 讲]({{< ref "11-quicksort.md" >}})随机化快排的同一个思想在树上的应用：**当"输入是随机的"这个假设不可靠时，就让算法自己制造随机性。**

---

## 六、代价汇总

| 操作 | 一般 BST | 平衡 BST |
|---|---|---|
| Search / Insert / Delete | O(h) | **O(log n)** |
| Min / Max / Pred / Succ | O(h) | **O(log n)** |
| InOrder 遍历 | Θ(n) | Θ(n) |
| 区间查询（输出 m 个） | O(h + m) | **O(log n + m)** |
| 构建（n 个元素） | O(nh) | O(n log n)，**有序输入可 Θ(n)** |

**最后一行值得注意**：从**已排序**的数组建平衡 BST 只需 Θ(n)——取中点作根，递归建左右子树，`T(n) = 2T(n/2) + O(1) = Θ(n)`。数据库从排序好的数据批量建索引（bulk loading）用的就是这个。

---

## 随堂自测

1. 有序字典比普通字典多了哪五类操作？各举一个真实场景。
2. 为什么"每个节点大于左孩子、小于右孩子"不足以保证是 BST？写出正确的验证函数。
3. 画出向空树依次插入 `[50, 30, 70, 20, 40, 60, 80]` 后的树，并写出中序遍历结果。
4. 给出无右子树节点求后继的算法，并说明它为什么正确（用中序遍历的语义解释）。
5. 删除有两个孩子的节点时，为什么用中序后继替换？为什么后继一定没有左孩子？
6. 用前驱替换是否也正确？总是用后继会带来什么长期问题？
7. 按升序插入 n 个键会得到什么树？为什么这个输入模式在工程中很常见？
8. 随机 BST 期望高度 O(log n)，为什么这个结论不足以让我们放心使用朴素 BST？给出三条理由。
9. 随机 BST 的期望节点深度是 1.39 log₂ n，随机化快排的期望比较是 1.39 n log₂ n。解释这不是巧合。
10. 如何从已排序数组在 Θ(n) 时间内建出平衡 BST？

