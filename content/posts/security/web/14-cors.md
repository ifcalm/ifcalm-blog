---
title: "第 14 篇：CORS——给同源策略开的口子别开成敞口"
date: 2026-09-01
weight: 14
tags: ["Web 安全"]
draft: false
summary: "CORS 不是'防护'，是同源策略的一份放行名单——它决定哪些外站的 JS 能读你的响应。配错了，等于把上一篇讲的那道'拦读内容'的墙拆掉。这一篇先用一个真实的服务器复现最常见的致命配置：把请求的 Origin 原样反射回去 + 允许携带凭据；再说清为什么真正的洞几乎总是'动态反射 Origin'而不是一个星号；最后把四种常见的'支持所有子域'写法跑一遍，看哪几种会放进攻击者自己能注册的域名。"
showToc: true
tocOpen: false
---

| | |
|---|---|
| **失效的假设** | "加了 CORS 头是为了让前端能调接口，配宽一点没关系" |
| **所属组** | W4 · 浏览器信任边界 |
| **前置** | [第 13 篇：CSRF]({{< ref "13-csrf.md" >}})。同一条同源策略，CSRF 钻它的漏，CORS 是给它开的口 |
| **复现环境** | Python 3 标准库，无外部依赖 |

## 一、CORS 是放行名单，不是防护

周五下午，前端同事在群里发了张截图：控制台一片红，`blocked by CORS policy`。

你搜了一下，在后端加了个响应头。刷新，好了。这事花了你四分钟。

**你和 CORS 的第一次相遇，是把它当成一个报错消掉的。** 而这四分钟留下了一个很难改掉的印象：CORS 是个麻烦，配得越宽越省事。

正好反了。

回到第 13 篇 §一：同源策略拦住"A 站的 JS 读 B 站的响应"。但现实里，`app.mycompany.com` 的前端**确实需要**读 `api.mycompany.com` 的响应——这是合法的跨源需求。CORS 就是那个**例外机制**：服务端通过响应头声明"我允许**这些**源来读我"。

```
同源策略      默认：别的源不能读我的响应
CORS         例外：我在响应头里【点名】允许的源，可以读
```

### 打个比方

同源策略是门口的保安。CORS 不是**第二个保安**——它是保安手里那张**放行名单**。

名单上写谁，谁就能进。所以往名单上添名字这个动作，方向和"加强安保"正好相反：**你每写一行，门就开大一点。**

而这一篇后面要讲的两种典型错法，用这个比方一句话就说清了：

```
反射 Origin      名单上写着"来人报什么名字，就照着放什么名字进来"
宽松匹配         名单上写着"名字里带 mycompany 的都放" —— 攻击者去改个名就行
```

⭐ 所以 CORS 头不是"防护措施"，是**你亲手给同源策略开的口子**。开对了，前端能用；开错了，等于把第 13 篇那道墙**替攻击者拆了**。它的危险方向和一般的"加个头更安全"完全相反——**这里加错头是拆墙**。

⚠️ 这个方向感很重要，也最容易搞反。绝大多数安全配置是"配得越严越安全"，而 CORS 是"配得越宽越危险"——很多人第一次接触它时是为了**消除一个报错**，那个心态下写出来的配置，几乎必然是宽的。

## 二、致命配置：反射 Origin + 允许凭据

看最常见、也最致命的一种错配：

```python
import threading, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

ALLOW = {"https://app.mycompany.com"}
class Api(BaseHTTPRequestHandler):
    def do_GET(self):
        origin = self.headers.get("Origin", "")
        self.send_response(200)
        if self.path == "/vuln":                      # 有洞：原样反射
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Credentials", "true")
        elif origin in ALLOW:                          # 白名单：只对名单内回显
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Credentials", "true")
        self.end_headers(); self.wfile.write(b'{"balance":12345}')
    def log_message(self, *a): pass

srv = HTTPServer(("127.0.0.1", 0), Api)
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"

def headers_for(path, origin):
    r = urllib.request.Request(base + path, headers={"Origin": origin})
    h = urllib.request.urlopen(r).headers
    return (h.get("Access-Control-Allow-Origin"), h.get("Access-Control-Allow-Credentials"))

print("evil.com 请求 /vuln，服务器回的 CORS 头:", headers_for("/vuln", "https://evil.com"))
print("   => 服务器亲口对 evil.com 说'允许你，且可带凭据'")
print("evil.com 请求 /safe，服务器回的 CORS 头:", headers_for("/safe", "https://evil.com"))
print("自家前端请求 /safe，服务器回的 CORS 头:", headers_for("/safe", "https://app.mycompany.com"))
srv.shutdown()
```

```
evil.com 请求 /vuln，服务器回的 CORS 头: ('https://evil.com', 'true')
   => 服务器亲口对 evil.com 说'允许你，且可带凭据'
evil.com 请求 /safe，服务器回的 CORS 头: (None, None)
自家前端请求 /safe，服务器回的 CORS 头: ('https://app.mycompany.com', 'true')
```

有洞版做了两件事，合起来要命：

```
① 把请求的 Origin 原样反射进 Access-Control-Allow-Origin
     等于说"无论谁来问，我都回答'允许你'"
② Access-Control-Allow-Credentials: true
     等于说"而且欢迎带着 cookie 来读"
```

于是 evil.com 的 JS 可以发一个**带受害者 cookie**的请求到你的 API，然后**读到响应内容**。同源策略本来拦的就是这个"读到响应"，现在被你亲手放行了。攻击者能读到的，是**以受害者身份**返回的数据——个人信息、令牌、私有内容。

⚠️ 注意这比 CSRF 更进一步：CSRF **读不到响应**（§13），只能盲发请求触发副作用；而 CORS 配错让攻击者**能读到响应**，等于开了数据外泄的正门。

## 三、为什么洞是"反射"，不是"星号"

有人以为 CORS 的危险配置是写了个 `*`（允许所有源）。其实浏览器帮你挡了一半。

> 这一条是**规范规定的行为**，不是本机实测：上面那个 demo 能证明服务器确实把 `evil.com` 回显了出去，但"浏览器据此放不放行读取"发生在浏览器里。

规范里有一条硬规则：**`Access-Control-Allow-Origin: *` 不能和 `Allow-Credentials: true` 同时生效。** 星号虽然允许任意源读，但**读不到带 cookie 的响应**——而不带 cookie 读到的通常是公开数据，危害有限。

所以攻击者真正需要、开发者真正会犯的错，是**动态反射 Origin**：把请求头里的 `Origin` 抄进 `Allow-Origin`。这样每个请求的 `Allow-Origin` 都精确等于请求方的源（绕过了"不能用星号"的限制），配上 `Credentials: true`，就凑齐了带凭据读取的条件——正是 §二 那个 `/vuln` 回给 `evil.com` 的两个头。

⭐ 一句话记住：**CORS 配错的典型现场，不是一个显眼的 `*`，是一段"把 Origin 回显出去"的动态代码。** 它常常是为了"支持多个子域""开发方便"写的，看起来很合理。

## 四、于是问题变成：白名单怎么写

上一节说了，反射必须先过白名单。那白名单本身怎么写？

这一步看着很土，却是 CORS 实际出洞最多的地方——因为"支持我们所有子域"这个需求太常见，而顺手写出来的匹配几乎都是错的。

> 下面这段和前面的 demo 性质不同：它**不是攻击复现**，是把四种真实存在的写法摆在一起算一遍。有价值的地方在于那几个攻击者能自己去注册的域名——它们是现实约束，不是我编的。

把四种常见写法拉出来跑一遍，让它们各自去面对这些域名：

```python
# 后端为了"支持我们所有子域"，常见的四种写法
MATCHERS = {
    '"mycompany.com" in origin        ': lambda o: "mycompany.com" in o,
    'origin.endswith("mycompany.com") ': lambda o: o.endswith("mycompany.com"),
    'origin.endswith(".mycompany.com")': lambda o: o.endswith(".mycompany.com"),
    'origin in {…精确集合…}           ': lambda o: o in {"https://app.mycompany.com"},
}
LEGIT = "https://app.mycompany.com"
# 下面每一个域名，攻击者都可以自己去注册、自己控制
ATTACKER = ["https://mycompany.com.evil.com",   # 把你的域名放进自己域名的前缀里
            "https://evil-mycompany.com",       # 注册一个只差一个连字符的域
            "https://notmycompany.com"]         # 注册一个以你的域名结尾的域

for name, f in MATCHERS.items():
    leaks = [o for o in ATTACKER if f(o)]
    print(f"{name} 自家前端={str(f(LEGIT)):<5} 放进来的攻击者源: {leaks or '无'}")
```

```
"mycompany.com" in origin         自家前端=True  放进来的攻击者源: ['https://mycompany.com.evil.com', 'https://evil-mycompany.com', 'https://notmycompany.com']
origin.endswith("mycompany.com")  自家前端=True  放进来的攻击者源: ['https://evil-mycompany.com', 'https://notmycompany.com']
origin.endswith(".mycompany.com") 自家前端=True  放进来的攻击者源: 无
origin in {…精确集合…}            自家前端=True  放进来的攻击者源: 无
```

**四种写法在第二列上完全一样**——自家前端全都能过。所以谁写的都"能用"，测试也全绿。差别全在第三列，而第三列在你的测试用例里根本不会出现。

逐行看：

```
in         最松。攻击者只要域名里【出现】这个串就行，
           mycompany.com.evil.com 是最典型的构造：你的域名成了他域名的一个子域
endswith   少放了一个，但还漏两个：evil-mycompany.com 只差一个连字符，
           notmycompany.com 也确实"以 mycompany.com 结尾" —— 而这两个域攻击者能直接注册
.endswith  加上那个点之后，上面三个全被挡住了
```

⚠️ 注意第三行：**加一个点，结果就完全不同。** 这类 bug 不是"想得不够周全"，是字符串匹配这个工具本身就不适合表达"域名的从属关系"——域名是有层级结构的，`endswith` 只看字符。

那第三种是不是就够了？**不够**，只是失效方式换了一种：`.endswith(".mycompany.com")` 等于把你**所有**子域都当成可信源。哪天一个废弃的 `old-blog.mycompany.com` 指向的 CDN 桶被别人接管（子域接管），攻击者就合法地站进了你的白名单里。**它挡住了外人注册的相似域，挡不住你自己家里失守的那一间。**

⭐ 所以结论是最后一行那种：**精确集合**。列出你确实需要的那几个源，逐字比较。数量有限、可以审计、没有解释空间——这和第 1 篇 ③ 白名单映射是同一条：**别去判断"这个来源安不安全"，而是判断"它在不在我写死的那张表里"。**

## 五、防御

```
① 白名单，精确匹配                维护一个明确的允许源集合，只对名单内的回显 Allow-Origin
② 绝不无条件反射 Origin           反射前必须过白名单校验（§二 的 /safe 就是这一条）
③ 带凭据要格外克制               Allow-Credentials:true 只给最必要的、可信的源
④ 名单用精确源，别用宽松匹配       in / endswith 都会放进攻击者注册的域，见 §四 那张表
⑤ 分清"要不要凭据"               公开数据用不带凭据的 CORS（可配 *），私有数据才谈 credentials
```

判断标准：**你的 `Access-Control-Allow-Origin` 是从请求头里抄来的吗？** 是——且同时 `Allow-Credentials: true`，就是那个致命组合。

## 六、这些防御的边界

**① 就算用了 `.endswith(".mycompany.com")`，你也把整个子域空间纳入了信任。** §四 最后一段说的：这条匹配挡住了外人注册的相似域，挡不住**子域接管**——一个废弃子域的 DNS 还指着一个已被释放的云资源，谁抢到谁就站进了你的白名单。所以要精确集合，并且把"下线子域时清理 DNS"当成安全流程的一部分。这和第 12 篇"默认拒绝"、第 1 篇"黑名单必输"同源——**宽松匹配就是变相黑名单。**

**② CORS 只约束浏览器里的 JS 读取，不是服务端授权。** CORS 拦的是"浏览器要不要把响应给这段 JS"。它**不能**替代服务端的认证和鉴权——用 curl、服务器对服务器的请求根本不理会 CORS。**别把 CORS 当访问控制**（那是 W3 的事）。

**③ 预检（preflight）不是安全边界。** `OPTIONS` 预检是浏览器的协商机制，攻击者可以直接发不触发预检的"简单请求"，或自己伪造 OPTIONS。别以为"有预检"就安全。

**关于时效**：CORS 的规则（星号与凭据互斥、预检触发条件）由规范定义，稳定。会变的是各框架 CORS 中间件的**默认配置**——有的默认反射 Origin，有的默认严格。用任何 CORS 库前，查它这个版本默认怎么处理 Origin 和 credentials。

## 七、本篇小结

```
CORS 不是防护，是你【亲手给同源策略开的口子】。配错 = 替攻击者拆掉第13篇那道墙。
方向和直觉相反：这里"加错头"是拆墙，不是加固。

⭐ 致命组合：反射 Origin（把请求的 Origin 抄进 Allow-Origin）+ Allow-Credentials:true
   => evil.com 能带着受害者 cookie 读你的响应（比 CSRF 更进一步：能读到数据）
⭐ 危险的是"反射"不是"星号"：浏览器禁止 * 与凭据共存，
   所以攻击者需要的是"动态回显 Origin"这段看似合理的代码

防御：精确白名单 + 反射前必过校验 + 凭据格外克制 + 别用后缀/包含匹配。
边界：CORS 只管浏览器 JS 读取，不是服务端鉴权(curl 无视它)；预检不是安全边界。
```

### 思考题

1. 用第 13 篇的"发得出去 vs 读得到回应"框架说明：CSRF 和 CORS 配错分别突破了同源策略的哪一半？为什么 CORS 配错"更严重"？
2. §三 说浏览器禁止 `*` 和凭据共存。如果没有这条规则，直接写 `Allow-Origin: *` + 凭据会怎样？这条规则实际上把攻击者逼向了哪种更"费事"的配置？
3. §四 的表里，`endswith("mycompany.com")` 放进了 `notmycompany.com`，而加一个点之后就没有了。为什么加这个点能挡住它，却挡不住子域接管？给出你会用的匹配方式，并说明它需要配套什么运维动作。
4. 为什么说"CORS 不能替代服务端鉴权"？构造一个场景：CORS 配得很严，但一个服务器到服务器的调用照样拿到了数据。这说明 CORS 保护的边界在哪？
5. 一个 API 既有公开数据（无需登录）又有私有数据（需 cookie）。你会给这两类分别配什么 CORS 策略？为什么公开数据可以用 `*` 而私有数据不能反射 Origin？
6. §五③ 说预检不是安全边界。什么样的请求不会触发预检？攻击者能否绕开预检直接打你的接口？这对"把安全逻辑放在 OPTIONS 处理里"意味着什么？
7. 把 CORS 白名单的"精确匹配"、CSRF 的令牌、第 10 篇 OAuth 的 redirect_uri 白名单放一起：它们都在拒绝"宽松匹配来源"。为什么在"来源校验"这件事上，宽松匹配总是等于黑名单、总是会漏？

> **相关**：[第 13 篇：CSRF]({{< ref "13-csrf.md" >}}) · [第 12 篇：纵向越权]({{< ref "12-privilege-escalation.md" >}}) · [第 15 篇：clickjacking 与 postMessage]({{< ref "15-clickjacking-postmessage.md" >}}) · [Web 安全机制篇]({{< ref "/posts/security/web" >}}) · [事件分析]({{< ref "/posts/security/web/incidents" >}})
