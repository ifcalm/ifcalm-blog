---
title: "第 7 讲：数字签名——ECDSA、可延展性与 Schnorr"
date: 2026-08-30
weight: 7
tags: ["区块链"]
draft: false
summary: "ECDSA 的完整推导与验证原理；随机数 k 重用为什么会直接泄露私钥（含 Sony PS3 事故的代数推演）与 RFC 6979 的修复；签名可延展性如何造成交易 ID 可变，SegWit 与 EIP-2 各自怎么处理；以及 Schnorr 签名的线性性为什么能带来签名聚合。"
showToc: true
tocOpen: false
---

上一讲有了密钥对 `(d, Q)`。这一讲用它来签名。

## 一、签名要满足什么

```
Sign(d, m)   → σ
Verify(Q, m, σ) → true / false
```

三个要求：

| 性质 | 含义 |
|---|---|
| **正确性** | 诚实生成的签名一定验证通过 |
| **不可伪造性** | ⭐ 即使攻击者能让你签任意多条他选的消息，他也无法伪造一条**新**消息的有效签名 |
| **公开可验证** | 任何人只要有公钥就能验证，不需要与签名者交互 |

⚠️ 第二条的标准名称是 **EUF-CMA**（适应性选择消息攻击下的存在性不可伪造）。注意它的强度：攻击者可以拿到任意多个"签名样本"，仍然伪造不出新的。

## 二、ECDSA

比特币和以太坊都用它。算法本身很短，但每一步都有讲究。

### 签名

```
输入：私钥 d，消息 m
① z = H(m) 的最左 256 位              ⚠️ 签的是哈希，不是消息本身
② 选一个随机数 k ∈ [1, n−1]           ⭐ 这一步是全部风险所在
③ R = k·G，取 r = R.x mod n           （若 r = 0 则重选 k）
④ s = k⁻¹ · (z + r·d) mod n           （若 s = 0 则重选 k）
输出：σ = (r, s)
```

### 验证

```
输入：公钥 Q，消息 m，签名 (r, s)
① 检查 r, s ∈ [1, n−1]
② z = H(m) 的最左 256 位
③ u₁ = z · s⁻¹ mod n
   u₂ = r · s⁻¹ mod n
④ R' = u₁·G + u₂·Q
⑤ 通过当且仅当 R'.x mod n == r
```

### 它为什么成立

代数推导只有三行：

```
由 s = k⁻¹(z + r·d)
⟹  k = s⁻¹(z + r·d) = s⁻¹z + s⁻¹r·d

两边乘 G：
    k·G = (s⁻¹z)·G + (s⁻¹r)·(d·G)
     R  =    u₁·G  +    u₂·Q            ⭐ 正是验证的第 ④ 步
```

⭐ **验证者算出的 `R'` 就是签名者当初的 `R`**——但验证者从头到尾不知道 `k`，也不知道 `d`。这就是签名的全部魔法。

## 三、⚠️ 随机数 k：一次重用就全盘皆输

第 ② 步那个 `k`（术语叫 **nonce**，一次性随机数）看起来只是个实现细节。**它是 ECDSA 最危险的地方。**

### 重用同一个 k 会怎样

假设用同一个 `k` 签了两条不同的消息 `m₁`、`m₂`：

```
s₁ = k⁻¹(z₁ + r·d)          ⚠️ 注意两次的 r 相同，因为 r 只依赖 k
s₂ = k⁻¹(z₂ + r·d)

相减：s₁ − s₂ = k⁻¹(z₁ − z₂)

⟹  k = (z₁ − z₂) · (s₁ − s₂)⁻¹ mod n        ← ⭐ k 被解出来了

再代回：s₁·k = z₁ + r·d
⟹  d = (s₁·k − z₁) · r⁻¹ mod n              ← ⭐ 私钥被解出来了
```

**只要两个签名的 `r` 相同，任何人都能在几毫秒内算出私钥。** 而 `r` 是签名的一部分，**公开在链上**——攻击者只需要扫描链上所有签名，找 `r` 重复的那些。

### 两个真实事故

```
① Sony PlayStation 3（2010 年公开）
   Sony 在固件签名中使用了一个固定的 k。
   ⚠️ 不是"随机数质量差"，是根本没有随机——代码里写死了一个常数。
   ⟹ 私钥被 fail0verflow 团队直接算出，任何人都能签署 PS3 认可的固件。

② 2013 年 Android 比特币钱包
   Android 的 SecureRandom 实现存在缺陷，某些设备上返回重复值。
   ⟹ 多个钱包产生了 r 相同的签名，攻击者扫链后清空了这些地址。
```

⭐ **注意这两个事故的共同点：密码学本身没有问题，ECDSA 也没有被攻破。出问题的是一个看起来无关紧要的实现细节。**

### 修复：RFC 6979 确定性 nonce

既然随机数这么危险，**干脆不用随机数**：

```
k = HMAC-SHA256(私钥 d, 消息哈希 z)      （实际算法更复杂，思路如此）
```

⭐ 这样 `k` 变成了 `(d, z)` 的确定性函数：

- 同一个私钥签**不同**消息 → `z` 不同 → `k` 必然不同 ✅
- 同一个私钥签**同一**消息 → 每次得到完全相同的签名 ✅（这也让测试变得可复现）
- 完全不依赖系统随机源 ✅

⚠️ **现代所有正经的比特币/以太坊库都默认使用 RFC 6979。** 如果你看到一个库要求你自己传 `k` 进去，那是个危险信号。

## 四、⚠️ 签名可延展性

ECDSA 有一个数学性质：

> **如果 `(r, s)` 是有效签名，那么 `(r, n − s)` 也是有效签名。**

验证一下：把 `s` 换成 `−s`，则 `u₁, u₂` 都变号，于是

```
R'' = (−u₁)·G + (−u₂)·Q = −(u₁·G + u₂·Q) = −R
```

而 `−R` 与 `R` 的 **x 坐标相同**（曲线关于 x 轴对称，第 6 讲），所以 `r` 不变，验证照样通过。

### 后果：交易 ID 可变

比特币的交易 ID 是**整笔交易（含签名）的哈希**。所以：

```
Alice 广播交易 T，txid = abc123...
       │
中间人截获，把签名 (r,s) 改成 (r, n−s)
       │
       ▼
交易 T' 内容等价、签名依然有效，但 txid = def456...   ⚠️ 变了

⟹ 若 T' 先被打包：
     Alice 的钱确实转出去了
     但她的钱包在等 abc123，永远等不到 ⟹ 以为交易失败
```

⭐ **这不能偷钱**（金额和收款方都没变，那些字段是被签名保护的），但它能制造混乱。历史上 Mt.Gox 曾以此为其资金损失的解释——**这个解释后来被普遍认为不成立**，但可延展性本身是真实存在的问题。

真正严重的后果在**依赖 txid 的合约**上：闪电网络等二层协议需要引用"还没上链的交易的 txid"，可延展性会让整个协议崩溃。

### 两种修复

```
比特币：BIP-62 / BIP-146 规定只接受 low-s（即 s ≤ n/2）
        ⭐ 更彻底的是 SegWit：把签名移出 txid 的计算范围
           ⟹ 改签名不再影响 txid，从结构上消除问题

以太坊：EIP-2（2016 年，Homestead 硬分叉）规定 s 必须 ≤ n/2
        ⚠️ 在此之前的交易不受此限制
```

## 五、公钥恢复：以太坊为什么不传公钥

比特币交易里通常带着公钥。以太坊交易**不带**——它靠一个技巧从签名里把公钥算回来。

```
验证公式：R = u₁·G + u₂·Q
移项：    Q = r⁻¹·(R − u₁·G) · ... （整理后可解出 Q）
```

已知 `r` 就知道 `R.x`，而符合这个 x 的点有两个（y 奇或偶），再加上 `r` 可能来自 `R.x` 或 `R.x + n` 的情况——所以需要额外 **2 比特** 来消歧义。这就是以太坊签名里的 `v`：

```
签名 = (r, s, v)   共 65 字节
    v = 27 或 28                          （早期）
    v = chainID·2 + 35 或 36              （EIP-155 之后）
```

⭐ **收益**：交易里省掉 33 或 65 字节的公钥。以太坊上每一笔交易都受益。

⭐ **附带好处**：`v` 里编码了 **chainID**，这是 EIP-155 引入的**跨链重放保护**——以太坊主网上的一笔交易，因为 `v` 不对，无法在其他 EVM 链上重放。

⚠️ **EIP-155 之前没有这个保护。** 2016 年 ETH/ETC 分叉后，同一笔交易可以在两条链上同时生效，造成了大量意外损失。

EVM 里的 `ecrecover` 预编译合约就是做这件事的：

```
ecrecover(hash, v, r, s) → 签名者地址
```

⚠️ **注意 `ecrecover` 在签名无效时返回零地址而不是报错。** 忘记检查返回值是否为 `address(0)` 是一个经典的合约漏洞（第 33 讲）。

## 六、Schnorr 签名：更简单也更强

Schnorr 签名比 ECDSA 早（1989 年），但因专利限制到 2008 年才自由使用，所以中本聪选了 ECDSA。比特币在 2021 年的 Taproot 升级中引入了它。

### 算法

```
签名：
① 选随机 k，R = k·G
② e = H(R ‖ Q ‖ m)
③ s = k + e·d mod n
   σ = (R, s)

验证：
   检查 s·G == R + e·Q
```

推导同样只有一行：

```
s·G = (k + e·d)·G = k·G + e·(d·G) = R + e·Q   ✅
```

### ⭐ 关键性质：线性

对比一下两个签名公式：

```
ECDSA ： s = k⁻¹(z + r·d)      ← ⚠️ 有求逆，d 和 k 纠缠在一起
Schnorr： s = k + e·d           ← ⭐ 关于 d 和 k 都是线性的
```

线性带来了一个 ECDSA 做不到的能力：**签名可以相加**。

```
Alice: s₁ = k₁ + e·d₁
Bob:   s₂ = k₂ + e·d₂
       ─────────────────
合并:  s  = s₁ + s₂ = (k₁+k₂) + e·(d₁+d₂)

⟹ 这是一个对聚合公钥 Q = Q₁ + Q₂ 的、完全合法的单个签名
```

⭐ **一个 2-of-2 多签，在链上看起来和一个普通单签完全一样。** 收益是三重的：

```
① 更小：n 个签名 → 1 个签名
② 更省 Gas / 手续费
③ ⭐ 更私密：链上看不出这是多签，也看不出参与人数
```

⚠️ 实际的多方聚合协议（MuSig2）比上面的朴素加法复杂得多——朴素做法有**恶意密钥攻击**（rogue key attack）：Bob 可以宣称自己的公钥是 `Q₂ − Q₁`，从而单独控制聚合公钥。真实协议需要额外的承诺轮次来防止这一点。

### 其他优势

| | ECDSA | Schnorr |
|---|---|---|
| 安全性证明 | 需要较强的假设（一般群模型） | ⭐ 在随机预言机模型下可归约到 ECDLP |
| 可延展性 | ⚠️ 有 | 无 |
| 聚合 | 不支持 | ⭐ 支持 |
| 签名大小 | 64–65 字节 | 64 字节 |
| 采用 | 比特币（传统）、以太坊 | 比特币 Taproot、多数新链 |

## 七、签的到底是什么

⚠️ 一个常见的疏忽：**签名保护的只是被纳入哈希的那些字段。**

以太坊传统交易签的是：

```
keccak256( RLP编码( nonce, gasPrice, gasLimit, to, value, data, chainID, 0, 0 ) )
```

注意其中每一项的作用：

| 字段 | 不签它会怎样 |
|---|---|
| `nonce` | ⚠️ 同一笔交易可被无限重放 |
| `to` / `value` | 中间人可以改收款人和金额 |
| `data` | 合约调用参数可被篡改 |
| `chainID` | ⚠️ 交易可在其他 EVM 链上重放（EIP-155 之前的真实问题） |
| `gasLimit` | 攻击者可把 gasLimit 改小让交易执行失败 |

⭐ **设计任何签名方案时的第一个问题永远是：哪些数据在哈希里，哪些不在？** 不在的那些，攻击者可以随意修改。

## 八、Go 实现

```go
package sign

import (
	"crypto/ecdsa"
	"crypto/rand"
	"crypto/sha256"
	"fmt"
	"math/big"
)

// Signature 是 ECDSA 签名的两个分量。
type Signature struct{ R, S *big.Int }

// Sign 演示 ECDSA 的签名过程。
// ⚠️ 生产环境请使用 RFC 6979 确定性 nonce（如 dcrec/secp256k1 的实现），
// 不要像这里一样依赖系统随机源——一次 k 重用就会泄露私钥。
func Sign(priv *ecdsa.PrivateKey, msg []byte) (*Signature, error) {
	curve := priv.Curve
	n := curve.Params().N
	z := new(big.Int).SetBytes(hashMsg(msg))

	for {
		k, err := rand.Int(rand.Reader, new(big.Int).Sub(n, big.NewInt(1)))
		if err != nil {
			return nil, err
		}
		k.Add(k, big.NewInt(1))

		rx, _ := curve.ScalarBaseMult(k.Bytes()) // R = k·G
		r := new(big.Int).Mod(rx, n)
		if r.Sign() == 0 {
			continue
		}

		// s = k⁻¹ (z + r·d) mod n
		kInv := new(big.Int).ModInverse(k, n)
		s := new(big.Int).Mul(r, priv.D)
		s.Add(s, z)
		s.Mul(s, kInv)
		s.Mod(s, n)
		if s.Sign() == 0 {
			continue
		}

		// ⭐ low-s 规范化：若 s > n/2 则取 n−s，消除可延展性（EIP-2 / BIP-146）
		half := new(big.Int).Rsh(n, 1)
		if s.Cmp(half) > 0 {
			s.Sub(n, s)
		}
		return &Signature{R: r, S: s}, nil
	}
}

// Verify 实现第二节的验证步骤。
func Verify(pub *ecdsa.PublicKey, msg []byte, sig *Signature) bool {
	curve := pub.Curve
	n := curve.Params().N

	if sig.R.Sign() <= 0 || sig.S.Sign() <= 0 ||
		sig.R.Cmp(n) >= 0 || sig.S.Cmp(n) >= 0 {
		return false
	}

	z := new(big.Int).SetBytes(hashMsg(msg))
	sInv := new(big.Int).ModInverse(sig.S, n)

	u1 := new(big.Int).Mul(z, sInv)
	u1.Mod(u1, n)
	u2 := new(big.Int).Mul(sig.R, sInv)
	u2.Mod(u2, n)

	x1, y1 := curve.ScalarBaseMult(u1.Bytes())          // u₁·G
	x2, y2 := curve.ScalarMult(pub.X, pub.Y, u2.Bytes()) // u₂·Q
	x, _ := curve.Add(x1, y1, x2, y2)                    // R' = u₁G + u₂Q

	return new(big.Int).Mod(x, n).Cmp(sig.R) == 0
}

// RecoverPrivateKey 演示 k 重用的后果：
// 给定两个使用了相同 k（因而 r 相同）的签名，直接解出私钥。
// ⭐ 这个函数能跑通，正是 Sony PS3 私钥被算出来的原理。
func RecoverPrivateKey(n *big.Int, r, s1, s2, z1, z2 *big.Int) *big.Int {
	// k = (z1 − z2) / (s1 − s2) mod n
	dz := new(big.Int).Sub(z1, z2)
	ds := new(big.Int).Sub(s1, s2)
	k := new(big.Int).Mul(dz, new(big.Int).ModInverse(ds, n))
	k.Mod(k, n)

	// d = (s1·k − z1) / r mod n
	d := new(big.Int).Mul(s1, k)
	d.Sub(d, z1)
	d.Mul(d, new(big.Int).ModInverse(r, n))
	d.Mod(d, n)
	return d
}

func hashMsg(msg []byte) []byte {
	h := sha256.Sum256(msg)
	return h[:]
}

func main() {
	fmt.Println("见各函数注释")
}
```

## 九、本讲小结

- **签名的三个要求**：正确性、EUF-CMA 不可伪造性（⭐ 攻击者可拿到任意多签名样本仍伪造不出新的）、公开可验证。
- **ECDSA 验证成立的原因只有一行代数**：`k = s⁻¹(z + rd)`，两边乘 `G` 就得到 `R = u₁G + u₂Q`。验证者算出了签名者的 `R`，却不知道 `k` 和 `d`。
- ⭐⚠️ **k 重用直接泄露私钥**：两个签名 `r` 相同 ⟹ `k = (z₁−z₂)/(s₁−s₂)` ⟹ `d = (s₁k−z₁)/r`。而 `r` 就公开在链上，攻击者只需扫链找重复。
- **Sony PS3 用了写死的 k，Android 钱包用了有缺陷的随机源。** ⭐ 两次事故里密码学都没被攻破，出问题的是实现细节。
- ⭐ **RFC 6979 用 `k = HMAC(d, z)` 彻底消除随机源依赖**：不同消息必然不同 k，同消息可复现，不依赖系统熵。
- ⚠️ **可延展性**：`(r,s)` 有效 ⟹ `(r, n−s)` 也有效，因为 `−R` 与 `R` 的 x 坐标相同。后果是 **txid 可变**，会破坏依赖未确认 txid 的二层协议。
- **两种修复**：low-s 规则（比特币 BIP-146、以太坊 EIP-2），以及 SegWit 把签名移出 txid 计算——后者是结构性的根治。
- **以太坊用 `v` 做公钥恢复**，省掉每笔交易的公钥字节；⭐ `v` 里还编码了 chainID，这是 EIP-155 的跨链重放保护。⚠️ `ecrecover` 失败时返回零地址而非报错。
- ⭐ **Schnorr 的 `s = k + e·d` 是线性的**，所以签名可以相加：n 个签名聚合成 1 个，更小、更省费、且**链上看不出这是多签**。⚠️ 朴素聚合有恶意密钥攻击，真实协议（MuSig2）需要额外承诺轮。
- ⭐ **签名只保护被纳入哈希的字段。** 设计时第一个问题永远是"哪些数据在哈希里"——不在的都可以被中间人修改。

## 思考题

1. 完整推导 ECDSA 的验证等式，说明为什么验证者不需要知道 `k`。
2. 给定 `n`、两个 `r` 相同的签名 `(r,s₁)`、`(r,s₂)` 和对应的 `z₁`、`z₂`，写出解出私钥的每一步。为什么 `r` 相同就意味着 `k` 相同？
3. RFC 6979 的确定性 nonce 让同一消息每次签出相同结果。这算不算信息泄露？为什么可以接受？
4. 证明 `(r, n−s)` 是有效签名。它为什么不能被用来偷钱？
5. SegWit 和 low-s 规则都能缓解可延展性。说明为什么前者是结构性根治而后者不是。
6. 以太坊交易不含公钥，靠 `v` 恢复。请说明为什么需要 2 比特而不是 1 比特。
7. 一个合约写 `require(ecrecover(h,v,r,s) == owner)`。如果 `owner` 恰好是 `address(0)` 会怎样？如果签名格式非法呢？
8. 用 Schnorr 的线性性推导两方聚合。然后说明 Bob 声称 `Q₂ = Q'− Q₁` 时能做什么，以及为什么这构成攻击。
9. 如果以太坊签名时漏掉了 `gasLimit` 字段，攻击者能做什么？漏掉 `chainID` 呢？

