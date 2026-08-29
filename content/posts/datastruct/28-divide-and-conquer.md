---
title: "第 28 讲：分治法"
date: 2026-08-28
weight: 28
tags: ["数据结构与算法"]
draft: false
summary: "分治的三步框架与适用判据、最大子数组、Karatsuba 大整数乘法、Strassen 矩阵乘法为什么能省下一次乘法、平面最近点对的 Θ(n log n) 与「只需检查 7 个点」的证明、快速幂与快速傅里叶变换。"
showToc: true
tocOpen: false
---

## 一、框架与适用判据

**分治三步**（[第 3 讲]({{< ref "03-recurrences.md" >}})）：

```
Divide：  把问题分成若干个规模更小的同类子问题
Conquer： 递归求解子问题（小到一定程度直接解）
Combine： 把子问题的解合并成原问题的解
```

**什么时候适合分治？**

| 条件 | 说明 |
|---|---|
| **① 子问题同构** | 子问题与原问题是同一类型，只是规模更小 |
| **② 子问题独立** | ⭐ 子问题之间**不重叠**——重叠了就该用动态规划（[第 31 讲]({{< ref "31-dynamic-programming-1.md" >}})） |
| **③ 合并高效** | 合并的代价要低于直接求解 |

⭐ **条件 ② 是分治与动态规划的分界线**：斐波那契数的"分治"会指数级重复计算 F(n−2)，因为子问题重叠——这时必须记忆化。

**已经学过的分治算法**：归并排序、快速排序、快速选择、BFPRT、二分查找、树的各种递归遍历。

---

## 二、最大子数组

> **问题**：数组 A 中找一个连续子数组，使其元素和最大。

**分治思路**：以中点划分，最大子数组只有三种可能：

```
      ┌──────────────┬──────────────┐
      │    左半       │    右半      │
      └──────────────┴──────────────┘
        ①完全在左半    ②完全在右半
        ③─────跨越中点─────
```

```go
func maxSubarrayDC(a []int, lo, hi int) int {
    if lo == hi {
        return a[lo]
    }
    mid := (lo + hi) / 2

    // ③ 跨越中点：必须包含 a[mid] 和 a[mid+1]，从中间向两边扩展
    leftBest, sum := math.MinInt, 0
    for i := mid; i >= lo; i-- {
        sum += a[i]
        leftBest = max(leftBest, sum)
    }
    rightBest, sum := math.MinInt, 0
    for i := mid + 1; i <= hi; i++ {
        sum += a[i]
        rightBest = max(rightBest, sum)
    }

    return max(maxSubarrayDC(a, lo, mid),
               maxSubarrayDC(a, mid+1, hi),
               leftBest+rightBest)
}
```

**递归式** `T(n) = 2T(n/2) + Θ(n) ⟹ Θ(n log n)`。

⚠️ **但这个问题有 Θ(n) 的解法**——Kadane 算法（一个一维 DP）：

```go
func maxSubarray(a []int) int {
    best, cur := a[0], a[0]
    for _, x := range a[1:] {
        cur = max(x, cur+x) // 要么接上前面，要么从这里重新开始
        best = max(best, cur)
    }
    return best
}
```

⭐ **教训：分治不总是最优解。** 这个问题的最优子结构其实是线性的（"以 i 结尾的最大子数组"只依赖 i−1），因此 DP 更合适。**遇到问题先问"子问题之间是什么依赖关系"，而不是先套框架。**

---

## 三、Karatsuba：大整数乘法

**朴素竖式乘法是 Θ(n²)**（n 位数）。

**朴素分治**：把 n 位数拆成两半：

```
x = x₁·10^(n/2) + x₀
y = y₁·10^(n/2) + y₀

xy = x₁y₁·10^n + (x₁y₀ + x₀y₁)·10^(n/2) + x₀y₀
```

需要 **4 次** n/2 位的乘法：`T(n) = 4T(n/2) + Θ(n) ⟹ Θ(n²)`——**毫无改进**。

### ⭐ Karatsuba 的技巧（1960）

**观察**：中间项 `x₁y₀ + x₀y₁` 可以由已算出的两项间接得到：

```
(x₁ + x₀)(y₁ + y₀) = x₁y₁ + (x₁y₀ + x₀y₁) + x₀y₀
⟹ x₁y₀ + x₀y₁ = (x₁+x₀)(y₁+y₀) − x₁y₁ − x₀y₀
```

**于是只需 3 次乘法**（加减法是 Θ(n)，可以随便用）：

```go
func karatsuba(x, y *big.Int, threshold int) *big.Int {
    if x.BitLen() <= threshold || y.BitLen() <= threshold {
        return new(big.Int).Mul(x, y) // 小数字直接乘
    }
    n := max(x.BitLen(), y.BitLen())
    m := n / 2

    // 拆成高低两半
    lowMask := new(big.Int).Sub(new(big.Int).Lsh(big.NewInt(1), uint(m)), big.NewInt(1))
    x0 := new(big.Int).And(x, lowMask)
    x1 := new(big.Int).Rsh(x, uint(m))
    y0 := new(big.Int).And(y, lowMask)
    y1 := new(big.Int).Rsh(y, uint(m))

    z2 := karatsuba(x1, y1, threshold)                                   // ① x₁y₁
    z0 := karatsuba(x0, y0, threshold)                                   // ② x₀y₀
    sx := new(big.Int).Add(x1, x0)
    sy := new(big.Int).Add(y1, y0)
    z1 := karatsuba(sx, sy, threshold)                                   // ③ (x₁+x₀)(y₁+y₀)
    z1.Sub(z1, z2)
    z1.Sub(z1, z0)                                                       // z1 = 中间项

    res := new(big.Int).Lsh(z2, uint(2*m))
    res.Add(res, new(big.Int).Lsh(z1, uint(m)))
    res.Add(res, z0)
    return res
}
```

**递归式**：

```
T(n) = 3T(n/2) + Θ(n)
     ⟹ 主定理情形 1（log₂3 ≈ 1.585 > 1）
     ⟹ T(n) = Θ(n^log₂3) = Θ(n^1.585)
```

⭐ **用加减法换掉一次乘法**——这个思路叫"代数恒等式降秩"，是分治优化的一大类。

**更快的乘法**：Toom-Cook（Θ(n^1.465)）、Schönhage-Strassen（基于 FFT，O(n log n log log n)）、2019 年 Harvey & van der Hoeven 的 **O(n log n)**（理论最优，但只在天文数字级别才有优势）。Go 的 `math/big` 会按位数自动在朴素乘法、Karatsuba 和 Toom-Cook 之间切换。

---

## 四、Strassen：矩阵乘法

**朴素矩阵乘法 Θ(n³)。分块分治**：

```
┌ A₁₁ A₁₂ ┐ ┌ B₁₁ B₁₂ ┐   ┌ C₁₁ C₁₂ ┐
│ A₂₁ A₂₂ │ │ B₂₁ B₂₂ │ = │ C₂₁ C₂₂ │

C₁₁ = A₁₁B₁₁ + A₁₂B₂₁
C₁₂ = A₁₁B₁₂ + A₁₂B₂₂
C₂₁ = A₂₁B₁₁ + A₂₂B₂₁
C₂₂ = A₂₁B₁₂ + A₂₂B₂₂
```

需要 **8 次** n/2 的矩阵乘法：`T(n) = 8T(n/2) + Θ(n²) ⟹ Θ(n³)`——同样毫无改进。

### Strassen 的 7 次乘法（1969）

**用 7 个精心构造的中间量代替 8 次乘法**：

```
M₁ = (A₁₁ + A₂₂)(B₁₁ + B₂₂)
M₂ = (A₂₁ + A₂₂) B₁₁
M₃ = A₁₁ (B₁₂ − B₂₂)
M₄ = A₂₂ (B₂₁ − B₁₁)
M₅ = (A₁₁ + A₁₂) B₂₂
M₆ = (A₂₁ − A₁₁)(B₁₁ + B₁₂)
M₇ = (A₁₂ − A₂₂)(B₂₁ + B₂₂)

C₁₁ = M₁ + M₄ − M₅ + M₇
C₁₂ = M₃ + M₅
C₂₁ = M₂ + M₄
C₂₂ = M₁ − M₂ + M₃ + M₆
```

```
T(n) = 7T(n/2) + Θ(n²)
     ⟹ Θ(n^log₂7) = Θ(n^2.807)
```

⭐ **这个结果在 1969 年是轰动性的**：在此之前人们普遍相信 Θ(n³) 是矩阵乘法的下界。Strassen 证明了这个"显然"的信念是错的。

**后续进展**：Coppersmith-Winograd O(n^2.376)、Le Gall O(n^2.373)、2024 年降到约 O(n^2.371)。**理论下界是 Ω(n²)**（至少要读完输入），中间的差距至今未解决——这是理论计算机科学的重大开放问题。

⚠️ **Strassen 在实践中的位置**：
- **n > 几百** 时才快过优化良好的朴素实现（因为常数大、需要额外内存）
- **数值稳定性差**（大量减法导致误差累积）
- 现代 BLAS 库（OpenBLAS、MKL）主要靠**分块 + SIMD + 缓存优化**做 Θ(n³)，只在极大矩阵上用 Strassen
- Coppersmith-Winograd 之后的算法常数大到"银河算法"（galactic algorithm）的程度——只在宇宙尺度的输入上才有优势

---

## 五、平面最近点对

> **问题**：平面上 n 个点，求距离最近的两个点。

朴素做法 Θ(n²)。**分治可以做到 Θ(n log n)。**

```
① 按 x 坐标排序，取中位线 L 把点分成左右两半
② 递归求左半最近距离 δ_L、右半最近距离 δ_R，令 δ = min(δ_L, δ_R)
③ 检查"跨越中线"的点对：只有落在中线两侧 δ 宽带内的点才可能更近
```

```
              │ L
     ●        │        ●
        ●     │   ●
   ●       ●  │ ●        ●
              │     ●
     ◀── δ ──▶│◀── δ ──▶
        只需检查这条带内的点
```

### ⭐ 关键引理：带内每个点只需检查后面 7 个

**把带内的点按 y 坐标排序**。对带内任一点 p，只需与 y 坐标排在它后面的**至多 7 个点**比较。

**证明**：考虑以 p 为左下角、宽 2δ、高 δ 的矩形。若矩形内有超过 8 个点，则左半（δ×δ 的正方形）或右半中必有两点距离 < δ——但它们同属左半或右半平面，与 δ 是各半最小距离矛盾。（更精确的分析给出 7 或 6 这个常数。）∎

```
       ◀───── 2δ ─────▶
     ┌─────────┬─────────┐  ▲
     │ ●     ● │ ●     ● │  │ δ
     │         │         │  │
     │ ●     ● │ ●     ● │  ▼
     └─────────┴─────────┘
     每个 δ×δ 正方形内至多 4 个点（否则内部有 < δ 的点对）
```

```go
type Point struct{ X, Y float64 }

func ClosestPair(pts []Point) float64 {
    byX := slices.Clone(pts)
    slices.SortFunc(byX, func(a, b Point) int { return cmp.Compare(a.X, b.X) })
    byY := slices.Clone(byX)
    slices.SortFunc(byY, func(a, b Point) int { return cmp.Compare(a.Y, b.Y) })
    return closest(byX, byY)
}

func closest(byX, byY []Point) float64 {
    n := len(byX)
    if n <= 3 {
        best := math.Inf(1)
        for i := 0; i < n; i++ {
            for j := i + 1; j < n; j++ {
                best = math.Min(best, dist(byX[i], byX[j]))
            }
        }
        return best
    }

    mid := n / 2
    midX := byX[mid].X
    // ⭐ 关键：在 O(n) 内把 byY 也分成左右两份，保持 y 有序（类似归并的逆过程）
    var leftY, rightY []Point
    inLeft := make(map[Point]bool, mid)
    for _, p := range byX[:mid] { inLeft[p] = true }
    for _, p := range byY {
        if inLeft[p] { leftY = append(leftY, p) } else { rightY = append(rightY, p) }
    }

    delta := math.Min(closest(byX[:mid], leftY), closest(byX[mid:], rightY))

    // 收集带内的点（已按 y 有序）
    var strip []Point
    for _, p := range byY {
        if math.Abs(p.X-midX) < delta {
            strip = append(strip, p)
        }
    }
    for i := range strip {
        for j := i + 1; j < len(strip) && j <= i+7; j++ { // 至多 7 个
            delta = math.Min(delta, dist(strip[i], strip[j]))
        }
    }
    return delta
}
```

⚠️ **必须预先排序并在递归中维护 y 有序**，否则每层都要重排，复杂度退化成 Θ(n log²n)。

```
T(n) = 2T(n/2) + Θ(n)  ⟹  Θ(n log n)
```

⭐ **"合并步骤只需 O(n)"这一点是通过一个组合引理（只需检查 7 个点）得到的，而不是通过更聪明的数据结构。** 这是分治算法设计的一个典型模式：**把合并步骤的代价压到线性，往往需要一个几何或组合的洞察。**

---

## 六、快速幂与 FFT

### 快速幂：Θ(log n)

```go
func Pow(a, n int, mod int) int {
    res := 1
    a %= mod
    for n > 0 {
        if n&1 == 1 {
            res = res * a % mod
        }
        a = a * a % mod // ⭐ 平方
        n >>= 1
    }
    return res
}
```

**原理**：`a^n = (a^(n/2))²`（n 偶）或 `a·(a^((n-1)/2))²`（n 奇）。`T(n) = T(n/2) + O(1) = Θ(log n)`。

**矩阵快速幂**：把递推 `F(n) = F(n−1) + F(n−2)` 写成矩阵形式，用快速幂在 **Θ(log n)** 内求第 n 个斐波那契数：

```
┌ F(n+1) ┐   ┌ 1 1 ┐^n   ┌ F(1) ┐
│ F(n)   │ = │ 1 0 │   × │ F(0) │
```

⭐ **任何线性递推都可以这样加速**，这是竞赛和密码学中的常用技巧。

### 快速傅里叶变换（FFT）

**问题**：两个 n 次多项式相乘，朴素做法 Θ(n²)。

**FFT 的分治思想**：

```
① 多项式有两种表示：系数表示 和 点值表示（n+1 个点唯一确定 n 次多项式）
② 点值表示下，乘法是 Θ(n)（对应点相乘即可）
③ FFT 在 Θ(n log n) 内做系数 ⟷ 点值的转换（取单位根为求值点）

系数 ──FFT──▶ 点值 ──逐点相乘 Θ(n)──▶ 点值 ──逆FFT──▶ 系数
     Θ(n log n)                              Θ(n log n)
⟹ 总计 Θ(n log n)
```

**分治在哪？** FFT 把多项式按下标奇偶拆成两半：

```
A(x) = A_even(x²) + x · A_odd(x²)
```

⭐ 由于单位根的性质 `ω_n^(k+n/2) = −ω_n^k`，计算 n 个点的值只需计算 n/2 个点两次：`T(n) = 2T(n/2) + Θ(n) ⟹ Θ(n log n)`。

**应用**：大整数乘法、信号处理、字符串匹配（带通配符）、卷积、多项式运算。Go 中可用 `gonum` 或自己实现（竞赛常用 NTT——在模意义下的整数版 FFT，无浮点误差）。

---

## 七、分治小结

| 算法 | 递归式 | 复杂度 | 关键洞察 |
|---|---|---|---|
| 二分查找 | T(n/2) + O(1) | Θ(log n) | 每次排除一半 |
| 归并排序 | 2T(n/2) + Θ(n) | Θ(n log n) | 合并两个有序表是线性的 |
| 快速选择 | T(n/2) + Θ(n) | Θ(n) | 只递归一侧 |
| BFPRT | T(n/5) + T(7n/10) + Θ(n) | Θ(n) | 花线性时间选好主元 |
| Karatsuba | 3T(n/2) + Θ(n) | Θ(n^1.585) | 用加减省一次乘法 |
| Strassen | 7T(n/2) + Θ(n²) | Θ(n^2.807) | 7 个中间量代替 8 次乘法 |
| 最近点对 | 2T(n/2) + Θ(n) | Θ(n log n) | 带内只需检查 7 个点 |
| FFT | 2T(n/2) + Θ(n) | Θ(n log n) | 单位根的对称性 |
| 快速幂 | T(n/2) + O(1) | Θ(log n) | 平方 |

⭐ **观察这张表**：几乎所有"打破朴素复杂度"的分治算法，靠的都是**减少子问题的个数**（8→7、4→3），而不是加快合并。这是因为主定理中 a 出现在指数上（`n^log_b a`），而 f(n) 只是加项——**降低 a 的收益远大于降低 f(n)**。

---

## 随堂自测

1. 分治适用的三个条件是什么？哪一个是它与动态规划的分界线？
2. 最大子数组的分治解是 Θ(n log n)，Kadane 是 Θ(n)。这说明什么？
3. 朴素分治大整数乘法是 4T(n/2)+Θ(n)，为什么复杂度没有改进？
4. 写出 Karatsuba 的代数恒等式，说明它如何把 4 次乘法降到 3 次。
5. Strassen 把 8 次乘法降到 7 次，复杂度从 Θ(n³) 变成什么？为什么这个改动收益这么大？
6. 为什么 Strassen 在小矩阵上反而更慢？列出三个原因。
7. 证明最近点对算法中"带内每点只需检查后 7 个点"。
8. 最近点对为什么必须预排序并在递归中维护 y 有序？不这么做复杂度是多少？
9. 用矩阵快速幂在 Θ(log n) 内求第 n 个斐波那契数，写出转移矩阵。
10. FFT 中分治体现在哪一步？为什么单位根的性质让子问题减半？
11. 观察分治算法汇总表，为什么"减少子问题个数"比"加快合并"收益更大？

---

> **上一讲**：[第 27 讲：网络流]({{< ref "27-network-flow.md" >}})　**下一讲**：[第 29 讲：回溯与穷举搜索]({{< ref "29-backtracking.md" >}})
