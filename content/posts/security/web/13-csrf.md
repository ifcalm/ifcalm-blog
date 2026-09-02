---
title: "第 13 篇：CSRF——浏览器替受害者带上了 cookie"
date: 2026-09-01
weight: 13
tags: ["Web 安全"]
draft: false
summary: "W4 开篇，先讲同源策略到底保护什么。CSRF 钻的正是它的一个空子：浏览器向某站发请求会自动带上该站的 cookie，不管请求从哪个页面发起。于是'只认 cookie'的状态改变端点能被任意站点伪造。这一篇起一个真实的 HTTP 服务器，用标准库的 http.cookiejar 当受害者的浏览器——cookie 由它按浏览器规则自动附带，于是“跨站提交就把邮箱改掉了”这件事是真的跑出来的。再说清 CSRF 令牌为什么有效、以及 SameSite 把这道防线前移到了浏览器。"
showToc: true
tocOpen: false
---

| | |
|---|---|
| **失效的假设** | "带着有效会话 cookie 的请求，就是用户本人有意发起的" |
| **所属组** | W4 · 浏览器信任边界 |
| **前置** | [第 8 篇：会话与令牌]({{< ref "08-session-tokens.md" >}})。CSRF 利用的正是"服务器认 cookie 不认人" |
| **复现环境** | Python 3 标准库，无外部依赖 |

## 一、先搞清楚同源策略保护什么

受害者在银行网站登录着，另开一个标签页打开了一个陌生站点。那个站点什么都没显示，但在背后向银行发了一个 POST——**并且成功了。**

攻击者没有偷到密码，没有偷到 cookie。他只是让受害者的浏览器发了一个请求。为什么这能成？答案要从同源策略说起。

W4 这一组都绕着**同源策略（Same-Origin Policy, SOP）**转，所以先把它说清——因为大多数人对它的理解是反的。

同源策略管的是：**A 站点页面里的 JavaScript，不能读取 B 站点的响应内容。** 你在 evil.com 打开的页面，其 JS 读不到 bank.com 返回的数据。这挡住了"恶意站点直接偷读你在别站的数据"。

但请注意它**不管**的那一半——这是所有 W4 漏洞的温床：

```
同源策略【拦】的       evil.com 的 JS 读取 bank.com 的【响应内容】
同源策略【不拦】的     evil.com 让浏览器【向 bank.com 发请求】
                     而且浏览器发这个请求时，会自动带上 bank.com 的 cookie
```

⭐ 记住这句话，W4 就通了一半：**"发得出去"和"读得到回应"是两件事，同源策略只管后者。** CSRF 利用的就是"发得出去 + 自动带 cookie"这前半段——它甚至不需要读到响应。

⚠️ 这一条第一次读会觉得别扭，因为它和"同源策略保护我"这个笼统印象冲突。如果一时转不过来，就先把它当成一句需要背下来的话：**同源策略从来没有阻止过任何一个请求被发出去。** 后面三篇（CSRF、CORS、clickjacking）全都长在这句话上。

## 二、CSRF：一个不需要读响应的攻击

```python
import threading, urllib.request, urllib.error, http.cookiejar, secrets
from http.server import BaseHTTPRequestHandler, HTTPServer

SESSION, CSRF = secrets.token_hex(8), secrets.token_hex(8)
account = {"email": "alice@bank.com"}

class Bank(BaseHTTPRequestHandler):
    def do_GET(self):                                     # 登录，下发 cookie
        self.send_response(200)
        self.send_header("Set-Cookie", f"session={SESSION}; Path=/")
        self.end_headers(); self.wfile.write(b"logged in")
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
        token = dict(p.split("=", 1) for p in body.split("&") if "=" in p).get("csrf")
        logged_in = f"session={SESSION}" in self.headers.get("Cookie", "")
        # /vuln 只看 cookie；/safe 还要求表单里带对 CSRF 令牌
        ok = logged_in and (self.path == "/vuln" or token == CSRF)
        if ok: account["email"] = "attacker@evil.com"
        self.send_response(200 if ok else 403); self.end_headers()
        self.wfile.write(b"changed" if ok else b"denied")
    def log_message(self, *a): pass

srv = HTTPServer(("127.0.0.1", 0), Bank)
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"

# 受害者的浏览器。cookiejar 和真浏览器一样：对同一站点的请求【自动附带】cookie
jar = http.cookiejar.CookieJar()
browser = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
browser.open(base + "/login")
print("浏览器存下的 cookie 数:", len(jar))

def cross_site_submit(path, body):
    """攻击者页面上的表单自动提交。攻击者拿不到 cookie，也拿不到 CSRF 令牌。"""
    try:
        r = browser.open(base + path, data=body.encode())
        return f"{r.status} {r.read().decode()}"
    except urllib.error.HTTPError as e:
        return f"{e.code} {e.read().decode()}"

print("跨站提交 -> /vuln:", cross_site_submit("/vuln", "email=attacker@evil.com"))
print("   账户邮箱现在是:", account["email"])
account["email"] = "alice@bank.com"
print("跨站提交 -> /safe:", cross_site_submit("/safe", "email=attacker@evil.com&csrf=guessed"))
print("   账户邮箱现在是:", account["email"], "(未被改动)")
srv.shutdown()
```

```
浏览器存下的 cookie 数: 1
跨站提交 -> /vuln: 200 changed
   账户邮箱现在是: attacker@evil.com
跨站提交 -> /safe: 403 denied
   账户邮箱现在是: alice@bank.com (未被改动)
```

拆开看：攻击者在 evil.com 放一个自动提交的表单，`action` 指向 `bank.com/change_email`。受害者一打开这个页面，浏览器就向 bank.com 发出了 POST——**并且自动带上了受害者在 bank.com 的 session cookie**（这是浏览器的默认行为，攻击者没碰 cookie，是浏览器替他带的）。

有洞的服务端**只看 cookie 在不在**，一看会话有效，就把邮箱改了。攻击者根本不需要读响应——他要的是"改邮箱"这个**副作用**，改成他的邮箱后再走"忘记密码"接管账号。

⭐ 失效的假设是：**"请求带着有效 cookie" ≠ "用户本人有意发起"。** cookie 证明的是"这个浏览器登录过 bank.com"，不是"用户点了这个按钮"。这个缺口，正是第 8 篇"服务器认令牌不认人"的阴暗面——令牌太"自动"了，自动到用户不知情也会带上。

### 打个比方

cookie 像一张**门禁卡**，而浏览器是个特别热心的助理：只要你去银行的门，它就自动替你刷卡——**不管是你自己走过去的，还是被人骗过去的。**

攻击者要的正是这一点。他不需要偷你的卡，只需要把你"骗到门口"。

## 三、CSRF 令牌为什么有效

修复版多要一样东西：一个**表单里的 CSRF 令牌**，且必须和服务端为该会话绑定的令牌匹配。

关键在于**攻击者拿不到这个令牌**——它由服务端随机生成、嵌在 bank.com 的合法页面里，而同源策略**恰好在这里帮了忙**：evil.com 的 JS **读不到** bank.com 页面的内容（这正是 §一 里 SOP 拦的那一半），所以攻击者没法把令牌填进他的伪造表单。

```
cookie      浏览器自动带 => 攻击者"免费"获得       => 不能单靠它证明意图
CSRF 令牌    要从页面里读出来才能带 => 攻击者读不到  => 能证明"请求来自我的页面"
```

⭐ 这是一个漂亮的互补：CSRF 攻击利用"同源策略不拦发请求"，CSRF 令牌利用"同源策略拦读内容"。**同一条规则的两半，一半是漏洞的来源，一半是修复的依据。**

## 四、SameSite：把防线前移到浏览器

CSRF 令牌是服务端的防线。还有一道更靠前的——cookie 的 `SameSite` 属性，让**浏览器**在跨站时干脆就不带 cookie。

> 下面三档是**浏览器规范规定的行为**，不是本机实测（判定发生在浏览器里，上面那个 `cookiejar` 不实现跨站判定）。以你的目标浏览器版本为准。

| SameSite | 跨站时会带 cookie 吗 | 效果 |
|---|---|---|
| `None` | 会 | 最宽松，完全靠服务端 CSRF 令牌兜 |
| `Lax` | 顶层导航 GET 会，跨站 POST 不会 | 挡住经典表单 CSRF |
| `Strict` | 都不会 | 最严，但"从外链点进来仍登录"的体验会受影响 |

⚠️ 这里有个广泛流传的误解值得纠正：**"现在浏览器默认就是 Lax，所以 CSRF 基本没了。"**

不对。**只有 Chromium 系（Chrome / Edge / Opera）把不带 `SameSite` 的 cookie 当 Lax。** Firefox 尝试过、因为破坏了太多站点而回退了；Safari 走的是另一套策略。也就是说，**如果你不显式写 `SameSite`，你的 cookie 在不同浏览器上行为不同**——而攻击者当然会挑对他有利的那个。

所以两条：**一、显式写，别靠默认。** 二、就算写了 `Lax` 也别把它当唯一防线——它仍放行**顶层导航 GET**（所以状态改变绝不能用 GET），跨子域、同站不同源等场景还有细节。纵深仍需 CSRF 令牌或 Origin 校验兜底，也就是 §三 那道服务端防线。

> 这一类没有单一的标志性公开事件，它以大量分散的个案存在；有技术细节的会收进[事件分析]({{< ref "/posts/security/web/incidents" >}})。

## 五、防御

```
① 状态改变操作要 CSRF 令牌         令牌嵌在页面里，攻击者跨站读不到（同源策略帮忙）
② cookie 设 SameSite=Lax/Strict    浏览器层面挡住大部分跨站携带
③ 校验 Origin / Referer           状态改变请求核对来源站点
④ 绝不用 GET 改状态               GET 在 Lax 下仍可能带 cookie，且易被预取/嵌入
⑤ 敏感操作二次确认                改密码/转账要求重输密码或 MFA
```

判断标准：**一个状态改变端点，仅凭 cookie（不带任何页面内令牌）能不能成功？** 能，就有 CSRF。

## 六、这些防御的边界

**① SameSite 不是完整答案。** 见 §四：GET、子域、`None` 的接口都是缺口。它是很好的默认纵深，不是免除 CSRF 令牌的理由。

**② CSRF 令牌依赖"同源策略拦读内容"这条不被破。** 如果站点同时有 XSS（第 5 篇），攻击者的脚本就跑在**同源**里，能直接读到 CSRF 令牌——**XSS 一破，CSRF 防御跟着塌。** 这也是为什么 XSS 优先级极高。

**③ 纯令牌认证（Authorization 头）天然免疫经典 CSRF。** 因为浏览器不会自动带 `Authorization` 头（它只自动带 cookie）。但用 cookie 存令牌就又把 CSRF 面引回来了。认证方式的选择直接影响 CSRF 暴露。

**关于时效**：CSRF 机制稳定。但**各浏览器的 SameSite 默认值和跨站判定规则一直在分头演进**，而且它们并不一致（见 §四）。任何"浏览器现在默认就安全了"的说法都要按当年、按具体浏览器核实——这是 W4 里时效性最强的一处。

## 七、本篇小结

```
同源策略：拦"evil.com 读 bank.com 的响应"，不拦"evil.com 让浏览器向 bank.com 发请求"。
=> "发得出去"和"读得到回应"是两件事。

⭐ CSRF 钻前半段：浏览器向 bank.com 发请求会自动带 bank.com 的 cookie
   只认 cookie 的状态改变端点 => 被任意站点伪造（攻击者甚至不需要读响应）
   失效的假设："带着有效 cookie" ≠ "用户有意发起"
⭐ CSRF 令牌钻后半段：令牌嵌在页面里，攻击者跨站【读不到】(同源策略帮忙)
   —— 同一条规则的两半：一半是漏洞来源，一半是修复依据

SameSite=Lax 把防线前移到浏览器，挡住经典表单 CSRF，但别当唯一防线。
⚠️ 别靠默认：只有 Chromium 系默认 Lax，Firefox/Safari 不是 —— 要显式写。
边界：XSS 一破，CSRF 令牌也读得到 => CSRF 防御跟着塌。
```

### 思考题

1. 用 §一 的"发得出去 vs 读得到回应"解释：为什么 CSRF 攻击者"不需要读响应"也能得手，而"偷读你别站数据"的攻击就被同源策略挡住了？
2. §三 说"同一条规则的两半，一半是漏洞来源、一半是修复依据"。把这句话对着 CSRF 攻击和 CSRF 令牌各展开一遍。
3. 为什么"状态改变绝不能用 GET"？结合 SameSite=Lax 仍放行顶层导航 GET，构造一个"用 GET 改状态"仍会中招的场景。
4. §七② 说"XSS 一破，CSRF 防御跟着塌"。为什么？攻击者的脚本此时跑在哪个源里，能读到什么？这对"该先修 XSS 还是先修 CSRF"有什么启示？
5. 用 `Authorization` 头 + 令牌的 API 天然免疫经典 CSRF，但如果开发者"为了方便"把令牌存进 cookie 自动带，会发生什么？
6. SameSite=Strict 最安全，却会让"从邮件链接点进来时未保持登录"。产品要平衡安全和体验，你会怎么给不同 cookie 分配 Strict/Lax？
7. 把 CSRF 令牌和第 10 篇 OAuth 的 `state`、第 12 篇的"默认拒绝"放一起：它们是不是都在做"证明这个请求属于我方发起的合法流程"？共同的模式是什么？

> **相关**：[第 8 篇：会话与令牌]({{< ref "08-session-tokens.md" >}}) · [第 5 篇：XSS]({{< ref "05-xss.md" >}}) · [第 14 篇：CORS]({{< ref "14-cors.md" >}}) · [Web 安全机制篇]({{< ref "/posts/security/web" >}}) · [事件分析]({{< ref "/posts/security/web/incidents" >}})
