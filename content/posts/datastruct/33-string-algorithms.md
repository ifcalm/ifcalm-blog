---
title: "第 33 讲：字符串算法——KMP、Rabin-Karp、Trie 与后缀结构"
date: 2026-08-28
weight: 33
tags: ["数据结构与算法"]
draft: false
summary: "朴素匹配为什么退化、KMP 失配函数的含义与线性时间的摊还论证、Rabin-Karp 的滚动哈希与多模式匹配、Trie 与 Aho-Corasick 自动机、后缀数组与 Z 函数，以及各方案的选型。"
showToc: true
tocOpen: false
---

## 一、字符串匹配问题

> **输入**：文本 T（长度 n）、模式 P（长度 m）
> **输出**：P 在 T 中所有出现的位置

**朴素做法**：在每个位置尝试匹配。

```go
func NaiveSearch(text, pat string) []int {
    var res []int
    for i := 0; i+len(pat) <= len(text); i++ {
        j := 0
        for j < len(pat) && text[i+j] == pat[j] {
            j++
        }
        if j == len(pat) {
            res = append(res, i)
        }
    }
    return res
}
```

**最坏 Θ(nm)**：

```
T = "aaaaaaaaaaaaaaab"
P = "aaaab"

每个位置都匹配 4 个字符才失败 ⟹ 4n 次比较
```

⚠️ **朴素算法的浪费在哪？** 失配后它把文本指针**回退**到 i+1 重新开始，**丢弃了刚刚获得的所有信息**。已经知道前 j 个字符匹配这个事实，本可以告诉我们下一次该从哪里开始。

**KMP 就是把这个信息利用起来。**

---

## 二、KMP 算法

### 失配函数

> **定义**：`π[i]` = 模式串 `P[0..i]` 的**最长真前缀**的长度，且该前缀同时也是 `P[0..i]` 的后缀。（真 = 不等于整个串）

```
P:     a  b  a  b  a  c  a
i:     0  1  2  3  4  5  6
π[i]:  0  0  1  2  3  0  1

π[4] = 3 表示 "ababa" 的最长 border 是 "aba"（长 3）
```

⭐ **π 的含义**："如果在位置 i+1 失配，我已经匹配上的后 π[i] 个字符，正好等于模式的前 π[i] 个字符——所以模式串可以直接往右滑，让这 π[i] 个字符对齐，**文本指针一步都不用回退**。"

```
文本:  ... a b a b a X ...
模式:      a b a b a c
                ↑ 在这里失配（X ≠ c）

π[4] = 3 ⟹ 模式滑动，让 "aba" 对齐：
文本:  ... a b a b a X ...
模式:          a b a b a c
                     ↑ 从这里继续比较
```

### 构造 π（自我匹配）

```go
func buildPrefixFunction(pat string) []int {
    pi := make([]int, len(pat))
    k := 0 // 当前最长 border 的长度
    for i := 1; i < len(pat); i++ {
        for k > 0 && pat[i] != pat[k] {
            k = pi[k-1] // ⭐ 失配则回退到更短的 border
        }
        if pat[i] == pat[k] {
            k++
        }
        pi[i] = k
    }
    return pi
}
```

⭐ **`k = pi[k-1]` 这一行是 KMP 的灵魂**：当前 border 用不上，就退到"border 的 border"——这本身是一个递归结构。

### 匹配

```go
func KMPSearch(text, pat string) []int {
    if len(pat) == 0 {
        return nil
    }
    pi := buildPrefixFunction(pat)
    var res []int
    k := 0
    for i := 0; i < len(text); i++ { // ⭐ i 永不回退
        for k > 0 && text[i] != pat[k] {
            k = pi[k-1]
        }
        if text[i] == pat[k] {
            k++
        }
        if k == len(pat) {
            res = append(res, i-len(pat)+1)
            k = pi[k-1] // 继续找下一个匹配（支持重叠）
        }
    }
    return res
}
```

### ⭐ 复杂度：Θ(n + m) 的摊还论证

内层 `for` 看起来可能循环很多次，为什么总代价是线性的？

**用[第 4 讲]({{< ref "04-amortized-analysis.md" >}})的势能法**：取 `Φ = k`（当前匹配长度）。

```
外层每次迭代：k 最多增加 1  ⟹  Φ 最多增加 n
内层每次迭代：k 严格减少（因为 pi[k−1] < k）  ⟹  Φ 减少 ≥ 1
```

**k 的总增量 ≤ n，且 k ≥ 0，所以内层循环的总次数 ≤ n。** 总代价 Θ(n)。构造 π 同理是 Θ(m)。∎

⭐ **这与[第 6 讲]({{< ref "06-stacks-queues.md" >}})单调栈"每个元素进出各一次"是完全相同的论证模式。** 认出这个模式，很多"看起来是 O(n²)"的循环都能证明是 O(n)。

---

## 三、Rabin-Karp 与滚动哈希

**思路**：把字符串映射成数字，用**哈希值比较**代替逐字符比较。

**滚动哈希**：从 `T[i..i+m−1]` 的哈希 O(1) 算出 `T[i+1..i+m]` 的哈希：

```
hash(s) = (s[0]·b^{m−1} + s[1]·b^{m−2} + … + s[m−1]) mod p

滚动：  new = ( (old − s[i]·b^{m−1}) · b + s[i+m] ) mod p
```

```go
func RabinKarp(text, pat string) []int {
    const base, mod = 256, 1_000_000_007
    n, m := len(text), len(pat)
    if m > n || m == 0 {
        return nil
    }

    h := 1 // b^(m-1) mod p
    for i := 0; i < m-1; i++ {
        h = h * base % mod
    }

    patHash, winHash := 0, 0
    for i := 0; i < m; i++ {
        patHash = (patHash*base + int(pat[i])) % mod
        winHash = (winHash*base + int(text[i])) % mod
    }

    var res []int
    for i := 0; i+m <= n; i++ {
        if winHash == patHash && text[i:i+m] == pat { // ⚠️ 必须验证，防哈希碰撞
            res = append(res, i)
        }
        if i+m < n {
            winHash = ((winHash-int(text[i])*h%mod+mod)%mod*base + int(text[i+m])) % mod
        }
    }
    return res
}
```

| | 复杂度 |
|---|---|
| 期望 | **Θ(n + m)** |
| 最坏（大量哈希碰撞） | Θ(nm) |

⚠️ **必须做字符串验证**，否则哈希碰撞会导致误报。

⚠️ **对抗性输入**：固定的模数和基数可以被构造出大量碰撞（这与[第 7 讲]({{< ref "07-hash-tables-chaining.md" >}})的散列洪水攻击是同一回事）。**解法同样是随机化**：运行时随机选取 base 和 mod。

### ⭐ Rabin-Karp 的真正优势：多模式匹配

单模式匹配 KMP 更稳。**但要在文本中同时查找 k 个等长模式时**，Rabin-Karp 只需把 k 个模式的哈希放进一个集合，然后扫一遍文本：

```
Θ(n + Σ|Pᵢ|)    而 KMP 要跑 k 遍
```

**应用**：抄袭检测（Rabin 指纹）、rsync 的分块同步、二维模式匹配、Karp-Rabin 指纹去重。

---

## 四、Trie

**Trie（前缀树 / 字典树）**：把公共前缀合并成同一条路径。

```
插入 "cat", "car", "card", "dog"

          root
         ╱    ╲
        c      d
        │      │
        a      o
       ╱ ╲     │
      t   r    g●
      ●   ●
          │
          d●
     ● 表示单词结尾
```

```go
type TrieNode struct {
    children [26]*TrieNode
    isEnd    bool
}

type Trie struct{ root *TrieNode }

func NewTrie() *Trie { return &Trie{root: &TrieNode{}} }

func (t *Trie) Insert(word string) {
    node := t.root
    for i := 0; i < len(word); i++ {
        c := word[i] - 'a'
        if node.children[c] == nil {
            node.children[c] = &TrieNode{}
        }
        node = node.children[c]
    }
    node.isEnd = true
}

func (t *Trie) Search(word string) bool {
    node := t.find(word)
    return node != nil && node.isEnd
}

func (t *Trie) StartsWith(prefix string) bool { return t.find(prefix) != nil }

func (t *Trie) find(s string) *TrieNode {
    node := t.root
    for i := 0; i < len(s); i++ {
        c := s[i] - 'a'
        if node.children[c] == nil {
            return nil
        }
        node = node.children[c]
    }
    return node
}
```

| 操作 | 复杂度 |
|---|---|
| 插入 / 查找 / 前缀查询 | **Θ(L)**（L = 字符串长度，**与 Trie 中单词数量无关**） |
| 空间 | O(总字符数 × 字符集大小) |

⭐ **Trie 相对散列表的两个优势**：
1. **支持前缀查询**（自动补全、IP 路由的最长前缀匹配）
2. **查找代价与集合大小无关**——散列表要算完整个字符串的哈希，Trie 在第一个不匹配的字符就返回

⚠️ **空间是主要问题**：每个节点 26 个指针（Go 中 208 字节）。优化方案：

| 优化 | 做法 |
|---|---|
| **压缩 Trie（Radix Tree / Patricia）** | 把只有一个孩子的链压成一条边。Linux 内核路由表、Redis 的 rax 用它 |
| 双数组 Trie | 用两个整数数组表示，空间极省，中文分词常用 |
| **用 map 代替数组** | 稀疏时省空间，代价是常数变大 |
| DAWG / 有向无环词图 | 合并相同后缀，进一步压缩 |

**应用**：自动补全、拼写检查、IP 路由表、词法分析、[第 8 讲]({{< ref "08-hash-tables-open-addressing.md" >}})之外的另一种字符串索引方案。

### Aho-Corasick 自动机

**Trie + KMP 的失配指针 = 多模式匹配的最优解。**

```
① 把所有模式串建成 Trie
② 用 BFS 给每个节点建 fail 指针（指向"最长真后缀所对应的节点"）
③ 在文本上跑一遍自动机，沿 fail 指针收集所有匹配
```

**复杂度 Θ(n + Σ|Pᵢ| + 匹配数)**——**一遍扫描找出所有模式的所有出现**。

⭐ **fail 指针就是 Trie 上的 π 函数**：KMP 是"单串上的自动机"，AC 自动机是"多串上的自动机"。理解了 KMP 就理解了 AC 的一半。

**应用**：敏感词过滤、入侵检测（Snort 规则匹配）、病毒特征扫描、生物序列搜索。

---

## 五、Z 函数与后缀结构

### Z 函数（扩展 KMP）

> `z[i]` = `s` 与 `s[i:]` 的**最长公共前缀**长度。

```go
func ZFunction(s string) []int {
    n := len(s)
    z := make([]int, n)
    z[0] = n
    l, r := 0, 0 // 当前最靠右的匹配区间 [l, r)
    for i := 1; i < n; i++ {
        if i < r {
            z[i] = min(r-i, z[i-l]) // ⭐ 利用之前算过的信息
        }
        for i+z[i] < n && s[z[i]] == s[i+z[i]] {
            z[i]++
        }
        if i+z[i] > r {
            l, r = i, i+z[i]
        }
    }
    return z
}
```

**Θ(n)**（同样的摊还论证：r 单调不减）。

**用于匹配**：对 `P + "\x00" + T` 求 Z 函数，`z[i] == len(P)` 的位置就是匹配点。

⭐ **Z 函数比 KMP 更容易写对，也更容易推广**（如求"每个后缀与原串的 LCP"）。很多竞赛选手已经用它替代 KMP。

### 后缀数组

> **后缀数组** `sa[i]` = 排名第 i 的后缀的起始位置（所有后缀按字典序排序）。
> **height 数组** `h[i]` = `sa[i]` 与 `sa[i−1]` 两个后缀的最长公共前缀长度。

```
s = "banana"

后缀              排序后
0: banana         5: a
1: anana          3: ana
2: nana           1: anana
3: ana            0: banana
4: na             4: na
5: a              2: nana

sa = [5, 3, 1, 0, 4, 2]
h  = [_, 1, 3, 0, 0, 2]
```

**构造**：倍增法 Θ(n log n)、DC3/SA-IS 算法 Θ(n)。

**能解决的问题**：

| 问题 | 做法 |
|---|---|
| 模式匹配 | 在 sa 上二分，O(m log n) |
| **最长重复子串** | `max(h[i])` |
| **不同子串个数** | `n(n+1)/2 − Σ h[i]` |
| 两个串的最长公共子串 | 拼接后求 h，取分属不同串的相邻对 |
| 任意两后缀的 LCP | h 数组上的区间最小值（RMQ） |

⭐ **`height` 数组是后缀数组威力的来源**：它把"任意两个后缀的 LCP"这个二维问题变成了"数组区间最小值"这个一维问题。

**后缀自动机（SAM）**：另一种后缀结构，Θ(n) 构建，能在线处理，解决"子串出现次数""字典序第 k 小子串"等问题，功能比后缀数组更强但更难实现。

---

## 六、选型

| 场景 | 方案 | 复杂度 |
|---|---|---|
| **单模式匹配** | **KMP 或 Z 函数** | Θ(n+m) |
| 单模式、实践最快 | **Boyer-Moore**（Go 的 `strings.Index` 用其变体） | 平均**亚线性** |
| **多模式匹配** | **Aho-Corasick** | Θ(n + Σm) |
| 多个等长模式 | Rabin-Karp | 期望 Θ(n) |
| **前缀查询 / 自动补全** | **Trie / Radix Tree** | Θ(L) |
| 同一文本反复查询 | **后缀数组 / 后缀自动机** | 预处理 Θ(n)，查询 O(m log n) |
| 相似度 / 编辑距离 | DP（[第 31 讲]({{< ref "31-dynamic-programming-1.md" >}})） | Θ(nm) |
| 判重 / 指纹 | 滚动哈希 | Θ(n) |

⭐ **一条实用提醒**：**Go 的 `strings.Contains` / `strings.Index` 已经用了高度优化的实现**（短模式用暴力 + SIMD，长模式用 Rabin-Karp 变体和 Boyer-Moore 的坏字符规则）。**除非你有特殊需求（多模式、前缀查询、反复查询同一文本），不要自己实现字符串匹配。**

**关键区分**：
- **文本固定、模式多变** → 对文本做预处理（后缀数组/自动机）
- **模式固定、文本流式** → 对模式做预处理（KMP/AC 自动机）

---

## 随堂自测

1. 朴素匹配的浪费在哪里？KMP 利用了什么信息？
2. π[i] 的精确定义是什么？给 "aabaaab" 手工算出它的 π 数组。
3. `k = pi[k-1]` 这一行在做什么？为什么它是一个递归结构？
4. 用势能法证明 KMP 是 Θ(n+m)。势能函数取什么？
5. 滚动哈希如何在 O(1) 内从一个窗口的哈希算出下一个？为什么必须做字符串验证？
6. Rabin-Karp 什么时候优于 KMP？
7. Trie 的查找复杂度为什么与集合大小无关？相比散列表它多了什么能力？
8. AC 自动机的 fail 指针与 KMP 的 π 函数是什么关系？
9. 后缀数组的 height 数组能直接解决哪三个问题？
10. "文本固定模式多变"和"模式固定文本流式"分别该预处理哪一边？

---

> **上一讲**：[第 32 讲：动态规划 II]({{< ref "32-dynamic-programming-2.md" >}})　**下一讲**：[第 34 讲：NP 完全性与应对 NP 难问题]({{< ref "34-np-completeness.md" >}})
