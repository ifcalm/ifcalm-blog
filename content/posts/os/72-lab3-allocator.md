---
title: "实验三：内存分配器——自己写一个 malloc"
date: 2026-09-03
weight: 72
tags: ["操作系统"]
draft: false
summary: "用 mmap 向内核要地，自己在上面切。实现空闲链表、切分、合并，然后用真实的程序压它。验收不靠自测——把你的分配器用 LD_PRELOAD 挂到真实命令上去，让 ls、grep、python 跑在你的 malloc 上。它们跑通了，才算你写对了。"
showToc: true
tocOpen: false
---

| | |
|---|---|
| **配套** | [第 9 篇：内存 API]({{< ref "09-memory-api.md" >}})、[第 11 篇：空闲空间管理]({{< ref "11-free-space.md" >}})、[第 12 篇：分页]({{< ref "12-paging.md" >}}) |
| **语言** | C（这个实验必须用 C） |
| **验收** | ⭐ **用 `LD_PRELOAD` 把你的分配器挂到 `ls`、`grep`、`python3` 上。它们跑通了才算对。** |

## 环境

```bash
docker run --rm -it -v "$PWD:/lab" -w /lab oslab bash
```

## 起步骨架

```c
/* mymalloc.c */
#define _GNU_SOURCE
#include <sys/mman.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>

typedef struct block {
    size_t        size;      /* 这一块有多大（不含头部） */
    int           free;      /* 空闲吗 */
    struct block *next;      /* 下一块（按地址排序） */
    struct block *prev;
} block_t;

#define HDR sizeof(block_t)
#define ALIGN(x) (((x) + 15) & ~(size_t)15)     /* ⚠️ malloc 必须 16 字节对齐 */

static block_t *head = NULL;

static block_t *more_memory(size_t need) {
    size_t len = ALIGN(need + HDR);
    if (len < (1 << 20)) len = 1 << 20;          /* 一次至少向内核要 1 MB */
    void *p = mmap(NULL, len, PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (p == MAP_FAILED) return NULL;
    block_t *b = p;
    b->size = len - HDR; b->free = 1; b->next = b->prev = NULL;
    return b;
}

void *malloc(size_t n) {
    /* TODO：1. 在链表里找一块够大的空闲块
             2. 找不到就 more_memory()
             3. 太大就切分
             4. 返回 (char*)b + HDR                */
    return NULL;
}

void free(void *p) {
    /* TODO：1. 从 p 往回退 HDR 拿到 block_t
             2. 标成空闲
             3. ★ 和左右邻居合并                    */
}

void *calloc(size_t n, size_t sz) { /* TODO：别忘了检查乘法溢出 */ return NULL; }
void *realloc(void *p, size_t n)  { /* TODO */ return NULL; }
```

## 任务

### 任务一：能分配

实现 `malloc`，先不管 `free`（`free` 写成空函数）。

**自查：**

```c
for (int i = 0; i < 1000; i++) {
    char *p = malloc(100);
    memset(p, 'A', 100);                 /* ⭐ 必须真写，才能发现重叠 */
}
```

⚠️ 如果两块地重叠了，`memset` 会互相踩，但**不一定崩**——第 9 篇讲过这件事。所以要主动检查：**每块写上自己的编号，最后统一验一遍**。

### 任务二：能释放和复用

实现 `free`，先不合并。

**自查：** `malloc(100)` / `free` 循环一百万次，`VmRSS` 必须**保持稳定**。涨了说明没复用上。

```c
static long rss(void) {
    FILE *f = fopen("/proc/self/status", "r"); char l[256]; long v = 0;
    while (fgets(l, sizeof l, f)) if (!strncmp(l, "VmRSS:", 6)) { sscanf(l+6, "%ld", &v); break; }
    fclose(f); return v;
}
```

### 任务三：合并

⭐ 第 11 篇说过，**合并是对付碎片的主力**。

**自查（这是第 11 篇那个演示的复刻）：**

```
分配 N 块 → 全部释放 → 再分配一块大的，应该成功
分配 N 块 → 隔一个释放一个 → 再分配一块大的，应该失败
```

**两种结果必须不同。** 如果都成功，说明你的"大块"不够大；如果都失败，说明合并没生效。

### 任务四：分离空闲链表

改成按大小分档（8、16、32、64…），每档一条链表。

**自查：** 分配一百万块，比较改造前后的耗时。⭐ **应该有明显提升，因为你不再遍历整条链表了。**

### ⭐ 任务五：真正的验收

把你的分配器编成动态库，挂到真实程序上：

```bash
gcc -shared -fPIC -O2 -o libmymalloc.so mymalloc.c
LD_PRELOAD=./libmymalloc.so ls -l /usr
LD_PRELOAD=./libmymalloc.so grep -r root /etc | head
LD_PRELOAD=./libmymalloc.so python3 -c "print(sum(range(1000000)))"
```

⭐ **这三条命令跑通、输出正确，才算你写对了。** 它们会用各种你没想到的方式调用 `malloc`——奇怪的大小、`realloc` 缩小、`calloc` 大数组、还有你没实现的 `posix_memalign`。

⚠️ **这一步几乎一定会失败几次。** 常见原因：

| 症状 | 多半是 |
|---|---|
| 段错误，栈里全是 libc | **对齐**。`malloc` 必须返回 16 字节对齐的地址 |
| `malloc(0)` 崩了 | 标准要求返回一个**可以被 free 的非空指针**（或 NULL），别返回野指针 |
| `free(NULL)` 崩了 | 标准要求这是**合法的空操作** |
| 一启动就死循环 | 你的 `malloc` 里调用了会调用 `malloc` 的函数（`printf` 就会） |
| 偶尔崩 | **`realloc` 缩小时的处理**，或者头部被写坏了 |

⭐ 最后一条特别值得体会：**你的头部就贴在用户数据前面**（第 9 篇讲的那个），**用户写出界一个字节，就把你的元数据涂了**。这就是那一篇说的"你涂掉的不只是别人的东西"。

## 挑战（可选）

- **线程安全**：加一把大锁，然后用第 18 篇的办法测它的扩展性，再改成每线程一个 arena。
- **对照 glibc**：用同一个负载分别跑你的分配器和 glibc，比 RSS 和耗时。⚠️ **你多半会输，去想为什么。**
- **加一个 canary**：在每块地的末尾写一个魔数，`free` 时检查。这样"写出界"就能被抓到了——**这就是一个迷你版的 ASan。**

## 交上来的东西

1. 代码。
2. 任务二、三、四的自查数据。
3. ⭐ 三条 `LD_PRELOAD` 命令的输出截图或记录。
4. 一段说明：**你在任务五踩了哪些坑，各自是什么原因。**
