---
title: "第 10 讲：UTXO 模型与比特币脚本"
date: 2026-08-30
weight: 10
tags: ["区块链"]
draft: false
summary: "把钱当成硬币而不是余额：UTXO 的定义、找零机制、手续费为什么是隐式的；比特币脚本作为一台栈式虚拟机的完整执行推演（P2PKH 逐步跟踪）、P2SH 的成本转移、多签的著名 off-by-one bug、时间锁与闪电网络的关系；以及 UTXO 模型的三个优点和它为什么写不了合约。"
showToc: true
tocOpen: false
---

**你**的钱包显示余额 100。

在以太坊上，这个 100 确确实实存在某个地方——一个字段，写着 100。

在比特币上，**没有任何地方写着 100**。你的钱包是把散落在链上的几枚"硬币"找出来、加了一遍，才告诉你这个数的。

同一句"我有 100 块"，两条链的含义完全不同，而这个差别会一路影响到交易长什么样、隐私有多好、能不能并行验证。

## 一、两种记账方式

```
账户模型（银行、以太坊）
   数据库里存：Alice → 100
   转 30 给 Bob：Alice -= 30，Bob += 30

UTXO 模型（现金、比特币）
   ⭐ 没有"余额"这个字段。
   只有一堆"硬币"，每一枚有面额和归属：
       硬币 #a3f2  面额 50  归 Alice
       硬币 #7b91  面额 30  归 Alice
       硬币 #c405  面额 20  归 Alice
   Alice 的余额 = 属于她的硬币加起来 = 100（这是算出来的，不是存着的）
```

**UTXO = Unspent Transaction Output，未花费的交易输出。** 它就是那枚"硬币"。

### 打个比方

两种模型的差别，就是**记账本**和**钱包**的差别。

账户模型是记账本：上面写着"你有 100 块"。这是一个**数字**，改它就是把数字擦掉重写。

UTXO 模型是钱包：里面装着一张 50、一张 30、一张 20。**"你有 100 块"不是写在哪儿的，是你把里面的钞票加起来的结果。**

⚠️ 由此直接跟出一条让很多人别扭的性质：**花钱要"找零"。** 你要付 60，手上没有正好 60 的钞票，只能掏出一张 50 加一张 30，然后**收回 20 的找零**。链上的交易长得和这一模一样——而不是"从余额里扣掉 60"。

⭐ 记住这个画面，后面几乎所有 UTXO 的特性都能自己推出来：为什么交易大小不固定、为什么隐私性更好一点、为什么并行验证更容易、以及为什么"我的余额"需要钱包去扫描计算。

## 二、交易是什么

> **一笔交易，就是销毁若干个旧 UTXO，创造若干个新 UTXO。**

```
Alice 要转 60 给 Bob，她手上有 50 和 30 两枚：

     输入                        输出
  ┌──────────┐            ┌──────────────┐
  │ #a3f2  50│───┐    ┌──▶│ 60 → Bob     │
  └──────────┘   ├────┤   └──────────────┘
  ┌──────────┐   │    │   ┌──────────────┐
  │ #7b91  30│───┘    └──▶│ 19.9 → Alice │  ⭐ 找零
  └──────────┘            └──────────────┘

  输入合计 80，输出合计 79.9
  差额 0.1 就是手续费——它是隐式的，没有专门的字段
```

三个要点：

```
① ⭐ UTXO 必须整体花费，不能只花一半
   ⟹ 所以必须有"找零"输出，把余下的还给自己

② 手续费 = 输入总额 − 输出总额，没有专门字段
   忘记写找零输出 = 把全部差额当手续费送给矿工。
      历史上真的发生过：2016 年有人一笔交易付了 291 BTC 手续费。

③ 被花掉的 UTXO 立刻从集合中删除
   ⟹ 想再花一次，就会发现它不在集合里 ⟹ 这就是双花检测
```

### coinbase 交易

每个区块的第一笔交易是特殊的：**它没有输入**，凭空创造新币。

```
coinbase 输出金额 ≤ 区块奖励 + 本块所有交易的手续费之和
```

⚠️ 节点会严格检查这个上限——这是"不能凭空增发"的执行点。

## 三、UTXO 长什么样

```go
type OutPoint struct {          // 指向某个 UTXO 的引用
    TxID  [32]byte              // 创造它的那笔交易
    Index uint32                // 是那笔交易的第几个输出
}

type TxOut struct {
    Value        int64          // 金额，单位聪（1 BTC = 10⁸ 聪）
    ScriptPubKey []byte         // ⭐ 锁定脚本：什么条件才能花掉它
}

type TxIn struct {
    PrevOut   OutPoint
    ScriptSig []byte            // 解锁脚本：证明你满足条件
    Sequence  uint32            // 用于时间锁和 RBF
}
```

⭐ **注意 `ScriptPubKey` 的措辞：它不是"这枚币属于某地址"，而是"满足这段脚本就能花掉它"。** 这个抽象比"归属"强大得多——它可以表达多签、时间锁、哈希锁等任意条件。

## 四、比特币脚本：一台栈式虚拟机

### 设计

```
基于栈：所有操作从栈上取参数，结果压回栈
⚠️ 没有循环，没有跳转 ⟹ 非图灵完备
```

⭐ **"非图灵完备"是刻意的设计，不是能力不足。** 好处有二：

```
① 执行时间有上界 ⟹ ⭐ 不需要 Gas 机制（对比第 22 讲）
② 行为可静态分析 ⟹ 更容易保证安全
```

代价是表达能力有限——写不了 DeFi。以太坊选择了相反的方向，代价就是必须发明 Gas。

### 验证过程

```
把 ScriptSig 和 ScriptPubKey 依次执行，
⭐ 最后栈顶为真则花费有效。
```

### P2PKH 完整推演

最经典的脚本，"支付到公钥哈希"：

```
ScriptPubKey (锁)：  OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
ScriptSig   (钥匙)： <sig> <pubKey>
```

一步步执行，右边是栈的状态（栈顶在右）：

```
初始                                       栈: [ ]

执行 ScriptSig：
  push <sig>                               栈: [ sig ]
  push <pubKey>                            栈: [ sig, pubKey ]

执行 ScriptPubKey：
  OP_DUP        复制栈顶                    栈: [ sig, pubKey, pubKey ]
  OP_HASH160    对栈顶做 RIPEMD160(SHA256)  栈: [ sig, pubKey, hash(pubKey) ]
  push <pubKeyHash>                        栈: [ sig, pubKey, hash(pubKey), pubKeyHash ]
  OP_EQUALVERIFY  弹出两个比较，不等则立即失败
                                           栈: [ sig, pubKey ]
  OP_CHECKSIG   弹出公钥和签名，验证签名     栈: [ true ]

⟹ 栈顶为真，花费有效 ✅
```

⭐ **这段脚本同时检查了两件事**：

```
① 你给的公钥，哈希后确实等于收款时锁定的那个哈希 → 你是收款人
② 你用对应私钥签了这笔交易                        → 你本人授权了这次花费
```

注意 **`OP_CHECKSIG` 签的不是整笔交易**，而是交易的一个特定"简化版本"（由 SIGHASH 标志决定包含哪些字段）。第 7 讲第七节讲过：**没被签的字段可以被改**。这正是可延展性的来源之一。

### 常用操作码

| 操作码 | 作用 |
|---|---|
| `OP_DUP` / `OP_DROP` / `OP_SWAP` | 栈操作 |
| `OP_HASH160` / `OP_SHA256` | 哈希 |
| `OP_EQUAL` / `OP_EQUALVERIFY` | 比较（后者失败即终止） |
| `OP_CHECKSIG` / `OP_CHECKMULTISIG` | 验签 |
| `OP_CHECKLOCKTIMEVERIFY` (CLTV) | 绝对时间锁：某高度/时间之前不可花 |
| `OP_CHECKSEQUENCEVERIFY` (CSV) | 相对时间锁：被创建后 N 个块内不可花 |
| `OP_RETURN` | 标记输出不可花，用于往链上写数据 |

### OP_CHECKMULTISIG 的 off-by-one

多签脚本：

```
ScriptPubKey：  2 <pubKey1> <pubKey2> <pubKey3> 3 OP_CHECKMULTISIG
ScriptSig：     OP_0 <sig1> <sig2>
                 ↑
        ⚠️ 这个 OP_0 是个纯粹的 bug 补丁
```

原始实现里 `OP_CHECKMULTISIG` **多弹出了一个栈元素**。这个 bug 被发现时比特币已经在运行，修复它需要硬分叉——**于是它被永久保留下来**，所有多签脚本都必须多塞一个无用的 `OP_0`。

**这是共识系统的一个普遍教训：一旦上线，bug 就变成了规范。** 第 21 讲会看到 EVM 里同样性质的历史包袱。

### 时间锁与闪电网络

CLTV / CSV 让"条件支付"成为可能：

```
这笔钱：
   要么 Alice 和 Bob 都签名，立刻可花
   要么 只有 Alice 签名，但必须等 1000 个区块之后

⭐ 这就是支付通道的核心：
   双方合作时随时结算，一方失联时另一方等待期过后可单方面取回。
```

闪电网络完全建立在这类脚本之上。而它对**交易 ID 稳定性**的依赖，正是第 7 讲说可延展性必须被修复的原因。

## 五、P2SH：把复杂性转移给花费者

一个 3-of-5 多签脚本很长。如果直接放进 `ScriptPubKey`：

```
⚠️ 付款人要为这段长脚本付手续费——可他只是想给钱而已
付款人还得知道收款人的完整多签配置
```

**P2SH（支付到脚本哈希）**把它倒过来：

```
锁定时： OP_HASH160 <脚本的哈希> OP_EQUAL      ← 只有 23 字节
花费时： 提供完整脚本 + 满足它的数据

⟹ ⭐ 复杂性和费用都由花费者承担，付款人只需知道一个地址
```

⭐ **这个"承诺 + 稍后揭示"的模式在区块链里反复出现**：Merkle 根、状态根、Rollup 的状态承诺，都是同一个思路——**链上只存哈希，需要时才提供原像**。

Taproot 进一步优化了它：合作路径下**链上只看到一个普通单签**，脚本的存在完全隐藏。

## 六、UTXO 模型的取舍

⭐ 这一节的每一条取舍，都能从"钱包 vs 记账本"直接读出来：**钱包便于并行清点、不容易泄露你的总额，但每次付款都要挑钞票、要找零，账也更难一眼看清。**

### 三个真实优点

```
① 并行验证
   每笔交易显式声明了它读写的全部状态（就是那几个 UTXO）
   ⟹ 不相交的交易可以并行验证，无需协调
   ⚠️ 对比账户模型：合约调用在执行前不知道会碰哪些状态

② 隐私性更好
   每次收款用新地址是自然做法，没有"账户"这个天然的关联点
   但找零仍会泄露关联（第 33 讲）

③ 无状态验证更友好
   验证一笔交易只需要它引用的那几个 UTXO，
   ⟹ 可以要求交易自带 UTXO 的存在性证明
```

### 三个真实缺点

```
① 写不了合约
   "全局状态"在 UTXO 模型里没有自然的表达。
   ⭐ 一个 DeFi 池子的余额是全局共享的，但 UTXO 每次只能被一个人花掉
   ⟹ 并发用户会互相冲突

② 钱包复杂
   要选择花哪几枚 UTXO（币选择算法），要处理找零，
   选择策略还会泄露隐私

③ UTXO 集合膨胀
   全节点必须把整个 UTXO 集合常驻内存或快速存储（否则验证极慢）
   以近年的规模计，条目数在一亿量级，序列化后数 GB。
   "粉尘攻击"：给别人发大量极小额 UTXO，
      既污染对方钱包，又永久增加全网的存储负担。
```

⭐ **注意第 ③ 条和第 3 讲的"状态增长"是同一个问题的两种表现**：账户模型膨胀的是账户和存储槽，UTXO 模型膨胀的是 UTXO 集合。**两者都只增不减。**

## 七、Go 实现

```go
package utxo

import (
	"errors"
	"fmt"
)

type OutPoint struct {
	TxID  [32]byte
	Index uint32
}

type TxOut struct {
	Value        int64
	ScriptPubKey []byte
}

type TxIn struct {
	PrevOut   OutPoint
	ScriptSig []byte
}

type Tx struct {
	In  []TxIn
	Out []TxOut
}

// Set 是全节点必须维护的 UTXO 集合。
// ⚠️ 它必须常驻快速存储——每笔交易的每个输入都要查一次。
type Set map[OutPoint]TxOut

// Validate 验证一笔普通交易（非 coinbase），返回手续费。
func (s Set) Validate(tx *Tx, verify func(sig, pubKey []byte, prev TxOut) bool) (int64, error) {
	if len(tx.In) == 0 || len(tx.Out) == 0 {
		return 0, errors.New("utxo: 交易必须有输入和输出")
	}

	// 同一笔交易内部也可能重复引用同一个 UTXO，必须单独检查
	seen := make(map[OutPoint]bool, len(tx.In))

	var inSum int64
	for _, in := range tx.In {
		if seen[in.PrevOut] {
			return 0, errors.New("utxo: 交易内部双花")
		}
		seen[in.PrevOut] = true

		// 双花检测就是这一句：不在集合里 = 不存在或已被花掉
		prev, ok := s[in.PrevOut]
		if !ok {
			return 0, fmt.Errorf("utxo: 引用了不存在或已花费的输出 %x:%d",
				in.PrevOut.TxID[:4], in.PrevOut.Index)
		}

		if !verify(in.ScriptSig, prev.ScriptPubKey, prev) {
			return 0, errors.New("utxo: 解锁脚本验证失败")
		}
		inSum += prev.Value
	}

	var outSum int64
	for _, out := range tx.Out {
		if out.Value < 0 {
			return 0, errors.New("utxo: 输出金额为负") // 漏掉这一条就能凭空造币
		}
		outSum += out.Value
	}

	if inSum < outSum {
		return 0, errors.New("utxo: 输出大于输入")
	}
	return inSum - outSum, nil // 手续费是隐式的差额
}

// Apply 把一笔已验证的交易作用到集合上。
func (s Set) Apply(txid [32]byte, tx *Tx) {
	for _, in := range tx.In {
		delete(s, in.PrevOut) // 花掉的立即删除
	}
	for i, out := range tx.Out {
		s[OutPoint{TxID: txid, Index: uint32(i)}] = out
	}
}
```

⭐ **注意 `Validate` 里那句 `if !ok`。整个双花防御就是这一行**：UTXO 一旦被花，就从集合里删了；再引用它，就查不到。

## 八、栈式脚本解释器（节选）

```go
// Eval 执行 ScriptSig + ScriptPubKey，栈顶为真则通过。
// ⚠️ 简化版：只实现 P2PKH 需要的几个操作码。
func Eval(scriptSig, scriptPubKey []byte, checkSig func(sig, pub []byte) bool) bool {
	var stack [][]byte

	run := func(script []byte) bool {
		for i := 0; i < len(script); {
			op := script[i]
			switch {
			case op >= 1 && op <= 75: // 直接压入 op 个字节
				if i+1+int(op) > len(script) {
					return false
				}
				stack = append(stack, script[i+1:i+1+int(op)])
				i += 1 + int(op)

			case op == OpDup:
				if len(stack) < 1 {
					return false
				}
				stack = append(stack, stack[len(stack)-1])
				i++

			case op == OpHash160:
				if len(stack) < 1 {
					return false
				}
				top := stack[len(stack)-1]
				stack[len(stack)-1] = hash160(top)
				i++

			case op == OpEqualVerify:
				if len(stack) < 2 {
					return false
				}
				a, b := stack[len(stack)-1], stack[len(stack)-2]
				stack = stack[:len(stack)-2]
				if !bytesEqual(a, b) {
					return false // VERIFY 类操作码失败即整体终止
				}
				i++

			case op == OpCheckSig:
				if len(stack) < 2 {
					return false
				}
				pub, sig := stack[len(stack)-1], stack[len(stack)-2]
				stack = stack[:len(stack)-2]
				stack = append(stack, boolBytes(checkSig(sig, pub)))
				i++

			default:
				return false // 未实现的操作码
			}
		}
		return true
	}

	if !run(scriptSig) || !run(scriptPubKey) {
		return false
	}
	return len(stack) > 0 && isTrue(stack[len(stack)-1])
}
```

## 九、本讲小结

- ⭐ **UTXO 模型里没有"余额"字段**，只有一堆带面额和锁定条件的"硬币"。余额是**算出来的**。
- **交易 = 销毁旧 UTXO + 创造新 UTXO。** UTXO **必须整体花费**，所以必须有找零输出。
- ⚠️ **手续费是隐式的差额**（输入 − 输出），没有专门字段。忘写找零 = 把差额全部送给矿工，历史上真的发生过。
- **双花检测就是"查集合里还在不在"**——花掉即删除，再引用就查不到。
- **`ScriptPubKey` 表达的是"满足什么条件能花"，而不是"属于谁"。** 这个抽象能表达多签、时间锁、哈希锁等任意条件。
- **脚本非图灵完备是刻意设计**：执行时间有上界 ⟹ **不需要 Gas**；行为可静态分析 ⟹ 更安全。代价是写不了 DeFi。
- **P2PKH 同时检查两件事**：你给的公钥哈希对得上锁定的哈希，且你用对应私钥签了名。
- **`OP_CHECKMULTISIG` 的多余 `OP_0` 是一个永远修不掉的 bug**。**共识系统一旦上线，bug 就变成了规范。**
- **P2SH 把复杂性和费用转移给花费者**，付款人只需知道一个地址。这个"链上存哈希、用时给原像"的模式在区块链里反复出现。
- **UTXO 的三个优点**：可并行验证（交易显式声明读写集）、隐私更好、对无状态验证友好。
- **三个缺点**：写不了共享状态的合约、钱包管理复杂、UTXO 集合只增不减且必须常驻内存（粉尘攻击）。

## 思考题

1. Alice 有面额 3、5、8 的三枚 UTXO，要转 10 给 Bob 并留 0.1 做手续费。写出至少两种可行的输入输出组合，并说明各自的优劣。
2. 为什么手续费不设成一个显式字段？这样设计有什么好处和风险？
3. 完整推演一次 P2PKH 脚本执行，写出每一步之后的栈状态。
4. 如果 `OP_EQUALVERIFY` 换成 `OP_EQUAL`（不立即终止），这段 P2PKH 脚本还安全吗？攻击者能做什么？
5. `OP_CHECKMULTISIG` 的 off-by-one 为什么不能被修复？如果强行修复会发生什么？
6. 设计一个脚本，表达"Alice 和 Bob 共同签名可立即花费；或者 Alice 单独签名但需等待 144 个区块"。
7. 说明为什么 UTXO 交易可以并行验证，而以太坊的合约调用不能。给出一个具体的冲突例子。
8. 为什么 UTXO 模型很难实现一个自动做市商（AMM）？"多个用户同时与同一个池子交易"在 UTXO 下会发生什么？
9. 粉尘攻击给受害者和全网分别造成什么成本？有什么防御手段？
10. 上面 Go 代码里 `if out.Value < 0` 这一行如果漏掉，攻击者能构造出什么交易？

