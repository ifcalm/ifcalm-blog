---
title: "第 21 讲：Gas——为什么它必须存在"
date: 2026-08-30
weight: 21
tags: ["区块链"]
draft: false
summary: "Gas 的三项职责与「计量」和「计价」分离的设计智慧；EIP-1559 之前一价拍卖的三个失败模式；基础费调整公式、±12.5% 限幅、以及销毁基础费为什么是必需的；EIP-1559 真正解决的不是费用高低而是费用估计；冷热访问定价与 Gas 退款被削减的原因。"
showToc: true
tocOpen: false
---

## 一、Gas 做三件事

⚠️ 很多人只知道 Gas 是"手续费"，但它同时承担三项完全不同的职责：

```
① 保证终止
   ⭐ 每条指令消耗 Gas，耗尽则强制中止
   ⟹ 死循环不会拖垮全网（第 20 讲）

② 为资源定价，防止 DoS
   每条指令的价格应反映它对节点的真实成本
   ⟹ 2016 年上海攻击正是因为这条没做好（第 20 讲第八节）

③ 分配稀缺的区块空间
   区块 Gas 上限是硬的，谁出价高谁先进
   ⟹ 这是一个拍卖市场
```

⭐ **第 ③ 项是最容易被忽略的**：Gas 不只是"付给节点的报酬"，它更是一套**稀缺资源的配给机制**。理解这一点，才能理解 EIP-1559 为什么要那样设计。

## 二、计量与计价分离

一个精妙的设计决定：

```
Gas 量   —— 由【协议】规定，⭐ 每条指令花多少 Gas 是共识规则的一部分
Gas 价格 —— 由【市场】决定，用户出价，单位是 wei/Gas
最终费用 = Gas 量 × Gas 价格
```

⭐ **为什么要分开：**

```
"一次 SSTORE 消耗多少计算资源"是一个【技术事实】，不随币价变化。
"一次 SSTORE 值多少钱"是一个【市场判断】，随币价和需求剧烈波动。

⟹ 如果混在一起，币价涨十倍就得改一次协议。
⟹ ⭐ 分开之后，协议只管技术，市场只管价格。
```

⚠️ **注意 Gas 量本身也需要维护**——第 20 讲的上海攻击和 EIP-150 就是例子。**技术事实不变，但我们对它的估计会变。**

## 三、用户侧的两个参数

```
gasLimit  —— 我最多愿意消耗多少 Gas
gasPrice  —— 我愿意为每单位 Gas 付多少（1559 后拆成两个，见第五节）
```

⚠️ **`gasLimit` 设错的两种后果不对称：**

```
设太低：⚠️ 执行到一半 Gas 耗尽
        ⟹ 状态变更【全部回滚】，
        但【已消耗的 Gas 不退】——你付了钱，什么都没得到

设太高：只是预扣多一些，用不完的会退回
        唯一的代价是余额被临时占用
```

⭐ **所以 `gasLimit` 应该往高了设。** 钱包的"预估 Gas"通常会在模拟结果上加一个缓冲，正是这个道理。

一个陷阱：**预估是在当前状态下模拟的，而交易真正执行时状态可能已经变了**（别人的交易先执行了）。这是"预估通过但实际失败"的常见原因。

## 四、一价拍卖的三个失败

EIP-1559 之前，费用机制是**一价拍卖（first-price auction）**：你出多少就付多少，矿工按价格排序打包。

三个问题：

```
① ⚠️ 用户无法合理定价
   出价的正确值取决于"别人出了多少"，而你看不到。
   ⟹ 要么大幅超付（多付几倍很常见），
      要么出价太低，交易卡在池子里几小时。

② 矿工有动机制造拥堵
   全部费用归矿工。
   ⟹ 矿工可以故意留空区块空间抬高价格，
      甚至自己发垃圾交易填满区块（成本是付给自己）。

③ 价格剧烈波动
   一个热门 NFT 铸造能让全网 Gas 价格瞬间涨十倍，
   ⟹ 而这与其他用户的交易毫无关系。
```

⭐ **注意第 ② 条的性质**：这不是"矿工不道德"，而是**机制设计上的激励错位**——**费用的收取者，同时也是供给的控制者。**

## 五、EIP-1559

伦敦升级（2021 年）把费用拆成两部分：

```
总费用 = gasUsed × (baseFee + priorityFee)
                     │          │
                     │          └─▶ 给验证者的小费（用户自定）
                     └─▶ ⭐ 由协议算出，并且【被销毁】
```

用户设两个上限：

```
maxFeePerGas         —— 我愿意付的总上限
maxPriorityFeePerGas —— 我愿意给的小费上限

实际支付 = min(maxFeePerGas, baseFee + maxPriorityFeePerGas)
⭐ 多余的自动退回
```

### 基础费怎么算

⚠️ **先说清楚一个前提**：区块 Gas 上限**不是协议写死的常数**，而是由出块者**逐块投票**微调的——每个区块最多把上限改动 ±1/1024。⭐ **所以它会随社区共识缓慢漂移**（历史上从 800 万一路上调，2021 年后长期在 3000 万，2025 年起继续上调）。下面用一个具体取值来演示机制，**重要的是那个反馈规则，不是这个数字**。

```
设区块 Gas 上限 = 3000 万
⭐ 目标用量 = 上限的一半 = 1500 万

baseFee(n+1) = baseFee(n) × ( 1 + (gasUsed − target) / target / 8 )
```

⭐ **两个关键性质：**

```
① 每个区块的变化被限制在 ±12.5%
   （满块 gasUsed = 2×target ⟹ +1/8 = +12.5%；空块 ⟹ −12.5%）

② ⭐ 它是一个【反馈控制器】：
   区块超过一半满 ⟹ 涨价 ⟹ 需求下降
   区块不到一半满 ⟹ 降价 ⟹ 需求上升
   ⟹ 长期把平均用量稳定在目标值附近
```

涨得有多快？

```
连续满块时：1.125ⁿ
   n = 9  ⟹ 约 2.9 倍
   n = 10 ⟹ 约 3.2 倍

⭐ 也就是【约 2 分钟】基础费就能涨到 3 倍。
⟹ 突发需求会被迅速定价出去，而不是让交易无限期堆积。
```

### 为什么必须销毁基础费

这是 EIP-1559 最重要也最容易被误解的部分。

```
如果基础费付给验证者：
   ⚠️ 第四节的问题 ② 原封不动——
      验证者仍然可以通过制造拥堵推高基础费来自肥。

销毁之后：
   验证者只拿小费，而小费是用户自愿给的、竞争性的一小部分。
   ⟹ 推高基础费对验证者【没有直接收益】
   ⟹ 激励错位被消除
```

⚠️ **销毁 ETH 的通缩效应是副作用，不是目的。** 把 EIP-1559 说成"为了让 ETH 通缩"是把因果搞反了——**销毁是为了修复激励，通缩只是后果。**

### EIP-1559 没有降低费用

这是最常见的误解。

```
费用的高低由【供需】决定：
   供给 = 区块空间（EIP-1559 没有增加它）
   需求 = 用户想做多少交易（EIP-1559 没有减少它）

⟹ ⭐ 均价不变是必然的。
```

**它真正改善的是：**

```
✅ 费用【可预测】：基础费公开可见，且变化有上界
✅ 大幅减少【超付】：不再需要盲目高出价
✅ 消除了验证者操纵拥堵的动机
✅ ⭐ 区块弹性：上限是目标的两倍，突发需求有缓冲空间
```

**一句话：EIP-1559 解决的是"费用估计"问题，不是"费用高"问题。后者只能靠扩容（第六单元）。**

## 六、冷热访问与访问列表

第 20 讲提到状态访问的真实成本远高于计算。EIP-2929（柏林升级）按此重新定价：

```
                     首次访问（冷）   再次访问（热）
读一个存储槽 SLOAD      2100            100
访问一个账户            2600            100
```

⭐ **理由直接对应硬件现实：**

```
第一次访问 ⟹ 一次随机磁盘 I/O（第 12 讲的 MPT 随机访问问题）
第二次访问 ⟹ 已在内存缓存里
⟹ ⭐ 价格应该反映这个差别，否则要么高估要么低估
```

**EIP-2930 访问列表**让交易可以预先声明它要访问哪些地址和槽：

```
好处：⭐ 预声明的项目按"热"价格计费（付一个较低的预付费）
     ⟹ 对于确定要多次访问的场景更便宜

但更深的意义在别处：
   预声明读写集正是并行执行的前提（第 11 讲讲的 Solana 做法）。
   访问列表为以太坊未来的并行化埋了一条路。
```

## 七、Gas 退款为什么被砍

早期设计：**清空一个存储槽可以退 Gas**（因为它减少了状态）。这个善意的设计被两次滥用：

```
① Gas 代币（GST2、CHI）
   ⭐ 在 Gas 便宜时【故意写入】一堆无用的存储槽，
      在 Gas 贵时清空它们领退款。
   ⟹ 等于把便宜时的 Gas "存起来"，是一种套利
   而它的净效果是【永久增加了状态膨胀】——
      写入的垃圾数据在被清空前一直占着所有节点的磁盘

② 让实际执行量超过区块上限
   退款让一个区块的【净】Gas 消耗低于实际执行量，
   ⟹ 于是一个 3000 万 Gas 的区块可能实际执行了 4000 万 Gas 的工作
   ⟹ 破坏了 gasLimit 作为"最坏情况执行时间"保证的作用
```

**EIP-3529（伦敦升级）的修复：**

```
① 退款上限从 gasUsed/2 降到 gasUsed/5
② 清空存储槽的退款从 15000 降到 4800
③ ⭐ 完全取消 SELFDESTRUCT 的退款
⟹ Gas 代币彻底失去经济性
```

⭐ **这里的教训值得记住：**

> **任何"负成本"的操作都会被套利。** 设计激励时，"鼓励清理状态"是好意图，但只要退款可以被**预先制造出来再兑现**，它就变成了一个可交易的期权。

## 八、Go：EIP-1559 与 Gas 计量

```go
package gas

import "math/big"

const (
	ElasticityMultiplier     = 2 // 区块上限 = 目标的 2 倍
	BaseFeeChangeDenominator = 8 // ⭐ 每块最多变化 1/8 = 12.5%
	MinBaseFee               = 7 // wei
)

// NextBaseFee 实现 EIP-1559 的基础费调整。
// 它是一个反馈控制器：超过目标就涨价，低于目标就降价，
// 把长期平均用量稳定在 target 附近。
func NextBaseFee(parentBaseFee *big.Int, parentGasUsed, parentGasLimit uint64) *big.Int {
	target := parentGasLimit / ElasticityMultiplier

	if parentGasUsed == target {
		return new(big.Int).Set(parentBaseFee)
	}

	if parentGasUsed > target {
		// 涨价：delta = baseFee × (used − target) / target / 8
		delta := new(big.Int).Mul(parentBaseFee, new(big.Int).SetUint64(parentGasUsed-target))
		delta.Div(delta, new(big.Int).SetUint64(target))
		delta.Div(delta, big.NewInt(BaseFeeChangeDenominator))
		if delta.Sign() == 0 {
			delta = big.NewInt(1) // 保证至少涨 1 wei，避免长期卡住
		}
		return new(big.Int).Add(parentBaseFee, delta)
	}

	// 降价
	delta := new(big.Int).Mul(parentBaseFee, new(big.Int).SetUint64(target-parentGasUsed))
	delta.Div(delta, new(big.Int).SetUint64(target))
	delta.Div(delta, big.NewInt(BaseFeeChangeDenominator))

	next := new(big.Int).Sub(parentBaseFee, delta)
	if next.Cmp(big.NewInt(MinBaseFee)) < 0 {
		return big.NewInt(MinBaseFee)
	}
	return next
}

// EffectiveGasPrice 计算实际支付的每单位 Gas 价格，以及给验证者的小费。
// baseFee 部分被销毁，只有 tip 归验证者——这消除了操纵拥堵的动机。
func EffectiveGasPrice(baseFee, maxFee, maxPriorityFee *big.Int) (paid, tip *big.Int, ok bool) {
	if maxFee.Cmp(baseFee) < 0 {
		return nil, nil, false // 出价低于基础费，交易根本无法进块
	}

	// tip = min(maxPriorityFee, maxFee − baseFee)
	room := new(big.Int).Sub(maxFee, baseFee)
	tip = new(big.Int).Set(maxPriorityFee)
	if tip.Cmp(room) > 0 {
		tip = room
	}

	paid = new(big.Int).Add(baseFee, tip)
	return paid, tip, true
}

// ─────────── 冷热访问计量（EIP-2929） ───────────

const (
	ColdSloadCost       = 2100 // 首次读一个存储槽：对应一次随机磁盘 I/O
	WarmStorageReadCost = 100  // 再次读：已在缓存里
	ColdAccountAccess   = 2600
)

type AccessList struct {
	warmSlots    map[[52]byte]bool // 地址(20) + 槽(32)
	warmAccounts map[[20]byte]bool
}

func NewAccessList() *AccessList {
	return &AccessList{
		warmSlots:    make(map[[52]byte]bool),
		warmAccounts: make(map[[20]byte]bool),
	}
}

// SloadCost 返回读一个槽的成本，并把它标记为热。
func (a *AccessList) SloadCost(addr [20]byte, slot [32]byte) uint64 {
	var key [52]byte
	copy(key[:20], addr[:])
	copy(key[20:], slot[:])

	if a.warmSlots[key] {
		return WarmStorageReadCost
	}
	a.warmSlots[key] = true
	return ColdSloadCost
}

// Prewarm 处理 EIP-2930 访问列表：交易预声明的项目直接标记为热。
// 更深的意义：预声明读写集是并行执行的前提（第 11 讲）。
func (a *AccessList) Prewarm(addrs [][20]byte, slots map[[20]byte][][32]byte) {
	for _, ad := range addrs {
		a.warmAccounts[ad] = true
	}
	for ad, ss := range slots {
		for _, s := range ss {
			var key [52]byte
			copy(key[:20], ad[:])
			copy(key[20:], s[:])
			a.warmSlots[key] = true
		}
	}
}

// CappedRefund 实现 EIP-3529：退款上限为已用 Gas 的 1/5。
// 上限存在的原因：无上限的退款会让区块【实际执行量】超过 gasLimit，
// 破坏 gasLimit 作为"最坏情况执行时间"的保证。
func CappedRefund(gasUsed, refund uint64) uint64 {
	max := gasUsed / 5
	if refund > max {
		return max
	}
	return refund
}
```

## 九、本讲小结

- ⭐ **Gas 同时做三件事**：保证终止、为资源定价防 DoS、**分配稀缺的区块空间**。第三项最容易被忽略，但它是理解 EIP-1559 的钥匙。
- **计量与计价分离**：Gas 量是协议规定的技术事实，Gas 价格由市场决定。⟹ **币价波动不需要改协议。**
- **`gasLimit` 设错的后果不对称**：太低会消耗 Gas 却什么都得不到，太高只是临时占用余额。**所以应该往高了设。**
- **预估 Gas 是在当前状态下模拟的**，而执行时状态可能已变——这是"预估通过但实际失败"的常见原因。
- **一价拍卖的三个失败**：用户无法定价（大幅超付）、**矿工有动机制造拥堵自肥**、价格剧烈波动。第二条是**机制设计的激励错位**——费用收取者同时是供给控制者。
- **EIP-1559 把费用拆成基础费（协议算出、销毁）+ 小费（给验证者）**。基础费按"目标是上限一半"做反馈控制，**每块变化限制在 ±12.5%，连续满块约 10 个块（2 分钟）能涨 3 倍。**
- ⭐⭐ **销毁基础费是必需的，不是为了通缩**：付给验证者的话，操纵拥堵自肥的动机原封不动。**通缩是副作用，不是目的。**
- **EIP-1559 没有也不可能降低费用**——它没改变供给也没改变需求。**它解决的是"费用估计"问题，不是"费用高"问题。**
- **冷热访问定价（EIP-2929）直接对应硬件现实**：首次访问是随机磁盘 I/O，之后在缓存。**访问列表（EIP-2930）更深的意义是为并行执行埋路。**
- **Gas 退款被砍的两个原因**：Gas 代币套利（且它净效果是永久增加状态膨胀）、以及退款让区块实际执行量超过 gasLimit。
- **普遍教训：任何"负成本"的操作都会被套利。** 只要退款能被预先制造再兑现，它就变成一个可交易的期权。

## 思考题

1. Gas 的三项职责中，哪一项在比特币里不存在？为什么比特币不需要它？
2. 如果 Gas 量和 Gas 价格不分离（直接用固定的 wei 计价），币价上涨十倍会发生什么？
3. 为什么 `gasLimit` 设太低会"付了钱什么都得不到"？这与 `REVERT` 的行为有什么不同？
4. 一价拍卖下，矿工自己发交易填满区块的"成本"是多少？为什么这构成激励错位？
5. 基础费从 10 gwei 开始，连续 5 个满块后是多少？连续 5 个空块后呢？
6. 如果基础费付给验证者而不是销毁，EIP-1559 还能解决哪些问题、不能解决哪些？
7. "EIP-1559 让 Gas 变便宜了"——用供需分析说明这句话为什么不成立。真正能降低费用的是什么？
8. 冷访问 2100 而热访问 100，差 21 倍。这个比例是怎么定的？如果定成 5 倍会有什么风险？
9. 描述 Gas 代币的完整套利流程。它对全网状态造成了什么净影响？
10. 除了 Gas 退款，你还能想到区块链里哪些"负成本"设计可能被套利？

