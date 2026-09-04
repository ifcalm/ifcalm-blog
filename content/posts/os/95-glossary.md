---
title: "术语表：中英文对照"
date: 2026-09-03
weight: 95
tags: ["操作系统"]
draft: false
summary: "操作系统里的中英文对应特别容易翻车：「页」到底是 page 还是 frame、「阻塞」是 blocked 还是 blocking、「中断」和「陷入」中文常常混着用。这一页把这些坑单独标出来，并注明每个词在哪一篇里第一次出现。"
showToc: true
tocOpen: false
---

⭐ **带 ⚠️ 的是最容易混的几组，单独看一下。**

## 一、⚠️ 最容易混的七组

| 中文 | 英文 | ⚠️ 坑在哪 |
|---|---|---|
| 页 / 页帧 | **page** / **frame** | ⚠️ **中文都叫"页"**。page 是**虚拟**地址空间里的一块，frame 是**物理**内存里的一块。"把页装进帧"才是准确的说法。第 12 篇 |
| 阻塞（状态） / 阻塞（调用） | **blocked** / **blocking** | ⚠️ 前者是进程状态（第 2 篇），后者是接口语义（第 22 篇）。"非阻塞 I/O"里的是后者 |
| 中断 / 陷入 / 异常 | **interrupt** / **trap** / **exception** | ⚠️ 中文常统称"中断"。**interrupt 来自外部设备**（异步），**trap 是程序主动触发**（`syscall`），**exception 是程序出错触发**（除零、缺页）。三者走同一条入口，但来源完全不同。第 4 篇 |
| 并发 / 并行 | **concurrency** / **parallelism** | ⚠️ 并发是**结构**（多件事在推进），并行是**执行**（同一时刻真的同时）。单核可以并发，不能并行。第 16 篇 |
| 内部碎片 / 外部碎片 | **internal** / **external fragmentation** | ⚠️ 内部 = **分给你了你没用完**（4 KB 的块存 1 字节）；外部 = **空间总量够但不连续**。第 10、11 篇 |
| 硬链接 / 软链接 | **hard link** / **symbolic link** | ⚠️ 硬链接**不是文件**（只是目录里多一条记录），软链接**是一个文件**（内容是路径字符串）。第 25 篇 |
| 信号 / 信号量 | **signal** / **semaphore** | ⚠️ **中文差一个字，英文毫无关系，用途也毫无关系。** 信号是内核从外面通知一个进程（第 3 篇），信号量是线程之间的同步原语（第 20 篇）。⭐ 一个记法：**信号会丢**（不排队，连发十个只到一个），**信号量不会丢**（`post` 早于 `wait` 也算数）——这恰好是它俩最要紧的差别 |

## 二、进程与调度

| 中文 | 英文 | 出处 |
|---|---|---|
| 进程 | process | 2 |
| 进程控制块 | PCB（process control block） | 2 |
| 上下文切换 | context switch | 4 |
| 受限直接执行 | limited direct execution | 4 |
| 抢占 | preemption | 4 |
| 陷阱表 | trap table | 4 |
| 信号 | signal | 3 |
| 信号处理函数 | signal handler | 3 |
| 异步信号安全 | async-signal-safe | 3 |
| 优雅关闭 | graceful shutdown | 3 |
| 僵尸进程 | zombie | 3 |
| 孤儿进程 | orphan | 3 |
| 写时复制 | copy-on-write（CoW） | 3, 24, 28, 29 |
| 周转时间 | turnaround time | 5 |
| 响应时间 | response time | 5 |
| 护航效应 | convoy effect | 5 |
| 最短作业优先 | SJF（shortest job first） | 5 |
| 时间片轮转 | round robin（RR） | 5 |
| 多级反馈队列 | MLFQ | 6 |
| 饥饿 | starvation | 6 |
| 完全公平调度器 | CFS（completely fair scheduler） | 7 |
| 虚拟运行时间 | vruntime | 7 |
| 缓存亲和性 | cache affinity | 7 |
| 负载均衡 | load balancing | 7 |

## 三、内存

| 中文 | 英文 | 出处 |
|---|---|---|
| 地址空间 | address space | 8 |
| 地址空间布局随机化 | ASLR | 8 |
| 内存管理单元 | MMU | 10 |
| 基址 / 界限 | base / bounds | 10 |
| 分段 | segmentation | 10 |
| 空闲链表 | free list | 11 |
| 切分 / 合并 | splitting / coalescing | 11 |
| 伙伴系统 | buddy allocator | 11 |
| 分页 | paging | 12 |
| 页表 | page table | 12 |
| 页表项 | PTE（page table entry） | 12 |
| 虚拟页号 / 物理帧号 | VPN / PFN | 12 |
| 有效位 / 脏位 / 访问位 | valid / dirty / accessed bit | 12, 15 |
| 缺页 | page fault | 12 |
| 按需分页 | demand paging | 12 |
| 地址转换后备缓冲 | TLB | 13 |
| 工作集 | working set | 13 |
| 大页 | huge page | 13, 14 |
| 多级页表 | multi-level page table | 14 |
| 倒排页表 | inverted page table | 14 |
| 交换区 | swap | 15 |
| 页面置换 | page replacement | 15 |
| 时钟算法 | clock algorithm | 15 |
| 颠簸 | thrashing | 15 |

## 四、并发

| 中文 | 英文 | 出处 |
|---|---|---|
| 线程 | thread | 16 |
| 竞态条件 | race condition | 16 |
| 临界区 | critical section | 16 |
| 互斥 | mutual exclusion | 16 |
| 数据竞争 | data race | 16, 73 |
| 原子的 | atomic | 17 |
| 测试并设置 | test-and-set | 17 |
| 比较并交换 | CAS（compare-and-swap） | 17 |
| 自旋锁 | spinlock | 17 |
| 互斥量 | mutex | 17 |
| 票号锁 | ticket lock | 17 |
| 粗粒度 / 细粒度锁 | coarse-/fine-grained locking | 18 |
| 读写锁 | reader-writer lock | 18 |
| 读者优先 / 写者优先 | reader-/writer-preferring | 18 |
| 饥饿 | starvation | 17, 18 |
| 近似计数器 | approximate / scalable counter | 18 |
| 无锁 | lock-free | 18 |
| 条件变量 | condition variable | 19 |
| 错失唤醒 | lost wakeup | 19 |
| 虚假唤醒 | spurious wakeup | 19 |
| Mesa 语义 | Mesa semantics | 19 |
| 惊群 | thundering herd | 19 |
| 信号量 | semaphore | 20 |
| 死锁 | deadlock | 21 |
| 活锁 | livelock | 21 |
| 循环等待 | circular wait | 21 |
| 优先级反转 / 继承 | priority inversion / inheritance | 21 |
| 检查时到使用时 | TOCTOU | 21, 30 |
| 事件驱动 | event-driven | 22 |
| 协程 | coroutine | 22 |
| 水平触发 / 边缘触发 | level-/edge-triggered | 22 |

## 五、持久化

| 中文 | 英文 | 出处 |
|---|---|---|
| 轮询 | polling | 23 |
| 中断合并 | interrupt coalescing | 23 |
| 直接内存访问 | DMA | 23 |
| 编程式 I/O | PIO | 23 |
| 寻道 / 旋转等待 | seek / rotational latency | 24 |
| 闪存转换层 | FTL | 24 |
| 写放大 | write amplification | 24 |
| 预留空间 | over-provisioning | 24 |
| 索引节点 | inode | 25 |
| 链接数 | link count / nlink | 25 |
| 文件描述符 | file descriptor（fd） | 25 |
| 目录项 | dentry / directory entry | 25, 26 |
| 超级块 | superblock | 26 |
| 位图 | bitmap | 26 |
| 间接块 | indirect block | 26 |
| 区段 | extent | 26 |
| 稀疏文件 | sparse file | 26 |
| 块组 | cylinder group / block group | 26 |
| 崩溃一致性 | crash consistency | 27 |
| 日志 | journaling | 27 |
| 检查点 | checkpoint | 27 |
| 屏障 | barrier | 27 |
| 日志结构文件系统 | LFS | 28 |
| 静默数据损坏 | silent data corruption | 28 |
| 默克尔树 | Merkle tree | 28 |

## 六、隔离

| 中文 | 英文 | 出处 |
|---|---|---|
| 命名空间 | namespace | 29 |
| 控制组 | cgroup | 29 |
| 联合文件系统 | union / overlay filesystem | 29 |
| 二级地址转换 | second-level address translation（EPT / Stage-2） | 29 |
| 能力 | capability | 30 |
| 侧信道 | side channel | 30 |
| 推测执行 | speculative execution | 30 |
| 内核页表隔离 | KPTI | 30 |

## 七、⚠️ 几个中文里说法不统一的

| 概念 | 常见的几种译法 | 建议 |
|---|---|---|
| **thrashing** | 颠簸 / 抖动 / 换页风暴 | 用"颠簸"，但**写文档时最好带上英文** |
| **starvation** | 饥饿 / 饿死 | 都可以 |
| **livelock** | 活锁 / 活死锁 | 用"活锁" |
| **spinlock** | 自旋锁 / 忙等锁 | 用"自旋锁"；"忙等"专指 busy-waiting 这个**行为** |
| **journaling** | 日志 / 日志式 / 记账 | ⚠️ 和 **log**（也译"日志"）容易混。**LFS 的 log 和 ext4 的 journal 不是一回事**——前者是"整个文件系统就是一个日志"，后者是"另开一块区域记意图" |
| **commit** | 提交 / 落实 | 用"提交" |
| **flush** | 刷 / 冲刷 / 落盘 | ⚠️ 注意区分 **flush TLB**（清空）和 **flush to disk**（写下去），中文都叫"刷"，含义相反 |

⭐ 最后一条尤其值得留意：**"刷 TLB"是把内容扔掉，"刷盘"是把内容写下去。** 同一个字，一个是丢弃，一个是保存。
