---
title: "macOS say 命令使用手册：让 Mac 朗读单词、句子并生成音频"
date: 2026-05-23
tags: ["macOS", "Terminal", "英语学习"]
draft: false
summary: "macOS 自带命令行朗读工具 say 的完整使用指南，覆盖语速控制、声音切换、音频生成、批量脚本与任务提醒等实用场景。"
showToc: true
tocOpen: false
---

## 一、什么是 macOS say？

`macOS say` 是 macOS 系统自带的命令行朗读工具，核心命令是：

```bash
say
```

它可以把文本转换成语音，也就是常说的 **Text to Speech，文本转语音**。

常见用途包括：

- 朗读英文单词
- 朗读英文句子
- 辅助英语发音练习
- 朗读文本文件
- 生成音频文件
- 在脚本执行完成后进行语音提醒

有些工具或插件里可能会把它叫作 `macos-say`，但在 macOS 终端中真正执行的命令通常是 `say`。

---

## 二、最基础用法

### 1. 朗读一个单词

```bash
say hello
```

### 2. 朗读一句话

```bash
say "Hello, how are you today?"
```

### 3. 朗读中文

```bash
say "你好，这是 macOS 的语音朗读功能。"
```

如果中文朗读效果不自然，可以尝试切换中文声音，具体方法见后文。

---

## 三、控制朗读速度

`say` 可以通过 `-r` 参数控制语速。

`-r` 可以理解为 `rate`，也就是朗读速率。

```bash
say -r 120 "algorithm"
```

数字越小，朗读越慢；数字越大，朗读越快。

### 常用语速参考

| 参数 | 大致效果 | 适合场景 |
|---|---|---|
| `-r 70` | 很慢 | 听清单词发音、拆音节 |
| `-r 90` | 慢速 | 英文单词发音练习 |
| `-r 120` | 稍慢 | 短句朗读、跟读练习 |
| `-r 160` | 正常偏慢 | 普通英文句子 |
| `-r 180` | 接近正常语速 | 日常听读 |
| `-r 220` | 偏快 | 快速浏览文本 |

例如：

```bash
say -r 90 "repository"
say -r 120 "repository"
say -r 180 "repository"
```

可以明显听出 `90` 最慢，`120` 适中，`180` 更接近日常朗读。

---

## 四、指定发音人 / 声音

### 1. 查看系统支持的声音

```bash
say -v '?'
```

该命令会列出当前 Mac 支持的所有声音。

不同 macOS 版本、不同系统语言配置下，可用声音可能不完全一样。

---

### 2. 使用指定声音朗读

```bash
say -v Samantha "algorithm"
```

常见英文声音示例：

```bash
say -v Samantha "repository"
say -v Daniel "schedule"
say -v Karen "database"
```

常见中文声音示例：

```bash
say -v Ting-Ting "你好，我正在学习英语发音。"
```

如果某个声音不存在，先执行：

```bash
say -v '?'
```

查看本机实际支持的声音名称。

---

## 五、练习英文单词的推荐方式

如果是为了练英文单词发音，推荐使用：

```bash
say -v Samantha -r 90 "entrepreneur"
```

这个组合的特点是：

- 使用英文发音人
- 语速比较慢
- 适合听清楚单词细节

也可以读多遍：

```bash
say -v Samantha -r 90 "entrepreneur. entrepreneur. entrepreneur."
```

---

## 六、让单词读得更清楚

对于较长的英文单词，可以通过逗号制造停顿。

例如：

```bash
say -v Samantha -r 90 "re, po, si, to, ry"
```

或者先拆读，再完整读：

```bash
say -v Samantha -r 90 "re, po, si, to, ry. repository."
```

再比如：

```bash
say -v Samantha -r 90 "en, tre, pre, neur. entrepreneur."
```

这种方式适合练习较难单词。

---

## 七、生成音频文件

`say` 不只能直接朗读，还可以把语音保存成音频文件。

### 1. 生成 AIFF 文件

```bash
say "hello world" -o hello.aiff
```

生成后会得到：

```text
hello.aiff
```

### 2. 指定声音和语速生成音频

```bash
say -v Samantha -r 100 "algorithm" -o algorithm.aiff
```

### 3. 生成 m4a 文件

部分 macOS 版本可以直接根据文件扩展名生成音频：

```bash
say -v Samantha -r 100 "hello world" -o hello.m4a
```

如果你的系统不支持直接输出 `.m4a`，可以先生成 `.aiff`，再用 `ffmpeg` 转换。

---

## 八、转换成 mp3

`say` 通常不直接输出 mp3。可以先生成 `.aiff`，再使用 `ffmpeg` 转成 `.mp3`。

### 1. 先安装 ffmpeg

如果你已经安装了 Homebrew，可以执行：

```bash
brew install ffmpeg
```

### 2. 生成 AIFF

```bash
say -v Samantha -r 100 "repository" -o repository.aiff
```

### 3. 转成 MP3

```bash
ffmpeg -i repository.aiff repository.mp3
```

最终会得到：

```text
repository.mp3
```

---

## 九、朗读文本文件

假设有一个文件 `words.txt`：

```text
algorithm
repository
database
entrepreneur
```

可以直接朗读整个文件：

```bash
say -f words.txt
```

也可以把文本文件朗读结果保存成音频：

```bash
say -f words.txt -o words.aiff
```

---

## 十、配合管道使用

`say` 也可以读取其他命令的输出。

### 1. 朗读 echo 输出

```bash
echo "database" | say
```

### 2. 朗读当前日期

```bash
date | say
```

### 3. 朗读当前目录文件名

```bash
ls | say
```

这个用法在脚本里比较方便。

---

## 十一、脚本执行完成后语音提醒

有些命令执行时间比较长，比如编译、打包、下载、测试。

可以在命令后面追加 `say`，让 Mac 在任务完成后提醒你。

例如：

```bash
npm run build && say "build finished"
```

或者：

```bash
go test ./... && say "tests passed"
```

失败时也可以提醒：

```bash
go test ./... || say "tests failed"
```

更完整一点：

```bash
go test ./... && say "tests passed" || say "tests failed"
```

这个用法非常适合长时间运行的任务。

---

## 十二、批量生成单词音频

假设有一个 `words.txt` 文件：

```text
algorithm
repository
database
entrepreneur
```

可以用下面的脚本批量生成 `.aiff` 音频：

```bash
while read word; do
  say -v Samantha -r 100 "$word" -o "$word.aiff"
done < words.txt
```

执行后会生成：

```text
algorithm.aiff
repository.aiff
database.aiff
entrepreneur.aiff
```

如果想批量转成 mp3：

```bash
for file in *.aiff; do
  ffmpeg -i "$file" "${file%.aiff}.mp3"
done
```

---

## 十三、批量生成「慢速 + 正常语速」两个版本

练英语时，有时需要慢速版和正常版。

```bash
while read word; do
  say -v Samantha -r 90 "$word" -o "${word}_slow.aiff"
  say -v Samantha -r 150 "$word" -o "${word}_normal.aiff"
done < words.txt
```

生成结果类似：

```text
algorithm_slow.aiff
algorithm_normal.aiff
repository_slow.aiff
repository_normal.aiff
```

---

## 十四、给自己设置一个快捷命令

如果经常练英文单词，可以在 shell 配置里加一个函数。

如果你用的是 zsh，编辑：

```bash
vim ~/.zshrc
```

加入：

```bash
word_say() {
  say -v Samantha -r 90 "$1"
}
```

保存后执行：

```bash
source ~/.zshrc
```

以后就可以这样使用：

```bash
word_say entrepreneur
word_say repository
word_say algorithm
```

如果单词里有空格，需要加引号：

```bash
word_say "machine learning"
```

---

## 十五、常见问题

### 1. `say -v Samantha` 报错怎么办？

说明本机没有这个声音。

先执行：

```bash
say -v '?'
```

找到本机已有的声音，再替换命令里的声音名称。

---

### 2. 中文读得不自然怎么办？

可以尝试中文声音，例如：

```bash
say -v Ting-Ting "你好，这是中文朗读测试。"
```

如果本机没有中文声音，可以到系统设置里下载更多语音。

一般路径为：

```text
系统设置 -> 辅助功能 -> 朗读内容 -> 系统声音
```

不同 macOS 版本菜单名称可能略有差异。

---

### 3. 如何让朗读更慢？

使用 `-r` 参数，例如：

```bash
say -r 90 "entrepreneur"
```

更慢可以使用：

```bash
say -r 70 "entrepreneur"
```

---

### 4. `90`、`120` 这些数字是什么意思？

它们表示朗读速率，可以大致理解为每分钟朗读多少个英文单词。

例如：

```bash
say -r 90 "algorithm"
```

大致表示以较慢速度朗读。

```bash
say -r 120 "algorithm"
```

比 `90` 快一些，但仍然偏慢。

---

### 5. 可以直接生成 mp3 吗？

通常不建议直接依赖 `say` 生成 mp3。

更稳定的方式是：

```bash
say "hello" -o hello.aiff
ffmpeg -i hello.aiff hello.mp3
```

---

## 十六、常用命令速查

| 场景 | 命令 |
|---|---|
| 朗读单词 | `say hello` |
| 朗读句子 | `say "Hello world"` |
| 慢速朗读 | `say -r 90 "repository"` |
| 指定声音 | `say -v Samantha "algorithm"` |
| 查看声音列表 | `say -v '?'` |
| 生成音频 | `say "hello" -o hello.aiff` |
| 朗读文本文件 | `say -f words.txt` |
| 配合管道 | `echo "hello" \| say` |
| 任务完成提醒 | `npm run build && say "build finished"` |
| 转 mp3 | `ffmpeg -i hello.aiff hello.mp3` |

---

## 十七、个人推荐配置

如果主要用于英语单词发音练习，我推荐：

```bash
say -v Samantha -r 90 "your word"
```

如果用于句子跟读，可以使用：

```bash
say -v Samantha -r 120 "I am learning English pronunciation."
```

如果用于任务提醒，可以使用：

```bash
go test ./... && say "tests passed" || say "tests failed"
```

整体来看，`say` 是 macOS 上一个非常轻量但实用的工具。它不需要额外安装，适合英语学习、脚本提醒、文本朗读和简单音频生成等场景。
