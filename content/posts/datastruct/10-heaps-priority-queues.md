---
title: "第 10 讲：堆与优先队列"
date: 2026-08-28
weight: 10
tags: ["数据结构与算法"]
draft: false
summary: "二叉堆的数组表示与堆序不变式、sift-down 与 sift-up 的实现、自底向上建堆为什么是 Θ(n) 而非 Θ(n log n) 的完整推导、堆排序、Top-K 与流式中位数的标准解法，以及各类堆的复杂度对照。"
showToc: true
tocOpen: false
---

## 一、优先队列 ADT

| 操作 | 语义 |
|---|---|
| `Push(x)` | 插入元素 |
| `Pop()` | 取出并删除**优先级最高**（最小或最大）的元素 |
| `Peek()` | 查看最高优先级元素 |
| `DecreaseKey(x, k)` | 提高某元素的优先级（Dijkstra 需要） |

**为什么不能用已有结构**：

| 实现 | Push | Pop | 问题 |
|---|---|---|---|
| 无序数组 | O(1) | **O(n)** | 每次要扫全表找最小 |
| 有序数组 | **O(n)** | O(1) | 插入要移动元素 |
| 平衡搜索树 | O(log n) | O(log n) | 可行，但常数大、维护了不需要的全序 |
| **二叉堆** | **O(log n)** | **O(log n)** | ⭐ 只维护"最小在顶"这一个弱得多的性质 |

⭐ **核心洞察：优先队列不需要全序，只需要"能拿到最小值"。** 维护更弱的不变式，就能付更少的代价——这是数据结构设计的一条通则。

---

## 二、二叉堆的两个不变式

**（1）结构性质**：是一棵**完全二叉树**——除最后一层外都填满，最后一层从左往右填。

**（2）堆序性质**（以最小堆为例）：**每个节点的值 ≤ 其所有子节点的值。**

⚠️ 注意堆序**不是**全序：左右子树之间没有任何大小关系。堆只保证根是全局最小，其他位置的相对顺序是任意的。

### 数组表示

完全二叉树可以无指针地压进数组，这是二叉堆最漂亮的地方：

```
             0:1
           ╱     ╲
      1:3          2:6
     ╱   ╲        ╱   ╲
   3:5   4:9    5:8   6:7
  ╱  ╲
7:10 8:12

数组：[1, 3, 6, 5, 9, 8, 7, 10, 12]
索引：  0  1  2  3  4  5  6   7   8
```

```
parent(i) = (i-1)/2      左child(i) = 2i+1      右child(i) = 2i+2
```

**好处**：零指针开销、完美的缓存局部性（父子在数组上相隔不远）、高度恰好是 ⌊log₂ n⌋。

**这正是[第 5 讲]({{< ref "05-arrays-linked-lists.md" >}})的结论在起作用**：能用连续数组表达的树，就不要用指针。

---

## 三、核心操作

一切都归结为两个"修复"操作：**sift-down（下沉）** 和 **sift-up（上浮）**。

### sift-down：节点太大，往下沉

```go
type MinHeap struct{ a []int }

// 假设 i 的两棵子树都是合法的堆，把 a[i] 下沉到正确位置
func (h *MinHeap) siftDown(i int) {
    n := len(h.a)
    for {
        smallest := i
        l, r := 2*i+1, 2*i+2
        if l < n && h.a[l] < h.a[smallest] {
            smallest = l
        }
        if r < n && h.a[r] < h.a[smallest] {
            smallest = r
        }
        if smallest == i {
            return // 已满足堆序
        }
        h.a[i], h.a[smallest] = h.a[smallest], h.a[i]
        i = smallest
    }
}
```

**代价**：最多走树高，**O(log n)**。

### sift-up：节点太小，往上浮

```go
func (h *MinHeap) siftUp(i int) {
    for i > 0 {
        p := (i - 1) / 2
        if h.a[p] <= h.a[i] {
            return
        }
        h.a[p], h.a[i] = h.a[i], h.a[p]
        i = p
    }
}
```

### Push 与 Pop

```go
func (h *MinHeap) Push(x int) { // O(log n)
    h.a = append(h.a, x) // 放在末尾，保持完全二叉树形状
    h.siftUp(len(h.a) - 1)
}

func (h *MinHeap) Pop() (int, bool) { // O(log n)
    if len(h.a) == 0 {
        return 0, false
    }
    top := h.a[0]
    last := len(h.a) - 1
    h.a[0] = h.a[last] // ⭐ 把最后一个元素挪到根，维持完全二叉树形状
    h.a = h.a[:last]
    if len(h.a) > 0 {
        h.siftDown(0)
    }
    return top, true
}

func (h *MinHeap) Peek() (int, bool) { // O(1)
    if len(h.a) == 0 { return 0, false }
    return h.a[0], true
}
```

⭐ **Pop 的技巧**：不能直接删掉根（会破坏完全二叉树形状），所以**把最后一个元素搬到根再下沉**。这一步同时维持了两个不变式。

---

## 四、⭐ 建堆为什么是 Θ(n)

给定一个乱序数组，就地建堆：

```go
func BuildHeap(a []int) *MinHeap {
    h := &MinHeap{a: a}
    for i := len(a)/2 - 1; i >= 0; i-- { // 从最后一个非叶节点往前
        h.siftDown(i)
    }
    return h
}
```

**为什么从后往前？** 因为 `siftDown(i)` 要求 i 的两棵子树已经是合法的堆。倒序遍历保证了这一点。

**为什么跳过 `len(a)/2` 之后的下标？** 那些全是叶节点，单个叶节点自己就是合法的堆。

### 朴素分析（松的上界）

n/2 次 siftDown，每次 O(log n) ⟹ **O(n log n)**。这个上界是对的，但不紧。

### 紧确分析

**关键观察：绝大多数节点在树的底部，而底部节点的下沉距离很短。**

高度为 h 的节点，siftDown 代价是 O(h)。完全二叉树中高度为 h 的节点最多有 `⌈n/2^{h+1}⌉` 个：

```
高度 0（叶）：  n/2   个节点，各 0 次交换
高度 1：        n/4   个节点，各 ≤ 1 次
高度 2：        n/8   个节点，各 ≤ 2 次
高度 h：        n/2^{h+1} 个节点，各 ≤ h 次
```

总代价：

```
T(n) = Σ_{h=0}^{⌊log n⌋} (n / 2^{h+1}) · O(h)
     = O(n · Σ_{h=0}^{∞} h/2^h)
```

用恒等式 `Σ_{h=0}^{∞} h·x^h = x/(1−x)²`，代入 x = 1/2：

```
Σ_{h=0}^{∞} h/2^h = (1/2)/(1/4) = 2
⟹  T(n) = O(2n) = Θ(n)                    ∎
```

⭐ **直觉版**：一半的节点是叶子，不用动；四分之一的节点最多动 1 步；八分之一最多动 2 步……**代价随节点数指数衰减，加权和收敛到常数。**

**这个结论有实际意义**：如果你要处理 n 个元素并反复取最小值，`BuildHeap` 一次 Θ(n) 比 n 次 `Push` 的 Θ(n log n) 快。Go 标准库的 `heap.Init` 就是这个 Θ(n) 版本。

⚠️ 对比：**逐个 Push 建堆确实是 Θ(n log n)**，因为 sift-up 的代价分布正好相反——大多数节点在底部，而**上浮的距离恰恰是它到根的距离**，没有"底部便宜"这个红利。

---

## 五、堆排序

```go
func HeapSort(a []int) {
    h := &maxHeap{a: a}
    n := len(a)
    for i := n/2 - 1; i >= 0; i-- { // Θ(n) 建大顶堆
        h.siftDown(i, n)
    }
    for end := n - 1; end > 0; end-- {
        a[0], a[end] = a[end], a[0] // 最大值换到末尾（已排好的位置）
        h.siftDown(0, end)          // 在剩下的 end 个元素上恢复堆序
    }
}
```

```
建堆后:  [9, 8, 6, 5, 3, 1]  堆区 ────────────────
换 9→尾: [1, 8, 6, 5, 3 | 9] 堆区 ──────────  已排序 ─
下沉修复:[8, 5, 6, 1, 3 | 9]
换 8→尾: [3, 5, 6, 1 | 8, 9]
   …
```

| 性质 | 值 |
|---|---|
| 时间 | **Θ(n log n)** 最好/平均/最坏一致 |
| 空间 | **O(1)** 原地 |
| 稳定 | **✗** |

⭐ **堆排序是唯一同时做到「最坏 Θ(n log n)」和「原地」的经典比较排序。** 归并稳定但要 Θ(n) 空间，快排原地但最坏 Θ(n²)。

**那为什么实践中很少单独用它？** 因为**缓存不友好**：siftDown 在数组上的跳跃步长是 2i+1，随着深度指数增长，几乎每一步都是缓存未命中。实测常常比快排慢 2–3 倍。

**但它有一个关键用途**：作为快速排序的**兜底**。**Introsort**（C++ `std::sort`）在递归深度超过 2 log n 时切换到堆排序，从而把最坏情况从 Θ(n²) 压到 Θ(n log n)，同时保留快排的平均性能。Go 的 pdqsort 也用了同样的兜底策略（[第 11 讲]({{< ref "11-quicksort.md" >}})）。

---

## 六、Go 标准库的 container/heap

Go 不提供泛型堆类型，而是提供一个**接口 + 算法**的组合：

```go
import "container/heap"

type IntHeap []int

func (h IntHeap) Len() int            { return len(h) }
func (h IntHeap) Less(i, j int) bool  { return h[i] < h[j] } // 改这行切换大顶/小顶
func (h IntHeap) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *IntHeap) Push(x any)         { *h = append(*h, x.(int)) }
func (h *IntHeap) Pop() any {
    old := *h
    n := len(old)
    x := old[n-1]
    *h = old[:n-1]
    return x
}

func main() {
    h := &IntHeap{5, 2, 8}
    heap.Init(h)          // Θ(n) 建堆
    heap.Push(h, 1)       // O(log n)
    x := heap.Pop(h)      // O(log n)，返回最小值
    _ = x
}
```

⚠️ **最容易踩的坑**：`IntHeap.Push/Pop` 是给 `heap` 包调用的**底层原语**（只管数组末尾的增删），**不是**用户接口。用户必须调 `heap.Push(h, x)` 而不是 `h.Push(x)`——后者会跳过 sift-up，直接破坏堆序。

---

## 七、三个标准应用

### 应用 1：Top-K

**问题**：n 个元素中找最大的 k 个（n 极大，k 很小）。

| 方法 | 复杂度 | 空间 |
|---|---|---|
| 全排序取前 k | Θ(n log n) | Θ(n) |
| **大小为 k 的最小堆** | **Θ(n log k)** | **Θ(k)** |
| 快速选择（[第 13 讲]({{< ref "13-selection.md" >}})） | 期望 Θ(n) | O(1) 原地 |

```go
// 维护一个大小为 k 的最小堆，堆顶是"当前第 k 大"
func TopK(nums []int, k int) []int {
    h := &IntHeap{}
    heap.Init(h)
    for _, x := range nums {
        if h.Len() < k {
            heap.Push(h, x)
        } else if x > (*h)[0] { // 比当前第 k 大还大，就替换掉堆顶
            heap.Pop(h)
            heap.Push(h, x)
        }
    }
    return *h
}
```

⭐ **反直觉但关键：求最大的 k 个要用最小堆。** 因为要淘汰的是"当前这 k 个里最小的那个"，堆顶必须是待淘汰者。

**为什么堆法在流式场景不可替代**：它只需要 Θ(k) 内存，且**只扫一遍**。数据是无限流时，快速选择根本无法使用。

### 应用 2：多路归并

k 个有序链表/文件合并成一个（[第 9 讲]({{< ref "09-insertion-merge-sort.md" >}})的外部排序核心）：

```
用一个大小为 k 的最小堆，存每个 run 的当前元素
每次弹出全局最小 → 写出 → 从它所在的 run 推进一个元素入堆
⟹ 总代价 Θ(N log k)，N 是元素总数
```

如果朴素地每次扫 k 个 run 找最小，是 Θ(Nk)。

### 应用 3：流式中位数（对顶堆）

**问题**：数据不断流入，任意时刻要能 O(1) 返回中位数。

```
      最大堆（存较小的一半）        最小堆（存较大的一半）
       ┌─────────────┐            ┌─────────────┐
       │  … 3  2  1  │   ◀──▶     │  4  5  6 …  │
       └──────▲──────┘            └──────▲──────┘
            堆顶 = 左半最大            堆顶 = 右半最小
                    ╲              ╱
                     中位数在这两个数之间
```

```go
type MedianFinder struct {
    lo *maxHeap // 较小的一半
    hi *minHeap // 较大的一半，size(hi) ∈ {size(lo), size(lo)+1}
}

func (m *MedianFinder) Add(x int) { // O(log n)
    heap.Push(m.hi, x)               // 先进右半
    heap.Push(m.lo, heap.Pop(m.hi))  // 右半最小移到左半（保证 lo 全部 ≤ hi）
    if m.lo.Len() > m.hi.Len() {     // 再平衡大小
        heap.Push(m.hi, heap.Pop(m.lo))
    }
}

func (m *MedianFinder) Median() float64 { // O(1)
    if m.hi.Len() > m.lo.Len() {
        return float64(m.hi.Top())
    }
    return float64(m.lo.Top()+m.hi.Top()) / 2
}
```

⭐ **`Add` 里那两行"先推给对面再拿回来"的写法很值得学**：它把"该放哪边"的判断消灭了。这又是[第 5 讲]({{< ref "05-arrays-linked-lists.md" >}})哨兵思路的变体——**用一点多余的工作换掉全部条件分支**。

---

## 八、各类堆的对比

| 堆 | Push | Pop-min | Peek | DecreaseKey | Meld（合并） |
|---|---|---|---|---|---|
| **二叉堆** | O(log n) | O(log n) | O(1) | O(log n) | O(n) |
| d 叉堆 | O(log_d n) | O(d·log_d n) | O(1) | O(log_d n) | O(n) |
| 二项堆 | O(log n) | O(log n) | O(log n) | O(log n) | **O(log n)** |
| **配对堆** | O(1) | O(log n)* | O(1) | o(log n)* | **O(1)** |
| **Fibonacci 堆** | **O(1)*** | O(log n)* | O(1) | **O(1)*** | **O(1)*** |

\* 表示摊还代价（[第 4 讲]({{< ref "04-amortized-analysis.md" >}})）

### 什么时候需要 Fibonacci 堆

Dijkstra（[第 25 讲]({{< ref "25-single-source-shortest-paths.md" >}})）的代价是

```
V 次 Pop-min + E 次 DecreaseKey

二叉堆：      O((V + E) log V)
Fibonacci 堆： O(E + V log V)      ← 稠密图 E = Θ(V²) 时明显更优
```

⚠️ **但实践中几乎没人用 Fibonacci 堆**：常数因子大、每个节点要存 4 个指针 + 度数 + 标记位、指针追逐、缓存极不友好。实测中它通常输给 **d 叉堆（d = 4）**——后者树更矮、每层的 d 个子节点在同一条缓存行上。

⭐ 这是[第 2 讲]({{< ref "02-asymptotic-analysis.md" >}})"渐近分析骗你的时候"最经典的实例：**理论最优 ≠ 实际最优。**

---

## 随堂自测

1. 堆序性质和全序有什么区别？为什么弱化不变式反而是优点？
2. 给出数组 `[16, 4, 10, 14, 7, 9, 3, 2, 8, 1]`，画出它的树形表示，并执行一次 `siftDown(1)`。
3. **证明自底向上建堆是 Θ(n)**，写出关键的求和步骤。为什么逐个 Push 建堆是 Θ(n log n)？
4. Pop 时为什么要把最后一个元素搬到根，而不是直接把根的某个子节点提上来？
5. 堆排序是原地且最坏 Θ(n log n)，为什么实践中还是快排更常用？
6. 求最大的 k 个元素，为什么用**最小堆**而不是最大堆？堆里应该存 k 个还是 n 个元素？
7. Top-K 有堆法（Θ(n log k)）和快速选择（期望 Θ(n)）两种，什么场景下必须用堆法？
8. 对顶堆求中位数：为什么 `Add` 要先把元素推进 hi、再从 hi 弹到 lo？直接判断该进哪边有什么问题？
9. Dijkstra 用 Fibonacci 堆理论更优，为什么实测常常输给 4 叉堆？

