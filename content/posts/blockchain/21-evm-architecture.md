---
title: "第 21 讲：EVM 的结构——一台 256 位栈机"
date: 2026-08-30
weight: 21
aliases: ["/posts/blockchain/20-evm-architecture/"]
tags: ["区块链"]
draft: false
summary: "从记账到运行程序：EVM 的六个数据区域及其成本差异；256 位字长的两个理由和三项代价（尤其是它为什么让 zkEVM 极其困难）；JUMPDEST 规则为什么存在；一段字节码的完整逐指令推演；以及 2016 年上海 DoS 攻击如何暴露了操作码定价的本质困难。"
showToc: true
tocOpen: false
---

前四个单元讲的都是"如何就一份账本达成一致"。从这一讲开始，问题变了：

> **如何就一次「程序执行」的结果达成一致？**

这个转变比它听起来要大得多。记账只需要加减法，而运行任意程序意味着要面对**停机问题**——第 22 讲会看到 Gas 正是为此发明的。

## 一、EVM 是什么

```
EVM = Ethereum Virtual Machine

一台【准图灵完备】的【栈式】虚拟机
```

⚠️ **"准"（quasi）这个词是精确的**：

```
图灵完备意味着可以写出永不停止的程序。
⟹ 而共识要求【每个节点都执行完并得到相同结果】
⟹ ⚠️ 一个死循环会让全网卡住

EVM 的解法：每条指令消耗 Gas，Gas 耗尽则强制中止。
⟹ 于是 EVM 在【有限步数内】是图灵完备的，超出则终止。
```

⭐ **对比第 10 讲的比特币脚本：它通过"禁止循环"来保证终止，代价是表达能力受限；EVM 通过"计费"来保证终止，代价是必须发明一整套 Gas 机制。**

## 二、六个数据区域

理解 EVM，先理解数据放在哪里——**因为它们的成本相差几个数量级**。

```
┌────────────┬──────────┬────────────┬──────────────────────────┐
│ 区域        │ 生命周期  │ 访问成本    │ 说明                      │
├────────────┼──────────┼────────────┼──────────────────────────┤
│ 栈 stack   │ 单次调用  │ ⭐ 极低(3)  │ 最多 1024 项，每项 256 位  │
│ 内存 memory│ 单次调用  │ 低(3+扩展)  │ 线性字节数组，扩展二次收费│
│ 存储storage│ 永久   │ 极高     │ 256→256 映射，写入两万 Gas │
│ calldata   │ 单次调用  │ 低          │ 只读的输入数据             │
│ code       │ 永久      │ 低          │ 只读的合约字节码           │
│ returndata │ 单次调用  │ 低          │ 上一次子调用的返回值        │
└────────────┴──────────┴────────────┴──────────────────────────┘
```

⭐ **成本差异是 EVM 编程的第一性原则：**

```
读一次栈：      3 Gas
读一次冷存储：  ⚠️ 2100 Gas       （约 700 倍）
写一次新存储槽：20000 Gas      （约 6600 倍）
```

⭐ **所以"优化 Gas"的绝大部分工作，就是"少碰 storage"。** 第 23 讲会展开。

### 栈

```
最大深度 1024，每项 256 位。
⚠️ 只能操作栈顶附近：
    DUP1..DUP16   复制栈顶往下第 1..16 项
    SWAP1..SWAP16 交换栈顶与往下第 1..16 项
```

**这个"16 项"的限制是真实的编程约束**：Solidity 里一个函数局部变量太多时会报 `Stack too deep`，根源就在这里。

### 内存

```
按字节寻址的线性数组，从 0 开始，初始全零。
⭐ 收费方式：按【触及过的最高字节】计算，且是【二次方增长】：

    cost(a) = 3a + a²/512        （a = 内存字数，每字 32 字节）
```

**二次方收费是防 DoS 的设计**：线性收费下，攻击者可以用固定 Gas 申请巨量内存把节点撑爆。二次项让大内存迅速变得不可承受。

## 三、为什么是 256 位

这是 EVM 最有争议的设计决定。

### 两个理由

```
① 匹配密码学原语
   keccak256 输出 256 位，地址是它的后 160 位。
   ⭐ 用 256 位字长，哈希和地址运算不需要拆分。

② 金额运算不溢出
   1 ETH = 10¹⁸ wei。
   64 位最大约 1.8×10¹⁹，只够表示 18 个 ETH。
   ⟹ 需要更宽的字长
```

### 三项代价

```
① 浪费
   绝大多数值（循环计数、数组下标、布尔值）远小于 256 位，
   ⚠️ 但每一项都占满 32 字节。

② 在真实 CPU 上慢
   主流 CPU 是 64 位的，一次 256 位加法要拆成 4 条指令，
      乘法和除法更糟。

③ 对零知识证明极其不友好 —— 这是最严重的一条
```

第三条值得展开，因为它决定了 zkEVM 的全部困难（第 28 讲）：

```
ZK 证明系统在【有限域】上工作，域的大小通常是一个 ~64 位或 ~254 位的素数。

⚠️ EVM 的 256 位运算不是域运算，它是【带进位的整数运算 + 取模 2²⁵⁶】。
⟹ 要在电路里模拟一次 256 位加法，
   必须把它拆成多个小段，再显式处理进位和范围检查
⟹ 一条 EVM 指令可能对应成千上万个电路约束

而位运算（AND/OR/XOR/SHR）更糟——
它们在算术电路里需要把每个数【逐位分解】，
   一次 256 位异或就是 256 个约束起步。
```

⭐ **一句话：EVM 是为"链上执行便宜"设计的，而不是为"被证明"设计的。** 这就是为什么 zkEVM 项目要么接受巨大的证明开销，要么放弃字节码级等价（第 28 讲会讲这几个层次）。

## 四、控制流与 JUMPDEST

```
JUMP   ── 弹出栈顶作为目标地址，跳过去
JUMPI  ── 弹出目标地址和条件，条件非零才跳
```

⚠️ **但目标地址必须是一个 `JUMPDEST` 指令的位置，否则执行立即失败。**

⭐ **为什么要这条规则？两个理由：**

```
① 防止跳进数据中间
   PUSH2 0x1234 在字节码里是三个字节 61 12 34。
   ⚠️ 如果允许跳到 0x12 那个字节，它会被当成指令 (DUP3) 执行
   ⟹ 同一段字节可以被解释成两种完全不同的程序

② 让静态分析可行
   有了 JUMPDEST，反汇编器和分析工具能确定
   "所有可能的跳转目标是这有限的几个位置"
   ⟹ 这是所有合约分析工具的基础
```

注意 EVM **没有函数调用指令**——Solidity 的内部函数调用是编译器用 `JUMP` + 手工维护返回地址实现的。

## 五、完整推演一段字节码

计算 `3 + 5` 并返回结果：

```
字节码： 6003 6005 01 6000 52 6020 6000 f3
```

逐条执行（栈顶写在右边）：

```
PC  指令              操作                          栈              Gas
──────────────────────────────────────────────────────────────────────
00  PUSH1 0x03       压入 3                        [3]              3
02  PUSH1 0x05       压入 5                        [3, 5]           3
04  ADD              弹出 5、3，压入 8              [8]              3
05  PUSH1 0x00       压入 0（内存偏移）              [8, 0]           3
07  MSTORE           ⭐ 弹出偏移 0 和值 8            []               3
                     memory[0..31] = 0x…08                        +3 扩展
08  PUSH1 0x20       压入 32（返回长度）             [32]             3
0a  PUSH1 0x00       压入 0（返回偏移）              [32, 0]          3
0c  RETURN           返回 memory[0..31]           —               0
──────────────────────────────────────────────────────────────────────
                                                      合计约 24 Gas
```

⚠️ **注意 `MSTORE` 的参数顺序**：它先弹出**偏移**，再弹出**值**。所以压栈时必须先压值、后压偏移——这种"参数逆序"是栈机编程最常见的错误来源。

## 六、调用与回滚

### 调用栈

```
一个合约可以调用另一个合约，⚠️ 深度上限 1024。
```

⚠️ **这个限制曾经是一类攻击的基础**：攻击者先递归调用自己 1023 层，再调用受害合约——受害合约内部的调用必然失败。如果受害合约没检查返回值，就会误以为转账成功。

EIP-150 引入的 **63/64 规则**大幅缓解了它：

```
每次子调用最多只能转交【当前剩余 Gas 的 63/64】
⟹ ⭐ Gas 会先于调用深度耗尽，深度攻击不再可行
```

### 三种终止方式

| 指令 | 状态变更 | Gas |
|---|---|---|
| `STOP` / `RETURN` | 保留 | 只扣已消耗的 |
| `REVERT` | **全部撤销** | 只扣已消耗的，**剩余退回** |
| 异常（Gas 耗尽、栈溢出、无效指令） | 全部撤销 | **全部扣光** |

⭐ **`REVERT` 是 EIP-140 才加入的（2017 年）。在此之前只能用 `throw`，它会烧光全部 Gas**——这就是早期合约动辄"消耗全部 Gas 失败"的原因。

## 七、预编译合约

有些运算用 EVM 字节码实现会贵到不可用（比如椭圆曲线配对）。以太坊把它们做成**预编译**——在特定地址上，由节点用原生代码直接执行：

```
0x01  ecrecover      ⭐ 从签名恢复地址（第 7 讲）
0x02  sha256
0x03  ripemd160
0x04  identity       内存拷贝
0x05  modexp         大数模幂
0x06  bn256Add       椭圆曲线加法
0x07  bn256ScalarMul
0x08  bn256Pairing   双线性配对（第 8 讲）——ZK 验证的基础
0x09  blake2f
0x0a  pointEvaluation KZG 证明验证（EIP-4844，第 29 讲）
```

⭐ **`0x08` 的存在直接决定了「链上验证 ZK 证明」是否可行。** 没有它，一次配对运算在 EVM 里要花掉几百万 Gas；有了它，验证一个 Groth16 证明只需几十万。

## 八、定价错误是真实的攻击面

2016 年 9 月，以太坊遭遇了持续数天的 DoS 攻击（史称"上海攻击"）：

```
攻击者发现某些操作码的 Gas 价格【远低于】它们的真实成本：

   EXTCODESIZE  当时 20 Gas
   ⚠️ 但它需要从磁盘读取一个账户 —— 一次随机 I/O（第 12 讲）

⟹ 攻击者写一个循环，对上千个随机地址调用 EXTCODESIZE
⟹ 花很少的 Gas，就让每个节点做上千次随机磁盘读
⟹ 出块时间从 15 秒涨到几分钟，部分节点直接跟不上
```

修复是 **EIP-150**：把这类涉及状态访问的操作码涨价 20–50 倍。

⭐ **教训是根本性的：**

> **Gas 价格必须反映「对最慢的那个节点」的真实成本，而不是"对一台高配机器的平均成本"。**
>
> ⚠️ **而"真实成本"会随硬件、状态大小、实现方式变化——所以 Gas 定价永远是一个需要持续维护的东西，不是一次性设定的常数。**

后续的 EIP-2929（冷热访问分离）、EIP-3529（削减退款）都是同一条线上的修正。

## 九、Go：mini-EVM 解释器

```go
package evm

import (
	"errors"
	"math/big"
)

const (
	OpStop     = 0x00
	OpAdd      = 0x01
	OpMul      = 0x02
	OpSub      = 0x03
	OpPush1    = 0x60
	OpMStore   = 0x52
	OpJump     = 0x56
	OpJumpI    = 0x57
	OpJumpDest = 0x5b
	OpReturn   = 0xf3
)

// twoPow256 用于模 2²⁵⁶ —— ⭐ EVM 的所有算术都在这个环上进行，
// 溢出是【静默回绕】而不是报错。
var twoPow256 = new(big.Int).Lsh(big.NewInt(1), 256)

type EVM struct {
	code   []byte
	stack  []*big.Int
	memory []byte
	pc     int
	gas    uint64

	jumpdests map[int]bool // 预扫描出的合法跳转目标
}

func New(code []byte, gas uint64) *EVM {
	return &EVM{code: code, gas: gas, jumpdests: scanJumpDests(code)}
}

// scanJumpDests 预扫描所有 JUMPDEST 的位置。
// 必须跳过 PUSH 的立即数，否则会把数据字节误认为指令——
// 这正是第四节说的"同一段字节可以被解释成两种程序"。
func scanJumpDests(code []byte) map[int]bool {
	dests := make(map[int]bool)
	for i := 0; i < len(code); i++ {
		op := code[i]
		if op == OpJumpDest {
			dests[i] = true
		}
		if op >= 0x60 && op <= 0x7f { // PUSH1..PUSH32
			i += int(op-0x60) + 1 // 跳过立即数
		}
	}
	return dests
}

func (e *EVM) push(v *big.Int) error {
	if len(e.stack) >= 1024 {
		return errors.New("evm: 栈溢出") // 硬上限 1024
	}
	e.stack = append(e.stack, new(big.Int).Mod(v, twoPow256))
	return nil
}

func (e *EVM) pop() (*big.Int, error) {
	if len(e.stack) == 0 {
		return nil, errors.New("evm: 栈下溢")
	}
	v := e.stack[len(e.stack)-1]
	e.stack = e.stack[:len(e.stack)-1]
	return v, nil
}

func (e *EVM) useGas(n uint64) error {
	if e.gas < n {
		e.gas = 0
		return errors.New("evm: Gas 耗尽") // 异常终止，Gas 全部扣光
	}
	e.gas -= n
	return nil
}

// Run 执行字节码，返回 RETURN 的数据。
func (e *EVM) Run() ([]byte, error) {
	for e.pc < len(e.code) {
		op := e.code[e.pc]

		switch {
		case op == OpStop:
			return nil, nil

		case op >= OpPush1 && op <= 0x7f: // PUSH1..PUSH32
			if err := e.useGas(3); err != nil {
				return nil, err
			}
			n := int(op-OpPush1) + 1
			end := e.pc + 1 + n
			if end > len(e.code) {
				end = len(e.code) // 代码末尾不足时按零填充，这是 EVM 的规定行为
			}
			val := new(big.Int).SetBytes(e.code[e.pc+1 : end])
			if err := e.push(val); err != nil {
				return nil, err
			}
			e.pc += 1 + n

		case op == OpAdd, op == OpMul, op == OpSub:
			if err := e.useGas(3); err != nil {
				return nil, err
			}
			a, err := e.pop()
			if err != nil {
				return nil, err
			}
			b, err := e.pop()
			if err != nil {
				return nil, err
			}
			var r *big.Int
			switch op {
			case OpAdd:
				r = new(big.Int).Add(a, b)
			case OpMul:
				r = new(big.Int).Mul(a, b)
			case OpSub:
				r = new(big.Int).Sub(a, b)
			}
			// 统一取模 2²⁵⁶：EVM 的溢出是静默回绕
			if err := e.push(r); err != nil {
				return nil, err
			}
			e.pc++

		case op == OpMStore:
			// 参数顺序：先弹偏移，再弹值
			off, err := e.pop()
			if err != nil {
				return nil, err
			}
			val, err := e.pop()
			if err != nil {
				return nil, err
			}
			if err := e.expandMemory(int(off.Uint64()) + 32); err != nil {
				return nil, err
			}
			val.FillBytes(e.memory[off.Uint64() : off.Uint64()+32])
			e.pc++

		case op == OpJump, op == OpJumpI:
			if err := e.useGas(8); err != nil {
				return nil, err
			}
			dst, err := e.pop()
			if err != nil {
				return nil, err
			}
			jump := true
			if op == OpJumpI {
				cond, err := e.pop()
				if err != nil {
					return nil, err
				}
				jump = cond.Sign() != 0
			}
			if jump {
				d := int(dst.Uint64())
				// 目标必须是 JUMPDEST，否则立即失败
				if !e.jumpdests[d] {
					return nil, errors.New("evm: 非法跳转目标")
				}
				e.pc = d
			} else {
				e.pc++
			}

		case op == OpJumpDest:
			if err := e.useGas(1); err != nil {
				return nil, err
			}
			e.pc++

		case op == OpReturn:
			off, _ := e.pop()
			length, _ := e.pop()
			start, end := off.Uint64(), off.Uint64()+length.Uint64()
			if err := e.expandMemory(int(end)); err != nil {
				return nil, err
			}
			return e.memory[start:end], nil

		default:
			return nil, errors.New("evm: 无效指令") // 同样烧光 Gas
		}
	}
	return nil, nil
}

// expandMemory 按需扩展内存并收费。
// 二次项 words²/512 是防 DoS 的关键：大内存迅速变得不可承受。
func (e *EVM) expandMemory(size int) error {
	if size <= len(e.memory) {
		return nil
	}
	words := uint64((size + 31) / 32)
	oldWords := uint64((len(e.memory) + 31) / 32)

	cost := func(w uint64) uint64 { return 3*w + w*w/512 }
	if err := e.useGas(cost(words) - cost(oldWords)); err != nil {
		return err
	}

	newMem := make([]byte, words*32)
	copy(newMem, e.memory)
	e.memory = newMem
	return nil
}
```

## 十、本讲小结

- ⭐ **从"记账"到"运行程序"的关键难题是停机问题**。比特币脚本用"禁止循环"解决，代价是表达能力；EVM 用"计费"解决，代价是必须发明整套 Gas 机制。
- ⭐ **六个数据区域的成本相差几个数量级**：栈 3 Gas，冷存储读 2100，新存储写 20000。**"优化 Gas"的绝大部分就是"少碰 storage"。**
- **栈只能操作最近 16 项** ⟹ Solidity 的 `Stack too deep` 就来自这里。
- **内存二次方收费是防 DoS 设计**：线性收费下攻击者能用固定 Gas 撑爆节点。
- **256 位字长的两个理由**：匹配 keccak/地址、金额不溢出（1 ETH = 10¹⁸ wei，64 位只够 18 个 ETH）。
- **三项代价**：浪费、在 64 位 CPU 上慢，**以及对 ZK 极其不友好**——EVM 的 256 位整数运算不是域运算，一条指令可能对应成千上万个电路约束，位运算更要逐位分解。**EVM 是为"执行便宜"设计的，不是为"被证明"设计的。**
- **JUMPDEST 规则的两个理由**：防止跳进 PUSH 的立即数中间（同一段字节被解释成两种程序），以及**让静态分析可行**。
- **1024 调用深度曾是攻击基础**；EIP-150 的 **63/64 规则**让 Gas 先于深度耗尽，从而堵死它。
- **`REVERT` 是 2017 年才加入的**。此前失败会烧光全部 Gas。
- **预编译 `0x08`（配对）直接决定了链上验证 ZK 证明是否可行**——几百万 Gas 与几十万 Gas 的差别。
- **2016 年上海攻击暴露了定价的本质困难**：`EXTCODESIZE` 只收 20 Gas 却要做一次随机磁盘 I/O。**Gas 价格必须反映"对最慢节点"的真实成本，而真实成本会随硬件和状态大小变化——所以定价是需要持续维护的，不是一次性常数。**

## 思考题

1. 为什么"运行任意程序"比"记账"在共识上难得多？停机问题在这里具体表现为什么？
2. 比较比特币脚本和 EVM 处理终止问题的两种方式，各自放弃了什么？
3. 一个合约把一个 `uint8` 存进 storage，实际占多少字节？为什么？（第 23 讲会给出优化办法）
4. 内存扩展如果改成线性收费，攻击者能用 100 万 Gas 申请多少内存？二次方收费下呢？
5. 详细说明为什么 256 位运算对 ZK 电路不友好。为什么位运算比算术运算更糟？
6. 如果 EVM 允许跳到任意位置，请构造一段字节码，说明它能被解释成两个完全不同的程序。
7. 手工推演字节码 `6002 6003 02 6000 52 6020 6000 f3`，写出每一步的栈状态和最终返回值。
8. 调用深度攻击的完整步骤是什么？63/64 规则为什么能堵死它？请估算 1024 层需要多少初始 Gas。
9. `REVERT` 和"异常终止"在 Gas 处理上的差别是什么？为什么这个差别对用户体验很重要？
10. 上海攻击中，攻击者花的 Gas 和节点付出的真实成本比例大约是多少？设计一个新的操作码时，你会用什么方法确定它的价格？

