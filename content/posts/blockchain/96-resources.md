---
title: "参考资料与延伸阅读"
date: 2026-08-30
weight: 96
tags: ["区块链"]
draft: false
summary: "按单元组织的原始论文、规范文档、可读源码与课程资源，并标注每一份的定位与难度，以及本课刻意没有覆盖的四个方向。"
showToc: true
tocOpen: true
---

**原则：优先读规范和源码，其次读原始论文，最后才读二手解读。** 这个领域的二手材料过期极快，而规范和论文不会。

## 一、原始论文

### 分布式共识（第 1–2、18 讲）

| 文献 | 说明 |
|---|---|
| Lamport, Shostak, Pease, *The Byzantine Generals Problem* (1982) | `n ≥ 3f+1` 的来源。论文本身不难，但要耐心读那个不可区分性论证 |
| Fischer, Lynch, Paterson, *Impossibility of Distributed Consensus with One Faulty Process* (1985) | FLP。证明较技术化，第一次读可只看结论与直觉 |
| Castro & Liskov, *Practical Byzantine Fault Tolerance* (1999) | 所有现代 BFT 的祖先。视图切换部分值得细读 |
| Yin et al., *HotStuff: BFT Consensus in the Lens of Blockchain* (2018) | 线性视图切换 + 流水线 |
| Buchman, Kwon, Milosevic, *The latest gossip on BFT consensus* (2018) | Tendermint 的正式描述 |

### 区块链设计（第 9–19 讲）

| 文献 | 说明 |
|---|---|
| Nakamoto, *Bitcoin: A Peer-to-Peer Electronic Cash System* (2008) | **九页，值得逐句读**。第 8 节（SPV）和第 11 节（双花概率）尤其重要 |
| Eyal & Sirer, *Majority is not Enough: Bitcoin Mining is Vulnerable* (2013) | 自私挖矿，`(1−γ)/(3−2γ)` 的来源 |
| Carlsten et al., *On the Instability of Bitcoin Without the Block Reward* (2016) | 费用狙击与纯手续费下的共识不稳定 |
| Buterin & Griffith, *Casper the Friendly Finality Gadget* (2017) | 可问责安全性的正式定义 |
| Buterin et al., *Combining GHOST and Casper* (2020) | Gasper 的完整描述 |

### 密码学（第 4–8、30 讲）

| 文献 | 说明 |
|---|---|
| Boneh & Shoup, *A Graduate Course in Applied Cryptography* | **免费在线**。哈希、签名、承诺、零知识全部覆盖，本课的密码学部分对应它的第 8、13、19 章 |
| Boneh, Lynn, Shacham, *Short Signatures from the Weil Pairing* (2001) | BLS 的原始论文 |
| Goldwasser, Micali, Rackoff, *The Knowledge Complexity of Interactive Proof Systems* (1985) | 零知识的定义（模拟器范式的起点） |
| Thaler, *Proofs, Arguments, and Zero-Knowledge* | **免费在线**。目前最好的通用 ZK 系统教材，比论文友好得多 |

### 扩容与 L2（第 25–29 讲）

| 文献 | 说明 |
|---|---|
| Al-Bassam, Sonnino, Buterin, *Fraud and Data Availability Proofs* (2018) | 数据可用性采样的奠基论文 |
| Buterin, *Endgame* (2021)、*A rollup-centric ethereum roadmap* (2020) | 路线转向的完整论证 |
| Zamyatin et al., *SoK: Communication Across Distributed Ledgers* (2019) | 跨链桥的系统化分类 |

## 二、规范与文档

⭐ **这一节的材料比任何教科书都权威，且随协议同步更新。**

```
以太坊黄皮书（Yellow Paper）
   ⭐ EVM 的形式化定义。符号密集，适合当字典查而不是通读

Ethereum Execution Specs（executable specs）
   用 Python 写的可执行规范 —— 比黄皮书好读得多，
      而且能直接跑。想搞清某个操作码的确切语义，看这个

Consensus Specs（ethereum/consensus-specs）
   信标链的 Python 规范。第 17、19 讲的罚没条件、
      非活跃泄漏、分叉选择，全部能在这里找到精确定义

EIP 索引（eips.ethereum.org）
   本课引用的：EIP-150 / 155 / 1559 / 1967 / 2535 / 2929 /
      2930 / 3529 / 4337 / 4844 / 6780 / 7702

BIP 索引（github.com/bitcoin/bips）
   BIP-9（软分叉信号）、BIP-32/39/44（HD 钱包）、
   BIP-37（布隆过滤器）、BIP-62/146（可延展性）、
   BIP-141（SegWit）、BIP-341（Taproot）
```

## 三、可读的源码

⭐ **读源码是这个领域最有效的学习方式。推荐顺序由易到难：**

```
btcd（Go）
   ⭐ 比特币的 Go 实现，比 Bitcoin Core 的 C++ 好读得多。
   看 blockchain/validate.go 和 txscript/ 两个目录

go-ethereum（Go）
   core/vm/          EVM 解释器，对照实验 4
   trie/             MPT 实现，对照第 12 讲
   core/state_transition.go   状态转移与 Gas 扣除

CometBFT（Go）
   consensus/state.go  Tendermint 的状态机，锁定规则在这里

Optimism / Arbitrum（Go + Solidity）
   欺诈证明的单步解释器（MIPS / WASM）——
   代码不长，且能看到第 26 讲那套二分协议的真实实现
```

⚠️ **一个建议：不要从主循环开始读。** 从"你已经理解的那个概念"对应的函数入手（比如先找 `applyTransaction`），再向外扩展。

## 四、课程

```
Stanford CS 251 — Blockchain Technologies（Dan Boneh）
   ⭐ 本课的主要参照。密码学部分比本课深，共识部分相当

MIT 6.5610 — Applied Cryptography（原 6.857）
   密码学基础更扎实，适合补第二单元

Berkeley CS 294-144 — Blockchain, CryptoEconomics
   经济学与机制设计部分更强，适合补第 16、32 讲
```

## 五、本课刻意没有覆盖的

⭐ **说清楚边界，比假装全覆盖更有用。**

```
① Solidity 语法与工具链
   ⭐ 本课把合约当作【被分析的对象】，不教怎么写。
   理由：语法的半衰期约两年，且资料极多。
   要学的话，直接读 Solidity 官方文档 + Foundry Book。

② ZK 证明系统的代数细节
   本课讲到"它证明的是什么陈述、简洁性从哪来"为止，
      不展开 R1CS / QAP / 多项式承诺的构造。
   想深入：Thaler 的 Proofs, Arguments, and Zero-Knowledge。

③ 具体协议的实现细节
   Uniswap、Aave、Compound 等的具体机制变化很快。
   本课只讲它们暴露出的【结构性问题】（预言机、清算激励、
      舍入方向），这些不会过期。

④ 非 EVM 生态的深入内容
   Solana 的 Sealevel、Move 语言、Cosmos SDK 等只在对比时提及。
   理由：本课的目标是把一个体系讲透，而不是横向罗列。
```

## 六、怎么继续

如果这门课读完了，三个方向各自值得投入：

```
① 深入密码学
   ⟹ Boneh & Shoup 全书 + Thaler
   ⟹ 目标：能读懂一篇新的证明系统论文

② 深入协议工程
   ⟹ 读 execution-specs 和 consensus-specs，
      ⭐ 然后去跟一个 EIP 的讨论过程（ethereum-magicians 论坛）
   ⟹ 目标：能判断一个提案的取舍是否成立

③ 深入安全
   ⟹ 读历史事故的完整分析报告（Rekt News、各家审计报告）
   ⟹ 用第 33 讲的四个问题去检查真实合约
   ⟹ 目标：能在代码里看出【没有被写下来的假设】
```

⭐ **而无论走哪个方向，第 33 讲最后那句话都适用：**

> **每一层"数学保证"，都在某个地方交接给了人的判断。
> ⭐ 工程能力的差别，在于知道保证在哪里停止。**

---

> **相关**：[术语与公式速查]({{< ref "95-glossary.md" >}})　**回到**：[课程目录]({{< ref "/posts/blockchain" >}})
