---
title: "实验 2：UTXO 链"
date: 2026-08-30
weight: 71
tags: ["区块链"]
draft: false
summary: "实现一条完整的 UTXO 链：交易结构与序列化、签名与验签、UTXO 集合维护、双花检测、区块组装与链验证，以及一个栈式脚本解释器。含五个必须能复现的攻击测试。"
showToc: true
tocOpen: false
---

对应[第 9 讲]({{< ref "09-blocks-and-chains.md" >}})与[第 10 讲]({{< ref "10-utxo-model.md" >}})。

**这个实验的目标是让你亲手体会：一条链的"共识规则"其实就是验证函数里的那几个 `if`。漏掉任何一个，就能凭空造币。**

## 任务一：数据结构与序列化

```go
type OutPoint struct {
    TxID  [32]byte
    Index uint32
}

type TxIn struct {
    PrevOut   OutPoint
    ScriptSig []byte
}

type TxOut struct {
    Value        int64      // 单位：聪
    ScriptPubKey []byte
}

type Tx struct {
    Version uint32
    In      []TxIn
    Out     []TxOut
}
```

**实现：**

```go
// Serialize 必须是确定性的：⭐ 同一笔交易永远得到同一串字节。
// 否则同一笔交易在不同节点上会算出不同的 TxID，共识立刻崩溃。
func (tx *Tx) Serialize() []byte

// TxID 使用双重 SHA-256（第 4 讲）。
func (tx *Tx) TxID() [32]byte
```

⚠️ **注意事项：**

```
① 变长字段必须先写长度（否则解析有歧义）
② ⭐ 字节序必须固定（比特币用小端）
③ map 遍历顺序不确定——序列化里绝不能出现 map
```

## 任务二：签名哈希

⭐ **这是最容易写错、也最重要的一步。**

```go
// SigHash 计算待签名的摘要。
// ⚠️ 关键问题：签名本身不能包含在被签名的数据里（循环依赖）。
//    做法是把所有 ScriptSig 清空后再序列化。
func (tx *Tx) SigHash(inputIndex int, prevScriptPubKey []byte) [32]byte
```

**要回答：**

```
① ⭐ 如果 SigHash 漏掉了 Out 里的 Value，攻击者能做什么？
② 如果漏掉了 PrevOut，能做什么？
③ 如果只签当前这一个输入，而不签其他输入，会怎样？
④ 为什么必须把 ScriptSig 清空？如果不清空会发生什么？
```

## 任务三：UTXO 集合与验证

```go
type UTXOSet map[OutPoint]TxOut

// Validate 验证一笔非 coinbase 交易，返回手续费。
func (s UTXOSet) Validate(tx *Tx) (fee int64, err error)
```

⭐ **必须检查的每一条（漏一条就有洞）：**

```
□ 输入和输出都非空
□ ⭐ 每个输入引用的 UTXO 存在于集合中          ← 这就是双花检测
□ 同一笔交易内部没有重复引用同一个 UTXO      ← 单独一条！
□ 解锁脚本验证通过
□ 每个输出的 Value ≥ 0                     ← 漏掉就能凭空造币
□ 每个输出的 Value ≤ 2100 万 BTC 的聪数     ← 防溢出
□ 输入总额 ≥ 输出总额
□ 累加时不溢出（用 int64 并检查上界）
```

## 任务四：脚本解释器

**实现一个支持 P2PKH 的栈式解释器：**

```go
func Eval(scriptSig, scriptPubKey []byte, sigHash []byte) bool
```

需要的操作码：`OP_DUP`、`OP_HASH160`、`OP_EQUALVERIFY`、`OP_CHECKSIG`，以及 `PUSH1..PUSH75`。

⚠️ **必须处理的边界：**

```
① 栈下溢（操作码需要的元素不够）
② PUSH 的长度超出脚本剩余字节
③ ⭐ 脚本长度上限（防 DoS）
④ 执行结束时栈顶为真，且【只有】栈顶被检查
```

**选做：实现 `OP_CHECKMULTISIG`，⭐ 包括那个多余的 `OP_0`（[第 10 讲]({{< ref "10-utxo-model.md" >}})第四节）。**

## 任务五：区块与链

```go
type Block struct {
    Header Header    // 复用第 9 讲的 80 字节结构
    Txs    []*Tx
}

// ValidateBlock 验证一个区块。
func ValidateBlock(b *Block, s UTXOSet, height uint64, prevHeader *Header) error
```

⭐ **区块级别的检查：**

```
□ 第一笔必须是 coinbase（无输入），其余都不是
□ ⭐ coinbase 输出 ≤ 区块奖励 + 本块所有手续费之和   ← 防增发的执行点
□ Merkle 根与交易列表一致（用实验 1 的实现）
□ 交易之间不能双花（B 花了 A 的输出可以，但两笔不能花同一个）
□ PoW 达标
□ 时间戳 > 前 11 块中位数
□ 区块序列化大小 ≤ 上限
```

## 任务六：五个必须能复现的攻击

**为下面每一条写一个测试，先证明"漏掉检查时攻击成功"，再证明"加上检查后失败"：**

```
① 双花
   同一个 UTXO 被两笔交易各花一次

② ⭐ 交易内双花
   一笔交易的两个输入指向同一个 UTXO
   如果你的 Validate 只查"UTXO 是否在集合里"，这一条会通过！

③ 负数输出
   一个输出 −100，另一个 +200
   输入输出总额检查会通过，但你凭空造了 100

④ coinbase 超发
   coinbase 输出比"奖励 + 手续费"多 1 聪

⑤ Merkle 根不匹配
   把区块里的一笔交易换掉，但保留原来的 Merkle 根
```

⭐ **第 ②③ 两条最值得写**——它们都是"看起来已经检查过了"但实际漏掉的情况。

## 任务七（选做）：链重组

```go
// AddBlock 处理新区块，必要时执行重组。
// ⭐ 按累计工作量（不是长度）选择主链（第 16 讲）。
func (c *Chain) AddBlock(b *Block) error
```

⚠️ **重组时必须正确地回滚 UTXO 集合：**

```
撤销一个区块时：
   ① ⭐ 删除它创建的所有 UTXO
   ② 恢复它花掉的所有 UTXO      ← 所以必须保存"撤销数据"
```

⭐ **这一步会让你真正理解为什么全节点要维护 undo 数据，以及为什么深度重组代价高昂。**


## 常见错误

```
① 序列化用了 map ⟹ 顺序不定 ⟹ TxID 不稳定
② SigHash 忘记清空 ScriptSig ⟹ 循环依赖
③ ⭐ 只检查"UTXO 在集合里"，漏掉交易内重复引用
④ 用 int 而非 int64 存金额 ⟹ 32 位平台上溢出
⑤ 手续费用无符号数 ⟹ 输出 > 输入时回绕成巨大正数
```

⭐ **第 ⑤ 条尤其值得注意：它是"用错整数类型"导致共识漏洞的经典形态。**

---

> **相关**：[第 10 讲：UTXO 模型与比特币脚本]({{< ref "10-utxo-model.md" >}})
