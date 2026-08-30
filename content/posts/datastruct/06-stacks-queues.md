---
title: "第 6 讲：栈、队列与双端队列"
date: 2026-08-28
weight: 6
tags: ["数据结构与算法"]
draft: false
summary: "三种受限序列 ADT 的 Go 实现与应用：栈与括号匹配、表达式求值、显式栈消除递归；环形缓冲队列的容量判定技巧；单调栈与单调队列这两个把 O(n²) 降成 O(n) 的模式。"
showToc: true
tocOpen: false
---

## 一、为什么要"受限"的结构

栈和队列能做的事，动态数组全都能做。那为什么还要单独定义它们？

**因为限制本身就是价值。** 一个只暴露 `Push/Pop` 的接口向读者承诺了"这里是后进先出的处理顺序"，而一个暴露 `Get(i)` 的接口什么也没承诺。**受限的 ADT 让不变式写在类型里，而不是写在注释里。**

| ADT | 访问规则 | 一句话 |
|---|---|---|
| 栈 Stack | LIFO（后进先出） | 只碰最近放进去的那个 |
| 队列 Queue | FIFO（先进先出） | 按到达顺序处理 |
| 双端队列 Deque | 两端都能进出 | 前两者的超集 |

---

## 二、栈

```go
type Stack[T any] struct{ data []T }

func (s *Stack[T]) Push(x T) { s.data = append(s.data, x) } // 摊还 O(1)

func (s *Stack[T]) Pop() (T, bool) { // O(1)
    var zero T
    if len(s.data) == 0 {
        return zero, false
    }
    n := len(s.data) - 1
    x := s.data[n]
    s.data[n] = zero // 断开引用，避免底层数组持有对象（见第 5 讲）
    s.data = s.data[:n]
    return x, true
}

func (s *Stack[T]) Peek() (T, bool) {
    var zero T
    if len(s.data) == 0 {
        return zero, false
    }
    return s.data[len(s.data)-1], true
}

func (s *Stack[T]) Len() int { return len(s.data) }
```

用切片实现栈是最优选择：三个操作全是 O(1)（Push 摊还），且完全顺序访问，缓存友好。

### 应用 1：括号匹配

```go
func BalancedBrackets(s string) bool {
    pairs := map[rune]rune{')': '(', ']': '[', '}': '{'}
    var st []rune
    for _, c := range s {
        switch c {
        case '(', '[', '{':
            st = append(st, c)
        case ')', ']', '}':
            if len(st) == 0 || st[len(st)-1] != pairs[c] {
                return false
            }
            st = st[:len(st)-1]
        }
    }
    return len(st) == 0
}
```

**为什么必须是栈？** 因为嵌套结构的本质就是 LIFO：最近打开的括号必须最先关闭。同样的道理让栈成为**所有递归下降解析器**的核心。

### 应用 2：调用栈与递归消除

函数调用本身就用栈实现：每次调用压入一个**栈帧**（返回地址、参数、局部变量）。因此**任何递归都可以用显式栈改写成迭代**。

```go
// 递归版
func InorderRec(root *TreeNode, visit func(int)) {
    if root == nil { return }
    InorderRec(root.Left, visit)
    visit(root.Val)
    InorderRec(root.Right, visit)
}

// 显式栈版：等价，但栈深度可控、不会爆调用栈
func InorderIter(root *TreeNode, visit func(int)) {
    var st []*TreeNode
    cur := root
    for cur != nil || len(st) > 0 {
        for cur != nil { // 一路向左，边走边压
            st = append(st, cur)
            cur = cur.Left
        }
        cur = st[len(st)-1]
        st = st[:len(st)-1]
        visit(cur.Val)
        cur = cur.Right
    }
}
```

> Go 的 goroutine 栈是可增长的：从 2 KB 起，不够就分配更大的栈并把内容整体拷过去，**64 位系统上默认上限 1 GB**（可用 `debug.SetMaxStack` 调整）。所以爆栈没有 C 那么容易，但深度递归仍会引发反复的栈扩容与拷贝。**递归深度可能达到 Θ(n) 时（如退化的二叉搜索树），显式栈更稳。**

### 应用 3：表达式求值

中缀 → 后缀（逆波兰）用 **Shunting-yard 算法**，后缀求值只需一个栈：

```go
func EvalRPN(tokens []string) int {
    var st []int
    for _, t := range tokens {
        switch t {
        case "+", "-", "*", "/":
            b, a := st[len(st)-1], st[len(st)-2]
            st = st[:len(st)-2]
            var r int
            switch t {
            case "+": r = a + b
            case "-": r = a - b
            case "*": r = a * b
            case "/": r = a / b
            }
            st = append(st, r)
        default:
            n, _ := strconv.Atoi(t)
            st = append(st, n)
        }
    }
    return st[0]
}
```

---

## 三、队列

### ⚠️ 用切片直接实现队列是错的

```go
// 反面教材
func (q *Queue) Dequeue() int {
    x := q.data[0]
    q.data = q.data[1:] // 看起来 O(1)……
    return x
}
```

这段代码的 `Dequeue` 确实是 O(1)，但**底层数组永远不会被回收**：`q.data` 一直指向原数组的中后段，前面出队的部分成了永久泄漏的内存。入队 n 次出队 n 次后，占用仍是 Θ(n)，而且如果继续 append，会不断分配新数组。

**正确做法是环形缓冲（circular buffer）。**

### 环形缓冲

```
容量 8，head=5, size=4：

  索引:  0    1    2    3    4    5    6    7
       ┌────┬────┬────┬────┬────┬────┬────┬────┐
       │ 92 │ 17 │    │    │    │ 45 │ 63 │ 88 │
       └────┴────┴────┴────┴────┴────┴────┴────┘
         ▲                        ▲
      尾部绕回                   head
       元素顺序：45 → 63 → 88 → 92 → 17
```

```go
type Queue[T any] struct {
    data []T
    head int // 队首下标
    size int // 元素个数
}

func NewQueue[T any](capacity int) *Queue[T] {
    if capacity < 1 { capacity = 1 }
    return &Queue[T]{data: make([]T, capacity)}
}

func (q *Queue[T]) Enqueue(x T) { // 摊还 O(1)
    if q.size == len(q.data) {
        q.grow()
    }
    q.data[(q.head+q.size)%len(q.data)] = x
    q.size++
}

func (q *Queue[T]) Dequeue() (T, bool) { // O(1)
    var zero T
    if q.size == 0 {
        return zero, false
    }
    x := q.data[q.head]
    q.data[q.head] = zero // 断开引用
    q.head = (q.head + 1) % len(q.data)
    q.size--
    return x, true
}

func (q *Queue[T]) grow() {
    grown := make([]T, 2*len(q.data))
    for i := 0; i < q.size; i++ { // 展平：搬运时顺便解开环绕
        grown[i] = q.data[(q.head+i)%len(q.data)]
    }
    q.data, q.head = grown, 0
}
```

### ⭐ 为什么要存 `size` 而不是 `tail`

如果只存 `head` 和 `tail`，"空"与"满"都表现为 `head == tail`，**无法区分**。三种标准解法：

| 方案 | 做法 | 代价 |
|---|---|---|
| **存 size**（上面用的） | 显式记录元素个数 | 多一个字段，最清晰 |
| **浪费一格** | 规定 `(tail+1)%cap == head` 为满，容量只用 cap−1 | 少存一个元素 |
| **存总入队/出队计数** | `size = enqueued − dequeued` | 需处理溢出 |

⚠️ 另一个细节：容量取 **2 的幂** 时，`% len(q.data)` 可以换成 `& (len(q.data)-1)`。取模是几十个周期的除法指令，位与是一个周期——在高吞吐队列（如网络收发环）里这是实打实的优化。

### Go 里的另一个选择：channel

```go
ch := make(chan int, 128) // 带缓冲的 channel 本质就是一个环形队列 + 锁 + 等待队列
ch <- x                   // 入队（满时阻塞）
x := <-ch                 // 出队（空时阻塞）
```

Go runtime 的 `hchan` 内部正是环形缓冲。**但 channel 带同步语义和调度开销**，单 goroutine 内部的算法（如 BFS）应该用上面的裸队列，不要用 channel。

---

## 四、双端队列

两端都支持 O(1) 插入删除。实现上就是环形缓冲的两端版本：

```go
type Deque[T any] struct {
    data []T
    head int
    size int
}

func (d *Deque[T]) PushBack(x T) {
    if d.size == len(d.data) { d.grow() }
    d.data[(d.head+d.size)%len(d.data)] = x
    d.size++
}

func (d *Deque[T]) PushFront(x T) {
    if d.size == len(d.data) { d.grow() }
    d.head = (d.head - 1 + len(d.data)) % len(d.data) // 注意负数取模
    d.data[d.head] = x
    d.size++
}
```

⚠️ `(d.head - 1) % n` 在 Go 中对负数返回负值（与 C 相同，与 Python 不同），必须写成 `(d.head - 1 + n) % n`。

---

## 五、两个把 O(n²) 变成 O(n) 的模式

这两个模式在面试和竞赛中出现频率极高，本质都是**摊还分析**（[第 4 讲]({{< ref "04-amortized-analysis.md" >}})）：每个元素最多进栈/队一次、出栈/队一次。

### 模式 1：单调栈——"下一个更大元素"

**问题**：对数组每个位置 i，求它右边第一个比 `a[i]` 大的元素的下标。

朴素做法 O(n²)。单调栈做法 O(n)：

```go
// 返回 next[i]：右边第一个 a[j] > a[i] 的下标 j，不存在则 -1
func NextGreater(a []int) []int {
    n := len(a)
    next := make([]int, n)
    var st []int // 存下标，对应的值从栈底到栈顶严格递减
    for i := 0; i < n; i++ {
        for len(st) > 0 && a[st[len(st)-1]] < a[i] {
            next[st[len(st)-1]] = i // a[i] 就是它要找的答案
            st = st[:len(st)-1]
        }
        st = append(st, i)
    }
    for _, j := range st { // 栈里剩下的没有更大元素
        next[j] = -1
    }
    return next
}
```

**不变式**：栈中下标对应的值**从栈底到栈顶递减**。

**为什么是 O(n)？** 内层 while 看起来可能循环很多次，但**每个下标只入栈一次、出栈一次**，所有内层循环次数之和 ≤ n。这是记账法的直接应用：入栈时预付出栈费用。

**典型应用**：柱状图中最大矩形、接雨水、股票跨度、每日温度。

### 模式 2：单调队列——滑动窗口最大值

**问题**：长度为 k 的窗口在数组上滑动，每个位置求窗口内最大值。

```go
func MaxSlidingWindow(a []int, k int) []int {
    var dq []int // 存下标，对应值从队首到队尾递减；队首始终是窗口最大值
    res := make([]int, 0, len(a)-k+1)
    for i, v := range a {
        // ① 队首过期就弹出
        if len(dq) > 0 && dq[0] <= i-k {
            dq = dq[1:]
        }
        // ② 从队尾弹掉所有不可能再成为最大值的元素
        for len(dq) > 0 && a[dq[len(dq)-1]] <= v {
            dq = dq[:len(dq)-1]
        }
        dq = append(dq, i)
        if i >= k-1 {
            res = append(res, a[dq[0]])
        }
    }
    return res
}
```

⭐ **第 ② 步的洞察**：如果 `a[j] <= a[i]` 且 `j < i`，那么 j **永远**不可能再是最大值——只要 j 在窗口里，i 也在。所以可以直接扔掉。这个"被更年轻更强的人淘汰"的论证叫**支配关系剪枝**，是单调队列类问题的通用思路。

同样每个元素进出各一次，**总代价 Θ(n)**。相比之下，用堆的做法是 O(n log k)。

---

## 六、代价与选型

| ADT | 推荐实现 | Push/Pop 两端 | 随机访问 | 备注 |
|---|---|---|---|---|
| 栈 | `[]T` | 尾端 O(1) 摊还 | 有（但不该用） | 最简单，缓存最优 |
| 队列 | 环形缓冲 | 两端 O(1) 摊还 | 有 | ⚠️ 别用 `s = s[1:]` |
| 队列（跨 goroutine） | `chan T` | O(1) + 同步 | 无 | 带阻塞与调度语义 |
| 双端队列 | 环形缓冲 | 两端 O(1) 摊还 | 有 | 单调队列的载体 |
| 队列（元素巨大/需稳定指针） | 双链表 | O(1) | 无 | 见[第 5 讲]({{< ref "05-arrays-linked-lists.md" >}}) |

---

## 随堂自测

1. 为什么 `q.data = q.data[1:]` 实现出队是错的？它的渐近复杂度和实际内存行为分别是什么？
2. 环形缓冲若只存 `head` 和 `tail`，为什么无法区分空和满？给出三种解法并比较。
3. 用两个栈实现一个队列，说明每个操作的摊还代价并证明它。
4. 用一个双端队列实现栈和队列各需要哪些操作？为什么说 Deque 是二者的超集？
5. 单调栈解"下一个更大元素"为什么是 O(n) 而不是 O(n²)？用摊还分析说明。
6. 滑动窗口最大值：为什么可以直接丢弃"更早且更小"的元素？如果要求最小值，代码怎么改？
7. `(head - 1) % n` 在 Go 中对 head = 0 会得到什么？为什么必须写成 `(head - 1 + n) % n`？

