---
title: "术语与公式速查"
date: 2026-08-30
weight: 95
tags: ["区块链"]
draft: false
summary: "全课定义过的术语、公式和关键数字集中在这一页，每条给出定义、判据和出处。按主题分组，查具体某个词用浏览器页内搜索。"
showToc: true
tocOpen: true
---

⚠️ **这一页只做速查，不做解释。** 每条给定义和出处，**为什么成立要回原讲看**。

## 一、信任模型与共识

| 术语 | 定义 / 判据 | 出处 |
|---|---|---|
| **双花** | 同一笔资金被花费两次。⭐ **本质是排序问题，不是验证问题** | [1]({{< ref "01-double-spending.md" >}}) |
| **女巫攻击** | 单个实体伪造大量身份获取不成比例的影响力 | [1]({{< ref "01-double-spending.md" >}}) |
| **预言机问题** | ⭐ 链能保证数据一致，**不能保证数据为真** | [1]({{< ref "01-double-spending.md" >}}) |
| **安全性（Safety）** | 两个诚实节点永不在同一位置确定不同的值。⭐ **"不会出错"** | [2]({{< ref "02-consensus-limits.md" >}}) |
| **活性（Liveness）** | 被提交的命令最终会被确定。⭐ **"不会卡住"** | [2]({{< ref "02-consensus-limits.md" >}}) |
| **同步 / 异步 / 部分同步** | 消息上界已知 / 无上界 / GST 之后才有上界 | [2]({{< ref "02-consensus-limits.md" >}}) |
| **拜占庭故障** | ⚠️ 任意行为：撒谎、发矛盾消息、串通、选择性沉默 | [2]({{< ref "02-consensus-limits.md" >}}) |
| `n ≥ 3f + 1` | ⭐ 等待时只能等 `n−f` 个，其中最多 `f` 个说谎 ⟹ `n−2f > f` | [2]({{< ref "02-consensus-limits.md" >}})、[18]({{< ref "18-bft-consensus.md" >}}) |
| **FLP 不可能性** | ⭐ 异步 + 确定性 + 一个崩溃故障 ⟹ 无解 | [2]({{< ref "02-consensus-limits.md" >}}) |
| **法定人数交集** | `\|A∩B\| ≥ 2q − n`，⭐ 必含至少一个诚实节点 | [18]({{< ref "18-bft-consensus.md" >}}) |
| **不可能三角** | ⚠️ **不是定理**。真正约束是 `T ≤ R / c` | [3]({{< ref "03-trilemma.md" >}}) |

## 二、密码学原语

| 术语 | 定义 / 公式 | 出处 |
|---|---|---|
| **抗原像 / 抗第二原像 / 抗碰撞** | 三种不同强度。⭐ 抗碰撞 ⟹ 抗第二原像，但 **⟹̸ 抗原像** | [4]({{< ref "04-hash-functions.md" >}}) |
| **生日界** | ⭐ n 位输出只有 `2^(n/2)` 的碰撞安全性 | [4]({{< ref "04-hash-functions.md" >}}) |
| **长度扩展攻击** | Merkle–Damgård 的输出就是内部状态 ⟹ 可续写 | [4]({{< ref "04-hash-functions.md" >}}) |
| **`SHA-256d`** | 比特币用的双重 SHA-256 | [4]({{< ref "04-hash-functions.md" >}}) |
| ⚠️ **Keccak-256 ≠ SHA3-256** | 填充规则不同。Go 里用 `sha3.NewLegacyKeccak256()` | [4]({{< ref "04-hash-functions.md" >}}) |
| **域分隔** | `leaf = H(0x00‖x)`，`node = H(0x01‖左‖右)` | [5]({{< ref "05-merkle-trees.md" >}}) |
| **Merkle 证明大小** | `log₂ n` 个哈希。⭐ 一百万笔 → 640 字节 | [5]({{< ref "05-merkle-trees.md" >}}) |
| **CVE-2012-2459** | ⚠️ 奇数节点复制最后一个 ⟹ 根不唯一 ⟹ 永久 DoS | [5]({{< ref "05-merkle-trees.md" >}}) |
| **ECDLP** | 已知 `P` 和 `kP` 求 `k`。最好攻击 `√n` ⟹ 256 位给 128 位安全 | [6]({{< ref "06-elliptic-curves.md" >}}) |
| **secp256k1** | `y² = x³ + 7`，`p = 2²⁵⁶ − 2³² − 977` | [6]({{< ref "06-elliptic-curves.md" >}}) |
| **压缩公钥** | 33 字节：`0x02/0x03 ‖ x`，前缀记 y 的奇偶 | [6]({{< ref "06-elliptic-curves.md" >}}) |
| **以太坊地址** | `keccak256(未压缩公钥去 0x04 前缀)[12:]` | [6]({{< ref "06-elliptic-curves.md" >}}) |
| **ECDSA 签名** | `s = k⁻¹(z + r·d)`，验证 `R' = z s⁻¹ G + r s⁻¹ Q` | [7]({{< ref "07-digital-signatures.md" >}}) |
| ⚠️ **k 重用解私钥** | `k = (z₁−z₂)/(s₁−s₂)`，`d = (s₁k − z₁)/r` | [7]({{< ref "07-digital-signatures.md" >}}) |
| **RFC 6979** | 确定性 nonce `k = HMAC(d, z)` | [7]({{< ref "07-digital-signatures.md" >}}) |
| **可延展性** | `(r,s)` 有效 ⟹ `(r, n−s)` 也有效。修复：low-s / SegWit | [7]({{< ref "07-digital-signatures.md" >}}) |
| **Schnorr** | `s = k + e·d`。⭐ **线性 ⟹ 可聚合** | [7]({{< ref "07-digital-signatures.md" >}}) |
| **双线性配对** | `e(aP, bQ) = e(P,Q)^(ab)` | [8]({{< ref "08-bls-commitments-vrf.md" >}}) |
| **BLS 签名** | `σ = d·H(m)`，验证 `e(σ,G) == e(H(m),Q)`。⭐ **非交互聚合** | [8]({{< ref "08-bls-commitments-vrf.md" >}}) |
| **Pedersen 承诺** | `C = x·G + r·H`。⭐ **加法同态** | [8]({{< ref "08-bls-commitments-vrf.md" >}}) |
| **VRF** | ⭐ 唯一性 + 伪随机 + 可验证。持有者**没有选择空间** | [8]({{< ref "08-bls-commitments-vrf.md" >}}) |
| **VDF** | 必须串行算 T 步，可快速验证。⭐ 消灭操纵者的信息优势 | [8]({{< ref "08-bls-commitments-vrf.md" >}}) |

## 三、账本与状态

| 术语 | 定义 / 公式 | 出处 |
|---|---|---|
| **区块头（比特币）** | 80 字节：version/prev/merkle/time/bits/nonce | [9]({{< ref "09-blocks-and-chains.md" >}}) |
| **全链区块头** | ⭐ 96 万 × 80 B ≈ **77 MB**，手机可存 | [9]({{< ref "09-blocks-and-chains.md" >}}) |
| **三个根** | 交易根（发生了什么）/ 状态根（现在什么样）/ 收据根（产生了什么） | [9]({{< ref "09-blocks-and-chains.md" >}}) |
| **时间戳规则** | > 前 11 块中位数，< 网络时间 +2 小时。⚠️ **可倒序** | [9]({{< ref "09-blocks-and-chains.md" >}}) |
| **软 / 硬分叉** | ⭐ 判据是"老节点认不认新块"，不是改动大小 | [9]({{< ref "09-blocks-and-chains.md" >}}) |
| **UTXO** | 未花费交易输出。⭐ **余额是算出来的，不是存着的** | [10]({{< ref "10-utxo-model.md" >}}) |
| **手续费（UTXO）** | ⭐ **隐式**：输入总额 − 输出总额 | [10]({{< ref "10-utxo-model.md" >}}) |
| **P2PKH** | `OP_DUP OP_HASH160 <hash> OP_EQUALVERIFY OP_CHECKSIG` | [10]({{< ref "10-utxo-model.md" >}}) |
| **P2SH** | ⭐ 锁定时只放脚本哈希，花费时才提供脚本 | [10]({{< ref "10-utxo-model.md" >}}) |
| **nonce（账户）** | ⭐ 三重职责：防重放、定序、派生 CREATE 地址 | [11]({{< ref "11-account-model.md" >}}) |
| **CREATE** | `keccak(rlp([sender, nonce]))[12:]` | [11]({{< ref "11-account-model.md" >}}) |
| **CREATE2** | `keccak(0xff‖sender‖salt‖keccak(initcode))[12:]`。⭐ 地址可预测 | [11]({{< ref "11-account-model.md" >}}) |
| **EIP-155** | chainID 进签名哈希 ⟹ 防跨链重放 | [7]({{< ref "07-digital-signatures.md" >}})、[11]({{< ref "11-account-model.md" >}}) |
| **MPT 三种节点** | 叶子 / 扩展 / 17 项分支 | [12]({{< ref "12-merkle-patricia-trie.md" >}}) |
| **HP 编码** | 前缀 nibble：最低位记奇偶，次低位记是否叶子 | [12]({{< ref "12-merkle-patricia-trie.md" >}}) |
| ⭐ **secure trie** | 键先哈希 ⟹ 防深度 DoS，⚠️ 代价是丧失局部性 | [12]({{< ref "12-merkle-patricia-trie.md" >}}) |
| **SPV** | ⚠️ 只验区块头，**完全不验证区块内容** | [13]({{< ref "13-light-clients.md" >}}) |
| **无状态客户端** | ⭐ 区块自带见证，验证者不保存状态 | [13]({{< ref "13-light-clients.md" >}}) |
| **Verkle 树** | 向量承诺 ⟹ **不需要兄弟节点**，见证 MB → 百 KB。⚠️ 不抗量子 | [13]({{< ref "13-light-clients.md" >}}) |
| **弱主观性** | ⭐ PoS 新节点必须从外部获得近期可信检查点 | [13]({{< ref "13-light-clients.md" >}})、[17]({{< ref "17-proof-of-stake.md" >}}) |

## 四、共识机制

| 术语 | 定义 / 公式 | 出处 |
|---|---|---|
| **PoW 谜题** | `H(header ‖ nonce) < target`。⭐ 三性质：难解易验、**无记忆**、可调 | [14]({{< ref "14-proof-of-work.md" >}}) |
| **出块间隔分布** | ⭐ 指数分布。`P(T>600s)=36.8%`，`P(T>3600s)=0.25%` | [14]({{< ref "14-proof-of-work.md" >}}) |
| **难度调整** | 每 2016 块，`新目标 = 旧目标 × 实际/20160分钟`，⚠️ 限幅 [1/4, 4] | [14]({{< ref "14-proof-of-work.md" >}}) |
| **算力估算** | `算力 ≈ D × 2³² / 600`。⚠️ **是估算不是测量** | [14]({{< ref "14-proof-of-work.md" >}}) |
| **分叉选择** | ⚠️ **累计工作量最大**，不是"最长" | [15]({{< ref "15-longest-chain-forks.md" >}}) |
| **孤块率** | ⭐ `≈ 传播时间 / 出块间隔` | [15]({{< ref "15-longest-chain-forks.md" >}}) |
| **双花概率** | 白皮书第 11 节。⭐ q=10% 时 z=6 → 0.024%；**q=25% 时 z=6 → 5%** | [15]({{< ref "15-longest-chain-forks.md" >}}) |
| **自私挖矿阈值** | ⭐ `α > (1−γ)/(3−2γ)`。γ=0.5 时只需 **25%** | [15]({{< ref "15-longest-chain-forks.md" >}}) |
| **安全预算** | ⭐ **= 矿工总收入 = 区块奖励 + 手续费** | [16]({{< ref "16-pow-economics.md" >}}) |
| **总量 2100 万** | `210000 × 50 × 2`。⚠️ 实际略少（整数截断） | [16]({{< ref "16-pow-economics.md" >}}) |
| **费用狙击** | ⭐ 纯手续费下重挖上一块比挖新块更赚 ⟹ **破坏"延长链最优"** | [16]({{< ref "16-pow-economics.md" >}})、[32]({{< ref "32-mev.md" >}}) |
| **罚没（slashing）** | ⭐ PoS 独有：资源在链内 ⟹ 协议可没收本金 | [17]({{< ref "17-proof-of-stake.md" >}}) |
| **无利害关系** | ⚠️ PoS 两边都签几乎零成本 ⟹ 分叉不收敛。罚没解决它 | [17]({{< ref "17-proof-of-stake.md" >}}) |
| **长程攻击** | ⚠️ 用旧验证者私钥重造历史链。⭐ 靠检查点 + 提款延迟防 | [17]({{< ref "17-proof-of-stake.md" >}}) |
| **罚没条件** | ⭐ 只有两条：双重提议、双重/环绕投票。**离线不罚没** | [17]({{< ref "17-proof-of-stake.md" >}}) |
| **相关性惩罚** | ⭐ 与同期被罚总量成比例 ⟹ **鼓励客户端多样性** | [17]({{< ref "17-proof-of-stake.md" >}}) |
| **非活跃泄漏** | 稀释不活跃方直到活跃方占 2/3。⚠️ 代价是可能永久分裂 | [17]({{< ref "17-proof-of-stake.md" >}}) |
| **PBFT 三阶段** | ⭐ PREPARE 保证同视图唯一，COMMIT 保证跨视图安全 | [18]({{< ref "18-bft-consensus.md" >}}) |
| **Tendermint 锁定** | PRECOMMIT 后锁定，⭐ 只有更高轮的 polka 才解锁 | [18]({{< ref "18-bft-consensus.md" >}}) |
| **HotStuff** | ⭐ 门限签名 O(n) + 多一阶段让视图切换 O(n³)→O(n) | [18]({{< ref "18-bft-consensus.md" >}}) |
| **Gasper** | ⭐ LMD-GHOST（分叉选择）+ Casper FFG（最终性） | [19]({{< ref "19-ethereum-consensus.md" >}}) |
| **slot / epoch** | 12 秒 / 32 slots = 6.4 分钟 | [19]({{< ref "19-ethereum-consensus.md" >}}) |
| **证成 / 最终确定** | >2/3 链接 ⟹ justified；连续两个 justified ⟹ 前一个 finalized | [19]({{< ref "19-ethereum-consensus.md" >}}) |
| ⭐ **可问责安全性** | 两个冲突检查点都确定 ⟹ **至少 1/3 质押可罚没** | [19]({{< ref "19-ethereum-consensus.md" >}}) |

## 五、执行环境

| 术语 | 定义 / 数值 | 出处 |
|---|---|---|
| **准图灵完备** | ⭐ 用 Gas 而非"禁止循环"来保证终止 | [20]({{< ref "20-evm-architecture.md" >}}) |
| **六个数据区域** | 栈 / 内存 / 存储 / calldata / code / returndata | [20]({{< ref "20-evm-architecture.md" >}}) |
| **内存收费** | ⭐ `3a + a²/512`（二次方，防 DoS） | [20]({{< ref "20-evm-architecture.md" >}}) |
| **256 位字长** | 为匹配 keccak 和金额。⚠️ **对 ZK 电路极不友好** | [20]({{< ref "20-evm-architecture.md" >}}) |
| **JUMPDEST 规则** | ⭐ 防跳进 PUSH 立即数 + 让静态分析可行 | [20]({{< ref "20-evm-architecture.md" >}}) |
| **63/64 规则** | 子调用最多拿剩余 Gas 的 63/64。⭐ 堵死深度攻击 | [20]({{< ref "20-evm-architecture.md" >}}) |
| **预编译 0x08** | 双线性配对。⭐ **决定链上验证 ZK 是否可行** | [20]({{< ref "20-evm-architecture.md" >}}) |
| **上海攻击** | ⚠️ EXTCODESIZE 定价过低 ⟹ 每 20 Gas 换一次随机 I/O | [20]({{< ref "20-evm-architecture.md" >}}) |
| **Gas 三职责** | 保证终止 / 为资源定价 / ⭐ **分配稀缺区块空间** | [21]({{< ref "21-gas.md" >}}) |
| **EIP-1559** | `baseFee`（⭐ **销毁**）+ `priorityFee`（给验证者） | [21]({{< ref "21-gas.md" >}}) |
| **基础费调整** | 目标 = 上限一半，⭐ 每块 **±12.5%**，10 个满块涨 3 倍 | [21]({{< ref "21-gas.md" >}}) |
| **冷 / 热访问** | SLOAD 冷 2100 / 热 100；账户冷 2600 / 热 100 | [21]({{< ref "21-gas.md" >}}) |
| **EIP-3529** | 退款上限 `gasUsed/5`，清槽退款 4800，取消 SELFDESTRUCT 退款 | [21]({{< ref "21-gas.md" >}}) |
| **SSTORE 四档** | 零→非零 20000；非零→非零 2900；非零→零 2900+退款；重复写 100 | [22]({{< ref "22-storage-layout.md" >}}) |
| **mapping 槽** | ⭐ `keccak256(pad32(key) ‖ pad32(slot))` | [22]({{< ref "22-storage-layout.md" >}}) |
| **嵌套 mapping 槽** | `keccak256(pad32(k₂) ‖ keccak256(pad32(k₁) ‖ pad32(slot)))` | [22]({{< ref "22-storage-layout.md" >}}) |
| **动态数组** | 槽存长度，元素从 `keccak256(slot)` 开始 | [22]({{< ref "22-storage-layout.md" >}}) |
| ⚠️ **private 不私密** | `eth_getStorageAt` 可直接读 | [22]({{< ref "22-storage-layout.md" >}}) |
| **delegatecall** | ⭐ **借用代码，操作自己的数据**。msg.sender 保持不变 | [23]({{< ref "23-call-semantics.md" >}}) |
| **EIP-1967 槽** | `keccak256("eip1967.proxy.implementation") − 1`。⭐ 减 1 防哈希原像撞击 | [23]({{< ref "23-call-semantics.md" >}}) |
| **Parity 冻结** | ⚠️ 库未初始化 → 被设 owner → selfdestruct → **51.4 万 ETH 永久冻结** | [23]({{< ref "23-call-semantics.md" >}}) |
| **EIP-4337** | UserOp → Bundler → EntryPoint → 钱包合约。⭐ 不改共识层 | [24]({{< ref "24-tx-lifecycle-aa.md" >}}) |
| **EIP-7702** | ⭐ 让存量 EOA 临时"贴上"合约代码 | [24]({{< ref "24-tx-lifecycle-aa.md" >}}) |
| **Block-STM** | 乐观并行 + 多版本内存 + ⭐ **按原始顺序验证** | [24]({{< ref "24-tx-lifecycle-aa.md" >}}) |

## 六、扩容

| 术语 | 定义 / 数值 | 出处 |
|---|---|---|
| **扩容三维度** | ⭐ 执行（Rollup）/ 数据（DAS）/ 状态（无状态 + Verkle） | [25]({{< ref "25-scaling-constraints.md" >}}) |
| ⭐ **L2 严格定义** | 运营者完全不合作时，**仅凭 L1 数据能单方面取回资产** | [25]({{< ref "25-scaling-constraints.md" >}}) |
| **Validium** | 数据在链下 + ZK 证明。⚠️ **正确但可能取不出来** | [25]({{< ref "25-scaling-constraints.md" >}})、[28]({{< ref "28-data-availability.md" >}}) |
| **1-of-N 诚实假设** | ⭐ 只需一个诚实的人在盯着，且他能把证明送上 L1 | [26]({{< ref "26-optimistic-rollup.md" >}}) |
| **交互式二分** | ⭐ log₂ 轮定位到**单条指令**，L1 只执行一步 | [26]({{< ref "26-optimistic-rollup.md" >}}) |
| **挑战期 7 天** | ⚠️ **不是技术需求，是安全边际**（抗审查冗余） | [26]({{< ref "26-optimistic-rollup.md" >}}) |
| **强制包含** | ⭐ 绕过排序器直接向 L1 提交 —— **单方面退出的技术保障** | [26]({{< ref "26-optimistic-rollup.md" >}}) |
| **完备 / 可靠 / 简洁 / 零知识** | ⭐ Rollup 真正需要的是**可靠性 + 简洁性** | [27]({{< ref "27-zk-rollup.md" >}})、[30]({{< ref "30-zero-knowledge.md" >}}) |
| **SNARK vs STARK** | 证明小/验证便宜 ⚠️ 需可信设置、不抗量子 ‖ 无需设置、⭐ 抗量子、证明大 | [27]({{< ref "27-zk-rollup.md" >}}) |
| **可信设置** | ⭐ MPC 仪式的 1-of-N；以太坊 KZG 仪式 **14 万+ 参与者** | [27]({{< ref "27-zk-rollup.md" >}}) |
| **zkEVM 五类型** | Type 1 完全等价（最慢）… Type 4 高级语言等价（最快，⚠️ 字节码不兼容） | [27]({{< ref "27-zk-rollup.md" >}}) |
| ⚠️ **电路 bug** | ⭐ 证明保证"电路被正确执行"，**不保证"电路写对了"** | [27]({{< ref "27-zk-rollup.md" >}}) |
| **数据可用性** | ⭐ 讲的是**发布**，不是存储。⚠️ **无法归责（渔夫困境）** | [28]({{< ref "28-data-availability.md" >}}) |
| **纠删码 + 采样** | ⭐ n→2n ⟹ 必须藏一半以上 ⟹ 失败概率 `(1/2)ᵏ`。**30 次 ≈ 10⁻⁹** | [28]({{< ref "28-data-availability.md" >}}) |
| **EIP-4844 blob** | 128 KiB/个，目标 3 上限 6，⭐ **独立费用市场**，约 18 天后删除 | [28]({{< ref "28-data-availability.md" >}}) |
| **桥的三类信任** | 原生验证（⭐ 无额外信任）/ 外部验证（⚠️ 等于那组人）/ 乐观验证 | [29]({{< ref "29-bridges.md" >}}) |
| **多链但非跨链** | ⭐ 桥让破坏面扩大到**所有相连的链** | [29]({{< ref "29-bridges.md" >}}) |

## 七、隐私与安全

| 术语 | 定义 / 判据 | 出处 |
|---|---|---|
| **Sigma 协议** | ⭐ 承诺 → 挑战 → 响应 | [30]({{< ref "30-zero-knowledge.md" >}}) |
| **知识提取器** | ⭐ 定义了"知道"：同一承诺答两个挑战 ⟹ `x = (s₁−s₂)/(e₁−e₂)` | [30]({{< ref "30-zero-knowledge.md" >}}) |
| **模拟器** | ⭐ 定义了"零知识"：先选 e、s 再倒推 R | [30]({{< ref "30-zero-knowledge.md" >}}) |
| **Fiat-Shamir** | `e = H(R‖P‖msg)`。⭐ **签名 = 非交互零知识证明** | [30]({{< ref "30-zero-knowledge.md" >}}) |
| ⚠️ **弱 Fiat-Shamir** | 哈希漏掉公开输入 ⟹ 可伪造（Frozen Heart 类） | [30]({{< ref "30-zero-knowledge.md" >}}) |
| **Schwartz–Zippel** | ⭐ `Pr ≤ d/\|F\|`。**简洁性的全部来源**：d≈10⁶、\|F\|≈2²⁵⁴ ⟹ 10⁻⁷⁰ | [30]({{< ref "30-zero-knowledge.md" >}}) |
| **回溯性** | ⚠️ 伪匿名地址被关联一次 ⟹ **全部历史与未来暴露** | [31]({{< ref "31-privacy.md" >}}) |
| **共同输入所有权** | 链分析最有效的聚簇启发式 | [31]({{< ref "31-privacy.md" >}}) |
| **nullifier** | ⭐ 让防双花与不可关联**同时成立** | [31]({{< ref "31-privacy.md" >}}) |
| ⭐ **匿名集** | 隐私的**唯一度量**。⟹ 隐私是公共品，有网络效应 | [31]({{< ref "31-privacy.md" >}}) |
| **关联集证明** | ⭐ 证明"我的存款不来自黑名单"而不暴露是哪一笔 | [31]({{< ref "31-privacy.md" >}}) |
| **MEV** | 通过包含/排除/重排交易可提取的价值。⭐ **只能重新分配，不能消除** | [32]({{< ref "32-mev.md" >}}) |
| **三明治** | ⭐ **利润与滑点容忍度几乎成正比** | [32]({{< ref "32-mev.md" >}}) |
| **PBS** | ⭐ 动机是**防中心化**，不是公平 | [32]({{< ref "32-mev.md" >}}) |
| **重组激励** | ⭐ 单块 MEV ≫ 区块奖励 ⟹ **"延长链最优"被打破** | [32]({{< ref "32-mev.md" >}}) |
| **CEI** | 检查 → 生效 → 交互。⭐ 防重入的正确顺序 | [33]({{< ref "33-contract-vulnerabilities.md" >}}) |
| **只读重入** | ⚠️ `view` 保证不改状态，**不保证读到的状态一致** | [33]({{< ref "33-contract-vulnerabilities.md" >}}) |
| **舍入原则** | ⭐ **永远向对协议有利的方向舍入** | [33]({{< ref "33-contract-vulnerabilities.md" >}}) |
| **闪电贷** | ⭐ 不是漏洞——它**移除了"攻击者需要有很多钱"这个隐含防御** | [33]({{< ref "33-contract-vulnerabilities.md" >}}) |
| ⭐ **形式化验证的边界** | 保证"实现符合规范"，⚠️ **不保证"规范正确"** | [33]({{< ref "33-contract-vulnerabilities.md" >}}) |

## 八、关键数字速查

```
比特币
   区块头 80 字节；全链区块头 ≈ 77 MB
   区块 1 MB / 10 分钟 ⟹ 约 6.7 tps
   难度调整周期 2016 块（14 天），限幅 [1/4, 4]
   当前区块奖励 3.125 BTC ⟹ 每天安全预算 450 BTC
   P(间隔>10分钟)=36.8%  P(间隔>1小时)=0.25%

以太坊
   slot 12 秒，epoch 6.4 分钟，最终性 ≈ 12.8 分钟
   区块 Gas 上限 3000 万，目标 1500 万
   验证者门槛 32 ETH
   SLOAD 冷 2100 / 热 100；SSTORE 新增 20000
   blob 128 KiB，目标 3 / 上限 6，保留约 18 天

密码学
   SHA-256 → 128 位碰撞安全
   secp256k1 → 128 位安全
   MPT 深度 ≈ 7–8；Verkle 深度 ≈ 4
   DA 采样 30 次 → 失败率 ≈ 10⁻⁹
```

---

> **相关**：[参考资料]({{< ref "96-resources.md" >}})　**回到**：[课程目录]({{< ref "/posts/blockchain" >}})
