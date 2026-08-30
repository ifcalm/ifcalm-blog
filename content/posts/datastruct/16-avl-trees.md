---
title: "第 16 讲：AVL 树与旋转"
date: 2026-08-28
weight: 16
tags: ["数据结构与算法"]
draft: false
summary: "旋转是所有平衡树的共同原语：它为什么保持 BST 性质。AVL 的平衡因子不变式、高度上界 1.44 log n 的斐波那契证明、插入的四种失衡情形与修复、删除为什么可能需要 O(log n) 次旋转。"
showToc: true
tocOpen: false
---

## 一、旋转：所有平衡树的共同原语

我们需要一种操作，它能**改变树的形状**（降低高度）而**不破坏 BST 性质**。这个操作就是**旋转（rotation）**。

```
        右旋 y ──────────────▶
      y                            x
    ╱   ╲                        ╱   ╲
   x     γ                      α     y
 ╱   ╲          ◀──────────           ╱  ╲
α     β          左旋 x               β    γ

中序遍历：α x β y γ                中序遍历：α x β y γ      ← 完全一致
```

⭐ **旋转前后中序遍历序列不变**，而中序序列不变就等价于 BST 性质保持（[第 15 讲]({{< ref "15-binary-search-trees.md" >}})）。这一行就是旋转正确性的全部证明。

**为什么有效**：`α < x < β < y < γ` 这个大小关系在两种形状下都成立，但树的高度分布变了——右旋把左边的重量转移到右边。

```go
type Node struct {
    Key         int
    Val         any
    Left, Right *Node
    Height      int // AVL 维护的额外信息
}

func height(x *Node) int {
    if x == nil { return -1 } // 空树高度定义为 -1，叶子为 0
    return x.Height
}

func update(x *Node) {
    x.Height = 1 + max(height(x.Left), height(x.Right))
}

func rotateRight(y *Node) *Node { // 返回新的子树根
    x := y.Left
    y.Left = x.Right
    x.Right = y
    update(y) // ⚠️ 必须先更新 y（它变成了孩子），再更新 x
    update(x)
    return x
}

func rotateLeft(x *Node) *Node {
    y := x.Right
    x.Right = y.Left
    y.Left = x
    update(x)
    update(y)
    return y
}
```

**旋转是 O(1) 的**：只改动常数个指针。这是所有平衡树能做到 O(log n) 修复的基础。

---

## 二、AVL 不变式

**1962 年 Adelson-Velsky 与 Landis 提出的第一种自平衡搜索树。**

> **AVL 性质**：对每个节点 x，
> ```
> 平衡因子 BF(x) = height(x.Left) − height(x.Right) ∈ {−1, 0, +1}
> ```

即**左右子树高度差不超过 1**。

```
      合法 AVL                  非法（BF = 2）
         3(h=2)                     3(h=2)
       ╱     ╲                    ╱
     1(h=0)  5(h=1)             1(h=1)
               ╲                ╱
                6(h=0)        0(h=0)
```

### ⭐ 高度上界：h < 1.44 log₂(n+2)

**问题**：满足 AVL 性质的树，高度最多是多少？等价地——**高度为 h 的 AVL 树最少有多少个节点？**

设 N(h) 为高度 h 的 AVL 树的最小节点数。为了让节点最少，根的两棵子树应尽可能矮，但又必须满足平衡因子约束，所以一棵高 h−1、另一棵高 h−2：

```
N(0) = 1                     单个节点
N(1) = 2                     根 + 一个孩子
N(h) = 1 + N(h−1) + N(h−2)
```

```
最小 AVL 树（h = 4，N = 12）：

              ●
           ╱     ╲
        ●          ●
      ╱   ╲       ╱
     ●     ●     ●
   ╱  ╲    ╱
  ●    ●  ●
 ╱
●
```

**这正是斐波那契递推。** 事实上 `N(h) = F(h+3) − 1`，其中 F 是斐波那契数。由 `F(k) ≈ φ^k/√5`（φ = (1+√5)/2 ≈ 1.618）：

```
n ≥ N(h) = F(h+3) − 1 ≈ φ^{h+3}/√5 − 1
⟹ h ≤ log_φ(√5(n+1)) − 3
     = log₂(n) / log₂(φ) + O(1)
     ≈ 1.4405 · log₂ n + O(1)                            ∎
```

⭐ **结论：AVL 树的高度最多比完美平衡树高 44%。** 所有操作因此是 **O(log n)** 的最坏情况保证——不是期望，不是摊还，是确定性保证。

**对照红黑树**（[第 17 讲]({{< ref "17-red-black-trees.md" >}})）的上界是 `2 log₂(n+1)`，即最多高 100%。**AVL 更严格 ⟹ 树更矮 ⟹ 查找更快，但维护成本更高。** 这个取舍是本讲和下一讲的主线。

---

## 三、插入后的四种失衡

插入一个节点后，从插入点向根回溯，第一个失衡的节点（|BF| = 2）称为 z。根据"插入发生在 z 的哪个孙子方向"，分四种情形：

```
① LL（左-左）           ② RR（右-右）
      z                      z
     ╱                        ╲
    y            右旋 z        y         左旋 z
   ╱          ─────────▶       ╲     ─────────▶
  x                             x

③ LR（左-右）           ④ RL（右-左）
      z                      z
     ╱                        ╲
    y      先左旋 y            y      先右旋 y
     ╲     再右旋 z           ╱       再左旋 z
      x    ─────────▶        x      ─────────▶
```

**LL 的修复（单旋）**：

```
        z(BF=2)                       y
       ╱      ╲                     ╱   ╲
      y        δ    右旋 z          x      z
    ╱   ╲            ─────▶       ╱ ╲    ╱ ╲
   x     γ                       α   β  γ   δ
  ╱ ╲
 α   β                    高度从 h+2 降回 h+1，且根的 BF = 0
```

**LR 的修复（双旋）**：单旋对 LR 无效，因为旋转后仍然失衡。必须先把 LR 变成 LL：

```
      z              z                 x
     ╱              ╱                ╱   ╲
    y     左旋 y    x     右旋 z      y     z
     ╲    ─────▶  ╱      ─────▶     ╱ ╲   ╱ ╲
      x          y                 α   β γ   δ
```

```go
func balance(x *Node) *Node {
    update(x)
    bf := height(x.Left) - height(x.Right)
    switch {
    case bf > 1: // 左重
        if height(x.Left.Left) < height(x.Left.Right) {
            x.Left = rotateLeft(x.Left) // LR：先把左孩子左旋，转成 LL
        }
        return rotateRight(x)
    case bf < -1: // 右重
        if height(x.Right.Right) < height(x.Right.Left) {
            x.Right = rotateRight(x.Right) // RL：转成 RR
        }
        return rotateLeft(x)
    }
    return x
}

func insert(x *Node, k int, v any) *Node {
    if x == nil {
        return &Node{Key: k, Val: v, Height: 0}
    }
    switch {
    case k < x.Key:
        x.Left = insert(x.Left, k, v)
    case k > x.Key:
        x.Right = insert(x.Right, k, v)
    default:
        x.Val = v
        return x
    }
    return balance(x) // 回溯路径上每个节点都检查并修复
}
```

⭐ **递归返回值即新子树根**这个写法（而不是维护 parent 指针）让代码短得多，是 Go/函数式风格里实现平衡树的标准做法。

### ⚠️ 插入只需要 O(1) 次旋转

**关键性质**：插入后，**第一次旋转就把子树高度恢复到插入前的值**，因此更上层不可能再失衡。

```
插入前 z 子树高 h+1 ⟹ 插入后高 h+2（失衡）⟹ 旋转后又是 h+1
⟹ z 的祖先看到的高度没变 ⟹ 不需要继续修复
```

**所以插入至多 1 次单旋或 1 次双旋（= 2 次旋转），O(1)。** 但仍需 O(log n) 时间沿路径更新高度。

---

## 四、删除：可能需要 O(log n) 次旋转

删除的修复逻辑与插入相同（同样是四种情形），但有一个本质区别：

⚠️ **删除后旋转可能让子树高度减少 1**，这会导致**祖先节点也失衡**，需要一路修复到根。

```
删除前 z 子树高 h+1 ⟹ 删除后失衡 ⟹ 旋转后可能变成 h
⟹ z 的父节点的平衡因子改变 ⟹ 可能失衡 ⟹ 继续向上
```

```go
func delete(x *Node, k int) *Node {
    if x == nil {
        return nil
    }
    switch {
    case k < x.Key:
        x.Left = delete(x.Left, k)
    case k > x.Key:
        x.Right = delete(x.Right, k)
    default:
        switch {
        case x.Left == nil:
            return x.Right
        case x.Right == nil:
            return x.Left
        default:
            s := x.Right
            for s.Left != nil { s = s.Left } // 中序后继
            x.Key, x.Val = s.Key, s.Val
            x.Right = delete(x.Right, s.Key)
        }
    }
    return balance(x) // 递归返回时逐层修复，最多 O(log n) 次旋转
}
```

| | 插入 | 删除 |
|---|---|---|
| 查找路径 | O(log n) | O(log n) |
| **旋转次数** | **O(1)** | **O(log n)** |
| 高度更新 | O(log n) | O(log n) |

⭐ **这个不对称性是理解各种平衡树差异的钥匙**：红黑树把删除的旋转次数也压到 O(1)（代价是不变式更复杂、树更高），因此在**删除密集**的场景（如 Linux 内核的进程调度红黑树）更受青睐。

---

## 五、AVL 与红黑树的对比

| | AVL | 红黑树 |
|---|---|---|
| 高度上界 | **1.44 log₂ n** | 2 log₂ n |
| 查找 | **更快**（树更矮） | 稍慢 |
| 插入旋转 | ≤ 2 | ≤ 2 |
| **删除旋转** | **O(log n)** | **≤ 3** |
| 每节点额外信息 | 高度（int）或 2 位平衡因子 | **1 位颜色** |
| 实现复杂度 | 中等 | 高 |
| 典型使用者 | 数据库内存索引、**读密集**场景 | **Linux CFS 调度器**、C++ `std::map`、Java `TreeMap` |

⭐ **选型规则**：

- **查找远多于修改** → AVL（更矮的树带来更少的缓存未命中）
- **修改频繁，尤其删除多** → 红黑树
- **数据在磁盘上** → 两个都不选，用 **B 树**（[第 18 讲]({{< ref "18-b-trees.md" >}})）
- **要实现简单 / 需要并发** → 跳表（[第 19 讲]({{< ref "19-skip-lists-treaps.md" >}})）

⚠️ 一个现实提醒：**实测差距通常远小于理论差距**。1.44 log n 与 2 log n 在 n = 10⁶ 时是 29 层与 40 层，看似差不少，但两者都远超缓存容量，真正的瓶颈是每层一次缓存未命中。**这正是 B 树存在的理由——把"层数"这个变量本身消灭掉。**

---

## 六、旋转的其他用途

旋转不只用于平衡，它是**任何要改变树形状**的操作的通用工具：

| 用途 | 讲次 |
|---|---|
| AVL / 红黑树的平衡修复 | 本讲、[第 17 讲]({{< ref "17-red-black-trees.md" >}}) |
| Treap 按优先级堆序上浮 | [第 19 讲]({{< ref "19-skip-lists-treaps.md" >}}) |
| 伸展树（Splay）把访问节点转到根 | [第 19 讲]({{< ref "19-skip-lists-treaps.md" >}}) |
| 增强信息（子树大小、区间最值）的维护 | [第 20 讲]({{< ref "20-augmenting-data-structures.md" >}}) |

⚠️ **旋转时必须同步更新所有增强信息**，且顺序不能错：**先更新变成孩子的那个节点，再更新变成父亲的**。上面 `rotateRight` 中先 `update(y)` 后 `update(x)` 就是这个原因。这是实现增强平衡树时最常见的 bug 来源。

---

## 随堂自测

1. 证明旋转保持 BST 性质。为什么"中序序列不变"就足够？
2. 在 `rotateRight` 中，为什么必须先 `update(y)` 再 `update(x)`？调换顺序会怎样？
3. 写出 N(h) 的递推式并说明它为什么是斐波那契。由此推出 h ≤ 1.44 log₂ n。
4. 依次插入 `[10, 20, 30, 40, 50, 25]`，画出每一步后的 AVL 树，标出发生的旋转类型。
5. 为什么 LR 情形不能用单旋修复？画图说明单旋后仍然失衡。
6. 证明：AVL 插入后至多需要一次单旋或一次双旋。关键性质是什么？
7. 为什么删除可能需要 O(log n) 次旋转而插入只需 O(1)？
8. AVL 高度上界 1.44 log n，红黑树 2 log n。为什么实践中红黑树用得更多？
9. n = 10⁶ 时两者的树高分别约是多少层？为什么这个差距在实测中往往不明显？

