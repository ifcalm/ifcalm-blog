---
title: "第 23 篇：路径穿越——文件名也是一个地址"
date: 2026-09-01
weight: 23
tags: ["Web 安全"]
draft: false
summary: "只要你的代码里有 os.path.join(某个目录, 用户给的名字)，就要看这一篇。用标准库演示三件事：../ 怎么跳出去；为什么给一个绝对路径时 join 会把你的基准目录整个丢掉（这一条最容易漏）；以及为什么 replace('../','') 这种清洗被 ....// 一击即破。正确的修复和 SSRF 那篇是同一句话——别判断名字长什么样，判断它最终落在哪。"
showToc: true
tocOpen: false
---

| | |
|---|---|
| **失效的假设** | "我拼了个目录前缀，所以读到的文件一定在这个目录里" |
| **所属组** | W8 · 服务端出站 |
| **前置** | [第 22 篇：SSRF]({{< ref "22-ssrf.md" >}})。同一条主线：用户给一个"地址"，服务端照着去取东西 |
| **复现环境** | Python 3 标准库，无外部依赖 |

## 一、同一条主线，换成文件系统

用户上传的文件都存在 `uploads/` 目录下。下载的时候，前端把文件名传过来，你去读那个文件给他。

有人把文件名传成了：

```
../../config/database.yml
```

上一篇里，用户给的是一个**网络地址**，你的服务器照着去发请求。这一篇里，用户给的是一个**文件名**，你的服务器照着去读磁盘。**同一条主线。**

```python
path = os.path.join(UPLOAD_DIR, user_filename)
open(path).read()
```

写下这行的人心里有一个很踏实的想法：**"我前面拼了 `UPLOAD_DIR`，所以它一定在 `UPLOAD_DIR` 里面。"**

这句话有两个漏洞，而其中一个连很多老手都不知道。

## 二、两条跳出去的路

```python
import os, tempfile

BASE = tempfile.mkdtemp()
UP = os.path.join(BASE, "uploads"); os.makedirs(UP)
open(os.path.join(UP, "photo.jpg"), "w").write("（一张图片）")
open(os.path.join(BASE, "secret.env"), "w").write("API_KEY=SK-LIVE-7F3A")   # 在 uploads 之外

def download(name):
    """把 uploads 目录下用户点名的文件读出来"""
    p = os.path.join(UP, name)
    try:    return repr(open(p).read())
    except Exception as e: return f"（{type(e).__name__}）"

print("正常            :", download("photo.jpg"))
print("用 ../ 跳出去   :", download("../secret.env"))
print("直接给绝对路径  :", download(os.path.join(BASE, "secret.env")))
print()
print("看看 os.path.join 到底拼出了什么：")
print("   join(UP, 'photo.jpg')      ->", os.path.join(UP, "photo.jpg").replace(BASE, "<BASE>"))
print("   join(UP, '../secret.env')  ->", os.path.join(UP, "../secret.env").replace(BASE, "<BASE>"))
print("   join(UP, '/etc/passwd')    ->", os.path.join(UP, "/etc/passwd"))
```

```
正常            : '（一张图片）'
用 ../ 跳出去   : 'API_KEY=SK-LIVE-7F3A'
直接给绝对路径  : 'API_KEY=SK-LIVE-7F3A'

看看 os.path.join 到底拼出了什么：
   join(UP, 'photo.jpg')      -> <BASE>/uploads/photo.jpg
   join(UP, '../secret.env')  -> <BASE>/uploads/../secret.env
   join(UP, '/etc/passwd')    -> /etc/passwd
```

第一条路你多半料到了：`../` 往上跳一级，`uploads/../secret.env` 最终落在 `secret.env` 上。

**第二条路是这一篇真正要你带走的东西。** 看最后一行：

```
os.path.join("<BASE>/uploads", "/etc/passwd")   ->   /etc/passwd
```

**你的基准目录整个消失了。** 这不是 bug，是 `os.path.join` 写在文档里的行为：**遇到一个绝对路径参数，它丢掉前面所有部分，从这个绝对路径重新开始。** Java 的 `Paths.get`、Node 的 `path.join`/`path.resolve` 有各自的版本，性质一样。

⚠️ 这一条第一次看会怀疑是不是写错了——`join` 不就是"接起来"吗？不是。它的规则是"从最后一个绝对路径开始接"，写在文档里，所有主流语言的路径库都有自己的版本。**这不是 bug，是你没读过的那半页文档。**

它格外阴险，因为它**看不出来**。`../` 在日志里、在代码 review 里是刺眼的，而一个 `/etc/passwd` 长得就像一个普通文件名。而且写检查的人一门心思在防 `..`，根本不会想到"前缀会被丢掉"这种事——**他假设 join 是"接起来"，可它不是。**

⭐ 回到第 1 篇那三个问题的第一个：**谁是解析器？** 这里的解析器是 `os.path.join` 和操作系统的路径解析，它们对"什么算一个路径"有一整套规则，而这套规则你没有完整地读过。

## 三、"那我把 `../` 删掉"

老朋友又来了。这次它输得特别快：

```python
def clean(s):
    return s.replace("../", "")          # 把 ../ 删掉，看着挺彻底

for p in ["../secret.env", "....//secret.env", "..%2fsecret.env"]:
    print(f"  {p:<22} -> {clean(p)!r}")
```

```
  ../secret.env          -> 'secret.env'
  ....//secret.env       -> '../secret.env'
  ..%2fsecret.env        -> '..%2fsecret.env'
```

**第二行。** 输入 `....//`，删掉中间那个 `../` 之后，**剩下的字符自己拼成了一个新的 `../`**。清洗函数亲手造出了它要删的东西。

这是"删除式清洗"这一类做法的通病：**删除会改变剩余字符的相邻关系**。想修就得循环删到不动点为止——而这只是把问题推给了第三行。

第三行是 `..%2f`（`%2f` 是 `/` 的百分号编码）。清洗函数看到的是一串无害的字符，可如果这个值在**后面某一步**才被 URL 解码，解码之后 `..%2f` 就变回了 `../`。这正是第 1 篇 §五 第 2 条那句话：**只要清洗和使用之间还隔着任何一步变换，清洗的结论就失效。**

## 四、正确的修复：判断落点，不判断名字

和上一篇 SSRF 的修复是**同一句话**：别去看这个字符串长什么样，去看它**最终指向哪里**。

在文件系统里，"最终指向哪里"有一个明确的答案——`os.path.realpath` 会把 `..`、符号链接、多余的斜杠全部解析掉，给你一个规范的绝对路径。拿到它之后，只问一个问题：**它在不在我的目录里？**

```python
import os, tempfile

BASE = tempfile.mkdtemp(); UP = os.path.join(BASE, "uploads"); os.makedirs(UP)
open(os.path.join(UP, "photo.jpg"), "w").write("（一张图片）")
open(os.path.join(BASE, "secret.env"), "w").write("API_KEY=SK-LIVE-7F3A")
ROOT = os.path.realpath(UP)

def download_safe(name):
    """不去判断名字长什么样，而是判断它【最终落在哪】"""
    p = os.path.realpath(os.path.join(UP, name))          # 先算出真实落点
    if os.path.commonpath([p, ROOT]) != ROOT:             # 落点必须在 uploads 之内
        return "拒绝：落点在 uploads 之外"
    try:    return "读到：" + repr(open(p).read())
    except FileNotFoundError: return "落点合法，但没有这个文件"

for name in ["photo.jpg", "../secret.env", "....//secret.env",
             os.path.join(BASE, "secret.env"), "/etc/passwd"]:
    print(f"  {name.replace(BASE, '<BASE>'):<24} -> {download_safe(name)}")
```

```
  photo.jpg                -> 读到：'（一张图片）'
  ../secret.env            -> 拒绝：落点在 uploads 之外
  ....//secret.env         -> 落点合法，但没有这个文件
  <BASE>/secret.env        -> 拒绝：落点在 uploads 之外
  /etc/passwd              -> 拒绝：落点在 uploads 之外
```

上一节那三种写法，加上绝对路径那条隐蔽的路，**全都被同一条规则挡住了**，而我没有为任何一种单独写过一行代码。

第三行值得单看：`....//secret.env` 被**放行**了，而且这是**对的**。它的落点是 `uploads/..../secret.env`——`....` 只是一个普通的目录名，这个路径老老实实待在 `uploads` 里面。这条规则**根本不需要认识 `....//` 这个花招**，它只问落点。

⭐ 对比一下两种思路，这是这一篇和第 1 篇共同的那句话在文件系统里的样子：

```
清洗式   我来想想哪些写法是危险的        —— 你要穷举攻击者的想象力
落点式   算出它最终指向哪，看在不在界内   —— 你只需要说清自己的边界
```

⚠️ 一个实现上的坑：必须用 `realpath`（会跟随符号链接），不能只用 `normpath`（只做字符串上的规范化）。否则攻击者上传一个指向 `/etc/passwd` 的符号链接，`normpath` 看不出任何问题——**它算的是字符串，不是文件系统的真实结构。**

## 五、它出现过的地方

展开在[事件分析]({{< ref "/posts/security/web/incidents" >}})里：

```
2021.10   Apache HTTP Server 2.4.49 / CVE-2021-41773
             路径规范化的一处改动引入了穿越；特定配置下还能到 RCE
2021.10   Apache HTTP Server 2.4.50 / CVE-2021-42013
             上一条的补丁【没修全】：它挡住了单次 URL 编码的 payload，
             却没考虑【双重编码】—— 把 . 写成 %25%32%65，解一次变成 %2e，
             再解一次才变回 . ，于是同一条穿越又走通了一遍
```

⭐ 这一对比单独一起更值一记：**补丁本身踩进了同一个坑。** 2.4.50 的修补者显然知道要处理 URL 编码——他处理了一次。可解码在这条路径上发生了**两次**，而检查只在其中一次之后。

这正是 §三 第三行那个 `..%2f` 的放大版：**清洗（或检查）和使用之间只要还隔着一次解码，结论就失效**；隔着两次，就需要你正好数对了次数。所以正确的做法不是"多解几次码"，而是 §四 那条——**别数解码次数，去看最终落点。**

## 六、防御

```
① 最好的文件名是用户不提供的      存文件时自己生成 ID，用户传 ID，映射到真实路径（白名单映射）
② 判断落点，不判断名字            realpath 之后必须在允许的根目录之内（§四）
③ 用 realpath，不要只用 normpath   否则符号链接绕过
④ 检查放在所有解码之后            别让 %2f 这类编码在你检查完之后才变回 /
⑤ 上传的文件不要放在能被执行的目录  存到 Web 根之外，或存对象存储；下载时由代码读出来给
⑥ 文件类型别信扩展名和 Content-Type 两者都是用户说了算，要看内容
```

判断标准：**你的代码里，有没有一处是把用户给的字符串拼进文件路径的？** 有，就必须能回答"这个路径最终落在哪，我校验了吗"。

⭐ ① 才是最省事的那条。用户传 `a3f9c1`、你查表得到真实路径，**用户的字符串从来没有进入路径**——这和第 1 篇 ③ 的白名单映射、第 2 篇 §五② 的动态列名是同一招。能用 ① 就别去做 ②。

## 七、这些防御的边界

**① 上传方向也要防。** 这一篇的 demo 是"读"，但**写**的方向更危险：`open(join(UP, name), "w")` 配上一个 `../../app/config.py`，就成了任意文件写入，通常直通 RCE。同一条落点检查两边都要做。

**② 压缩包解压是重灾区。** 归档格式里的条目名可以带 `../`，解压时按名字写文件就跳出去了（有个诨名叫 Zip Slip）。**解压必须对每一个条目单独做 §四 的落点检查**，别信任归档里的名字。

**③ 大小写和 Unicode。** 在大小写不敏感的文件系统上，`Secret.env` 和 `secret.env` 是同一个文件；某些 Unicode 规范化会让两个不同的字符串指向同一个路径。这又是"检查和使用看到的不是同一个字符串"（第 17 篇）。落点式检查天然免疫这一类，清洗式不免疫。

**④ 容器不是边界。** "跑在容器里，最多读到容器内的文件"——可容器里通常有你的源码、配置和挂进来的密钥。最小权限（只读挂载、专用用户）要一起上。

**关于时效**：路径解析的语义（`..`、绝对路径覆盖、符号链接）极其稳定，这一篇不会过时。会变的是各语言标准库的**具体函数行为**——哪个函数跟随符号链接、哪个只做字符串规范化，不同语言不同版本有差别，用之前查文档。

## 八、本篇小结

```
和上一篇同一条主线：用户给一个"地址"，服务端照着去取东西。
上一篇的地址是 URL，这一篇是文件路径。

⭐ 两条跳出去的路，第二条最容易漏：
   ../          往上跳，刺眼、好防
   绝对路径      os.path.join 遇到绝对路径会【丢掉前面所有部分】—— 你的基准目录消失了
                长得像普通文件名，日志和 review 都看不出来
⭐ replace("../","") 一击即破：....// 删完之后自己拼回一个 ../
   删除会改变剩余字符的相邻关系；再加上 %2f 那一层，清洗和使用之间隔着一次解码
⭐ 修复 = 判断落点：realpath 算出真实路径，检查它在不在允许的根目录内
   这条规则不需要认识任何一种花招，只需要你说清自己的边界
   （最省事的还是让用户根本不提供文件名：传 ID，查表映射）

边界：写方向比读方向更危险(任意写常直通 RCE) · 解压要逐条目检查 ·
      必须 realpath 不能只 normpath(符号链接) · 检查要在所有解码之后
```

### 思考题

1. §二 最后一行里 `os.path.join` 把基准目录丢掉了。为什么说这一条比 `../` 更难在代码 review 里发现？如果要加一条静态检查规则，你会让它报什么模式？
2. `....//` 击破了 `replace("../","")`。如果改成"循环删除直到不再变化"，还能被绕过吗？再对照 §三 第三行说明：为什么这条路走到底也不对？
3. §四 放行了 `....//secret.env`，文中说这是对的。用"落点"这个概念解释为什么放行它不构成漏洞。
4. 为什么必须用 `realpath` 而不是 `normpath`？构造一个场景，让 `normpath` 的检查通过、而文件真实落在目录之外。
5. §七① 说写方向更危险。设想一个"用户上传头像"的接口，文件名完全由用户控制。列出三个他可能想覆盖的文件，并说明各自的后果。
6. 把这一篇的"判断落点"和第 22 篇的"判断解析出来的 IP"放一起，用一句话概括它们共同的模式。再想想第 1 篇的参数化——它算不算同一个模式的第三个实例？
7. §六① 说最好的做法是用户根本不提供文件名。什么样的产品需求会让 ① 做不到？在那种情况下，②～⑥ 里哪几条变成了必需？

> **相关**：[第 22 篇：SSRF]({{< ref "22-ssrf.md" >}}) · [第 1 篇：注入的一般形式]({{< ref "01-injection-general-form.md" >}}) · [第 17 篇：解析器差异]({{< ref "17-parser-differential.md" >}}) · [第 20 篇：配置与暴露]({{< ref "20-misconfiguration.md" >}}) · [Web 安全机制篇]({{< ref "/posts/security/web" >}}) · [事件分析]({{< ref "/posts/security/web/incidents" >}})
