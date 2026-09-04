---
title: "实验一：写一个 shell"
date: 2026-09-03
weight: 70
tags: ["操作系统"]
draft: false
summary: "用 fork / exec / wait / pipe / dup2 写一个能真正用的 shell。验收标准不由我给——你的 shell 跑出来的东西要和 bash 跑出来的一模一样，diff 说了算。从执行一条命令开始，逐步加上重定向、管道、后台任务和信号处理。"
showToc: true
tocOpen: false
---

| | |
|---|---|
| **配套** | [第 3 篇：进程 API]({{< ref "03-process-api.md" >}})、[第 2 篇：进程]({{< ref "02-process.md" >}}) |
| **语言** | Python 3（`os` 模块几乎原样暴露系统调用）；想用 C 也完全可以 |
| **验收** | ⭐ **和 `bash` 的输出逐字节 `diff`。裁判是 bash，不是我。** |

## 为什么做这个

第 3 篇讲过：`fork` 和 `exec` 之间那道缝，是 shell 全部功能的所在地。**重定向、管道、改工作目录，全在那道缝里。**

看懂那句话和自己写出来，是两回事。

## 环境

```bash
docker run --rm -it -v "$PWD:/lab" -w /lab oslab bash
```

## 起步骨架

```python
#!/usr/bin/env python3
# mysh.py
import os, sys

def parse(line):
    """先用最笨的办法：按空格切。后面再改。"""
    return line.strip().split()

def run(argv):
    if not argv:
        return
    if argv[0] == "exit":
        sys.exit(0)
    if argv[0] == "cd":                    # ⚠️ cd 必须在父进程里做，想想为什么
        os.chdir(argv[1] if len(argv) > 1 else os.path.expanduser("~"))
        return
    pid = os.fork()
    if pid == 0:
        try:
            os.execvp(argv[0], argv)
        except FileNotFoundError:
            print(f"mysh: {argv[0]}: command not found", file=sys.stderr)
        os._exit(127)                      # ⚠️ 这里必须是 _exit，不是 exit
    else:
        os.waitpid(pid, 0)

def main():
    while True:
        try:
            line = input("mysh$ ")
        except EOFError:
            break
        run(parse(line))

main()
```

⚠️ 两个坑已经埋在注释里了，动手前先想清楚：

1. **`cd` 为什么不能 fork 出去做？**（提示：子进程改的是谁的工作目录？）
2. **子进程里为什么必须 `os._exit` 而不是 `sys.exit`？**（提示：第 1 篇踩过这个坑——缓冲区。）

## 任务

### 任务一：跑通一条命令

让上面的骨架能跑 `ls -l`、`echo hello`、`/bin/date`。

**验收：**

```bash
echo -e 'echo hello\nls /etc/hostname\nexit' | python3 mysh.py
```

### 任务二：重定向

支持 `>`、`>>`、`<`。

⭐ **实现要点全在第 3 篇第四节**：在 `fork` 之后、`exec` 之前，用 `os.dup2` 把 0/1/2 号描述符换掉。

**验收（`diff` 说了算）：**

```bash
cat > t.sh <<'EOF'
ls /etc > out1.txt
echo hello >> out1.txt
wc -l < out1.txt
exit
EOF
python3 mysh.py < t.sh > mine.txt 2>&1
bash          < t.sh > theirs.txt 2>&1
diff mine.txt theirs.txt && echo "★ 通过"
```

### 任务三：管道

支持 `a | b`，然后支持任意长的 `a | b | c | d`。

**实现要点：**

```
1. os.pipe() 得到 (r, w)
2. fork 出左边：把 w 接到它的 1 号，关掉 r 和 w
3. fork 出右边：把 r 接到它的 0 号，关掉 r 和 w
4. ★ 父进程也必须关掉 r 和 w
5. 两个都 wait
```

⚠️ **第 4 步是最容易漏的，漏了的症状是程序挂住。** 想清楚为什么：管道的读端在**所有**持有写端的进程都关闭之后才会读到 EOF。父进程留着写端不放，右边就永远等不到结束。

**验收：**

```bash
echo 'cat /etc/services | grep tcp | wc -l' > t.sh; echo exit >> t.sh
diff <(python3 mysh.py < t.sh) <(bash < t.sh) && echo "★ 通过"
```

### 任务四：后台任务

支持结尾的 `&`：不 `wait`，直接返回提示符。

⚠️ **然后你就会攒僵尸**（第 3 篇第五节）。请在每次显示提示符之前，用 `os.waitpid(-1, os.WNOHANG)` 循环收掉所有已经结束的子进程。

**验收：**

```bash
# 起 20 个后台任务，然后检查有没有僵尸
{ for i in $(seq 20); do echo "sleep 0.1 &"; done; echo "sleep 1"; echo exit; } > t.sh
python3 mysh.py < t.sh
ps -eo stat --no-headers | grep -c Z    # ★ 应该是 0
```

### 任务五：信号

- **Ctrl-C 只该杀掉前台的子进程，不该杀掉你的 shell。**
- 前台子进程在跑的时候，shell 本身要忽略 `SIGINT`。

**验收：** 跑一个 `sleep 100`，按 Ctrl-C。`sleep` 死掉，提示符回来，shell 还活着。

⚠️ 别忘了[第 3 篇第六节]({{< ref "03-process-api.md" >}})那两条：**`SIGCHLD` 不排队**（同时退出的多个后台任务只会给你一个信号，所以要 `while ... WNOHANG` 收干净），以及**处理函数里只置标志位、真正的活儿留给主循环**。

⭐ 想做得完全对，还需要**进程组**和 `tcsetpgrp`——那已经超出这门课的范围了。做到"shell 不死"即可。

## 挑战（可选）

- **`$?`**：上一条命令的退出码。
- **变量展开**：`echo $HOME`。
- **通配符**：`ls *.py`。⚠️ 注意：这个是**由 shell 展开的**，不是由 `ls` 展开的——`ls` 收到的是已经展开好的一串文件名。
- **`&&` 和 `||`**：短路。

## 交上来之前自查

1. 每一个 `fork` 出来的子进程，都被 `wait` 过吗？（前台的同步 wait，后台的 `WNOHANG` 收）
2. 每一个 `os.pipe()` 拿到的描述符，**在所有三个进程里**都关干净了吗？
3. `exec` 失败的时候，子进程会怎样？会不会变成第二个 shell？
4. 起一千条命令，`ls /proc/self/fd` 会不会越来越多？

⭐ 第 4 条是**描述符泄漏**的自查，做法和第 9 篇查内存泄漏是一个思路：**跑一万遍，看那个数字涨不涨。**
