---
title: "实验五：迷你文件系统——在一个普通文件上做出 inode 和目录"
date: 2026-09-03
weight: 74
tags: ["操作系统"]
draft: false
summary: "拿一个 16 MB 的普通文件当「磁盘」，在上面摆出超级块、位图、inode 表和数据块，实现 mkfs、create、write、read、mkdir、ls、unlink。验收方式很硬：把你的文件系统挂到 FUSE 上，然后用真正的 cp、tar、diff 去操作它——这些工具会用你没想到的方式调用你的接口，它们通过了才算数。"
showToc: true
tocOpen: false
---

| | |
|---|---|
| **配套** | [第 25 篇：文件与目录]({{< ref "25-files-and-directories.md" >}})、[第 26 篇：文件系统实现]({{< ref "26-filesystem-implementation.md" >}}) |
| **语言** | Python 3 |
| **验收** | ⭐ **`tar` 进去、`tar` 出来、`diff` 说一模一样。裁判是 tar 和 diff。** |

## 环境

```bash
docker run --rm -it -v "$PWD:/lab" -w /lab oslab bash
```

FUSE 部分需要额外装一个包（在容器里）：

```bash
apt-get update && apt-get install -y python3-fuse fuse3
```

⚠️ 挂载 FUSE 需要 `--privileged` 或 `--cap-add SYS_ADMIN --device /dev/fuse`。**如果装不上或挂不上，任务五有一个不依赖 FUSE 的替代验收方案**，见那一节。

## 磁盘布局

一个 16 MB 的文件，块大小 4096，共 4096 块：

```
块 0      超级块
块 1      inode 位图     （1 位一个 inode，够 32768 个）
块 2      数据块位图     （1 位一块，够 32768 块，我们只有 4096）
块 3–34   inode 表       （每个 inode 128 字节，一块 32 个，共 1024 个）
块 35–    数据块
```

### 结构

```python
import struct

BLK   = 4096
NINODE = 1024
INODE_FMT = "<HHIIQ 15I 4x"          # 类型 链接数 uid 大小 时间 15个块指针
assert struct.calcsize(INODE_FMT) == 128

SUPER_FMT = "<8sIIIIII"              # 魔数 总块数 inode数 各区起始块
MAGIC = b"MINIFS01"

DIRENT_FMT = "<I28s"                 # inode号 + 名字（最长 27 字节 + \0）
assert struct.calcsize(DIRENT_FMT) == 32
```

⭐ **目录的内容就是一串 `DIRENT`**——第 26 篇那个"目录大小随文件数线性增长"的实测，在这里由你自己实现出来。

## 任务

### 任务一：mkfs

```python
def mkfs(path, nblocks=4096):
    """把 path 初始化成一个空的文件系统，根目录是 inode 1"""
```

必须做的事：

1. 写超级块（魔数 + 各区起始位置）。
2. 位图清零，然后**把元数据区那几块标成已用**。⚠️ 忘了这一步，你的数据会覆盖掉自己的 inode 表。
3. 建根目录 inode（类型=目录，链接数=2），它的数据块里放 `.` 和 `..`（都指向自己）。

**验收：** `hexdump -C disk.img | head -5` 能看到魔数；再跑一次 `mkfs` 结果应该完全一致（**确定性**）。

### 任务二：create / write / read

```python
def create(path) -> inode_num
def write(ino, offset, data)
def read(ino, offset, length) -> bytes
```

先只支持 **12 个直接块**（48 KB 上限），间接块放到任务四。

⭐ **写入时要按块处理**：算出落在哪几块、每块的偏移，没分配的块要从位图里要一块。

**验收（自查）：**

```python
mkfs("disk.img")
ino = create("/a.txt")
write(ino, 0, b"hello world")
assert read(ino, 0, 11) == b"hello world"
write(ino, 5000, b"X")                     # 跨块
assert read(ino, 5000, 1) == b"X"
assert read(ino, 100, 10) == b"\0" * 10    # ⭐ 洞里读出来必须是 0（第 26 篇的稀疏文件）
```

### 任务三：目录

```python
def mkdir(parent_ino, name) -> ino
def lookup(parent_ino, name) -> ino or None
def readdir(ino) -> [(name, ino), ...]
def unlink(parent_ino, name)
def link(parent_ino, name, ino)            # 硬链接
```

⚠️ 这里有几件必须做对的事，全部来自第 25 篇：

- **`link` 要把目标 inode 的链接数加 1。**
- **`unlink` 减 1，减到 0 才回收数据块和 inode。**
- **`mkdir` 建的目录，链接数是 2**（它自己的 `.` 加上父目录里的那条），而且**父目录的链接数要加 1**（因为多了一个 `..` 指向它）。

⭐ 最后一条是新手最容易漏的。**自查：`mkdir` 三个子目录之后，父目录的链接数应该是 5**（2 + 3）。

**验收：**

```python
d = mkdir(1, "docs")
a = create_in(d, "a.txt"); write(a, 0, b"data")
link(1, "a_hardlink", a)
assert nlink(a) == 2
unlink(d, "a.txt")
assert nlink(a) == 1
assert read(a, 0, 4) == b"data"            # ⭐ 第 25 篇那个实验的复刻
```

### 任务四：间接块

加一级间接块（`i_block[12]` 指向一个装满块号的块），支持到 `48 KB + 4 MB`。

**验收：** 写一个 2 MB 的文件，随机读 1000 个位置校验；然后 `unlink`，⭐ **检查位图里的空闲块数回到了写之前的值**——间接块本身也要回收。

### ⭐ 任务五：接到 FUSE 上，让真工具来验

```python
import fuse
class MiniFS(fuse.Fuse):
    def getattr(self, path): ...
    def readdir(self, path, offset): ...
    def open(self, path, flags): ...
    def read(self, path, size, offset): ...
    def write(self, path, buf, offset): ...
    def mkdir(self, path, mode): ...
    def unlink(self, path): ...
```

```bash
mkdir /mnt/mini
python3 minifs.py disk.img /mnt/mini -f &
```

**然后用真工具压它：**

```bash
cp -r /etc/default /mnt/mini/          # 真的 cp
tar cf /tmp/out.tar -C /mnt/mini .     # 真的 tar
mkdir /tmp/back && tar xf /tmp/out.tar -C /tmp/back
diff -r /etc/default /tmp/back/default && echo "★ 通过"
```

⭐ **`cp` 和 `tar` 会用一堆你没想到的方式调用你的接口**：`stat` 每个文件、按 128 KB 一块读、`utimens` 设时间、检查 `st_nlink` 认硬链接。**它们通过了，才说明你的实现是自洽的。**

### 不用 FUSE 的替代验收

如果 FUSE 装不上，用这个（弱一些，但仍然不是自己验自己）：

```python
# 把一整棵真实目录树导进你的文件系统，再导出来，用 diff 比
import subprocess, os, filecmp
copy_tree_into("/etc/default")           # 你写的导入函数
copy_tree_out("/tmp/back")               # 你写的导出函数
subprocess.run(["diff", "-r", "/etc/default", "/tmp/back"], check=True)
print("★ 通过")
```

## 挑战（可选）

- **`fsck`**：写一个检查器。查孤儿 inode、位图和 inode 不一致、链接数对不对。⭐ **然后故意把镜像改坏几个字节，看它能不能查出来**（第 27 篇）。
- **块组**：把盘分成几个组，每组自带 inode 表，实现第 26 篇的 FFS 局部性。测一下有没有变化。
- **稀疏统计**：实现 `st_blocks`，让 `du` 和 `ls -s` 报出正确的实际占用。

## 交上来的东西

1. 代码。
2. 任务二、三、四的自查输出。
3. ⭐ 任务五的 `diff` 结果。
4. 一段说明：**你在接 FUSE 时踩了哪些坑**——真实工具的哪些调用是你没预料到的。
