---
title: "第 11 讲：账户模型——nonce、重放与两种模型的权衡"
date: 2026-08-30
weight: 11
tags: ["区块链"]
draft: false
summary: "以太坊的两类账户与状态的四个字段；nonce 同时承担的三项职责及其带来的队头阻塞；跨链重放攻击与 EIP-155；CREATE 与 CREATE2 的地址派生公式及「反事实部署」；以及 UTXO 与账户模型的完整权衡对比和 Solana、Cardano 的混合方案。"
showToc: true
tocOpen: false
---

## 一、两类账户

以太坊回到了银行式的记账：**地址 → 状态** 的一张大表。但它有两种账户：

```
① 外部账户（EOA, Externally Owned Account）
   由私钥控制，⭐ 只有它能发起交易

② 合约账户
   由代码控制，没有私钥
   ⚠️ 不能主动做任何事——只能被调用
```

⭐ **这条规则值得反复强调：链上的一切都始于某个 EOA 发起的交易。**

```
没有"定时任务"、没有"到点自动执行"、没有后台线程。
一个合约里写着"每天 12 点分红"，
⚠️ 也必须有人在 12 点发一笔交易去调用它，并且付 Gas。
```

这就是"keeper"、"自动化机器人"这类角色存在的原因，也是很多协议设计里被忽略的成本。

## 二、账户状态的四个字段

```go
type Account struct {
    Nonce       uint64      // ⭐ 三重职责，见第三节
    Balance     *big.Int    // 余额，单位 wei（1 ETH = 10¹⁸ wei）
    StorageRoot [32]byte    // 该账户存储的 MPT 根（第 12 讲）
    CodeHash    [32]byte    // 代码的 keccak256
}
```

区分两类账户只看后两个字段：

```
EOA：      StorageRoot = 空树根，CodeHash = keccak256("")
合约账户： CodeHash ≠ keccak256("")
```

⚠️ 由此得到一个安全上的坑：

```solidity
// ⚠️ 常见的"只允许 EOA 调用"的写法：
require(msg.sender.code.length == 0);

// 它挡不住：合约在【构造函数执行期间】code.length 仍然是 0
// ⟹ 攻击者可以在部署合约的同时发起攻击调用，绕过这个检查
```

## 三、nonce 的三重职责

nonce 是一个只增不减的计数器，**它同时承担三件事**：

### ① 防重放

```
没有 nonce 会怎样？
   Alice 签了"转 10 ETH 给 Bob"
   ⚠️ Bob 可以把这笔已上链的交易一遍遍重新广播
   ⟹ 每次都是合法签名，Alice 被反复扣款

有了 nonce：
   交易里写明 nonce = 5
   ⭐ 链上执行后 Alice 的 nonce 变成 6
   ⟹ 再提交同一笔交易，nonce 对不上，直接拒绝
```

### ② 定序

同一个账户的交易必须**严格按 nonce 递增顺序**执行：

```
待处理池里有 nonce = 5, 6, 7 三笔
⟹ 必须先执行 5，再 6，再 7
```

⚠️ **这带来了队头阻塞（head-of-line blocking）：**

```
nonce=5 的交易 Gas 价格给低了，一直没被打包
⟹ nonce=6、7 即使给了高价也无法执行
⟹ 整个账户卡死

⭐ 解法：用相同的 nonce=5 重发一笔更高 Gas 价格的交易（"替换"），
   通常是发一笔 0 ETH 给自己的空交易把 5 顶掉。
```

这正是钱包里"加速"和"取消"按钮的原理。

### ③ 派生合约地址

见第五节。

## 四、跨链重放与 EIP-155

nonce 防住了同一条链上的重放。**但跨链呢？**

```
2016 年 ETH/ETC 分叉后，两条链的状态完全相同：
   同样的地址、同样的余额、同样的 nonce

⟹ ⚠️ Alice 在 ETH 上发的一笔交易，签名在 ETC 上同样有效
⟹ 任何人把它复制到 ETC 上广播，Alice 在 ETC 上的币也被转走了
```

这在当时造成了大量真实损失。**EIP-155 的修复**是把 `chainID` 纳入签名：

```
签名内容 = keccak256(RLP(nonce, gasPrice, gasLimit, to, value, data, chainID, 0, 0))
                                                                    ↑
                                                     ⭐ chainID 进了哈希
```

⭐ **于是同一笔交易在不同链上的签名不同，天然无法重放。** 第 7 讲第五节讲过，chainID 最终被编码进签名的 `v` 值里。

⚠️ **但这只保护了 EOA 交易。合约内部的签名验证（EIP-712 那类）必须自己处理 chainID**，否则同样会被跨链重放——这是审计里的常见发现（第 33 讲）。

## 五、合约地址是怎么算出来的

### CREATE：由部署者和 nonce 决定

```
地址 = keccak256( RLP([部署者地址, 部署者当时的 nonce]) )[12:]
```

⭐ **完全确定**：知道谁部署、他当时 nonce 多少，就能算出地址。⚠️ 但你必须先知道 nonce，而 nonce 会变。

### CREATE2：由部署者、盐和代码决定

```
地址 = keccak256( 0xff ‖ 部署者地址 ‖ salt ‖ keccak256(初始化代码) )[12:]
```

⭐ **不含 nonce ⟹ 地址完全可预测，且与部署时机无关。**

这带来一个很有用的能力，**反事实部署（counterfactual deployment）**：

```
你可以先算出合约地址，向它转账、把它写进其他合约，
⚠️ 而这个合约此刻根本还不存在。
需要时再部署即可——地址一定对得上。

⭐ 账户抽象钱包（第 24 讲）大量使用这个技巧：
   用户拿到地址就能收款，直到第一次发交易时才真正部署合约，省下部署 Gas。
```

⚠️ **历史上的坑**：CREATE2 加上 `SELFDESTRUCT`，曾经允许**在同一个地址上先后部署完全不同的代码**：

```
① CREATE2 部署合约 A（用户审计了 A，认为安全）
② 调用 SELFDESTRUCT 销毁 A
③ ⚠️ 用同样的 salt 再次 CREATE2，部署恶意合约 B
⟹ 地址没变，代码变了。所有"我信任这个地址"的假设全部失效
```

坎昆升级的 EIP-6780 把 `SELFDESTRUCT` 限制为"只在同一笔交易内部署的合约才真正销毁"，基本堵死了这条路。⭐ **但教训仍然成立：**"地址不变 ⟹ 代码不变"在过去不是一个安全的假设，而很多协议曾经这样假设。

## 六、UTXO 与账户模型的完整对比

| 维度 | UTXO | 账户 |
|---|---|---|
| **状态表示** | 一堆未花费输出 | 地址 → 状态的映射 |
| **余额** | ⚠️ 算出来的 | 直接存着 |
| **防重放** | 天然（花过就没了） | ⭐ 靠 nonce |
| **并行验证** | ⭐ 天然支持（读写集显式） | ⚠️ 困难（执行前不知道碰哪些状态） |
| **隐私** | 较好（新地址无天然关联） | ⚠️ 差（账户就是身份） |
| **共享状态合约** | ⚠️ 极难 | ⭐ 自然 |
| **交易体积** | 大（要列出所有输入输出） | 小 |
| **状态膨胀** | UTXO 集合只增不减 | 账户与存储槽只增不减 |
| **轻客户端查余额** | ⚠️ 要扫全链找属于你的 UTXO | ⭐ 一个 Merkle 证明搞定 |
| **无状态验证** | ⭐ 友好 | 需要额外机制（第 13 讲） |

⭐ **一句话概括这个权衡：**

> **UTXO 把状态切成互不相干的小块，换来了并行和隐私，代价是无法表达共享状态。**
> **账户模型把状态集中成一张大表，换来了合约能力，代价是天然串行。**

### 为什么以太坊必须选账户模型

一个 AMM 池子的储备是**全局共享**的：

```
UTXO 下：池子是一个 UTXO
   ⟹ Alice 和 Bob 同时交易，两人都想花掉同一个 UTXO
   ⟹ ⚠️ 只有一个能成功，另一个必须重试
   ⟹ 高并发下几乎不可用

账户下：池子是一个合约账户，两笔交易顺序执行，各自更新余额 ✅
```

⭐ **"共享可变状态"是 DeFi 的基础，而 UTXO 模型在设计上就排斥它。** 这不是实现难度问题，是模型的本质差异。

## 七、两个混合方案

### Solana：账户模型 + 强制预声明

Solana 用账户模型，但要求**每笔交易预先声明它会读写哪些账户**：

```
交易头里写明：
   读账户: [A, B]
   写账户: [C]

⟹ ⭐ 调度器可以据此判断哪些交易互不冲突，从而并行执行（Sealevel）
```

⭐ **这等于把 UTXO 的"显式读写集"优点移植到了账户模型上。**

⚠️ 代价有两个：

```
① 编程模型复杂：开发者必须提前列出所有可能触碰的账户，
   而这在动态调用（合约调合约）下很难精确知道
② 声明错了交易就失败，或者只能保守地多声明 ⟹ 并行度下降
```

### Cardano：eUTXO

扩展 UTXO：给输出附加**数据（datum）**，给花费附加**校验脚本（validator）**：

```
⟹ 可以表达有状态的合约，同时保留 UTXO 的并行性
⚠️ 但"多人同时与一个池子交互"的冲突问题仍然存在，
   需要额外的批处理设计（batcher）来缓解
```

## 八、Go 实现

```go
package account

import (
	"errors"
	"math/big"

	"golang.org/x/crypto/sha3"
)

type Address [20]byte

type Account struct {
	Nonce       uint64
	Balance     *big.Int
	StorageRoot [32]byte
	CodeHash    [32]byte
}

type State map[Address]*Account

type Tx struct {
	From     Address
	To       Address
	Value    *big.Int
	Nonce    uint64
	GasLimit uint64
	GasPrice *big.Int
	ChainID  uint64 // ⭐ EIP-155：进入签名哈希，防跨链重放
}

// Apply 执行一笔转账。⚠️ 检查顺序很重要：
// nonce 和余额的检查必须在任何状态修改之前完成。
func (s State) Apply(tx *Tx) error {
	from, ok := s[tx.From]
	if !ok {
		return errors.New("account: 发送方不存在")
	}

	// ① nonce 必须严格等于当前值 —— ⭐ 这一条同时防重放和保证顺序
	if tx.Nonce != from.Nonce {
		return errors.New("account: nonce 不匹配")
	}

	// ② 余额必须覆盖转账额 + 最大可能的 Gas 费用
	//    ⚠️ 必须按 GasLimit 预扣，而不是按实际消耗——执行前无法知道实际消耗
	maxGasCost := new(big.Int).Mul(new(big.Int).SetUint64(tx.GasLimit), tx.GasPrice)
	total := new(big.Int).Add(tx.Value, maxGasCost)
	if from.Balance.Cmp(total) < 0 {
		return errors.New("account: 余额不足")
	}

	// ③ 修改状态
	from.Nonce++
	from.Balance.Sub(from.Balance, tx.Value)

	to, ok := s[tx.To]
	if !ok { // 收款方不存在则创建 —— ⚠️ 这就是状态增长的来源之一
		to = &Account{Balance: new(big.Int)}
		s[tx.To] = to
	}
	to.Balance.Add(to.Balance, tx.Value)
	return nil
}

// CreateAddress 实现 CREATE：keccak256(rlp([sender, nonce]))[12:]
func CreateAddress(sender Address, nonce uint64) Address {
	h := sha3.NewLegacyKeccak256()
	h.Write(rlpEncodeList(sender[:], rlpEncodeUint(nonce)))
	var out Address
	copy(out[:], h.Sum(nil)[12:])
	return out
}

// Create2Address 实现 CREATE2：keccak256(0xff ‖ sender ‖ salt ‖ keccak256(initCode))[12:]
// ⭐ 不含 nonce ⟹ 地址与部署时机无关，可以提前算出来。
func Create2Address(sender Address, salt [32]byte, initCode []byte) Address {
	ih := sha3.NewLegacyKeccak256()
	ih.Write(initCode)
	codeHash := ih.Sum(nil)

	h := sha3.NewLegacyKeccak256()
	h.Write([]byte{0xff})
	h.Write(sender[:])
	h.Write(salt[:])
	h.Write(codeHash)

	var out Address
	copy(out[:], h.Sum(nil)[12:])
	return out
}
```

## 九、本讲小结

- **两类账户**：EOA 由私钥控制，合约账户由代码控制。⭐ **链上一切都始于某个 EOA 的交易**——没有定时任务，"自动执行"必须有人付 Gas 去触发。
- **账户状态四个字段**：nonce、balance、storageRoot、codeHash。⚠️ 用 `code.length == 0` 判断 EOA **挡不住构造函数期间的合约**。
- ⭐ **nonce 一个字段承担三件事**：防重放、定序、派生 CREATE 地址。
- ⚠️ **严格递增带来队头阻塞**：低价的 nonce=5 卡住，后面全卡。解法是用同一 nonce 重发更高价的交易顶掉它——这就是钱包"加速/取消"的原理。
- ⚠️ **跨链重放是真实发生过的损失**（2016 ETH/ETC）。EIP-155 把 chainID 纳入签名哈希解决了它。⚠️ **但合约内部的签名验证必须自己处理 chainID**。
- **CREATE 地址 = `keccak(rlp([sender, nonce]))[12:]`；CREATE2 = `keccak(0xff‖sender‖salt‖keccak(initcode))[12:]`。**
- ⭐ **CREATE2 不含 nonce ⟹ 地址可预测 ⟹ 反事实部署**：先给一个还不存在的合约转账，用时才部署。账户抽象钱包大量使用。
- ⚠️ **CREATE2 + SELFDESTRUCT 曾允许同一地址换代码**，EIP-6780 基本堵死。⭐ **但"地址不变 ⟹ 代码不变"曾经不是安全假设**，而很多协议这样假设过。
- ⭐ **核心权衡**：UTXO 把状态切碎，换来并行和隐私，代价是无法表达共享状态；账户模型集中状态，换来合约能力，代价是天然串行。
- **AMM 池子的储备是全局共享的**，UTXO 下多人并发会互相冲突——这是模型的本质差异，不是实现难度。
- **Solana 把"显式读写集"移植到账户模型上**换取并行；⚠️ 代价是开发者必须提前声明所有会触碰的账户，动态调用下很难精确。

## 思考题

1. 一个合约写着"每月 1 号自动分红"。链上实际会发生什么？谁来付 Gas？如果没人调用会怎样？
2. 为什么 `require(msg.sender.code.length == 0)` 挡不住合约？写出攻击者的完整步骤。
3. nonce 同时做三件事。如果把"防重放"和"定序"拆成两个独立字段，会带来什么好处和坏处？
4. 你的 nonce=5 交易卡住了，nonce=6、7 都在池子里。请写出解除阻塞的具体操作，并说明为什么要用 0 ETH 自转。
5. EIP-155 之前，一笔 ETH 主网交易能被重放到哪些链上？需要满足什么条件？
6. 一个合约用 EIP-712 验证链下签名但没有把 chainID 放进域分隔符。攻击者能做什么？
7. 用 CREATE2 公式说明反事实部署：给出"先收款、后部署"的完整时间线，并指出如果初始化代码改了会怎样。
8. 为什么 UTXO 模型很难实现 AMM？请具体描述两个用户同时交易时会发生什么。
9. Solana 要求预声明读写账户。如果一个合约会根据链上数据动态决定调用哪个合约，开发者该怎么声明？这会怎样影响并行度？
10. 上面 `Apply` 里为什么必须按 `GasLimit` 而不是实际消耗来预扣余额？

