---
title: "第 24 讲：调用语义——delegatecall、代理与可升级性的代价"
date: 2026-08-30
weight: 24
aliases: ["/posts/blockchain/23-call-semantics/"]
tags: ["区块链"]
draft: false
summary: "CALL、DELEGATECALL、STATICCALL 三者上下文的精确差别；代理模式如何实现「可升级」以及存储冲突为什么会毁掉一切；EIP-1967 伪随机槽的巧妙之处；Parity 多签冻结 51 万 ETH 的完整成因；以及可升级性在信任模型上究竟改变了什么。"
showToc: true
tocOpen: false
---

同一段代码，用不同的方式调用，会改写**不同人的**数据。

这句话是很多重大合约事故的全部根源——包括那次把整个钱包库"自杀"掉、锁死几十万个 ETH 的事件。

### 打个比方

三种调用的区别，是**你怎么请一个专家来干活**：

```
CALL          你把活外包给他，他在【他自己的办公室】做，用他的档案柜
DELEGATECALL  ⭐ 你把他请进【你的办公室】，他用【你的】档案柜干活
STATICCALL    同 CALL，但合同写明：只许看，不许改任何东西
```

⚠️ 中间那一条是全部危险的来源：**代码是他的，数据是你的。** 你请来的人如果不靠谱，他动的是你柜子里的东西。

而这里最容易被读漏的一点是：**DELEGATECALL 不是一个"高级用法"，它是代理合约（也就是几乎所有可升级合约）的工作原理。** 也就是说，你日常打交道的大部分合约，都在用这条指令——**危险的不是它被用了，是用它的人有没有想清楚"谁的柜子"这件事。**

## 一、三种调用

合约调合约时，有三条不同的指令，**区别全部在"用谁的上下文"**。

```
CALL          在【被调用者】的上下文里执行被调用者的代码
DELEGATECALL  ⭐ 在【调用者】的上下文里执行被调用者的代码
STATICCALL    同 CALL，但禁止任何状态修改
```

用一张表把上下文变量说清楚。假设 **A 调用 B**：

| | `msg.sender` | `msg.value` | `address(this)` | **读写的 storage** |
|---|---|---|---|---|
| **CALL** | A | 新传的值 | B | **B 的** |
| **DELEGATECALL** | **A 的 caller** | **A 收到的 value** | **A** | **A 的** |
| **STATICCALL** | A | 0（不可转账） | B | B 的（只读） |

⭐ **一句话记住 delegatecall：**

> **借用别人的代码，操作自己的数据。**

⚠️ **注意 `DELEGATECALL` 那一行的 `msg.sender`：它不是 A，而是"调用 A 的那个人"。** 这个细节是很多权限漏洞的来源——一个函数以为自己在检查直接调用者，实际检查的是更外层的人。

## 二、代理模式

`delegatecall` 让"可升级合约"成为可能：

```
┌──────────────────┐          ┌───────────────────┐
│   Proxy（代理）   │          │ Implementation    │
│                  │          │  （逻辑实现）      │
│ ⭐ 保存全部数据    │ delegate │                   │
│ 保存 impl 地址    │─────────▶│ 只有代码，无数据 │
│ fallback 转发一切 │  call    │                   │
└──────────────────┘          └───────────────────┘
        ▲
        │ 用户始终与这个地址交互
```

```
⭐ 升级 = 把 Proxy 里存的 implementation 地址改成新合约。
   数据全部在 Proxy 里，一个字节都不用迁移。
```

最小实现：

```solidity
contract Proxy {
    // ⚠️ 这个变量存在哪个 slot，是全部问题的核心。见第三节。
    address implementation;

    fallback() external payable {
        address impl = implementation;
        assembly {
            calldatacopy(0, 0, calldatasize())
            // delegatecall：用 impl 的代码，操作【本合约】的存储
            let ok := delegatecall(gas(), impl, 0, calldatasize(), 0, 0)
            returndatacopy(0, 0, returndatasize())
            switch ok
            case 0 { revert(0, returndatasize()) }
            default { return(0, returndatasize()) }
        }
    }
}
```

## 三、存储冲突：代理模式的头号杀手

⚠️ 这就是"请进你的办公室、用你的档案柜"最直接的后果：**两个人对同一个档案柜的编号规则理解不一致**，于是 A 以为在写第 3 格，B 以为第 3 格放的是别的东西。下面这一节讲的全是怎么让两边对齐编号。

`delegatecall` 用的是**调用者的存储**，而两个合约的变量布局是**各自独立编译**的。

```
Proxy 的布局：            Implementation 的布局：
   slot 0: implementation    slot 0: owner
                             slot 1: totalSupply
```

⚠️ **灾难就在这里：**

```
用户调用 Proxy 的某个函数
   ⟹ delegatecall 到 Implementation
   ⟹ Implementation 的代码写 owner（它以为是 slot 0）
   ⟹ ⭐ 实际写进了 Proxy 的 slot 0
   ⟹ Proxy 的 implementation 地址被覆盖成了一个地址值！

⟹ 下次调用时，Proxy 会 delegatecall 到一个随机地址
⟹ 合约彻底变砖，数据永久锁死
```

### EIP-1967：伪随机槽

解法是**把代理的元数据放到一个几乎不可能被撞上的槽里**：

```
implementation 槽 = keccak256("eip1967.proxy.implementation") − 1
admin 槽         = keccak256("eip1967.proxy.admin") − 1
```

⭐ **两个设计细节都值得注意：**

```
① 用哈希做槽号
   ⟹ Solidity 的顺序分配永远从 0、1、2… 开始，
      ⭐ 不可能碰到一个 2²⁵⁶ 空间里的随机位置

② 为什么要减 1
   ⟹ 让这个槽号【不是任何已知字符串的 keccak 输出】。
      如果它恰好等于 keccak256(x)，那么一个动态数组或 mapping
      就可能通过精心构造的键映射到这里。
      减 1 之后，要撞上它就需要先找到一个哈希原像——不可行。
```

**这是一个很典型的"防御性偏移"技巧**，同样的思路在很多协议里出现。

## 四、四种升级模式

| 模式 | 升级逻辑在哪 | 特点 |
|---|---|---|
| **透明代理** | 在 Proxy 里 | 管理员调用走代理自己的逻辑，其他人走 delegatecall。每次调用多一次 SLOAD 判断身份 |
| **UUPS** | 在 Implementation 里 | Proxy 更轻更省 Gas。**新实现忘记带升级函数 ⟹ 永久锁死** |
| **Beacon** | 在一个共享的 Beacon 里 | 一次升级同时改掉成千上万个代理 |
| **Diamond（EIP-2535）** | 按函数选择器路由到不同 facet | 突破合约大小限制，复杂度高 |

⭐ **透明代理为什么要区分管理员**：如果管理员和普通用户都走 delegatecall，那么当实现合约里恰好有一个函数与代理的 `upgradeTo` **选择器相同**时，管理员就永远无法调用到实现的那个函数——这叫**函数选择器冲突**。透明代理通过"看是不是管理员"来消除歧义。

## 五、初始化：Parity 冻结事件

代理模式下**不能用构造函数**：

```
构造函数在【Implementation 部署时】执行，
⟹ 它写的是 Implementation 自己的存储
⟹ ⭐ 而 Proxy 的存储里什么都没有
```

所以必须改用一个普通函数：

```solidity
function initialize(address owner_) external initializer {
    owner = owner_;
}
```

⚠️ **而这引入了一个新的攻击面：如果实现合约本身没有被初始化，任何人都可以去初始化它。**

### 2017 年 11 月的 Parity 事件

这是这个漏洞最著名、损失最惨重的一次：

```
① Parity 多签钱包采用"共享库"设计：
   每个用户的钱包是一个轻量合约，
   ⭐ 通过 delegatecall 调用一个公共的 WalletLibrary。

② 那个 WalletLibrary 合约【自己从未被初始化】。
   它只是一份代码，本不该有 owner。

③ 一个用户调用了 WalletLibrary 的 initWallet()，
   把自己设成了这个【库合约】的 owner。

④ 然后他调用了库里的 kill()，触发 SELFDESTRUCT。

⑤ 库合约被销毁 ⟹ 所有 delegatecall 到它的钱包
   全部指向一个【空地址】
   ⟹ 587 个钱包、约 51.4 万 ETH 【永久冻结】，至今无法取出。
```

⭐ **三个层次的教训：**

```
① 实现合约必须在部署时立刻被"锁死"
   ⟹ 现在的标准做法是在构造函数里调用 _disableInitializers()

② ⭐ delegatecall 建立了一个【单点依赖】
   一个库合约的死亡，会同时杀死所有依赖它的合约。
   而"合约不可变"的直觉让人低估了这个风险。

③ SELFDESTRUCT 是一个危险的原语
   EIP-6780 之后它被大幅限制（第 11 讲），
   但历史上它造成的损失已经无法挽回。
```

## 六、可升级性到底改变了什么

这一节是本讲的重点，也是整门课反复出现的主题。

```
智能合约最初的价值主张是：
   ⭐ "代码即法律"——部署之后没有人能改，包括作者。

可升级性把这个前提【整个拿掉了】：
   你信任的不再是【代码】，而是【持有升级密钥的那个人】。
```

⭐ **这不必然是坏事。** 复杂协议几乎不可能一次写对，没有升级能力意味着一个 bug 就是永久损失。但**它必须被明说**，因为它改变了整个风险模型：

```
不可升级：⭐ 风险 = 代码有 bug
可升级：  风险 = 代码有 bug ∪ 升级者作恶 ∪ 升级密钥被盗
```

### 评估一个可升级协议的四个问题

```
① ⭐ 谁能升级？
   单个 EOA？多签？DAO 投票？
   "多签"要看阈值和签名者是否独立——3/5 但五个人在同一家公司，
      实质就是 1 个人。

② 有没有时间锁？
   升级提案到生效之间有多长？
   ⟹ 时间锁的唯一作用是【给用户留出撤离的时间】。
      没有时间锁的升级，等于随时可以清空所有资金。

③ 升级范围有多大？
   能改任意逻辑，还是只能改几个参数？

④ 我能退出吗？
   如果我不同意某次升级，能不能在它生效前把资产取走？
```

⭐ **第 ② 和第 ④ 条是一对：时间锁只有在你能退出时才有意义。**

**一个必须点破的事实**：许多号称"去中心化"的协议，其升级权掌握在少数几个密钥手里。**审计报告审的是当前那份实现代码，而它明天可以被换掉。**

## 七、Go：调用上下文模拟

```go
package callframe

type Address [20]byte

// Context 是一次调用的执行上下文。
type Context struct {
	Sender  Address // msg.sender
	Address Address // address(this) —— ⭐ 也决定用谁的存储
	Value   uint64  // msg.value
	Code    []byte  // 正在执行的代码
	Static  bool    // true 时禁止任何状态修改
}

// Call 构造 CALL 的上下文：
// 存储和 this 都切换到被调用者。
func Call(cur *Context, target Address, code []byte, value uint64) *Context {
	return &Context{
		Sender:  cur.Address, // 调用者变成 msg.sender
		Address: target,      // this 和存储都是 target 的
		Value:   value,
		Code:    code,
		Static:  cur.Static, // static 具有传染性：一旦进入就无法脱离
	}
}

// DelegateCall 构造 DELEGATECALL 的上下文：
// 只换代码，其余全部保持不变——"借用代码，操作自己的数据"。
func DelegateCall(cur *Context, code []byte) *Context {
	return &Context{
		Sender:  cur.Sender,  // 保持不变！不是 cur.Address
		Address: cur.Address, // this 和存储仍是调用者的
		Value:   cur.Value,   // 也保持不变，不能重新指定
		Code:    code,        // 唯一改变的东西
		Static:  cur.Static,
	}
}

// StaticCall 构造 STATICCALL：同 CALL，但强制只读。
func StaticCall(cur *Context, target Address, code []byte) *Context {
	c := Call(cur, target, code, 0)
	c.Static = true // 一旦置位，整个子调用树都无法写状态
	return c
}

// ─────────── EIP-1967 槽计算 ───────────

// EIP1967Slot 计算代理元数据的存储位置。
// 减 1 让结果不是任何已知字符串的 keccak 输出，
// 从而无法被 mapping 或动态数组的寻址公式撞上。
func EIP1967Slot(label string) [32]byte {
	h := keccak256([]byte(label))
	// 大端序减 1
	for i := 31; i >= 0; i-- {
		if h[i] > 0 {
			h[i]--
			break
		}
		h[i] = 0xff
	}
	return h
}

// StorageCollision 检查代理与实现的存储布局是否冲突。
// 这正是把 implementation 放在 slot 0 会导致合约变砖的原因。
func StorageCollision(proxySlots, implSlots map[uint64]string) map[uint64][2]string {
	conflicts := make(map[uint64][2]string)
	for slot, pName := range proxySlots {
		if iName, ok := implSlots[slot]; ok {
			conflicts[slot] = [2]string{pName, iName}
		}
	}
	return conflicts
}
```

## 八、本讲小结

- ⭐ **delegatecall 的一句话定义：借用别人的代码，操作自己的数据。** 三种调用的区别全在"用谁的上下文"。
- **delegatecall 下 `msg.sender` 不是调用者，而是"调用调用者的那个人"**——很多权限漏洞源于此。
- **代理模式让升级 = 改一个地址**，数据一字节都不用迁移。
- **存储冲突是代理模式的头号杀手**：实现合约以为在写自己的 slot 0，实际写进了代理的 implementation 地址 ⟹ **合约彻底变砖，数据永久锁死。**
- **EIP-1967 用 `keccak256(标签) − 1` 做槽号**：哈希让顺序分配撞不上；**减 1 让它不是任何已知字符串的哈希输出**，从而无法被 mapping/数组的寻址公式撞上。
- **四种升级模式各有取舍**：透明代理（解决选择器冲突，但每次调用多一次 SLOAD）、UUPS（更省 Gas，**新实现忘带升级函数就永久锁死**）、Beacon（一次改全部）、Diamond（突破大小限制但复杂）。
- **代理不能用构造函数**，必须用 `initialize()`。**而未被初始化的实现合约可以被任何人初始化。**
- **Parity 事件的完整链条**：共享库从未初始化 → 有人把自己设成库的 owner → 调用 kill 触发 SELFDESTRUCT → **587 个钱包、约 51.4 万 ETH 永久冻结**。
- **三个教训**：实现合约必须在部署时锁死初始化；**delegatecall 建立单点依赖，库的死亡会杀死所有依赖者**；SELFDESTRUCT 是危险原语。
- ⭐⭐ **可升级性拿掉了"代码即法律"这个前提**：你信任的不再是代码，而是**持有升级密钥的人**。风险从"代码有 bug"扩大到"代码有 bug ∪ 升级者作恶 ∪ 密钥被盗"。
- **评估可升级协议的四个问题**：谁能升级（多签要看签名者是否真的独立）、有没有时间锁、能改多大范围、**我能不能在升级生效前退出**。**时间锁只有在你能退出时才有意义。**

## 思考题

1. A 调用 B，B 用 delegatecall 调用 C。在 C 的代码里，`msg.sender`、`address(this)` 分别是谁？读写的是谁的存储？
2. 为什么 delegatecall 的 `msg.value` 不能重新指定？如果可以，会带来什么攻击？
3. 完整推演一次存储冲突：给出代理和实现的变量声明，说明哪一次写入会把合约变砖。
4. EIP-1967 为什么要减 1？如果不减，构造一个能撞上它的 mapping 键需要什么条件？
5. 什么是函数选择器冲突？透明代理如何消除它？UUPS 为什么不需要处理这个问题？
6. UUPS 模式下，如果新实现忘了继承升级逻辑会怎样？有办法补救吗？
7. 完整复述 Parity 事件的因果链，指出至少三个本可以阻断它的环节。
8. `_disableInitializers()` 在构造函数里做了什么？为什么它能防住这类攻击？
9. 一个协议说"我们的合约由 5/9 多签控制，且有 48 小时时间锁"。用第六节的四个问题评估它，并指出你还需要问什么。
10. "这个协议经过了顶级机构审计"——在可升级的前提下，这句话到底保证了什么？

