---
title: "实验 4：mini-EVM"
date: 2026-08-30
weight: 73
tags: ["区块链"]
draft: false
summary: "实现一台可运行的 EVM 子集：栈、内存、存储、Gas 计量、JUMPDEST 校验、调用与回滚语义。用它编译并跑通一个简单合约，然后亲手复现三个真实的定价与语义陷阱。"
showToc: true
tocOpen: false
---

对应[第 20–23 讲]({{< ref "20-evm-architecture.md" >}})。

⭐ **写一台 EVM 是理解它的最快方式**——每一个"为什么这样设计"的问题，在你实现它的时候都会自己冒出来。

## 任务一：核心解释器

```go
type EVM struct {
    code      []byte
    stack     []*uint256.Int     // ⭐ 或用 big.Int，但要处理模 2²⁵⁶
    memory    []byte
    storage   map[[32]byte][32]byte
    pc        int
    gas       uint64
    refund    uint64
    jumpdests map[int]bool
    static    bool
    depth     int
}
```

**必须实现的操作码：**

```
算术：   ADD MUL SUB DIV SDIV MOD SMOD ADDMOD MULMOD EXP
比较：   LT GT SLT SGT EQ ISZERO
位运算： AND OR XOR NOT BYTE SHL SHR SAR
哈希：   KECCAK256
栈：     POP PUSH1..PUSH32 DUP1..DUP16 SWAP1..SWAP16
内存：   MLOAD MSTORE MSTORE8 MSIZE
存储：   SLOAD SSTORE
控制流： JUMP JUMPI PC JUMPDEST
终止：   STOP RETURN REVERT INVALID
```

⚠️ **四个必须处理对的地方：**

```
① ⭐ 所有算术都在【模 2²⁵⁶】上进行，溢出是【静默回绕】而不是报错
② ⭐ SDIV / SMOD / SLT / SGT 是【有符号】的，
   要按二进制补码解释 —— ⚠️ 且 EVM 规定 x / 0 = 0，不是异常
③ ⭐ SAR 是算术右移（补符号位），SHR 是逻辑右移（补 0）
④ ⚠️ EXP 的 Gas 与指数的字节长度有关，不是固定值
```

### ⭐ JUMPDEST 预扫描

```go
func scanJumpDests(code []byte) map[int]bool {
    dests := make(map[int]bool)
    for i := 0; i < len(code); i++ {
        if code[i] == OpJumpDest {
            dests[i] = true
        }
        if code[i] >= 0x60 && code[i] <= 0x7f {
            i += int(code[i]-0x60) + 1   // ⭐ 必须跳过 PUSH 的立即数
        }
    }
    return dests
}
```

⚠️ **写一个测试：构造一段字节码，其中 PUSH 的立即数恰好是 `0x5b`（JUMPDEST 的操作码）。断言你的扫描【没有】把它当成合法跳转目标。**

⭐ **这一条如果写错，同一段字节可以被解释成两个不同的程序（[第 20 讲第四节]({{< ref "20-evm-architecture.md" >}})）。**

## 任务二：Gas 计量

```go
func (e *EVM) useGas(n uint64) error
func (e *EVM) expandMemory(size int) error
```

⭐ **内存扩展的二次方收费：**

```
cost(words) = 3×words + words²/512
每次扩展只收【增量】
```

**必须测试：**

```
① 申请 1 KB 内存 vs 1 MB 内存的成本比 —— ⭐ 观察二次项如何主导
② ⚠️ 一个循环不断扩展内存，在给定 Gas 下最多能申请多少？
③ ⭐ 如果改成线性收费，同样的 Gas 能申请多少？（说明为什么必须是二次的）
```

⭐ **SSTORE 的四档定价（[第 22 讲第三节]({{< ref "22-storage-layout.md" >}})）：**

```
零 → 非零        20000
非零 → 非零       2900
非零 → 零        2900 + 退款 4800
同一交易内重复写   100
```

⚠️ **退款上限是 `gasUsed / 5`（EIP-3529），且必须在交易结束时才结算。**

## 任务三：存储布局计算

**实现 [第 22 讲]({{< ref "22-storage-layout.md" >}}) 的三个公式：**

```go
func MappingSlot(slot uint64, key []byte) [32]byte
func NestedMappingSlot(slot uint64, k1, k2 []byte) [32]byte
func DynamicArraySlot(slot uint64, index uint64) [32]byte
```

⭐ **验证方法：找一个真实的以太坊合约（比如任意 ERC-20），用你的公式算出某个地址的 balance 槽，再用 `eth_getStorageAt` 从公开节点读一次，⭐ 对比结果。**

⚠️ **对得上，说明你的实现正确；对不上，通常是"key 没有左填充到 32 字节"。**

## 任务四：调用语义

```go
func (e *EVM) Call(target Address, code []byte, value uint64, input []byte) ([]byte, error)
func (e *EVM) DelegateCall(code []byte, input []byte) ([]byte, error)
func (e *EVM) StaticCall(target Address, code []byte, input []byte) ([]byte, error)
```

⭐ **必须正确的三点：**

```
① ⭐ DelegateCall 保持 msg.sender、msg.value 和【存储】不变，只换代码
② ⭐ StaticCall 具有【传染性】：一旦进入，整个子调用树都禁止写状态
③ ⭐ 63/64 规则：子调用最多拿到当前剩余 Gas 的 63/64（EIP-150）
```

**写一个测试证明第 ③ 条让深度攻击失效：**

```go
func TestDepthAttackFailsWithGas(t *testing.T) {
    // ⭐ 尝试递归调用 1024 层
    // 断言：在合理的初始 Gas 下，Gas 会先于深度耗尽
    // ⚠️ 算一算：要真的达到 1024 层，需要多少初始 Gas？
}
```

## ⭐ 任务五：三个必须复现的陷阱

### ① 存储冲突（第 23 讲第三节）

```go
func TestProxyStorageCollision(t *testing.T) {
    // 代理合约把 implementation 地址放在 slot 0
    // 实现合约的第一个变量也在 slot 0
    // ⭐ 调用一次，断言 implementation 地址被覆盖 ⟹ 合约变砖
    // ⚠️ 然后换成 EIP-1967 槽，断言问题消失
}
```

### ② 定价错误引发的 DoS（第 20 讲第八节）

```go
func TestUnderpricedStateAccess(t *testing.T) {
    // ⭐ 给 SLOAD 一个错误的低价格（比如 20 Gas，模拟 EIP-150 之前）
    // 写一个循环，用固定 Gas 触发尽可能多次状态访问
    // 统计：⚠️ 每单位 Gas 引发了多少次"磁盘读"
    // 再改成 EIP-2929 的冷热定价，对比这个比值
}
```

### ③ REVERT 与异常的 Gas 差别

```go
func TestRevertVsException(t *testing.T) {
    // ⭐ REVERT：状态回滚，剩余 Gas 退回
    // ⚠️ 无效指令：状态回滚，Gas 全部扣光
    // 断言两者的剩余 Gas 不同
}
```

## 任务六：跑通一个真实合约

**手写（或用 solc 编译）一个最小的计数器合约，用你的 EVM 跑通：**

```solidity
contract Counter {
    uint256 public count;
    function increment() public { count += 1; }
}
```

⭐ **需要额外实现：**

```
① calldata 与函数选择器分发（前 4 字节匹配）
② CALLDATALOAD / CALLDATASIZE / CALLDATACOPY
③ RETURN 返回 ABI 编码的结果
```

⭐ **验证：连续调用 `increment()` 三次，然后调用 `count()`，断言返回 3。并统计每次调用的 Gas——对比真实以太坊上的数值（约 43000 首次、26000 之后），看你的实现差在哪里。**

## 提交清单

```
□ evm.go            解释器主体
□ opcodes.go        操作码实现
□ gas.go            Gas 计量与内存扩展
□ storage.go        槽计算三公式
□ call.go           三种调用语义 + 63/64 规则
□ jumpdest_test.go  ⭐ PUSH 立即数中的 0x5b 不被误认
□ traps_test.go     ⭐ 三个陷阱的复现
□ counter_test.go   跑通计数器合约
□ ANSWERS.md        任务二三个问题 + Gas 对比分析
```

## ⚠️ 常见错误

```
① ⭐ 用 int 或 int64 存栈元素 ⟹ 无法表示 256 位
② ⚠️ 忘记 EVM 的除零返回 0 而不是 panic
③ ⭐ MSTORE 的参数顺序搞反（先弹偏移，再弹值）
④ ⚠️ 内存扩展按"申请量"而不是"触及的最高字节"计费
⑤ ⭐ StaticCall 的只读标志没有向下传递
⑥ ⚠️ SSTORE 退款立即结算 ⟹ 绕过了 gasUsed/5 的上限
```

---

> **相关**：[第 20 讲]({{< ref "20-evm-architecture.md" >}})、[第 21 讲]({{< ref "21-gas.md" >}})、[第 22 讲]({{< ref "22-storage-layout.md" >}})、[第 23 讲]({{< ref "23-call-semantics.md" >}})
