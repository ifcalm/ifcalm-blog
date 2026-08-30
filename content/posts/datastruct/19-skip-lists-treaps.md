---
title: "第 19 讲：随机化平衡——跳表与 Treap"
date: 2026-08-28
weight: 19
tags: ["数据结构与算法"]
draft: false
summary: "不靠旋转规则、靠随机数维持平衡的两种结构：跳表的多级索引与期望 O(log n) 证明、Treap 的堆序优先级与「随机 BST 等价」定理、split/merge 这对强大的原语，以及为什么 Redis 和 LevelDB 选择跳表。"
showToc: true
tocOpen: false
---

## 一、第三条路线

[第 16–18 讲]({{< ref "16-avl-trees.md" >}})的平衡树都走**确定性**路线：定义一个严格的结构不变式，每次修改后检查并修复。代价是**规则复杂、实现容易出错**——红黑树的删除是公认最难写对的经典数据结构之一。

**随机化路线的想法**：不定义严格的不变式，而是**让结构由随机数决定形状**，然后证明它**以极高概率**是平衡的。

⭐ 这正是[第 7 讲]({{< ref "07-hash-tables-chaining.md" >}})全域散列、[第 11 讲]({{< ref "11-quicksort.md" >}})随机化快排的同一思想：**当"输入是随机的"不可靠时，让算法自己产生随机性。** 保证从"对所有输入都成立的最坏情况"变成"对所有输入都成立的高概率"。

---

## 二、跳表

**出发点**：有序链表查找是 Θ(n)，因为不能二分。**能不能给链表加索引？**

```
Level 3  H ──────────────────────────────────▶ 30 ──────────────▶ nil
Level 2  H ──────────────▶ 10 ──────────────▶ 30 ──────▶ 50 ───▶ nil
Level 1  H ──────▶ 5 ───▶ 10 ──────▶ 20 ───▶ 30 ──────▶ 50 ───▶ nil
Level 0  H ─▶ 3 ─▶ 5 ─▶ 8 ─▶ 10 ─▶ 15 ─▶ 20 ─▶ 30 ─▶ 40 ─▶ 50 ─▶ nil

查找 40：从最高层开始，能往右就往右，不能就下降一层
         L3: H→30（下一个是 nil > 40，下降）
         L2: 30→50 太大，下降
         L1: 30→50 太大，下降
         L0: 30→40 ✓
```

**每个节点的层数在插入时随机决定**：以概率 p（通常 1/2 或 1/4）不断往上加一层。

```go
const maxLevel = 32
const p = 0.25 // Redis 用 0.25

type skipNode struct {
    key  int
    val  any
    next []*skipNode // next[i] 是第 i 层的后继
}

type SkipList struct {
    head  *skipNode
    level int // 当前最高层
    rng   *rand.Rand
}

func (s *SkipList) randomLevel() int {
    lv := 1
    for lv < maxLevel && s.rng.Float64() < p {
        lv++
    }
    return lv
}

func (s *SkipList) Get(key int) (any, bool) {
    x := s.head
    for i := s.level - 1; i >= 0; i-- { // 从最高层往下
        for x.next[i] != nil && x.next[i].key < key {
            x = x.next[i] // 能往右就往右
        }
    }
    x = x.next[0]
    if x != nil && x.key == key {
        return x.val, true
    }
    return nil, false
}

func (s *SkipList) Put(key int, val any) {
    update := make([]*skipNode, maxLevel) // 每层的插入点前驱
    x := s.head
    for i := s.level - 1; i >= 0; i-- {
        for x.next[i] != nil && x.next[i].key < key {
            x = x.next[i]
        }
        update[i] = x
    }
    if nxt := x.next[0]; nxt != nil && nxt.key == key {
        nxt.val = val
        return
    }

    lv := s.randomLevel()
    if lv > s.level { // 新层的前驱都是头节点
        for i := s.level; i < lv; i++ {
            update[i] = s.head
        }
        s.level = lv
    }
    n := &skipNode{key: key, val: val, next: make([]*skipNode, lv)}
    for i := 0; i < lv; i++ { // 逐层链入，与链表插入完全一样
        n.next[i] = update[i].next[i]
        update[i].next[i] = n
    }
}
```

⭐ **注意插入代码有多简单**：没有旋转，没有情形分析，就是"在每一层做一次普通的链表插入"。这就是随机化路线最大的工程价值。

### 期望复杂度分析

**期望层数**：节点层数服从几何分布，`E[层数] = 1/(1−p)`。p = 1/2 时是 2，p = 1/4 时是 1.33。

**期望空间**：`n · 1/(1−p)` 个指针。p = 1/4 时约 1.33n——**比红黑树的 2n 个孩子指针还省**。

**期望高度**：第 i 层有节点的概率是 p^{i−1}，最高层约为 `log_{1/p} n`，**期望 Θ(log n)**。

**期望查找代价**：⭐ **倒着分析**——从目标节点反向走查找路径。在任意位置，路径要么向左（该节点在这一层继续存在，概率 p），要么向上（概率 1−p）：

```
设 C(k) = 向上爬 k 层的期望步数
C(k) = (1−p)(1 + C(k−1)) + p(1 + C(k))
     = 1/(1−p) + C(k−1)
⟹ C(k) = k/(1−p)
```

层数是 Θ(log n)，故**期望查找代价 = Θ(log n)**。∎

**高概率界**：可以进一步证明，查找代价超过 `c log n` 的概率是 `O(1/n^α)`。**n = 10⁶ 时退化的概率小到可以忽略。**

---

## 三、为什么 Redis 和 LevelDB 选跳表

| 优势 | 说明 |
|---|---|
| **实现简单** | 插入删除就是链表操作，无旋转、无情形分析。代码量约为红黑树的 1/3 |
| **范围查询天然高效** | 第 0 层就是有序链表，定位后直接顺序遍历 |
| **并发友好** | ⭐ 修改只影响局部指针，容易做**无锁**或细粒度锁；平衡树的旋转要锁住整棵子树 |
| **空间可调** | 通过 p 在空间与时间之间连续调节 |

**Redis 的 zset（有序集合）** 用"跳表 + 散列表"组合：跳表支持 `ZRANGE`、`ZRANK` 等有序操作，散列表支持 `ZSCORE` 的 O(1) 查询。Redis 作者 antirez 明确说过选择跳表的理由就是**实现简单和范围查询友好**。

**LevelDB / RocksDB 的 MemTable** 用跳表：因为需要"多读者并发 + 单写者"的场景，跳表的无锁读实现远比平衡树容易。

⚠️ **跳表的劣势**：缓存局部性差（每层都是指针追逐）、每个节点是变长的、最坏情况理论上仍是 O(n)（概率极低）。所以在**单线程、纯内存、追求极致性能**的场景，B 树往往更快（[第 18 讲]({{< ref "18-b-trees.md" >}})）。

---

## 四、Treap

**Treap = Tree + Heap**。每个节点有两个值：

- **key**：满足 **BST 性质**（左小右大）
- **priority**：满足 **堆性质**（父节点优先级高于子节点）

**插入时优先级取随机数。**

```
     (key, priority)
        (30, 95)
       ╱        ╲
   (10, 60)    (50, 70)
     ╱           ╱    ╲
 (5, 20)    (40, 35) (70, 55)

按 key 看是 BST；按 priority 看是最大堆
```

### ⭐ 关键定理

> **给定一组互异的 key 和互异的 priority，满足两个性质的树是唯一的。**

**证明**：优先级最大的必须是根（堆性质），其余节点按 key 与根比较分到左右子树（BST 性质），递归即可。∎

**推论（这才是重点）**：随机分配优先级得到的 Treap，**其形状与"按 key 的随机排列依次插入 BST"完全同分布**——因为优先级的大小顺序就相当于插入顺序。

由[第 15 讲]({{< ref "15-binary-search-trees.md" >}})的结论，**随机 BST 的期望高度是 O(log n)**（约 4.311·ln n ≈ 2.99 log₂ n），所以 **Treap 的期望高度也是 O(log n)，且与 key 的插入顺序无关**。

⭐ **这就是 Treap 的全部魅力：它把"随机插入序列"这个我们控制不了的假设，变成了"随机优先级"这个我们完全控制的东西。**

### 实现

```go
type treapNode struct {
    key         int
    pri         uint32
    left, right *treapNode
}

func rotateRight(y *treapNode) *treapNode {
    x := y.left
    y.left = x.right
    x.right = y
    return x
}

func rotateLeft(x *treapNode) *treapNode {
    y := x.right
    x.right = y.left
    y.left = x
    return y
}

func insert(t *treapNode, key int, rng *rand.Rand) *treapNode {
    if t == nil {
        return &treapNode{key: key, pri: rng.Uint32()}
    }
    if key < t.key {
        t.left = insert(t.left, key, rng)
        if t.left.pri > t.pri { // 违反堆序，上浮
            t = rotateRight(t)
        }
    } else if key > t.key {
        t.right = insert(t.right, key, rng)
        if t.right.pri > t.pri {
            t = rotateLeft(t)
        }
    }
    return t
}

func remove(t *treapNode, key int) *treapNode {
    if t == nil {
        return nil
    }
    switch {
    case key < t.key:
        t.left = remove(t.left, key)
    case key > t.key:
        t.right = remove(t.right, key)
    default:
        // 把目标节点旋转下沉，直到它成为叶子
        switch {
        case t.left == nil:
            return t.right
        case t.right == nil:
            return t.left
        case t.left.pri > t.right.pri:
            t = rotateRight(t)
            t.right = remove(t.right, key)
        default:
            t = rotateLeft(t)
            t.left = remove(t.left, key)
        }
    }
    return t
}
```

**插入：像 BST 一样插到叶子，然后按优先级旋转上浮。删除：旋转下沉到叶子再摘掉。** 期望旋转次数 O(1)，期望深度 O(log n)。

---

## 五、split 与 merge：Treap 最有价值的能力

Treap 有一对普通平衡树很难提供的原语：

```
split(t, k)  →  (L, R)：把 t 按 key 拆成"全 < k"和"全 ≥ k"两棵 Treap
merge(L, R)  →  t     ：合并两棵 Treap（要求 L 的所有 key < R 的所有 key）
```

```go
func split(t *treapNode, k int) (l, r *treapNode) {
    if t == nil {
        return nil, nil
    }
    if t.key < k {
        l2, r2 := split(t.right, k)
        t.right = l2
        return t, r2
    }
    l2, r2 := split(t.left, k)
    t.left = r2
    return l2, t
}

func merge(l, r *treapNode) *treapNode {
    switch {
    case l == nil:
        return r
    case r == nil:
        return l
    case l.pri > r.pri:
        l.right = merge(l.right, r)
        return l
    default:
        r.left = merge(l, r.left)
        return r
    }
}
```

**两者都是期望 O(log n)。** 有了它们，很多操作变得平凡：

| 操作 | 实现 |
|---|---|
| 插入 k | `split(t,k)` → `merge(merge(L, 新节点), R)` |
| 删除 k | `split` 两次，丢掉中间那棵，`merge` 两边 |
| **删除区间 [a,b)** | 两次 split，丢掉中间整棵子树，一次 merge——**O(log n)** |
| **区间聚合/翻转** | 把区间 split 出来，在子树根上打懒标记 |

⭐ **"把一个区间整体摘出来"这个能力**是普通平衡树做不到的，它让 Treap 成为竞赛中处理**区间操作序列**（文本编辑器的 rope、可持久化数据结构）的首选。改用**按大小 split**（而不是按 key），Treap 就变成一个支持 O(log n) 任意位置插入删除的**序列**结构——正是[第 5 讲]({{< ref "05-arrays-linked-lists.md" >}})末尾提到的"数组与链表都做不到的那个结构"。

---

## 六、伸展树：另一种"不平衡"的平衡

**伸展树（splay tree）** 不用随机数，也不维护任何平衡信息。它只有一条规则：

> **每次访问一个节点，就通过一系列旋转把它转到根。**

旋转采用 zig / zig-zig / zig-zag 三种模式（关键是 zig-zig 要**先转祖父再转父**，而不是连续两次单旋——这才能让路径长度减半）。

| 性质 | 值 |
|---|---|
| 单次操作 | 最坏 O(n) |
| **摊还** | **O(log n)**（势能函数 `Φ = Σ log(子树大小)`，[第 4 讲]({{< ref "04-amortized-analysis.md" >}})） |
| 额外空间 | **0**（不存高度、颜色、优先级） |
| **工作集性质** | 最近访问过的元素**下次访问更快** |

⭐ **工作集性质是伸展树独有的**：如果访问模式有局部性（80% 的请求集中在 20% 的数据），伸展树会自动把热点数据聚集在根附近，实际性能可以**优于**任何静态平衡树。这也是缓存、词法分析器中它被选用的原因。

⚠️ 代价：**每次读操作也要写树**（旋转），这对并发和只读缓存极不友好。

---

## 七、对比

| | AVL | 红黑树 | B 树 | **跳表** | **Treap** | **伸展树** |
|---|---|---|---|---|---|---|
| 平衡机制 | 高度不变式 | 颜色不变式 | 半满约束 | **随机层数** | **随机优先级** | **访问即旋转** |
| 保证类型 | 最坏 | 最坏 | 最坏 | **期望/高概率** | **期望** | **摊还** |
| 实现复杂度 | 中 | **高** | 中 | **低** | **低** | 中 |
| 额外空间/节点 | 高度 | 1 bit | 键数组 | 1.33 指针 | 优先级 | **0** |
| 并发友好 | 差 | 差 | 中 | **好** | 中 | **很差** |
| 特殊能力 | — | — | 磁盘友好 | 范围扫描 | **split/merge** | **工作集性质** |
| 代表用户 | 数据库内存索引 | Linux、STL | 所有数据库 | **Redis、LevelDB** | 竞赛、rope | 缓存 |

⭐ **一条实用建议**：需要自己实现一个有序结构时，**跳表和 Treap 是正确的默认选择**。它们在 100 行内可以写对，性能与红黑树同阶，而红黑树的删除很可能写出隐蔽的 bug。**把复杂度花在你的业务上，而不是花在重新实现一个 1972 年的数据结构上。**

---

## 随堂自测

1. 随机化平衡与确定性平衡的保证有什么本质区别？为什么前者对"对抗性输入"仍然安全？
2. 跳表的期望层数、期望空间与 p 的关系是什么？p = 1/4 相比 p = 1/2 各有什么取舍？
3. 用"倒着走查找路径"的方法推导跳表期望查找代价 Θ(log n)。
4. 为什么跳表比平衡树更容易做并发？举一个具体的实现困难来说明平衡树的问题。
5. 证明：给定互异的 key 与互异的 priority，Treap 的形状唯一。
6. 为什么随机优先级的 Treap 等价于随机顺序插入的 BST？这个等价为什么重要？
7. 写出 Treap 的 `split` 与 `merge`，说明如何用它们在 O(log n) 内删除整个区间 [a, b)。
8. 伸展树的摊还 O(log n) 用什么势能函数证明？什么是工作集性质？
9. 伸展树"读操作也要写树"会在什么场景造成问题？
10. 你要给自己的项目实现一个有序 map，只能用 200 行代码，你选什么？为什么不选红黑树？

