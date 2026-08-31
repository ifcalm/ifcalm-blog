---
title: "第 20 讲：以太坊的实际共识——LMD-GHOST 加 Casper FFG"
date: 2026-08-30
weight: 20
aliases: ["/posts/blockchain/19-ethereum-consensus/"]
tags: ["区块链"]
draft: false
summary: "以太坊如何把中本聪共识的「无准入、不停机」和 BFT 的「确定性最终性」缝在一起：LMD-GHOST 的子树权重分叉选择、Casper FFG 的证成与最终确定两条规则、可问责安全性为什么让回滚的代价等于三分之一总质押，以及 2023 年真实发生过的最终性停滞。"
showToc: true
tocOpen: false
---

## 一、要同时满足两个矛盾的目标

```
目标 A：支持【百万级】验证者，任何人可加入退出
        ⟹ ⚠️ BFT 做不到（第 19 讲：消息复杂度限制在百量级）

目标 B：提供【确定性最终性】，一旦确定永不回滚
        ⟹ 中本聪共识做不到（第 16 讲：只有概率最终性）
```

以太坊的做法是**分成两层，各管一件事**：

```
┌─────────────────────────────────────────────┐
│ Casper FFG（最终性小工具）                    │
│ ⭐ 每 2 个 epoch 把一个检查点【永久确定】       │
│    这一层是 BFT 式的                          │
├─────────────────────────────────────────────┤
│ LMD-GHOST（分叉选择）                         │
│ 每个 slot 决定"当前链头在哪"                │
│    这一层是中本聪式的                          │
└─────────────────────────────────────────────┘
        合称 Gasper
```

⭐ **关键的粘合技巧是「委员会抽样」**：每个 slot 只让一个随机委员会投票，而不是全体验证者。**这让消息复杂度与验证者总数解耦**，从而绕过第 19 讲那个限制。

## 二、时间结构

```
1 slot  = 12 秒
1 epoch = 32 slots = 384 秒 = 6.4 分钟

每个 epoch 开始时：
   ⭐ 把全部验证者随机打散，均分到这 32 个 slot 的委员会里
   ⟹ 每个验证者【每个 epoch 恰好投一次票】

每个 slot：
   0 秒  提议者广播区块
   4 秒  本 slot 的委员会投票（attest）
   8 秒  聚合者把委员会的 BLS 签名聚合（第 8 讲）
```

⚠️ 提议者由 RANDAO 提前若干 epoch 确定，且**名单是公开的**——这带来一个真实的 DoS 风险（第七节）。

## 三、LMD-GHOST：按子树重量选链头

### GHOST 与最长链的区别

```
最长链（比特币）：选链最长的那条
GHOST：⭐ 从根开始，每一步都走【子树总权重最大】的那个分支
```

看一个具体例子：

```
                 A
              ┌──┴──┐
              B      C
            ┌─┴─┐    │
            D   E    F
                     │
                     G
                     │
                     H

按"最长链"：  A→C→F→G→H  长度 5，获胜
按 GHOST：    B 的子树有 {B,D,E} 三个块的投票权重
              C 的子树有 {C,F,G,H} 四个块
              ⟹ ⭐ 但比较的不是块数，而是【投给这些块的验证者权重之和】
```

⭐ **GHOST 的关键洞察：那些"没进主链但投给了这一侧"的票，也应该算数。**

```
最长链的问题：一个分支上的分散投票被完全浪费
GHOST：⭐ 它们仍然为这一侧贡献重量
⟹ 攻击者要压过的不只是主链，而是【整棵子树的重量】
⟹ 在出块快、分叉多的链上，安全性显著提升
```

### LMD：只看最新消息

**LMD = Latest Message Driven，只统计每个验证者的最新一票。**

```
⭐ 为什么必须这样：
   ① 每个验证者只应有一票的权重，
      否则历史投票会被累积重复计算
   ② 验证者改变主意（跟随新链头）时，旧票应该失效
```

于是分叉选择算法是：

```
从最新的【已最终确定】的检查点出发
while 当前节点有子节点：
    ⭐ 走向"最新投票权重之和"最大的那个子节点
返回叶子节点作为链头
```

⚠️ 注意起点：**LMD-GHOST 只在最终确定的检查点之后运行。已确定的部分根本不参与分叉选择**——这就是最终性的意义。

## 四、Casper FFG：两条规则

FFG 不负责出块，它只做一件事：**周期性地给某些区块盖上"永久确定"的章。**

```
检查点（checkpoint）= 每个 epoch 第一个 slot 的那个区块
投票 = 一条从 source 检查点到 target 检查点的【链接】
```

### 规则一：证成（Justified）

```
若一个检查点 T 收到了【超过 2/3 质押】的投票链接 (S → T)，
且 S 本身已经是 justified 的，
⟹ ⭐ 则 T 变成 justified。
```

### 规则二：最终确定（Finalized）

```
若 S 是 justified，且它的【直接下一个】检查点 T 也变成了 justified，
⟹ ⭐ 则 S 变成 finalized（永久确定，不可回滚）。
```

### 正常流程

```
epoch N   的检查点被 justified
epoch N+1 的检查点被 justified
   ⟹ ⭐ epoch N 的检查点 finalized

⟹ 正常情况下，最终性延迟约 2 个 epoch ≈ 12.8 分钟
```

⚠️ 对比：比特币"6 个确认"约 60 分钟，且只是概率保证。**以太坊 12.8 分钟给出的是确定性保证**——但代价是第 18 讲讲过的那些额外假设。

## 五、可问责安全性：最终性的真正含义

这是整个设计最深刻的地方。

> **定理**：要让两个互相冲突的检查点都被 finalized，**至少 1/3 的总质押必须犯下可罚没的错误**。

论证思路（用第 19 讲的法定人数交集）：

```
两个冲突检查点各需要 > 2/3 的投票。
两个 2/3 集合的交集 > 1/3。
⭐ 交集里的验证者，必然做出了双重投票或环绕投票（第 18 讲）
⟹ 他们全部可以被罚没
```

⭐ **这条定理把"最终性"从一个技术概念变成了一个可以标价的经济概念：**

```
⚠️ 回滚一个已 finalized 的区块，不是"不可能"，
而是"会让至少三分之一的总质押被销毁"。

而由于相关性惩罚（第 18 讲），
当 1/3 的质押同时被罚时，他们几乎会损失【全部】本金。
```

这叫**经济最终性（economic finality）**。它比"概率最终性"强得多，因为代价是**确定的、可计算的、且会被真的执行**——而不是一个概率。

⭐ **同时它也诚实地承认：最终性不是物理定律，是一个足够贵的价签。**

## 六、它既不是纯 PoS，也不是纯 BFT

这是本讲标题里那个"实际"的含义：

| 场景 | 传统 BFT | 中本聪共识 | 以太坊 |
|---|---|---|---|
| 正常出块 | 需全体参与 | 概率性 | 委员会抽样 + GHOST |
| 最终性 | 立即 | 永远只是概率 | 约 12.8 分钟后确定 |
| **网络分区时** | **停机** | 两边各自出块 | **继续出块，但不最终确定** |
| 分区恢复后 | 继续 | 短链被抛弃 | 重新最终确定 |
| 分区长期不恢复 | 一直停机 | 两条链共存 | **非活跃泄漏，稀释少数派** |

⭐ **"继续出块但不最终确定"是一个非常务实的中间状态**：

```
链没有停（用户仍能交易，UX 不中断）
但所有人都知道"这段还没确定"
⟹ ⭐ 交易所和大额结算可以选择等待最终性
⟹ 而日常小额支付可以照常进行
```

⚠️ 而如果分区持续太久，**非活跃泄漏**（第 18 讲）会启动：不投票的一方质押被持续稀释，直到活跃方重新占到 2/3。**代价是两边最终会各自恢复最终性，链永久分裂。**

## 七、现实中的问题

### ① 最终性停滞是真的发生过的

```
2023 年 5 月，以太坊主网出现过两次最终性停滞
（一次约 25 分钟，一次约 1 小时）：
   ⭐ 链继续出块，用户交易正常，
   但检查点无法被 finalized。

起因是客户端在处理大量旧投票时的实现问题
（资源消耗过高导致节点跟不上），不是协议本身的缺陷。
```

⭐ **两个教训：**

```
① 设计生效了 —— 链没有停，没有分叉，没有资金损失。
   "继续出块但不最终确定"这个中间状态正是为此而存在的。

② ⚠️ 但它再次证明了第 16 讲的话：
   【实现的差异和缺陷本身就是共识风险】。
   这也正是第 18 讲相关性惩罚要鼓励客户端多样性的原因。
```

### ② 提议者名单提前公开

```
RANDAO 提前确定未来若干 epoch 的提议者，且名单公开。
⚠️ 攻击者可以对下一个提议者发动 DDoS，让他错过出块。
```

⭐ 缓解方向是**单秘密领导者选举（SSLE）**——用密码学让提议者只有自己知道，直到他出块为止（思路与第 8 讲 Algorand 的 VRF 抽签相同）。

### ③ 12.8 分钟仍然太长

正在推进的方向是**单 slot 最终性（SSF）**：每个 slot 就完成最终确定。

难点正是第 19 讲那个限制：**要让百万验证者在 12 秒内完成一轮 BFT 投票**，需要签名聚合和消息传播上的重大突破。

## 八、Go：FFG 状态机

```go
package gasper

type Checkpoint struct {
	Epoch uint64
	Root  [32]byte
}

// FFG 维护证成与最终确定的状态。
type FFG struct {
	justified map[Checkpoint]bool
	finalized map[Checkpoint]bool

	// links[source][target] = 支持这条链接的质押总量
	links map[Checkpoint]map[Checkpoint]uint64

	totalStake uint64
}

func NewFFG(genesis Checkpoint, totalStake uint64) *FFG {
	f := &FFG{
		justified:  map[Checkpoint]bool{genesis: true}, // 创世检查点默认已证成
		finalized:  map[Checkpoint]bool{genesis: true},
		links:      make(map[Checkpoint]map[Checkpoint]uint64),
		totalStake: totalStake,
	}
	return f
}

// threshold 返回 2/3 门槛。⭐ 用整数运算避免浮点误差——共识代码里这一点很关键。
func (f *FFG) threshold() uint64 { return f.totalStake*2/3 + 1 }

// AddVote 记录一条 (source → target) 投票链接并尝试推进状态。
func (f *FFG) AddVote(source, target Checkpoint, stake uint64) {
	// 只有从已证成的 source 出发的链接才有效
	if !f.justified[source] {
		return
	}
	if f.links[source] == nil {
		f.links[source] = make(map[Checkpoint]uint64)
	}
	f.links[source][target] += stake

	// 规则一：超过 2/3 ⟹ target 被证成
	if f.links[source][target] >= f.threshold() && !f.justified[target] {
		f.justified[target] = true

		// 规则二：若 source 是 target 的【直接前驱】epoch，则 source 被最终确定
		if target.Epoch == source.Epoch+1 {
			f.finalized[source] = true
		}
	}
}

func (f *FFG) IsFinalized(c Checkpoint) bool { return f.finalized[c] }

// SafetyMargin 返回"要让两个冲突检查点都被最终确定，
// 至少需要多少质押被罚没"。
// 这就是第五节的可问责安全性：答案恒为总质押的 1/3。
func (f *FFG) SafetyMargin() uint64 {
	return f.totalStake / 3
}

// ─────────── LMD-GHOST 分叉选择 ───────────

type Block struct {
	Root     [32]byte
	Parent   [32]byte
	Children [][32]byte
}

// HeadBlock 实现 LMD-GHOST：从最终确定的检查点出发，
// 每一步都走【子树最新投票权重最大】的分支。
func HeadBlock(blocks map[[32]byte]*Block, start [32]byte, weights map[[32]byte]uint64) [32]byte {
	cur := start
	for {
		b := blocks[cur]
		if b == nil || len(b.Children) == 0 {
			return cur
		}
		best, bestW := b.Children[0], subtreeWeight(blocks, b.Children[0], weights)
		for _, c := range b.Children[1:] {
			if w := subtreeWeight(blocks, c, weights); w > bestW {
				best, bestW = c, w
			}
		}
		cur = best
	}
}

// subtreeWeight 递归累加整棵子树的投票权重。
// 这正是 GHOST 与"最长链"的区别：
// 分叉侧的投票不被浪费，它们仍为这一侧贡献重量。
func subtreeWeight(blocks map[[32]byte]*Block, root [32]byte, weights map[[32]byte]uint64) uint64 {
	total := weights[root]
	if b := blocks[root]; b != nil {
		for _, c := range b.Children {
			total += subtreeWeight(blocks, c, weights)
		}
	}
	return total
}
```

## 九、本讲小结

- ⭐ **以太坊把两种共识缝在一起**：底层 LMD-GHOST（中本聪式，支持百万验证者）+ 上层 Casper FFG（BFT 式，提供最终性）。合称 Gasper。
- **粘合的关键是委员会抽样**：每 slot 只有一个随机委员会投票，**让消息复杂度与验证者总数解耦**，绕过第 19 讲的规模限制。
- **时间结构**：slot 12 秒，epoch 32 slots = 6.4 分钟，每个验证者每 epoch 恰好投一次票。
- **GHOST 的洞察：分叉侧的投票不应被浪费**，它们仍为那一侧贡献子树重量 ⟹ 攻击者要压过的是整棵子树。这在出块快、分叉多的链上显著提升安全性。
- **LMD 只统计每个验证者的最新一票**——防止历史投票被重复累计，并让"改变主意"生效。
- **Casper FFG 两条规则**：收到 >2/3 投票链接则**证成**；连续两个 epoch 都被证成则前一个**最终确定**。正常延迟约 **2 个 epoch ≈ 12.8 分钟**。
- ⭐⭐ **可问责安全性**：要让两个冲突检查点都最终确定，**至少 1/3 的总质押必须犯下可罚没的错误**（法定人数交集）。加上相关性惩罚，他们几乎会损失全部本金。
- **这把"最终性"从技术概念变成了可标价的经济概念**：回滚不是不可能，而是会销毁至少三分之一的总质押。**它诚实地承认最终性是一个足够贵的价签，而不是物理定律。**
- **分区时的行为是三者中最务实的**：BFT 停机、中本聪共识分叉，**以太坊继续出块但不最终确定**——UX 不中断，而大额结算可以选择等待。
- **2023 年 5 月真的发生过两次最终性停滞**（约 25 分钟和 1 小时），链继续出块、无资金损失。设计生效了，但它再次证明**实现缺陷本身就是共识风险**。
- **提议者名单提前公开带来 DoS 风险**，缓解方向是单秘密领导者选举（SSLE）；12.8 分钟仍嫌长，方向是单 slot 最终性（SSF）。

## 思考题

1. 为什么以太坊不能直接用 Tendermint？为什么也不能直接用比特币的最长链？请分别给出定量的理由。
2. 委员会抽样如何让消息复杂度与验证者总数解耦？它引入了什么新的安全考虑？
3. 用第三节的例子说明 GHOST 和最长链会选出不同的链头。在什么情况下两者结果相同？
4. 为什么 LMD 必须"只算最新一票"？如果累计所有历史投票，攻击者能做什么？
5. 手工推演一次最终确定：从 epoch 10 开始，写出 epoch 10、11、12 各自的证成与最终确定状态变化。
6. 完整证明可问责安全性：为什么两个冲突检查点都被最终确定，就意味着 1/3 的质押可被罚没？
7. "经济最终性"和"概率最终性"的区别是什么？为什么说前者更强？它们各自的"不确定性"来自哪里？
8. 网络分区时，Tendermint 停机、比特币分叉、以太坊继续出块但不确定。分别说出这三种行为对交易所意味着什么。
9. 2023 年的最终性停滞中，链继续出块。如果你是交易所的风控负责人，这段时间你会怎么做？
10. 提议者名单提前公开的 DoS 风险有多严重？SSLE 用什么思路解决它？它和第 8 讲的 Algorand 抽签有什么共同点？

