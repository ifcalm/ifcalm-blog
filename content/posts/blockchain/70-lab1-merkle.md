---
title: "实验 1：Merkle 树与包含证明"
date: 2026-08-30
weight: 70
tags: ["区块链"]
draft: false
summary: "从零实现一棵带域分隔的 Merkle 树、包含证明的生成与验证，并动手复现两个真实漏洞：比特币的 CVE-2012-2459 重复叶子攻击，以及缺少域分隔时的第二原像攻击。附完整测试与参考实现。"
showToc: true
tocOpen: false
---

对应[第 5 讲]({{< ref "05-merkle-trees.md" >}})。⭐ **这个实验的重点不是"写出一棵树"，而是亲手让两个真实漏洞复现出来**——只有看到它们真的成立，才会真正记住为什么需要域分隔和单射性。

## 环境

```bash
mkdir -p lab1 && cd lab1 && go mod init lab1
```

只用标准库，无外部依赖。

## 任务一：基础实现

在 `merkle.go` 中实现：

```go
// New 构建一棵 Merkle 树。
func New(items [][]byte) (*Tree, error)

// Root 返回根哈希。
func (t *Tree) Root() []byte

// Proof 返回第 index 个元素的包含证明。
func (t *Tree) Proof(index int) ([]Step, error)

// Verify 只用 root、item、path 验证包含性。
// ⭐ 注意签名里没有树——这正是轻客户端能工作的原因。
func Verify(root, item []byte, path []Step) bool
```

**要求：**

```
① ⭐ 叶子用 0x00 前缀，内部节点用 0x01 前缀（域分隔）
② ⭐ 奇数节点时【不复制】最后一个，而是原样上提
③ 证明的每一步必须记录兄弟在左还是在右
```

### ⚠️ 自检

```go
func TestProofRoundTrip(t *testing.T) {
    for n := 1; n <= 33; n++ {   // ⭐ 一定要覆盖 1 和各种奇数
        items := make([][]byte, n)
        for i := range items {
            items[i] = []byte{byte(i)}
        }
        tree, _ := New(items)
        for i := 0; i < n; i++ {
            p, _ := tree.Proof(i)
            if !Verify(tree.Root(), items[i], p) {
                t.Fatalf("n=%d i=%d 验证失败", n, i)
            }
            // ⚠️ 反例也必须失败
            if Verify(tree.Root(), []byte("wrong"), p) {
                t.Fatalf("n=%d i=%d 接受了错误的元素", n, i)
            }
        }
    }
}
```

⭐ **`n` 从 1 到 33 全覆盖是关键**：绝大多数 Merkle 实现的 bug 都出现在"叶子数不是 2 的幂"的边界上。

## 任务二：复现 CVE-2012-2459

**实现一个"比特币风格"的 Merkle 根计算——即奇数节点时复制最后一个：**

```go
// BitcoinStyleRoot 复刻比特币的做法：奇数层时复制最后一个节点。
// ⚠️ 这正是 CVE-2012-2459 的成因。
func BitcoinStyleRoot(items [][]byte) []byte
```

**然后证明它不是单射的：**

```go
func TestCVE20122459(t *testing.T) {
    a := []byte("tx-A")
    b := []byte("tx-B")
    c := []byte("tx-C")

    root1 := BitcoinStyleRoot([][]byte{a, b, c})
    root2 := BitcoinStyleRoot([][]byte{a, b, c, c}) // ⚠️ C 出现两次

    if !bytes.Equal(root1, root2) {
        t.Fatal("应当相同——如果不同，说明你的实现和比特币不一致")
    }
    t.Logf("⚠️ 两个不同的交易列表得到了相同的根：%x", root1)
}
```

**思考并回答：**

```
① 攻击者拿到合法区块 [A,B,C]，构造 [A,B,C,C] 转发给受害节点。
   ⭐ 受害节点会走到哪一步才发现问题？
② 它把哪个值记进了"无效缓存"？
③ ⭐ 为什么真正的区块 [A,B,C] 随后到达时会被丢弃？
④ 除了"检测重复相邻节点"，还有什么修法？比较各自代价。
```

## 任务三：复现第二原像攻击

**实现一个【没有域分隔】的版本：**

```go
// NoDomainSepRoot 叶子和内部节点用同一个哈希，不加前缀。
func NoDomainSepRoot(items [][]byte) []byte {
    level := make([][]byte, len(items))
    for i, it := range items {
        h := sha256.Sum256(it)      // ⚠️ 没有 0x00 前缀
        level[i] = h[:]
    }
    for len(level) > 1 {
        next := [][]byte{}
        for i := 0; i < len(level); i += 2 {
            if i+1 == len(level) {
                next = append(next, level[i])
                continue
            }
            h := sha256.Sum256(append(level[i], level[i+1]...)) // ⚠️ 没有 0x01 前缀
            next = append(next, h[:])
        }
        level = next
    }
    return level[0]
}
```

**任务：构造一棵"叶子数更少"的树，让它的根与一棵 4 叶子树相同。**

```
提示：
   4 叶子树的根 = H( H(h₀‖h₁) ‖ H(h₂‖h₃) )
   ⭐ 如果把 (h₀‖h₁) 和 (h₂‖h₃) 这两串 64 字节数据当成【两个叶子】，
      会发生什么？
```

⭐ **做完之后，用带域分隔的版本再试一次，确认攻击失效。**

## 任务四：空投白名单

**实现[第 5 讲第七节]({{< ref "05-merkle-trees.md" >}})的应用：**

```go
type Airdrop struct {
    Address [20]byte
    Amount  uint64
}

// BuildWhitelist 为 n 个地址构建 Merkle 树。
// ⭐ 叶子的编码必须确定且无歧义——
//    ⚠️ 如果地址和金额直接拼接而长度可变，会有歧义攻击。
func BuildWhitelist(list []Airdrop) (*Tree, error)
```

**要回答的问题：**

```
① ⭐ 10 万个地址，合约需要存多少字节？直接存列表需要多少？
② 每个用户领取时要提交多少字节的证明？
③ ⚠️ 合约怎么防止同一个人重复领取？
④ ⭐ 如果叶子编码成 address ‖ amount 且两者都是变长的，
   构造一个歧义攻击（提示：想想"AB"‖"C" 和 "A"‖"BC"）
```

## 任务五（选做）：不存在性证明

**把叶子按键排序，实现：**

```go
// ProveAbsence 证明 key 不在集合中。
// ⭐ 做法：给出排序后相邻的两个叶子 lo < key < hi 各自的包含证明，
//    并证明它们在树中确实相邻。
func (t *SortedTree) ProveAbsence(key []byte) (*AbsenceProof, error)
```

⚠️ **难点：如何证明"它们在树中相邻"？** 提示：叶子下标相差 1，而下标信息隐含在证明路径的左右方向序列里。

## 参考实现要点

```go
const (
    leafPrefix = 0x00
    nodePrefix = 0x01
)

func hashLeaf(data []byte) []byte {
    h := sha256.New()
    h.Write([]byte{leafPrefix})   // ⭐ 域分隔的全部内容就是这一个字节
    h.Write(data)
    return h.Sum(nil)
}

func hashNode(l, r []byte) []byte {
    h := sha256.New()
    h.Write([]byte{nodePrefix})
    h.Write(l)
    h.Write(r)
    return h.Sum(nil)
}
```

**奇数节点的处理（与比特币不同）：**

```go
for i := 0; i < len(level); i += 2 {
    if i+1 == len(level) {
        next = append(next, level[i])   // ⭐ 上提，不复制
    } else {
        next = append(next, hashNode(level[i], level[i+1]))
    }
}
```

⭐ **证明这个策略是单射的**：给定根，能唯一还原出树的形状——因为每一层的节点数由叶子数唯一决定（`ceil(n/2)`），而"上提"不引入任何新的哈希输入。

## 提交清单

```
□ merkle.go            带域分隔的实现
□ merkle_test.go       n = 1..33 的往返测试 + 反例测试
□ cve_test.go          CVE-2012-2459 复现，并输出相同的两个根
□ preimage_test.go     无域分隔时的第二原像攻击，及加上域分隔后失效
□ airdrop.go           白名单构建 + 四个问题的书面回答
□ ANSWERS.md           任务二、四的问答
```

---

> **相关**：[第 5 讲：Merkle 树与包含证明]({{< ref "05-merkle-trees.md" >}})
