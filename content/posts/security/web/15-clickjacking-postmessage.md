---
title: "第 15 篇：Clickjacking 与 postMessage——窗口之间的信任"
date: 2026-09-01
weight: 15
tags: ["Web 安全"]
draft: false
summary: "W4 收尾，讲两个跨窗口的信任问题。Clickjacking：攻击者用透明 iframe 把你的页面叠在他的页面上，用户以为点的是这边、其实点的是那边——防线是告诉浏览器'我不许被别人嵌'。postMessage：跨窗口通信时接收方不校验来源，就把任何页面发来的消息当可信处理。两段 demo 都得在浏览器里跑，因为这两件事的判定权都在浏览器手里：能不能被 iframe、消息的 origin 是什么，都是它说了算。"
showToc: true
tocOpen: false
---

| | |
|---|---|
| **失效的假设** | "在我页面上的点击是用户对我点的 / 发到我窗口的消息是可信方发的" |
| **所属组** | W4 · 浏览器信任边界 |
| **前置** | [第 13 篇：CSRF]({{< ref "13-csrf.md" >}})、[第 14 篇：CORS]({{< ref "14-cors.md" >}}) |
| **复现环境** | Python 3 标准库起服务器，**但两段 demo 都要在浏览器里看结果**——这一篇的裁判只能是浏览器 |

## 一、两个问题，一个主题

用户在一个抽奖页面上点了「立即领取」。他真的点了，位置也没偏。

但那一下点在了一个透明 iframe 上，下面是他银行页面的「确认转账」。

W4 前两篇讲的是"跨站的请求和响应"。这一篇收尾，讲**跨窗口**：一个页面嵌着另一个页面（iframe），或者两个窗口互发消息。它们共享一个主题——

> **窗口把两个源放到了一起，但"挨在一起"不等于"可以互相信任"。**

两个具体问题：**clickjacking**（攻击者把你的页面嵌进他的页面，劫持点击）和 **postMessage 不验来源**（接收跨窗口消息却不看是谁发的）。

## 二、Clickjacking：你以为点的是这边

攻击者把你的页面（比如银行的"确认转账"页）用一个**透明的 iframe** 叠在他自己的页面上，上面盖着诱人的东西（"点击领奖"）。用户看着点的是"领奖"，手指落下的位置**正好是**下层你页面里的"确认转账"按钮。

用户的点击是真的、cookie 是真的、请求是真的、你的服务端日志里也一切正常——**只有"用户以为自己在点什么"是假的。**

### 打个比方

这是一份**签字页调包**：别人递给你一摞纸，最上面那张写着"参加抽奖登记表"，你签了名。可他事先在那一摞里做了手脚——你的笔尖穿过一张透明的复写纸，签在了下面那张转账授权书上。签名是你亲手签的，笔迹鉴定不出任何问题。

问题从来不在签名，在**你被展示的是哪一张纸**。所以防线也不在"验证签名"，而在**不许别人把你的纸垫到他的下面**。

### 这一段的裁判必须是浏览器

前面几篇的 demo 都能在 Python 里跑完，这一篇不行——**"这个页面能不能被嵌进别人的页面"完全是浏览器的决定**。所以下面这段起一个真实的服务器，然后请你在**浏览器**里打开它：

```python
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

BANK = """<body style="margin:0;font:16px sans-serif">
<h3>Bank</h3><button style="padding:14px 22px">确认转账 ¥10000</button></body>"""

ATTACKER = """<body style="font:16px sans-serif">
<h2>抽奖页面</h2>
<p>下面两个框分别嵌 /vuln 和 /safe。哪个能被嵌进来，由浏览器说了算。</p>
<div style="display:flex;gap:24px">
  <div><b>/vuln（没设任何头）</b><br>
    <iframe id="a" src="/vuln" width="300" height="120" style="border:2px solid #c00"></iframe></div>
  <div><b>/safe（X-Frame-Options: DENY）</b><br>
    <iframe id="b" src="/safe" width="300" height="120" style="border:2px solid #0a0"></iframe></div>
</div>
<pre id="out" style="background:#eee;padding:10px"></pre>
<script>
setTimeout(() => {
  const probe = id => { try { return document.getElementById(id).contentDocument
        ?.body?.innerText.trim().replace(/\s+/g,' ') || "(空白)"; } catch(e){ return "(跨源，读不到)"; } };
  out.textContent = "iframe /vuln 里实际渲染出了: " + probe("a")
                  + "\niframe /safe 里实际渲染出了: " + probe("b");
}, 400);
</script></body>"""

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        if self.path == "/safe":
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write((ATTACKER if self.path == "/" else BANK).encode())
    def log_message(self, *a): pass

srv = HTTPServer(("127.0.0.1", 8931), H)
print("用浏览器打开 http://127.0.0.1:8931/ ，然后看页面底部那两行")
srv.serve_forever()
```

在浏览器里打开后，页面底部会打印出：

```
iframe /vuln 里实际渲染出了: Bank 确认转账 ¥10000
iframe /safe 里实际渲染出了: (空白)
```

左边红框里，**银行那个"确认转账 ¥10000"的按钮真的出现在了攻击者的页面上**——攻击者只要给这个 iframe 加上 `opacity:0`，再在同一位置铺一个"立即领取"，clickjacking 就成立了。右边绿框是空的。

同时浏览器控制台里会有一行：

```
Framing 'http://127.0.0.1:8931/' violates the following Content Security Policy
directive: "frame-ancestors 'none'". The request has been blocked.
```

⭐ 请注意这句话是**浏览器说的，不是我说的**。这一节唯一有意义的证据就是它：一个响应头改变了另一个网站能不能把你画进它的页面里。

两个头的关系：

```
什么都不设                              => 谁都能把你嵌进 iframe，clickjacking 成立
X-Frame-Options: DENY / SAMEORIGIN      老机制，只能表达"全禁"或"只许同源"
CSP: frame-ancestors 'none' / 白名单     新机制，能列多个允许源；两者都在时以它为准
```

⚠️ clickjacking 是这份清单里最不像"漏洞"的一个，第一次读会觉得它不该算在里面。它没有利用任何实现错误——**参与其中的每一行代码都在正确工作**。这也正是它值得单独一节的原因：它说明"安全"这件事的边界，比"代码有没有写错"要宽。

⭐ 再注意 clickjacking 的巧妙：它**不突破任何技术边界**——不注入、不越权、不偷 cookie。它利用的是**视觉和信任的错位**。所有请求都合法，所以服务端日志、WAF、扫描器全都看不出异常——**能看出问题的只有"我的页面允许被谁嵌"这一个配置项。**

## 三、postMessage：别人发的消息，你当成自己人

上一节是"别人把你嵌进去"。这一节反过来：**你嵌了别人，或者别人拿到了你的窗口引用，然后给你发消息。**

`postMessage` 是浏览器给跨窗口通信开的正门（父页面和 iframe、opener 和弹窗之间传数据）。它很有用，但有个必须做的动作：**接收方要校验消息的来源。**

这一段的裁判同样是浏览器——因为 `e.origin` 这个字段**由浏览器填写、页面无法伪造**，这正是全部机制的支点。下面起两个端口（= 两个不同的源），父页面上挂两个处理器：一个不验来源，一个验：

```python
import threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer

APP = """<body style="font:15px sans-serif"><h3>你的应用（父窗口）</h3>
<iframe src="EVIL/widget" width="0" height="0"></iframe>
<pre id="log" style="background:#eee;padding:10px"></pre>
<script>
const TRUSTED = "APP";
window.addEventListener("message", e => {           // 有洞：不看是谁发的
  log.textContent += "有洞处理器 收下了指令: " + e.data + "  （来自 " + e.origin + "）\n";
});
window.addEventListener("message", e => {           // 修复：先验来源
  if (e.origin !== TRUSTED) {
    log.textContent += "验来源处理器 丢弃了这条: 来自 " + e.origin + "\n"; return; }
  log.textContent += "验来源处理器 收下了指令: " + e.data + "\n";
});
</script></body>"""

WIDGET = """<script>
  parent.postMessage("transferAllFunds", "*");   // 攻击者的 iframe 向父窗口喊话
</script>"""

def mk(port, page):
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers()
            self.wfile.write(page().encode())
        def log_message(self,*a): pass
    s = HTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=s.serve_forever, daemon=True).start(); return s

APP_O, EVIL_O = "http://127.0.0.1:8941", "http://127.0.0.1:8942"
mk(8941, lambda: APP.replace("EVIL", EVIL_O).replace("APP", APP_O))
mk(8942, lambda: WIDGET)
print("用浏览器打开", APP_O)
while True: time.sleep(1)
```

浏览器里打开 `http://127.0.0.1:8941`，页面上会出现：

```
有洞处理器 收下了指令: transferAllFunds  （来自 http://127.0.0.1:8942）
验来源处理器 丢弃了这条: 来自 http://127.0.0.1:8942
```

两个处理器**收到的是同一条消息**，浏览器一视同仁地送到了两个人手上。区别只在第二个多问了一句"你是谁"。

注意括号里那个 `8942`：**浏览器如实写上了发送方的真实源**，攻击者的 JS 无法把它改成 `8941`。这是这里唯一可靠的来源凭据——`e.origin` 之于 postMessage，就像第 13 篇的 CSRF 令牌、第 14 篇经过校验的 `Origin` 头。**不看它，等于把"谁在说话"这个信息直接扔掉。**

⚠️ 而且注意：那个 iframe 宽高都是 0，用户什么都看不见。**攻击者不需要用户做任何事**，页面一加载消息就发出去了。

另一半对称的责任在**发送方**：`postMessage(data, targetOrigin)` 的第二个参数别用 `*`（上面 widget 里用的就是 `*`，所以它能喊给任何父窗口）。指定确切的目标源，否则你发出去的数据可能落进不该收到它的窗口——比如你的页面正被别人 iframe 着（回到 §二）。

> 这一类没有单一的标志性公开事件，它以大量分散的个案存在；有技术细节的会收进[事件分析]({{< ref "/posts/security/web/incidents" >}})。

## 四、防御

```
Clickjacking
① CSP: frame-ancestors           声明谁能 iframe 你（'self' 或白名单），推荐
② X-Frame-Options                老浏览器兜底（DENY / SAMEORIGIN）
③ 敏感操作二次确认               即使被嵌，关键动作要求额外确认/重认证

postMessage
④ 接收方必校验 event.origin      白名单来源，不匹配直接丢弃
⑤ 发送方指定 targetOrigin        别用 *，指定确切目标源
⑥ 校验消息结构                   别信任 data 的形状，当成不可信输入处理（W1）
```

判断标准两句：clickjacking——**你的敏感页面允许被任意站点 iframe 吗？** postMessage——**你的消息处理器看 event.origin 了吗？**

## 五、这些防御的边界

**① frame 保护要覆盖所有敏感页面。** 常见的漏是"主站设了，但某个子页面/老页面/第三方托管页忘了设"。攻击者只需要一个能嵌的敏感页。默认全站设置、按需放开，比逐页添加可靠（又是"默认拒绝"）。

**② origin 校验要用严格相等，不是包含。** 和第 14 篇 CORS 白名单一样：`origin.includes("mycompany.com")` 会被 `mycompany.com.evil.com` 绕过。用完整源精确比较。

**③ postMessage 的内容仍是不可信输入。** 就算来源对了，消息的 `data` 也可能被可信页面自身的漏洞污染（比如那个页面有 XSS）。所以来源校验之后，内容仍要按 W1 的输入处理——**信任来源 ≠ 信任内容**。

**关于时效**：`X-Frame-Options` 正逐步让位于 CSP `frame-ancestors`；两者的浏览器支持和优先级随版本变。postMessage 的 origin 语义稳定。涉及具体 CSP 指令支持度要按当年浏览器核实。

## 六、本篇小结

```
跨窗口的主题：窗口把两个源放到一起，但"挨在一起"不等于"能互相信任"。

⭐ Clickjacking：透明 iframe 叠在攻击者页面上，用户以为点这边、实际点那边
   不突破任何技术边界，纯视觉/信任错位 —— 技术检查看不出异常
   防线：告诉浏览器"我不许被嵌"—— CSP frame-ancestors / X-Frame-Options
⭐ postMessage：接收方不验 event.origin => 任何页面发的消息都被当可信指令
   防线：先验 origin(浏览器填写、不可伪造) 再信内容 —— 和"先验签再信任"同一招
   发送方也别用 targetOrigin: *

边界：frame 保护要覆盖所有敏感页(默认全设)；origin 用精确相等；
      信任来源 ≠ 信任内容(来源对了，data 仍是不可信输入)。
```

### 思考题

1. Clickjacking"不突破任何技术边界"，所有请求都合法。这对"只靠服务端日志/WAF 检测攻击"意味着什么？为什么这类攻击必须在"页面能不能被嵌"这一层防？
2. §二 说被嵌页面里的点击"cookie 是真的、操作是真的"。这和第 13 篇 CSRF 有什么本质区别？（提示：CSRF 伪造请求，clickjacking 让用户真的点。）
3. postMessage 的 `event.origin` 为什么"不可伪造"？它由谁填写？把它和第 13 篇 CSRF 令牌、第 14 篇 CORS 的 Origin 头放一起，哪些来源标识可信、哪些不可信，判断依据是什么？
4. §六③ 说"信任来源 ≠ 信任内容"：一个来源校验正确的 postMessage，其 data 仍可能有害。构造一个场景（提示：可信页面自己有 XSS）。这一条为什么把 W4 和 W1 连了起来？
5. 为什么发送方的 `targetOrigin` 也不能用 `*`？构造一个"发消息用了 *"导致敏感数据泄露给错误窗口的场景。
6. `X-Frame-Options: SAMEORIGIN` 和 `CSP: frame-ancestors 'self'` 效果相近。为什么推荐用后者？（提示：多白名单源、以及两个头同时存在时的优先级。）
7. 回顾整个 W4：CSRF、CORS、clickjacking、postMessage 四个问题，能不能用一句话概括它们共同的失效假设？同源策略在这四个里分别扮演了什么角色（漏洞来源 / 修复依据 / 被绕过 / 被拆除）？

> **相关**：[第 13 篇：CSRF]({{< ref "13-csrf.md" >}}) · [第 14 篇：CORS]({{< ref "14-cors.md" >}}) · [第 6 篇：不安全反序列化]({{< ref "06-insecure-deserialization.md" >}}) · [Web 安全机制篇]({{< ref "/posts/security/web" >}}) · [事件分析]({{< ref "/posts/security/web/incidents" >}})
