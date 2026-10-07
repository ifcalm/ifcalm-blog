---
title: "LLM 系统原理"
description: "一门系统原理向的 LLM 课程：31 讲课堂笔记，从「猜下一个词」讲到推理模型与 Agent，配 6 个 Python/NumPy 实验、4 套习题与完整解答、复习指南、术语表与参考资料。"
summary: "从零讲起（不假设机器学习背景）：数学与神经网络基础、Transformer 架构、预训练、对齐与微调、推理与部署、检索与 Agent、局限与安全，共 31 讲。6 个纯 Python + NumPy 实验（不依赖任何深度学习框架），4 套 Problem Set（含参考答案）、术语表与参考资料。只讲机制、数学和边界，不讲某个产品的用法。"
layout: "list"
---

这是一门**系统原理向**的 LLM 课程。它回答的问题只有一个：

> **一个大语言模型是怎么被造出来的？每一个设计决策在解决什么问题，代价是什么？**

组织方式延续 [CS 251：区块链系统原理]({{< ref "/posts/blockchain" >}}) 的做法：每一个机制都先给出**它要解决的问题**，再给出**设计**，最后给出**这个设计放弃了什么**。

## 课程信息

| 项目 | 内容 |
|---|---|
| **课程层次** | 不需要机器学习背景——第二单元从零讲起，只假设你会读一点代码 |
| **代码语言** | **纯 Python + NumPy**，不引入 PyTorch/TensorFlow 等深度学习框架。反向传播、注意力机制、mini-Transformer 全部手写实现，逼自己看清楚每一步在算什么 |
| **组织方式** | 每讲固定六节：场景引入 → 直觉类比 → 机制细节 → 代价与局限 → 和其他机制的关系 → 小结与思考题 |

## 这门课不讲什么

**不讲怎么调用某个模型的 API，不讲 prompt 技巧合集，不对比哪个产品更好用。**

这些东西的半衰期以月计，而且到处都是。这门课讲的是**不会过期的那一层**：为什么自注意力是 $O(n^2)$、为什么 RLHF 有效但代价是什么、为什么长上下文是工程难题而不只是"调个参数"。

> ⚠️ **关于时效性**：这个领域变化比区块链更快——具体模型的参数规模、context window 长度、某个 benchmark 的分数，六个月就可能过时。本课的处理方式是**把「设计约束」和「当前取值」分开写**：比如讲上下文长度会讲清楚它的工程瓶颈由什么决定，具体的"多少 token"只作为当前实例出现。模型换了，正文的推理仍然成立。

## 课程结构

课程分为八个单元，共 31 讲。

### Unit 1 · 问题与历史（第 1–2 讲）
在讲任何架构之前，先把问题定义清楚：语言模型到底在解决什么，以及为什么早期方案会遇到瓶颈。

- [第 1 讲：语言模型要解决的问题——从「猜下一个词」到「理解语言」]({{< ref "01-next-token-prediction.md" >}})
- [第 2 讲：为什么不是 RNN/LSTM——序列模型的瓶颈]({{< ref "02-rnn-limits.md" >}})

### Unit 2 · 数学与机器学习基础（第 3–6 讲）
不假设任何机器学习背景，从零讲起：表示、概率、神经网络、反向传播。

- [第 3 讲：向量、矩阵与「表示」是什么]({{< ref "03-vectors-and-representations.md" >}})
- [第 4 讲：概率语言模型——下一个词的分布]({{< ref "04-probabilistic-language-models.md" >}})
- [第 5 讲：神经网络最小实现——一层、非线性为什么必要]({{< ref "05-neural-network-basics.md" >}})
- [第 6 讲：梯度下降与反向传播——模型怎么「学会」]({{< ref "06-gradient-descent-backprop.md" >}})

### Unit 3 · Transformer 架构（第 7–12 讲）
全课最核心的单元：从分词到自注意力，把一个 Transformer 拆到能自己实现的程度。

- [第 7 讲：分词——BPE 为什么不按字/词切]({{< ref "07-tokenization-bpe.md" >}})
- [第 8 讲：词嵌入与位置编码]({{< ref "08-embeddings-positional-encoding.md" >}})
- [第 9 讲：自注意力——Q/K/V 到底在算什么]({{< ref "09-self-attention.md" >}})
- [第 10 讲：多头注意力、前馈层、残差与 LayerNorm]({{< ref "10-multihead-ffn-layernorm.md" >}})
- [第 11 讲：Decoder-only vs Encoder-Decoder]({{< ref "11-decoder-vs-encoder-decoder.md" >}})
- [第 12 讲：MoE——参数量和计算量的解耦]({{< ref "12-mixture-of-experts.md" >}})

### Unit 4 · 预训练（第 13–15 讲）
模型怎么从一堆文本里学出语言能力，以及"更大更好"这条经验规律的真实代价。

- [第 13 讲：预训练目标与自监督学习]({{< ref "13-pretraining-objective.md" >}})
- [第 14 讲：数据——规模、质量、去重、合成数据与多阶段训练]({{< ref "14-pretraining-data.md" >}})
- [第 15 讲：Scaling Laws]({{< ref "15-scaling-laws.md" >}})

### Unit 5 · 对齐与微调（第 16–20 讲）
预训练模型和一个"能对话、听指令"的模型之间还差什么，以及这中间每一步在用什么换什么。

- [第 16 讲：SFT——指令微调]({{< ref "16-supervised-finetuning.md" >}})
- [第 17 讲：RLHF——原理与代价]({{< ref "17-rlhf.md" >}})
- [第 18 讲：DPO 等更新对齐方法]({{< ref "18-dpo.md" >}})
- [第 19 讲：推理模型与 RLVR——测试时计算]({{< ref "19-reasoning-models-rlvr.md" >}})
- [第 20 讲：对齐解决了什么问题、留下什么隐患]({{< ref "20-alignment-tradeoffs.md" >}})

### Unit 6 · 推理与部署（第 21–24 讲）
模型训好之后，怎么把它跑起来、跑得快、跑得便宜。

- [第 21 讲：采样策略——temperature/top-p/top-k]({{< ref "21-sampling-strategies.md" >}})
- [第 22 讲：KV Cache、量化、批处理]({{< ref "22-kv-cache-quantization.md" >}})
- [第 23 讲：上下文长度——工程瓶颈]({{< ref "23-context-length.md" >}})
- [第 24 讲：测试时计算的代价——延迟与成本]({{< ref "24-inference-time-compute-cost.md" >}})

### Unit 7 · 检索、Agent 与系统集成（第 25–28 讲）
单个模型调用之外，怎么把外部知识和工具接进来，让模型完成多步任务。

- [第 25 讲：RAG 原理——模型知道的为什么不够]({{< ref "25-rag-principles.md" >}})
- [第 26 讲：Embedding 与向量检索]({{< ref "26-embeddings-vector-search.md" >}})
- [第 27 讲：Function calling——工具调用机制]({{< ref "27-function-calling.md" >}})
- [第 28 讲：多步推理与规划——ReAct 等范式]({{< ref "28-agent-planning-react.md" >}})

### Unit 8 · 局限与安全（第 29–31 讲）
这个系统在结构上做不到什么，以及它的攻击面在哪。

- [第 29 讲：幻觉的机制性成因]({{< ref "29-hallucination.md" >}})
- [第 30 讲：Prompt injection、越狱]({{< ref "30-prompt-injection-jailbreak.md" >}})
- [第 31 讲：可解释性的现状边界]({{< ref "31-interpretability-limits.md" >}})

## 实验

六个实验，全部用**纯 Python + NumPy**，不依赖任何深度学习框架。

- [实验 1：手写反向传播（标量/小型 MLP）]({{< ref "70-lab1-backprop.md" >}})
- [实验 2：手写 BPE tokenizer]({{< ref "71-lab2-bpe-tokenizer.md" >}})
- [实验 3：手写自注意力机制]({{< ref "72-lab3-self-attention.md" >}})
- [实验 4：mini-Transformer 完整前向传播]({{< ref "73-lab4-mini-transformer.md" >}})
- [实验 5：采样策略 + KV cache 模拟]({{< ref "74-lab5-sampling-kvcache.md" >}})
- [实验 6：mini-RAG（embedding + 余弦检索）]({{< ref "75-lab6-mini-rag.md" >}})

## 习题

每套习题都附**完整解答**，不是"答案略"。

- [习题集 1：数学、神经网络与 Transformer 架构（第 1–12 讲）]({{< ref "80-problem-set-1.md" >}})
- [习题集 2：预训练与对齐（第 13–20 讲）]({{< ref "81-problem-set-2.md" >}})
- [习题集 3：推理与部署（第 21–24 讲）]({{< ref "82-problem-set-3.md" >}})
- [习题集 4：检索、Agent 与安全（第 25–31 讲）]({{< ref "83-problem-set-4.md" >}})

## 参考

- [复习指南]({{< ref "90-exam-guide.md" >}})
- [术语与符号表]({{< ref "95-glossary.md" >}})
- [参考资料与延伸阅读]({{< ref "96-resources.md" >}})
