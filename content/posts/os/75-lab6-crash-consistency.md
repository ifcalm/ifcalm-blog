---
title: "实验六：崩溃一致性——模拟断电，验证日志"
date: 2026-09-03
weight: 75
tags: ["操作系统"]
draft: false
summary: "给实验五那个文件系统加一层可以随时「断电」的块设备：写到第 N 次就直接扔掉后面所有的写。然后穷举所有的断点，看每一次崩溃之后文件系统还对不对。你会发现没日志的版本有大量崩点会留下损坏，加了日志之后应该一个都没有。验收不是「试了几次没事」，是穷举。"
showToc: true
tocOpen: false
---

| | |
|---|---|
| **配套** | [第 27 篇：崩溃一致性]({{< ref "27-crash-consistency.md" >}})、[第 28 篇：现代文件系统]({{< ref "28-modern-filesystems.md" >}}) |
| **前置** | ⭐ **必须先做完[实验五]({{< ref "74-lab5-filesystem.md" >}})** |
| **验收** | ⭐ **穷举所有崩溃点。不是抽样，是穷举。** |

## 这个实验的核心工具

真的断电没法在实验里反复做。但我们可以做一件**更强**的事：**穷举所有可能的断电时刻。**

做法是在你的文件系统和镜像文件之间插一层：

```python
class CrashDisk:
    """一个可以在第 N 次写之后「断电」的块设备"""
    def __init__(self, path, crash_after=None, reorder=False):
        self.f = open(path, "r+b")
        self.n = 0
        self.crash_after = crash_after
        self.reorder = reorder
        self.pending = []                  # 还没落盘的写（模拟页缓存）
        self.dead = False

    def write_block(self, blkno, data):
        if self.dead:
            return                          # 断电之后所有写都消失
        self.n += 1
        self.pending.append((blkno, data))
        if self.crash_after is not None and self.n >= self.crash_after:
            self.dead = True
            self._settle()                  # 断电瞬间，把已提交的落下去
            return
        if len(self.pending) > 8:
            self._settle()

    def flush(self):                        # 对应 fsync：强制落盘
        if not self.dead:
            self._settle()

    def _settle(self):
        order = self.pending
        if self.reorder:
            import random; order = order[:]; random.shuffle(order)   # ★ 磁盘可以重排
        for blkno, data in order:
            self.f.seek(blkno * 4096); self.f.write(data)
        self.f.flush(); os.fsync(self.f.fileno())
        self.pending = []
```

⚠️ 注意 `reorder` 那个开关。第 27 篇讲过：**没有 barrier 的话，磁盘可以重排写入顺序。** 打开它，你的日志实现要是漏了 `flush`，立刻就会暴露。

## 任务

### 任务一：不加日志，穷举崩溃点

把实验五的文件系统接到 `CrashDisk` 上，做一个操作，比如：

```python
def workload(fs):
    ino = fs.create(1, "new.txt")
    fs.write(ino, 0, b"A" * 8192)          # 两个数据块
```

先跑一遍，记下这个操作总共产生了多少次 `write_block`，设为 `N`。

然后**对每一个 `k ∈ [1, N]`**：

```python
for k in range(1, N + 1):
    shutil.copy("clean.img", "test.img")   # 从干净的镜像开始
    disk = CrashDisk("test.img", crash_after=k)
    try:
        workload(FS(disk))
    except CrashedException:
        pass
    problems = check("test.img")           # 你的 fsck
    print(f"崩在第 {k} 次写之后：{problems or '一致'}")
```

`check()` 至少要查这些（第 27 篇第二节那张表）：

- 有没有 inode 指向一个**在位图里标着空闲**的块？（⚠️ 灾难：会被重复分配）
- 有没有块在位图里标着已用，**但没有任何 inode 指向它**？（块泄漏，不致命）
- 目录项指向的 inode 是不是**真的存在且链接数 > 0**？
- inode 的链接数，和实际有多少目录项指向它，对得上吗？

**验收：** ⭐ **你必须能列出一张表，说明每个崩溃点分别产生了哪一类不一致，以及它落在第 27 篇那张表的哪一行。** 而且**必然会有若干个 `k` 产生"灾难"级的不一致**——找不到的话，检查你的 `check()` 写全了没有。

### 任务二：加日志

按第 27 篇第三节的五步实现：

```
1. 把要改的块写进日志区（TxBegin + 各块内容）
2. ★ flush()
3. 写 TxEnd
4. ★ flush()
5. 再去改真正的位置（checkpoint）
```

然后实现 `recover()`：挂载时扫日志区，**有 TxBegin 也有 TxEnd 的重做，只有 TxBegin 的丢弃**。

**验收：** ⭐ **重新跑任务一那个穷举，每一个 `k` 在 `recover()` 之后都必须是一致的。有一个不是就算没通过。**

### 任务三：证明那两个 flush 是必需的

**把第 2 步的 `flush()` 注释掉，打开 `reorder=True`，再穷举一遍。**

⭐ **你应该看到损坏重新出现**，而且是最恶劣的那种：**一条被标成"已提交"、内容却是垃圾的日志，恢复时照着它把好数据也改坏了。**

⚠️ 这正是第 27 篇那句话的实证：**一条不完整但被标成完整的日志，比没有日志更危险。**

**把这个实验的输出留下来**——它是这个实验里最有价值的一条证据。

### 任务四：三种模式

实现第 27 篇那张表里的三档，各自穷举一遍：

| 模式 | 日志里写什么 | 你应该观察到 |
|---|---|---|
| `journal` | 元数据 + 数据 | 全部一致，**写入次数最多** |
| `ordered` | 只有元数据，但**保证数据块先落盘** | 全部一致，写入次数少约一半 |
| `writeback` | 只有元数据，不管顺序 | 元数据一致，⚠️ **但会出现"文件里有旧垃圾"** |

⭐ **`writeback` 那一档的验证方式**：先写一个填满 `'B'` 的文件再删掉（让那些块进空闲池），然后创建新文件写 `'A'`，在中间崩溃。**恢复后如果读到 `'B'`，你就复现了那个数据泄露。**

**这一档是这个实验的高潮：文件系统结构完全自洽，`fsck` 一个问题都查不出来，而文件内容是别人删掉的数据。**⭐ 第 27 篇那句"**一致 ≠ 正确**"，到这里就不用背了。

### 任务五（挑战）：写时复制

不用日志，改用第 28 篇的写时复制：**所有的改动都写到新块，最后原子地换一次根指针。**

**验收：** 穷举所有崩溃点，**每一个都必须一致，而且不需要任何 `recover()`**——⭐ 因为盘上永远是某个完整的版本。

**然后比较三者的写入次数**（无日志 / 日志 / CoW）。你会看到第 27、28 篇讲的那些代价，变成你自己测出来的数字。

## 交上来的东西

1. `CrashDisk` 和你的 `check()`。
2. ⭐ 任务一的穷举表：崩溃点 → 不一致类型 → 对应第 27 篇那张表的哪一行。
3. 任务二的穷举结果（全绿）。
4. ⭐ 任务三的输出——**证明少一个 flush 会怎样**。
5. 任务四 `writeback` 模式下读到 `'B'` 的那一次记录。
6. 三种方案的写入次数对比。

## 自查

- 你的穷举真的覆盖了**所有** `k` 吗？还是只抽样了几个？
- `reorder=True` 打开了吗？没打开的话，你的实现可能依赖了一个磁盘并不保证的顺序。
- ⭐ 你的 `check()` 有没有可能**漏报**？想想怎么验证检查器本身——**故意造一个已知的损坏，看它报不报。**
