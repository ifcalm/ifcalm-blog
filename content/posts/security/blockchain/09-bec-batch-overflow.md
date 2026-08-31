---
title: "第 9 篇：BEC batchOverflow——一个乘法毁掉一个代币"
date: 2026-08-31
weight: 9
tags: ["区块链安全"]
draft: false
summary: "2018 年 4 月，BEC 代币被凭空铸出 2×2²⁵⁵ 枚，交易所紧急下架，价格归零。最讽刺的是：这个合约通篇都在用 SafeMath，唯独出问题的那一行乘法是裸的。这一篇讲「防护措施用得不一致等于没用」，以及 Solidity 0.8 之后仍然会静默溢出的三个地方。"
showToc: true
tocOpen: false
---

| | |
|---|---|
| **时间** | 2018 年 4 月 22 日 |
| **后果** | 凭空铸出 2 × 2²⁵⁵ 枚代币，交易所下架，价格归零 |
| **同期** | SMT（SmartMesh）等多个代币被同类漏洞打穿 |
| **类别** | C3 数值假设失效 |

## 一、背景：一个"省 Gas"的批量转账

BEC（BeautyChain）是 2018 年的一个 ERC-20 代币。它在标准 ERC-20 之外加了一个便利函数：一次性给多个地址转同样金额。

```
batchTransfer([地址1, 地址2, 地址3], 100)
   ⟹ 三个人各收到 100 个代币，发送方扣 300

⭐ 本意是省 Gas —— 一笔交易顶三笔。
```

## 二、漏洞在哪

```solidity
function batchTransfer(address[] _receivers, uint256 _value)
    public whenNotPaused returns (bool)
{
    uint cnt = _receivers.length;

    // ⚠️⚠️ 就是这一行 —— 裸的乘法
    uint256 amount = uint256(cnt) * _value;

    require(cnt > 0 && cnt <= 20);
    require(_value > 0 && balances[msg.sender] >= amount);

    balances[msg.sender] = balances[msg.sender].sub(amount);   // ✅ SafeMath
    for (uint i = 0; i < cnt; i++) {
        balances[_receivers[i]] = balances[_receivers[i]].add(_value);  // ✅ SafeMath
        Transfer(msg.sender, _receivers[i], _value);
    }
    return true;
}
```

⭐ **看清楚这段代码的讽刺之处：**

```
balances[...].sub(amount)   ⟹ 用了 SafeMath ✅
balances[...].add(_value)   ⟹ 用了 SafeMath ✅
uint256(cnt) * _value       ⟹ ⚠️⚠️ 裸的，没有 SafeMath

⟹ 团队【知道】要防溢出，也【引入了】SafeMath 库，
   ⭐ 但漏掉了一行。
```

> ⭐**而漏掉的这一行，恰好是那个用来做检查的中间量。**
>
> 和[第 8 篇]({{< ref "08-bitcoin-value-overflow.md" >}})一模一样：**溢出发生在"用于判断的算式"里，而不是"用于转账的算式"里。**

## 三、攻击复盘

攻击者的输入极其简单：

```
_receivers = [地址A, 地址B]        ⟹ cnt = 2
_value     = 2²⁵⁵
             = 578960446186580977117854925043439539266
               34992332820282019728792003956564819968
```

逐行推演：

```
① amount = 2 × 2²⁵⁵ = 2²⁵⁶
   ⚠️ uint256 的模是 2²⁵⁶
   ⟹ 2²⁵⁶ mod 2²⁵⁶ = ⭐ 0

② require(cnt > 0 && cnt <= 20)
   ⟹ 2 在范围内 ✅

③ require(_value > 0 && balances[msg.sender] >= amount)
   ⟹ _value 是个天文数字，> 0 ✅
   ⟹ balances[攻击者] >= 0   ⭐ 恒真！攻击者余额是 0 也能通过
   ✅ 通过

④ balances[攻击者] = balances[攻击者].sub(0)
   ⟹ ⭐ 一分钱没扣

⑤ 循环：
   balances[A] = 0.add(2²⁵⁵) = 2²⁵⁵
   balances[B] = 0.add(2²⁵⁵) = 2²⁵⁵
   ⟹ ⭐ 两个地址各获得 2²⁵⁵ 枚代币
```

**净效果**：攻击者不需要持有任何代币，一笔交易凭空造出了远超总发行量的代币。

### 后果

```
① 攻击者把代币抛向交易所
② 价格瞬间崩塌
③ 交易所紧急暂停 BEC 交易与提现
④ ⚠️ 代币事实上归零 —— 因为"总量"这个概念已经失去意义

⭐ 注意这里的损失形态和别的案例不同：
   没有一分钱被"从合约里偷走"。
   被摧毁的是【这个代币的价值本身】。
```

⚠️ **同一时期，SMT（SmartMesh）等多个代币被完全相同的模式打穿**——因为这段 `batchTransfer` 代码被大量项目互相复制。

## 四、为什么没被发现

### ① 防护措施用得不一致，等于没用

```
⭐ 安全库的价值来自【覆盖率】，不是【存在性】。

   "我们用了 SafeMath" ——
   ⚠️ 这句话在审计报告里看起来是一条正面结论，
      但它没有回答真正的问题：
      ⭐【是不是【每一处】算术都用了？】

⟹ 99% 的覆盖率和 0% 的覆盖率，
   在攻击者眼里是一样的 ——
   他只需要那 1%。
```

### ② `batchTransfer` 不是标准函数，所以不在审计清单上

```
ERC-20 的审计有成熟的检查清单：
   transfer / approve / transferFrom / 授权竞态 / 返回值……

⚠️ 而 batchTransfer 是【项目自己加的】。
   ⭐ 自定义函数没有现成的清单可对照，
      而它们恰恰是最可能出问题的部分。

⟹ 一条经验：审计时把函数分成
      "标准的" 和 "自己加的" 两堆，
   ⭐ 后者要花更多时间。
```

### ③ `>= amount` 这个检查看起来天经地义

```
require(balances[msg.sender] >= amount)

⭐ 这行代码在任何 code review 里都会被一眼扫过 ——
   "检查余额，没问题"。

⚠️ 没有人会停下来问：
   "如果 amount 本身就是错的呢？"

⟹ 检查的【正确性】依赖于被检查的量的【正确性】。
   这一层依赖关系，几乎从来不被显式审视。
```

## 五、防御

### ① 用 0.8+ 的默认检查（但要知道它不管什么）

```solidity
// ✅ Solidity 0.8.0 起，这行溢出会 revert
uint256 amount = cnt * _value;
```

⚠️ **但下面这三处，0.8 仍然不管：**

```solidity
// ⚠️ ① unchecked 块 —— 为省 Gas 显式关闭检查
unchecked { amount = cnt * _value; }

// ⚠️ ② 内联汇编 —— 完全绕过编译器
assembly { amount := mul(cnt, value) }

// ⚠️⚠️ ③ 显式类型转换 —— 【静默截断，不 revert】
uint128 small = uint128(bigValue);      // 高位直接丢弃
uint32  ts    = uint32(block.timestamp); // 2106 年回绕
int256  s     = int256(hugeUint);        // 可能变成负数
```

⭐ **第 ③ 条是今天最常见的溢出来源**，因为很多人以为"升级到 0.8 就没有溢出问题了"。用 OpenZeppelin 的 `SafeCast`：

```solidity
using SafeCast for uint256;
uint128 small = bigValue.toUint128();   // ⭐ 越界会 revert
```

### ② 结构上消除这个中间量

⭐ **最好的修复不是"给这行加检查"，而是让这个危险的中间量根本不存在：**

```solidity
function batchTransfer(address[] calldata to, uint256 value) external {
    require(to.length > 0 && to.length <= 20, "bad count");
    require(value > 0, "zero value");

    for (uint256 i = 0; i < to.length; i++) {
        // ⭐ 每一笔都走标准 transfer 的完整检查
        _transfer(msg.sender, to[i], value);
    }
}
```

⭐ **好处**：批量函数退化成"循环调用单笔转账"，**不引入任何新的算术**，也就不可能引入新的算术漏洞。**它复用了已经被审计过的路径。**

>⭐ **一条通用的设计原则：批量操作应该是单笔操作的循环，而不是一个"优化过的等价实现"。**
> 每一次"为了省 Gas 而重写的等价逻辑"，都是一次新的漏洞机会。

### ③ 检查前置于计算

```solidity
// ⚠️ 先算后检查 —— 算的时候就可能出事
uint256 amount = cnt * value;
require(balances[msg.sender] >= amount);

// ✅ 先检查输入的合理范围，再计算
require(value <= MAX_REASONABLE_VALUE, "value too large");   // ⭐
require(cnt <= 20, "too many");
uint256 amount = cnt * value;
```

### ④ 不变量测试

```solidity
// ⭐ 用 Foundry 的 invariant 测试，让工具反复随机调用你的函数，
//    每次之后检查这条永远该成立的性质：
function invariant_totalSupplyMatchesSumOfBalances() public {
    assertEq(token.totalSupply(), sumAllBalances());
}
```

⭐ **这条不变量能自动抓住本案**：`batchTransfer` 凭空造币之后，`totalSupply` 和余额总和立刻对不上。**而写这条不变量只需要三行。**

## 六、⭐ 举一反三

### 核心命题一：一致性

> ⭐⭐ **防护措施的价值等于它的覆盖率，不是它的存在性。**

```
同一条规律的其它形态：

   · 大部分函数有 nonReentrant，漏了一个   ⟹ [第 1 篇]({{< ref "01-the-dao.md" >}})的跨函数重入
   · 大部分外部调用检查了返回值，漏了一个
   · 大部分敏感函数有 onlyOwner，漏了一个   ⟹ [第 4 篇]({{< ref "04-parity-multisig-1.md" >}})
   · 大部分地址参数检查了非零，漏了一个     ⟹ [第 7 篇]({{< ref "07-nomad-bridge.md" >}})

⭐ 检查方法：不要问"我们用了 X 吗"，
   要问"有哪几处【没有】用 X？为什么？"
   ⟹ 后者能列出清单，前者只能得到一个"用了"。
```

**工具化**：用 Slither / Semgrep 写一条规则，扫出所有裸算术、所有无修饰符的 external 函数、所有未检查的返回值。**让"漏掉一处"变成机器能发现的事。**

### 核心命题二：自定义函数的风险溢价

```
⭐ 把合约里的函数分成两类：

   ① 标准/已被广泛审计的（OpenZeppelin 的实现、ERC 标准接口）
      ⟹ 风险低，因为有成千上万双眼睛看过

   ② ⚠️ 项目自己加的便利函数、优化函数、"聚合"函数
      ⟹ 风险高，而且【没有现成的检查清单】

⟹ 审计时间应该向 ② 倾斜，
   而实践中往往相反 —— 因为 ① 更容易照着清单打勾。
```

⭐ **一条经验判据**：任何名字里带 `batch` / `multi` / `bulk` / `all` / `optimized` 的函数，都值得单独花时间。

### 核心命题三：检查的正确性依赖被检查量的正确性

```
require(balance >= amount)

⭐ 这行代码保证的是 "balance ≥ amount" 这个【关系】，
   它完全不保证 amount 【本身是对的】。

⟹ 一般化：
   每一个 require，都建立在它所引用的变量的正确性之上。
   ⚠️ 如果那些变量来自计算，你就必须先保证那个计算是对的。

⟹ 追溯每个 require 里的变量，一直追到
   "外部输入" 或 "已被验证的存储" 为止。
   ⭐ 中间的每一步计算，都是这个 require 的一部分。
```

### 一条能抓住整类问题的测试

```
⭐ 给任何一个代币合约写这四条不变量，让 fuzzer 去跑：

   ① totalSupply == Σ balances
   ② 除 mint/burn 外，任何操作后 totalSupply 不变
   ③ 任何操作后，没有账户余额凭空增加
   ④ ⭐ 转账前后，(发送方减少量) == (接收方增加量)

⚠️ 本案违反 ①②③④ 全部四条。
   而这四条加起来不到 20 行代码。
```

## 七、本案小结

- **一行裸乘法**：`uint256 amount = uint256(cnt) * _value;`——`cnt=2`、`_value=2²⁵⁵` 时 `amount` 溢出成 **0**。
- ⭐⭐ **最讽刺的地方：合约通篇在用 SafeMath**（`.sub()`、`.add()` 都用了），**唯独漏了这一行**。团队知道要防溢出、也引入了库，但漏了一处。
- **和[第 8 篇]({{< ref "08-bitcoin-value-overflow.md" >}})结构完全相同**：溢出发生在**用于判断的算式**里，不是用于转账的算式里。相隔八年、换了语言，同一个错误。
- **`balances[msg.sender] >= 0` 恒真**——攻击者余额为 0 也能通过检查，扣款 `.sub(0)` 一分钱没扣，两个地址各得 2²⁵⁵ 枚。
- **损失形态特殊**：没有一分钱被从合约里偷走，**被摧毁的是这个代币的价值本身**。同期 SMT 等多个代币因复制同一段代码被打穿。
-⭐ **防护措施的价值等于覆盖率，不是存在性。** "我们用了 SafeMath"没有回答真正的问题——**99% 覆盖率和 0% 在攻击者眼里一样，他只需要那 1%。** 该问的是"**哪几处没有用？为什么？**"
- ⚠️ **`batchTransfer` 是项目自己加的函数，不在 ERC-20 的标准审计清单上。** 凡是名字带 `batch`/`multi`/`bulk`/`optimized` 的，都值得单独花时间。
-⭐ **最好的修复不是给那行加检查，而是让危险的中间量不存在**：把批量函数写成"循环调用已被审计的单笔 `_transfer`"，不引入任何新算术。
- ⚠️ **Solidity 0.8 之后仍会静默溢出的三处**：`unchecked` 块、内联汇编、**显式类型转换**（`uint128(x)` 越界静默截断，不 revert）。第三条是今天最常见的溢出来源。
- **四条不变量（不到 20 行）能自动抓住本案**：`totalSupply == Σbalances` 在攻击后立刻对不上。

## 思考题

1. 逐行推演 `cnt=2`、`_value=2²⁵⁵` 的执行过程，写出每一步 `amount` 和各账户余额的值。
2. 如果攻击者用 `cnt=4`、`_value=2²⁵⁴`，结果一样吗？还有哪些 `(cnt, value)` 组合能让 `amount` 恰好为 0？
3. 为什么说"溢出发生在用于判断的算式里"比"发生在转账的算式里"更危险？
4. 把 `batchTransfer` 改成"循环调用 `_transfer`"。这个写法多花了多少 Gas？你认为这个代价值得吗？
5. 写一段 Solidity，它在 0.8.20 下编译通过、不 revert，但结果是错的。（提示：类型转换）
6. `uint32(block.timestamp)` 会在哪一年回绕？如果一个协议用它做时间比较，届时会发生什么？
7. 为本篇提到的四条代币不变量写出 Foundry 的 invariant 测试代码。
8. 用 Slither 或 Semgrep 写一条规则，扫出项目里所有"没有被 SafeMath 或 0.8 检查保护的算术"。你会怎么定义这个模式？
9. "每一个 require 都建立在它所引用变量的正确性之上。"请挑一个你写过的 require，把它引用的每个变量追溯到外部输入或已验证的存储。
10. BEC 和 SMT 被同一个模式打穿，因为代码被互相复制。这和[第 2 篇]({{< ref "02-lendfme-erc777.md" >}})的"fork 一份安全代码不等于得到安全代码"是同一个问题吗？请说明异同。
