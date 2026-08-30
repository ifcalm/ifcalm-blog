---
title: "第 22 讲：合约存储布局——slot、mapping 与打包"
date: 2026-08-30
weight: 22
tags: ["区块链"]
draft: false
summary: "2²⁵⁶ 个存储槽如何被分配：顺序分配、变量打包、动态数组与 mapping 的哈希寻址公式；为什么 mapping 无法遍历；SSTORE 的四档定价与打包优化的真实收益边界；以及 private 变量为什么根本不是私密的。"
showToc: true
tocOpen: false
---

## 一、存储是什么样的

```
每个合约账户有自己的存储：

    storage : uint256 → uint256

⭐ 一共 2²⁵⁶ 个"槽（slot）"，每个 32 字节，【初始全为零】。
```

⭐ **"初始全零"这个约定很重要，它带来两个后果：**

```
① 不需要初始化 —— 没写过的槽读出来就是 0
② ⚠️ "从未使用"和"值恰好是 0"【无法区分】
```

第 ② 条在实践中会咬人：

```solidity
mapping(address => uint256) balances;

// ⚠️ 这句话无法区分"这个人余额是 0"和"这个人从来没出现过"
if (balances[user] == 0) { ... }

// ⭐ 需要额外的标志位：
mapping(address => bool) registered;
```

## 二、Solidity 的分配规则

### 顺序分配与打包

```solidity
contract Example {
    uint256 a;    // slot 0
    uint128 b;    // slot 1，占低 16 字节
    uint128 c;    // slot 1，占高 16 字节  ⭐ 和 b 打包在一起
    address d;    // slot 2，占 20 字节
    uint96  e;    // slot 2，占剩下 12 字节 ⭐ 20 + 12 = 32，正好塞满
    uint256 f;    // slot 3
}
```

规则：

```
① 按声明顺序，从 slot 0 开始
② ⭐ 如果下一个变量能装进当前 slot 的剩余空间，就打包进去
③ ⚠️ 装不下就开新槽，剩余空间【浪费】
```

⚠️ **所以声明顺序会影响 Gas：**

```solidity
// ❌ 占 3 个 slot
uint128 a;   // slot 0（浪费 16 字节）
uint256 b;   // slot 1
uint128 c;   // slot 2（浪费 16 字节）

// ✅ 占 2 个 slot
uint128 a;   // slot 0
uint128 c;   // slot 0  ⭐ 打包
uint256 b;   // slot 1
```

⭐ **`address(20) + uint96(12) = 32` 是最经典的组合**，在协议代码里随处可见。

### 定长数组

```solidity
uint256[3] arr;   // 从 slot p 开始，连续占 p, p+1, p+2
```

### ⭐ 动态数组

```solidity
uint256[] arr;    // 假设在 slot p

slot p          存【长度】
元素 arr[i] 存在  keccak256(p) + i
```

### ⭐ Mapping

```solidity
mapping(uint256 => uint256) m;   // 假设在 slot p

⚠️ slot p 本身【不存任何东西】（留空）

m[k] 存在：  keccak256( k ‖ p )

    其中 k 和 p 都左填充到 32 字节，拼接成 64 字节再哈希
```

**嵌套 mapping：**

```solidity
mapping(address => mapping(address => uint256)) allowance;  // slot p

allowance[a][b] 存在：
    keccak256( b ‖ keccak256( a ‖ p ) )
```

⭐ **理解这个公式的价值：它让你能直接从链上读出任意合约的任意 mapping 值**——第七节会用到。

### ⚠️ 为什么 mapping 用哈希，以及它的代价

```
键空间是 2²⁵⁶，不可能预先分配连续区间。
⟹ ⭐ 用哈希把键"散列"到整个 2²⁵⁶ 的槽空间里
   （碰撞概率可忽略，第 4 讲）

⚠️ 代价：
   ⭐ 无法遍历 mapping —— 因为没有任何地方记录"哪些键被用过"
```

这是 Solidity 一个著名的限制。要能遍历，必须自己额外维护一个数组：

```solidity
mapping(address => uint256) balances;
address[] holders;             // ⚠️ 额外的存储成本
mapping(address => bool) seen; // 防止重复加入
```

### string 与 bytes

```
⭐ 短的（≤ 31 字节）：数据和长度【一起存在槽内】
    slot 内容 = 数据 ‖ (长度 × 2)          ← 最低位为 0

   长的（≥ 32 字节）：
    slot 内容 = 长度 × 2 + 1               ← ⭐ 最低位为 1 作为标记
    数据存在 keccak256(p) 开始的连续槽里
```

⭐ **用最低位区分长短**是一个很典型的位技巧：长度乘 2 后最低位必然为 0，于是这一位空出来做标志。

## 三、SSTORE 的定价

存储是 EVM 里最贵的资源，且价格分四档（EIP-2200 + EIP-3529）：

```
零 → 非零        20000 Gas      ⭐ 最贵：新增了状态
非零 → 非零       2900 Gas       （热访问；首次访问还要加 2100 冷访问费）
非零 → 零        2900 Gas + 退款 4800    ⭐ 减少了状态
同一交易内重复写   100 Gas        ⭐ 已经"脏"了，不再额外计费
```

⭐ **定价逻辑非常清楚：它按"对全网状态的净影响"收费。**

```
新增一个槽 ⟹ 所有节点要永久多存 32 字节 ⟹ 收 20000
修改已有槽 ⟹ 状态大小不变 ⟹ 只收 2900
清空一个槽 ⟹ 减少状态 ⟹ 退钱（⚠️ 但有上限，第 21 讲）
```

### 读取

```
SLOAD 冷：2100      SLOAD 热：100
```

⭐ **对比一下就能看出优化的方向：**

```
读一次冷存储 = 2100 Gas
在内存里操作 = 3 Gas

⟹ ⭐ 循环里反复读同一个 storage 变量是最常见的浪费。
   把它先读进 memory，能省掉几乎全部开销。
```

## 四、优化实践

### ① 缓存 storage 读

```solidity
// ❌ 每次循环都读一次 storage
for (uint i = 0; i < items.length; i++) { ... }
//                    ↑ items.length 每次都是一次 SLOAD

// ✅ 读一次
uint256 len = items.length;
for (uint i = 0; i < len; i++) { ... }
```

### ② ⚠️ 打包不总是划算

⭐ **这是最容易被误解的一点。**

```
打包的收益：⭐ 多个变量共用一个 slot，一次 SLOAD/SSTORE 搞定
打包的成本：⚠️ 读写单个字段需要【位移和掩码】运算

⟹ ⭐ 只有当这些字段【经常被同时读写】时，打包才划算。
   如果它们总是被【分别】访问，打包反而会因为多余的位运算变贵。
```

```solidity
// ✅ 划算：这三个字段总是一起更新
struct Position {
    uint128 amount;    // ┐
    uint64  timestamp; // ├ 一个 slot，一次 SSTORE
    uint64  lockUntil; // ┘
}

// ⚠️ 未必划算：如果 owner 几乎不变而 count 频繁变化，
//    每次改 count 都要读出整个 slot、掩码、写回
struct Bad {
    address owner;
    uint96  count;
}
```

### ③ constant 与 immutable

```solidity
uint256 constant  MAX = 100;     // ⭐ 编译期常量，直接嵌入字节码
address immutable OWNER;         // ⭐ 构造时确定，也嵌入字节码

⟹ 读取成本 = 3 Gas（PUSH），而不是 2100 Gas（SLOAD）
```

⚠️ **`immutable` 不占用任何 storage slot**——这也意味着它无法被代理合约的 delegatecall 正确共享（第 23 讲）。

## 五、⚠️ private 变量不是私密的

⭐ **这是最重要的一条实践认知：**

```solidity
contract Secret {
    uint256 private password = 42;   // ⚠️ 它在 slot 0
}
```

任何人都可以直接读出来：

```
eth_getStorageAt(合约地址, 0, "latest")   ⟹ 0x…2a
```

⭐ **`private` 和 `internal` 只是 Solidity 编译期的可见性修饰符，它们约束的是「别的合约能不能调用」，完全不影响链上数据的可读性。**

```
⚠️ 链上所有数据都是公开的：
   ① 存储可以被 eth_getStorageAt 直接读
   ② 未上链的交易在 mempool 里也是公开的（第 32 讲的 MEV 基础）
   ③ 即使是"内部计算的中间值"，也能通过模拟执行看到
```

⭐ **推论：任何需要保密的东西，都不能以明文形式进入链上。** 正确做法是第 8 讲的承诺方案（先提交哈希、后揭示），或第 30 讲的零知识证明。

## 六、Go：计算存储槽

```go
package storage

import (
	"math/big"

	"golang.org/x/crypto/sha3"
)

func keccak(parts ...[]byte) []byte {
	h := sha3.NewLegacyKeccak256()
	for _, p := range parts {
		h.Write(p)
	}
	return h.Sum(nil)
}

// pad32 把值左填充到 32 字节。⚠️ Solidity 的所有槽计算都基于 32 字节对齐。
func pad32(b []byte) []byte {
	out := make([]byte, 32)
	copy(out[32-len(b):], b)
	return out
}

// MappingSlot 计算 m[key] 的存储位置：keccak256(key ‖ slot)
// ⭐ 这就是能直接从链上读出任意 mapping 值的原因。
func MappingSlot(mappingSlot uint64, key []byte) []byte {
	return keccak(pad32(key), pad32(new(big.Int).SetUint64(mappingSlot).Bytes()))
}

// NestedMappingSlot 计算 m[k1][k2]：keccak256(k2 ‖ keccak256(k1 ‖ slot))
func NestedMappingSlot(mappingSlot uint64, k1, k2 []byte) []byte {
	inner := MappingSlot(mappingSlot, k1)
	return keccak(pad32(k2), inner)
}

// DynamicArraySlot 计算动态数组第 index 个元素的位置。
// ⚠️ 数组【长度】存在 slot 本身，元素从 keccak256(slot) 开始。
func DynamicArraySlot(arraySlot uint64, index uint64) []byte {
	base := new(big.Int).SetBytes(
		keccak(pad32(new(big.Int).SetUint64(arraySlot).Bytes())))
	base.Add(base, new(big.Int).SetUint64(index))
	return pad32(base.Bytes())
}

// ─────────── 打包布局的计算 ───────────

type Field struct {
	Name string
	Size int // 字节数
}

type Placement struct {
	Field  string
	Slot   uint64
	Offset int // ⭐ 在槽内的字节偏移
}

// Layout 模拟 Solidity 的打包规则：顺序分配，装得下就打包，装不下开新槽。
func Layout(fields []Field) []Placement {
	var out []Placement
	var slot uint64
	var used int

	for _, f := range fields {
		if used+f.Size > 32 { // ⚠️ 装不下，开新槽，当前槽剩余空间浪费
			slot++
			used = 0
		}
		out = append(out, Placement{Field: f.Name, Slot: slot, Offset: used})
		used += f.Size
	}
	return out
}

// SstoreCost 返回一次 SSTORE 的成本和退款额（EIP-2200 + EIP-3529 简化版）。
// ⭐ 定价按"对全网状态的净影响"：新增最贵，修改次之，清除退钱。
func SstoreCost(current, new_ *big.Int, alreadyWritten bool) (cost, refund uint64) {
	if alreadyWritten {
		return 100, 0 // ⭐ 同一交易内重复写，槽已经"脏"了
	}
	zeroCur := current.Sign() == 0
	zeroNew := new_.Sign() == 0

	switch {
	case zeroCur && !zeroNew:
		return 20000, 0 // ⚠️ 新增状态：所有节点永久多存 32 字节
	case !zeroCur && zeroNew:
		return 2900, 4800 // ⭐ 清除状态：退款（EIP-3529 后从 15000 降到 4800）
	case zeroCur && zeroNew:
		return 100, 0 // 零写零，无变化
	default:
		return 2900, 0 // 修改已有值：状态大小不变
	}
}
```

## 七、本讲小结

- **存储是 2²⁵⁶ 个 32 字节的槽，初始全零。** ⚠️ **"从未使用"和"值为 0"无法区分**——需要额外的标志位。
- **Solidity 按声明顺序分配槽，能装下就打包**。⚠️ **声明顺序会影响 Gas**：`uint128, uint256, uint128` 占 3 槽，重排后只占 2 槽。⭐ `address(20) + uint96(12)` 是最经典的组合。
- **动态数组**：槽本身存长度，元素从 `keccak256(p)` 开始。**Mapping**：槽本身留空，`m[k]` 在 `keccak256(k ‖ p)`；嵌套则是 `keccak256(k₂ ‖ keccak256(k₁ ‖ p))`。
- ⭐ **mapping 用哈希是因为 2²⁵⁶ 的键空间无法预分配**。⚠️ **代价是无法遍历**——没有任何地方记录哪些键被用过。
- **string/bytes 用最低位区分长短**：长度乘 2 后最低位必为 0，空出来做标志。
- ⭐ **SSTORE 按"对全网状态的净影响"定价**：零→非零 20000（新增状态）、非零→非零 2900（大小不变）、非零→零 2900 + 退款（减少状态）。
- ⭐ **冷 SLOAD 2100 vs 内存 3 Gas** ⟹ **循环里反复读同一个 storage 变量是最常见的浪费**。
- ⚠️ **打包不总是划算**：收益是共用一次 SLOAD/SSTORE，成本是位移和掩码。⭐ **只有字段经常被同时读写时才划算。**
- **`constant` / `immutable` 直接嵌入字节码**，读取 3 Gas 而非 2100。⚠️ `immutable` 不占槽，因此无法被 delegatecall 共享。
- ⭐⭐ **`private` 变量根本不是私密的**：`eth_getStorageAt` 可以直接读出来。`private`/`internal` 只约束"别的合约能不能调用"。
- ⭐ **推论：任何需要保密的东西都不能明文上链。** 正确做法是承诺方案（第 8 讲）或零知识证明（第 30 讲）。

## 思考题

1. 写出 `uint64 a; address b; uint64 c; uint128 d;` 的槽分配。重新排序使占用最少，并算出省了多少。
2. 一个 mapping 在 slot 3，键是地址 `0xAB…CD`。写出计算其值所在槽的完整步骤。
3. 为什么 mapping 的 slot 本身留空不用？如果把长度存在那里会有什么问题？
4. 你需要遍历所有持币地址。请给出一个方案，并算出它相比纯 mapping 增加了多少存储成本。
5. 一个 30 字节的 string 和一个 40 字节的 string 分别怎么存？给出两者槽内容的具体形式。
6. 为什么"零→非零"比"非零→非零"贵近 7 倍？这个差价对应什么真实成本？
7. 一个循环执行 100 次，每次读同一个 storage 变量。缓存到 memory 能省多少 Gas？
8. 举一个"打包反而更贵"的具体例子，估算两种布局的 Gas 差别。
9. 一个合约用 `uint256 private secret` 存了一个抽奖种子。写出攻击者读出它的完整步骤。
10. 一个密封竞价拍卖合约要求出价保密。用第 8 讲的承诺方案设计它，并说明每一步链上存了什么。

