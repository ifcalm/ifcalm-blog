---
title: "第 5 篇：XSS——注入的目标是别人的浏览器"
date: 2026-09-01
weight: 5
tags: ["Web 安全"]
draft: false
summary: "XSS 是注入的一种，只是解析器换成了受害者的浏览器、被注入的语法是 HTML/JS。这一篇用标准库证明三件事：一份 html.escape 为什么只在“HTML 文本节点”一个上下文里安全（对 javascript: 和无引号属性一个字符都改不动）；用真实的 html.parser 站在浏览器那一侧看，转义过的值放进无引号属性后仍然解析出了事件处理器；以及用一个真实的 HTTP 服务器测出——URL 片段里的 payload 根本不发给服务端，所以服务端转义对 DOM 型完全够不着。"
showToc: true
tocOpen: false
---

| | |
|---|---|
| **失效的假设** | "把用户输入转义一下再放进页面就安全了" |
| **所属组** | W1 · 注入 |
| **前置** | [第 1 篇：注入的一般形式]({{< ref "01-injection-general-form.md" >}})。XSS 就是解析器 = 浏览器的那一类注入 |
| **和前四篇的不同** | 前四篇注入打的是**你的**后端；XSS 打的是**其他用户的**浏览器 |
| **复现环境** | Python 3 标准库，无外部依赖 |

## 一、XSS 只是"解析器换成了浏览器"

你在做一个评论区。用户填昵称和内容，你把它们渲染进页面。有人把昵称改成了 `<script>alert(1)</script>`——**然后每一个打开这个页面的人，浏览器都执行了它。**

这一篇的解析器，在别人的电脑上。

前四篇的注入，解析器是数据库、shell、表达式引擎——都在**你的服务器上**。XSS 换了个解析器：**受害者的浏览器**。被注入的语法是 HTML 和 JavaScript，被攻击的也不是你，是**碰巧打开了这个页面的其他用户**。

机制没变，还是第 1 篇那句：一段数据被拼进一个会被解析的字符串。只不过这次，拼出来的字符串是 HTML，读它的是浏览器，而浏览器一旦把你的数据读成了 `<script>`，就会**以受害者的身份**执行它——读取他的 Cookie、冒充他发请求、改他看到的页面。

所以第一反应还是那个老朋友："那我把用户输入转义一下。"

### 打个比方

你把一段文字交给排版工，交代一句："里面的特殊符号，你处理一下。"

他会问你一个你多半没想过的问题：**"这段字要印在哪儿？"**

印在正文里，要处理的是一套符号；印在书名号里，是另一套；印在页脚的网址里，又是另一套。**没有一套"通用的特殊符号"**——离开了"印在哪儿"，"特殊符号"这四个字根本没有含义。

你只交代了"处理一下"，他只能按最常见的那套（正文）处理。而你要印的地方是网址栏。

⭐ 这一篇要说的就是这件事：**转义是对的方向，但"转义一下"这句话缺了唯一重要的信息——给哪个上下文用。**

## 二、一份转义，只在一个上下文里安全

看这段。它把同一份"标准 HTML 转义"作用到三个位置的 payload 上：

```python
from html import escape                      # 标准的 HTML 转义：< > & " ' 都会被转义

payloads = {
    "HTML 文本节点":  "<script>alert(1)</script>",
    "无引号属性":     "x onmouseover=alert(1)",
    "href 属性":      "javascript:alert(1)",
}
for ctx, raw in payloads.items():
    enc = escape(raw, quote=True)
    print(f"{ctx:12} | 转义改动了吗: {str(enc != raw):5} | 结果: {enc}")
```

```
HTML 文本节点    | 转义改动了吗: True  | 结果: &lt;script&gt;alert(1)&lt;/script&gt;
无引号属性        | 转义改动了吗: False | 结果: x onmouseover=alert(1)
href 属性      | 转义改动了吗: False | 结果: javascript:alert(1)
```

**看中间那一列。** 第一行 `True`——转义确实把 `<script>` 变成了 `&lt;script&gt;`，在 HTML 文本节点里，安全。

后两行是 `False`：**转义一个字符都没改动。**

```
x onmouseover=alert(1)      里面没有 < > & " '，转义无事可做
javascript:alert(1)         同样没有 HTML 特殊字符
```

可它们都是**活的 XSS**：

```
无引号属性  value=x onmouseover=alert(1)
            那个空格没被转义，于是 onmouseover 成了一个【新属性】——一个事件处理器

href 属性   href=javascript:alert(1)
            这是个合法的 URL scheme。HTML 转义根本不处理 scheme，
            点一下链接就执行
```

⭐ 这正是第 1 篇那张表在 HTML 世界里的实例：**「危险」是（数据，上下文）的属性。** `html.escape` 只为一个上下文设计——HTML 文本节点。把它用到属性、URL、JS、CSS 里，它要么不够（放过了 `javascript:`），要么用错了字符集（属性该转义空格，它没有）。

"转义一下"之所以是句危险的话，就因为它省掉了"给哪个上下文"——而这恰恰是唯一重要的信息。

### 正确的说法：编码由目标上下文决定

同一个用户数据，去往不同位置，要用不同的编码：

```
HTML 文本节点         转义 < > &
带引号属性 value="…"   再加上把 " 转义；且【必须】带引号
无引号属性            别用。它的可注入面大得多（一个空格就能加事件处理器）
URL 位置 href="…"     先校验 scheme（只允许 http/https），再做 URL 编码
<script> 里的 JS      别把用户数据拼进 JS 代码；要传就用 JSON 编码放进数据位置
CSS 里                CSS 转义；同样别把用户数据拼进 style
```

⚠️ 用错上下文的编码 = 没编码。上面的输出就是证据：给 `href` 用 HTML 转义，`javascript:` 原样穿过。

## 三、站在浏览器那一侧看一眼

上一节是"转义改动了什么"。但真正决定安不安全的不是转义函数，是**浏览器的 HTML 解析器最后读出了什么**。用标准库里那个真的 HTML 解析器，替我们看一眼：

```python
from html import escape
from html.parser import HTMLParser

class SeesTags(HTMLParser):
    """站在浏览器的位置：这段 HTML 里，解析出了哪些【标签】和【事件属性】？"""
    def __init__(self): super().__init__(); self.tags=[]; self.handlers=[]
    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.handlers += [k for k, _ in attrs if k.startswith("on")]

def parse(html):
    p = SeesTags(); p.feed(html); return p.tags, p.handlers

nick = '<script>alert(1)</script>'
print("文本节点，未转义      :", parse(f"<p>{nick}</p>"))
print("文本节点，已转义      :", parse(f"<p>{escape(nick)}</p>"))

attr = 'x onmouseover=alert(1)'
print("无引号属性，已转义    :", parse(f"<div title={escape(attr)}>"))
print("带引号属性，已转义    :", parse(f'<div title="{escape(attr)}">'))
```

```
文本节点，未转义      : (['p', 'script'], [])
文本节点，已转义      : (['p'], [])
无引号属性，已转义    : (['div'], ['onmouseover'])
带引号属性，已转义    : (['div'], [])
```

第二行：转义之后解析器只看见 `p`，`<script>` 变成了字面文字。**这是转义起作用的样子。**

第三行才是重点：**同一份转义**，值放进**无引号属性**里，解析器解析出了一个 `onmouseover` 事件处理器。转义函数没做错什么——它按 HTML 文本节点的规则干完了活；错的是**这个位置根本不是文本节点**。

第四行给出了那个便宜的修复：**属性带上引号**，同一个值就老老实实待在属性里了。

⭐ 这就是"用错上下文的编码 = 没编码"的现场，而且判定它的不是我，是 `html.parser`——浏览器读这段 HTML 时做的判断和它一样。

⚠️ 这里最反直觉的一点是：**转义函数没有 bug。** `html.escape` 一丝不苟地完成了它被设计来做的事。出错的是调用它的人——在一个不是文本节点的位置，用了文本节点那套规则。所以这个 bug 在代码 review 里几乎看不出来：那一行写着 `escape(x)`，看上去无可指摘。

## 四、三种 XSS，差别只在"数据在哪一步进页面"

XSS 常被分成三型。名字不重要，重要的是它们**防御的位置不一样**，而区别可以用一句话说清：**数据是在哪一步被写进页面的。**

```
反射型   数据在这次请求的 URL/表单里 -> 服务端把它拼进响应 HTML -> 浏览器解析
存储型   数据先存进数据库 -> 以后每次有人打开页面，服务端把它拼进 HTML -> 浏览器解析
DOM 型   数据由前端 JS 自己从 URL / postMessage / localStorage 读出来
         -> 直接写进 innerHTML 等位置 -> 浏览器解析。【服务端全程不参与】
```

前两型的共同点是"服务端拼了这段 HTML"，所以服务端的模板转义能管到。第三型不行——而"不行"到什么程度，可以直接测出来：

```python
import threading, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

server_saw = []
class Log(BaseHTTPRequestHandler):
    def do_GET(self):
        server_saw.append(self.path)          # 服务端记下它到底收到了什么
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self, *a): pass

srv = HTTPServer(("127.0.0.1", 0), Log)
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"

# 反射型：数据在 query 里 —— 服务端看得到
urllib.request.urlopen(base + "/p?nick=<script>alert(1)</script>").read()
# DOM 型：数据在 # 片段里 —— 由前端 JS 自己读出来用
urllib.request.urlopen(base + "/p#nick=<script>alert(1)</script>").read()

for path in server_saw:
    print("服务端实际收到的请求行:", path)
print()
print("片段里的 payload 到过服务端吗:", any("alert" in p for p in server_saw[1:]))
srv.shutdown()
```

```
服务端实际收到的请求行: /p?nick=<script>alert(1)</script>
服务端实际收到的请求行: /p

片段里的 payload 到过服务端吗: False
```

两次请求，浏览器地址栏里都带着那段 payload。**但服务端只见到了一次。** 第二次到达服务端的请求行是干干净净的 `/p`——`#` 后面的内容，HTTP 协议规定**根本不发给服务器**。

⭐ 所以：**你在服务端做的任何转义、任何 WAF 规则，对 DOM 型完全够不着。** 服务器从头到尾没见过这段数据。很多团队"XSS 已经在模板层统一转义了"的自信，正是栽在这一型上——模板层是服务端，而 DOM 型的战场整个在浏览器里。

DOM 型的防御在前端，而且同样是"别拼进会解析的位置"：

```
危险（把字符串当 HTML 解析）        安全（把字符串当数据）
--------------------------------------------------------
el.innerHTML = userInput            el.textContent = userInput
el.outerHTML = ...                  el.setAttribute('title', userInput)
document.write(userInput)           （需要富文本时，用经过审计的净化库）
location = userInput                先校验 scheme 再赋值
```

这张表和命令注入的 argv、SQL 的参数化是**同一招**：用一个"只当数据、不当语法"的 API，而不是自己去拼再想办法转义。

## 五、为什么 XSS 是最难灭干净的注入

SQL、命令注入都在一个进程里，边界清楚。XSS 难，因为它的输出点**散落在整个前端**，而且每个点的上下文都可能不同：

```
同一个用户昵称，在一个页面上可能同时出现在——
  <span>这里</span>              (HTML 文本节点)
  <input value="这里">           (带引号属性)
  <a href="/u/这里">             (URL 路径)
  <script>var u="这里"</script>  (JS 字符串)
  onclick="greet('这里')"        (事件处理器里的 JS)
每一个都需要【不同】的编码，漏一个就是一个 XSS。
```

这就是为什么现代防御不再依赖"记得在每个点转义对"，而是靠**框架的自动上下文编码**（下一节）——把"每次都要做对"换成"默认就对"。这和第 2 篇 SQL 那句"防护贴在拼接点上、而点很多"是同一个困境，也是同一个出路。

### 它出现过的地方

展开在[事件分析]({{< ref "/posts/security/web/incidents" >}})里：

```
2005      Samy 蠕虫（MySpace）          存储型 XSS 自我传播，是 XSS 蠕虫的原型
```

## 六、防御

### ① 首选：用框架的自动上下文编码，别手工转义

现代前端框架（把数据绑定到 DOM 的那些）默认会**根据插入位置自动选择编码**：文本位置转 HTML、属性位置转属性、URL 位置校验 scheme。你只要把数据当数据交给它，别自己拼 HTML 字符串。

```
交给框架的数据绑定 / 文本节点 API      —— 默认安全
自己拼 HTML 字符串再 innerHTML         —— 回到手工转义的老路，且要每个上下文都对
```

### ② 需要富文本时：用经过审计的净化库，白名单标签

用户要能发**格式**（粗体、链接）时，不能简单转义（会把格式也转掉）。此时用成熟的 HTML 净化库，**白名单**允许的标签和属性，默认拒绝 `<script>`、事件处理器、`javascript:` scheme。别自己写正则去删标签——那是黑名单，第 1 篇讲过它为什么必输。

### ③ URL 一律先校验 scheme

```
只允许 http: / https:（按需加 mailto:）
显式拒绝 javascript: data: vbscript:
```

§二 的输出说明了为什么：HTML 转义救不了 `javascript:`，URL 位置必须单独校验 scheme。

### ④ 纵深：CSP、HttpOnly、SameSite

```
CSP（内容安全策略）   限制页面能执行哪些脚本源，能把"注入成功"降级为"注入了但跑不起来"
Cookie HttpOnly       让 JS 读不到会话 Cookie，削弱 XSS 偷 Cookie 的收益
Cookie SameSite       限制跨站携带，和 CSRF 一起防（见 W4）
```

⚠️ CSP 是**减损**不是**根治**：它提高门槛，但配置不当或页面本身留了 `unsafe-inline` 就会打折。把 CSP 当墙、省掉输出编码，是常见误判——顺序永远是先 ①②③ 把注入堵死，CSP 兜底。

## 七、这些防御的边界

**① 框架的"自动安全"有逃逸口。** 每个前端框架都留了"我就是要插入原始 HTML"的出口（`dangerouslySetInnerHTML`、`v-html`、`[innerHTML]` 之类）。用到它，就回到了手工净化，必须配 ②。这和第 2 篇"ORM 的 `.raw()` 逃逸口"是一模一样的结构。

**② DOM 型只能在前端防。** 见 §四。服务端做得再干净都够不着，必须在前端审计所有"把字符串当 HTML/URL 用"的 sink。

**③ 富文本净化是持续对抗。** HTML 净化库的绕过（利用解析器怪癖、mutation XSS）时有出现。用成熟库并保持更新；任何"这个净化配置是安全的"结论都要带上库版本。

**关于时效**：注入的机制（数据进了会解析的上下文）稳定不变。但**浏览器的解析行为、CSP 的能力、各框架的默认转义策略在持续演进**，属于 W1 里时效性偏强的一篇。涉及具体 CSP 指令或框架版本时要核实。

## 八、本篇小结

```
XSS = 解析器换成受害者的浏览器、被注入的语法是 HTML/JS 的注入。
打的不是你的后端，是其他用户的会话。

⭐ 「转义一下」是句危险的话——它漏了唯一重要的信息：转义给哪个上下文
   一份 html.escape 只在"HTML 文本节点"安全
   对 javascript:（href）和 x onmouseover=（无引号属性）一个字符都改不动
   => 编码必须由【目标上下文】决定

⭐ 三型的区别只在"数据在哪一步被写进页面"
   存储型/反射型：服务端写 HTML => 服务端能防
   DOM 型：数据从不经过服务端 => 服务端转义完全够不着，只能前端防

防御优先级：
   ① 用框架的自动上下文编码，别手工拼 HTML（首选）
   ② 富文本 -> 白名单净化库，别自己写正则删标签
   ③ URL 一律先校验 scheme（HTML 转义救不了 javascript:）
   ④ 纵深 -> CSP / HttpOnly / SameSite，兜底不替代 ①②③

和 SQL、命令注入同一招：用"只当数据不当语法"的 API（textContent / 数据绑定），
不要自己拼字符串再想办法转义。
```

### 思考题

1. §二 里 `html.escape` 对 `javascript:alert(1)` 一个字符没改。如果改用"URL 编码"去处理它，能挡住吗？为什么正确做法是"先校验 scheme"而不是"编码更狠一点"？
2. 一个页面把用户昵称同时放进 `<span>` 和 `<a href="/u/{昵称}">`。如果只做了 HTML 文本转义，哪个位置还有洞？构造一个昵称说明（不需可用 payload，说明思路即可）。
3. §四 里第二个请求到服务端时只剩 `/p`。据此说明：为什么"在服务端加个 WAF 过滤 XSS"对 DOM 型几乎无效？把它和"存储型能不能靠 WAF 防"对比。
4. `el.textContent = x` 和 `el.innerHTML = x` 的区别，用第 1 篇"谁是解析器"解释：前者有没有解析器参与？
5. 富文本净化为什么不能用"删掉 `<script>` 标签"这种黑名单实现？举一个不含 `<script>` 却能执行 JS 的 HTML 片段思路（对照 §三 那个被解析出来的 `onmouseover`）。
6. CSP 能"把注入成功降级为注入了但跑不起来"。它具体拦的是哪一步——注入进 HTML，还是脚本执行？为什么 `unsafe-inline` 会让它大打折扣？
7. 把 XSS 的 `textContent`、SQL 的参数化、命令注入的 argv 放在一起：它们共同拿掉了什么？用第 1 篇的定义（结构是否随数据变化）统一表述。

> **相关**：[第 1 篇：注入的一般形式]({{< ref "01-injection-general-form.md" >}}) · [第 2 篇：SQL 注入]({{< ref "02-sql-injection.md" >}}) · [Web 安全机制篇]({{< ref "/posts/security/web" >}}) · [事件分析]({{< ref "/posts/security/web/incidents" >}})
