---
title: "第 10 篇：OAuth 与 MFA——把第三方和第二因子接进来"
date: 2026-09-01
weight: 10
tags: ["Web 安全"]
draft: false
summary: "W2 收尾，讲两件把外部环节接进认证的事：用第三方登录（OAuth）和加第二因子（MFA）。OAuth 的坑集中在'回调回来的这个 code 是不是本会话发起的'——缺了 state 就是登录 CSRF。MFA 的坑在于'开了 ≠ 安全'：用一张矩阵说清短信/TOTP/推送/passkey 各自挡得住和挡不住什么，为什么只有绑定源域的 passkey 能扛住实时钓鱼。"
showToc: true
tocOpen: false
---

| | |
|---|---|
| **失效的假设** | "接了大厂 OAuth / 开了 MFA，认证这块就交出去了/搞定了" |
| **所属组** | W2 · 认证与会话 |
| **前置** | [第 8 篇：会话与令牌]({{< ref "08-session-tokens.md" >}})。OAuth 回来后还是要落到一个会话令牌上 |
| **复现环境** | Python 3 标准库，无外部依赖 |

## 一、把外部环节接进认证，接缝就是新的攻击面

上个月你们全员开了双因子，这周财务还是被骗走了一笔钱。

过程是这样的：攻击者做了一个和你们登录页一模一样的站。财务在上面输了密码，又输了手机上那六位数。而在同一分钟里，攻击者把这两样原样填进了**真的**登录页——六位数还在有效期内。

双因子全程都在工作。它验过了，通过了。**只是它没法知道自己是在替谁验。**

前三篇的认证都在你自己院子里：你存密码、你发令牌、你验签。这一篇讲两件把**外部**接进来的事：

```
OAuth / 第三方登录   把"验明身份"外包给 IdP（Google/GitHub…），你只接收结果
MFA / 第二因子       在密码之外，再要一个"你拥有的东西"
```

### 打个比方

这两件事都像**把一段工作外包出去**。

外包本身能提高质量——对方比你专业。但它引入了一个你原来没有的问题：**交接的那一刻。** 快递员把包裹递过来时，你怎么确认这是你订的那个包裹，而不是别人塞给你的？

OAuth 的接缝就在这一下：IdP 把用户"送回来"时，手里拿着一个 code。**你怎么知道这个 code 是这次、这个人的？**

MFA 的接缝在另一处：你雇了第二道验证，可你有没有搞清楚**它到底在验什么**。开头那个例子里，六位数验的是"你手上有那部手机"——它从来没有验过"你现在正在登录的是不是真站点"。

⭐ 共同的教训：**风险从"你的代码"转移到了"接缝处"**，而接缝最容易被漏掉，因为它不属于任何一边。这一篇就盯这两条缝。

## 二、OAuth：回来的这个 code，是本会话发起的吗

OAuth 授权码流程简化成一句话：用户去 IdP 那边点了"同意"，IdP 带着一个 **授权码（code）** 把浏览器重定向回你的 `redirect_uri`，你拿这个 code 去换令牌。

问题来了：**你怎么知道这个回调，是当前这个浏览器自己发起的那次授权？**

下面这段起了**两个**真实的 HTTP 服务器——一个演 IdP、一个演你的站——中间的 302 跳转由 `urllib` 真的走一遍，cookie 由 `http.cookiejar` 真的带：

```python
import threading, urllib.request, http.cookiejar, secrets, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

# ── 身份提供方（IdP）：授权后 302 回业务方，带上一个 code ──
class IdP(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
        back = q["redirect_uri"][0] + "?code=" + q["who"][0] + "-CODE"
        if "state" in q: back += "&state=" + q["state"][0]
        self.send_response(302); self.send_header("Location", back); self.end_headers()
    def log_message(self, *a): pass

# ── 业务方（你的站）：拿 code 换令牌，把结果绑到当前浏览器会话 ──
bound, pending = {}, {}
class RP(BaseHTTPRequestHandler):
    def sid(self):
        for kv in self.headers.get("Cookie","").split(";"):
            if kv.strip().startswith("sid="): return kv.strip()[4:]
        return ""
    def do_GET(self):
        u = urllib.parse.urlsplit(self.path); q = urllib.parse.parse_qs(u.query)
        self.send_response(302 if u.path.startswith("/start") else 200)
        if u.path.startswith("/start"):                      # 发起授权
            st = secrets.token_hex(3); pending[self.sid()] = st
            extra = "" if "vuln" in u.path else "&state=" + st
            kind = "vuln" if "vuln" in u.path else "safe"
            self.send_header("Location", f"{IDP}/auth?who=victim&redirect_uri={RPB}/cb/{kind}{extra}")
            self.end_headers(); return
        if u.path.startswith("/cb"):                         # 回调
            code = q.get("code",[""])[0]
            if "safe" in u.path and q.get("state",[None])[0] != pending.get(self.sid()):
                self.end_headers(); self.wfile.write("403 state 不匹配，拒绝绑定".encode()); return
            bound[self.sid()] = code.replace("-CODE","")      # 用 code 换令牌并绑定到本会话
        self.end_headers()
        self.wfile.write(f"这个浏览器会话现在属于账号: {bound.get(self.sid(),'（无）')}".encode())
    def log_message(self, *a): pass

a = HTTPServer(("127.0.0.1",0), IdP); b = HTTPServer(("127.0.0.1",0), RP)
for s in (a,b): threading.Thread(target=s.serve_forever, daemon=True).start()
IDP = f"http://127.0.0.1:{a.server_address[1]}"; RPB = f"http://127.0.0.1:{b.server_address[1]}"

def victim_browser():
    jar = http.cookiejar.CookieJar()
    c = http.cookiejar.Cookie(0,"sid","victim-session",None,False,"127.0.0.1",False,False,
                              "/",True,False,None,False,None,None,None); jar.set_cookie(c)
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

for flavor in ("vuln","safe"):
    br = victim_browser()
    br.open(f"{RPB}/start/{flavor}").read()                  # 受害者正常走一遍授权
    # 攻击者先用【自己的账号】在 IdP 拿一个 code，再诱导受害者的浏览器访问回调
    r = br.open(f"{RPB}/cb/{flavor}?code=ATTACKER-CODE").read().decode()
    print(f"/cb/{flavor:<5} 收到攻击者的 code 之后 ->", r)
a.shutdown(); b.shutdown()
```

```
/cb/vuln  收到攻击者的 code 之后 -> 这个浏览器会话现在属于账号: ATTACKER
/cb/safe  收到攻击者的 code 之后 -> 403 state 不匹配，拒绝绑定
```

**第一行是灾难。** 受害者的浏览器会话，现在绑在**攻击者的账号**上了。

⚠️ 先停一下，把方向搞清楚，这里几乎所有人第一次都会读反。

不是攻击者进了受害者的账号，是**受害者进了攻击者的账号**——而且他毫不知情，页面看着一切正常，他还在正常用。于是他之后上传的文件、填的地址、绑的支付方式，全都存进了**攻击者名下**，攻击者随时可以登录自己的账号去取。这叫**登录 CSRF / 授权码注入**。

有洞版错在哪？它**来者不拒**：任何 code 送到 `/cb`，就拿去换令牌、绑到当前会话。它从来没问过一句"这个回调是这个浏览器刚才发起的那一次吗"。

⭐ 修复就是那个常被当成"可选参数"的 `state`：发起授权时生成一个随机值存进会话，回调时校验"这个 state 是不是本会话刚才发出去的那个"。攻击者能塞给你一个 code，但他**猜不到受害者会话里那个 state**——第二行就是他撞在这道门上。

`state` 的作用和第 8 篇的令牌轮换、第 6 篇的先验签是同一类：**在信任一个外部回来的东西之前，确认它属于这一次、这个人。** 它和下一组要讲的 CSRF 令牌（第 13 篇）几乎是同一个东西——名字不同而已。

OAuth 另外两条必守（机制同源，都是"别信任回调里攻击者能操纵的部分"）：

```
redirect_uri 白名单   IdP 只能回调到你预登记的确切地址，
                     否则 code 会被送到攻击者的域（open redirect + 窃码）
                     ⚠️ "白名单"要精确匹配，别用前缀/包含 —— 见第 14 篇 §三 那张表
用 PKCE              公共客户端（SPA/App）必须用，防授权码在传输中被截获后重放
```

## 三、MFA：开了不等于安全

MFA 常被当成"开了就万事大吉"的开关。真相是**不同的第二因子，挡得住的攻击差别很大**——而差别的关键只有一个问题：

> 这个第二因子，**能不能被转发？**

先看它为什么是这个问题。攻击者搭一个和真站点长得一模一样的钓鱼页，受害者在上面输入密码和第二因子，攻击者**实时转发**到真站点去登录。密码能转发（就是一串字），短信验证码能转发（也是一串字），TOTP 能转发（还是一串字）。**凡是"一串字"，都能被转发。**

唯一挡得住的，是那种**签名里绑着"我现在在哪个网站"**的因子——passkey / WebAuthn。下面用 HMAC 把这件事的密码学原因摆出来：

```python
import hmac, hashlib, secrets

device_key = secrets.token_bytes(32)          # 存在认证器（手机/安全钥匙）里，永不外传

def authenticator_sign(origin, challenge):
    """认证器只对【浏览器告诉它的真实源域】签名——这是 WebAuthn 的核心"""
    return hmac.new(device_key, origin.encode() + challenge, hashlib.sha256).digest()

def server_verify(expected_origin, challenge, signature):
    want = hmac.new(device_key, expected_origin.encode() + challenge, hashlib.sha256).digest()
    return hmac.compare_digest(want, signature)

ch = secrets.token_bytes(16)

# 正常登录：浏览器在 bank.com 上，认证器对 bank.com 签名
sig = authenticator_sign("https://bank.com", ch)
print("在真站点登录                    :", server_verify("https://bank.com", ch, sig))

# 实时钓鱼：受害者在 evil.com 上操作。浏览器如实告诉认证器"当前源是 evil.com"。
stolen = authenticator_sign("https://evil.com", ch)
print("攻击者把钓来的签名转发给 bank.com:", server_verify("https://bank.com", ch, stolen))

# 对比：OTP 只是一串数字，换个地方照样能用
otp = "483920"
print("同一个 OTP 在钓鱼站和真站点通用  :", otp == otp)
```

```
在真站点登录                    : True
攻击者把钓来的签名转发给 bank.com: False
同一个 OTP 在钓鱼站和真站点通用  : True
```

**第二行是全部的重点。** 攻击者拿到了一个**完全有效**的签名——受害者真的用手机确认了、认证器真的签了。可这个签名里绑着 `evil.com`，而 `bank.com` 拿自己的域去验，算出来的不一样。**转发这条路在数学上被封死了**，不靠用户警觉，不靠培训。

最后一行是对照：OTP 就是六位数字，它不知道自己是在哪个页面上被输入的，所以在哪儿都能用——**这正是它挡不住实时钓鱼的原因。**

按"能不能转发"把常见因子排一下：

```
因子              挡撞库/弱密码   挡实时钓鱼      备注
─────────────────────────────────────────────────────────────
短信验证码          能            不能          还多一条 SIM 交换的路
TOTP（验证器 App）  能            不能          比短信好，但仍是"一串字"
推送批准            能            很弱          有"推送疲劳"：连轰十次直到用户点同意
passkey/WebAuthn    能             能           签名绑源域，见上面第二行
```

⚠️ 所以"我们开了 MFA"这句话，安全值取决于开的是哪一档。**把短信 MFA 和 passkey 当成同一件事，是这一节要拆掉的那个假设。** 另外注意上表最后一列：推送批准挡不住的是**人**——攻击者不需要破解任何东西，只需要在半夜连发十次推送。

## 四、它出现过的地方

展开在[事件分析]({{< ref "/posts/security/web/incidents" >}})里：

```
2022      Uber                         MFA 疲劳轰炸 + 社工，最终让员工点了「批准」
```

⭐ Uber 那次精准命中 §三 的矩阵：MFA 开着，但用的是"推送批准"，正好是疲劳轰炸能打穿的那一格。**开了 MFA 不等于选对了 MFA。**

## 五、防御

```
OAuth
① state 必校验            发起时随机生成存会话，回调时比对 —— 根治登录 CSRF
② redirect_uri 白名单     只允许预登记的确切地址，别用前缀/通配匹配
③ 公共客户端用 PKCE       防授权码被截获重放
④ 校验 IdP 返回的令牌      别只看"有没有 code"，要验 IdP 令牌的签名与 aud

MFA
⑤ 高价值场景上 passkey    唯一能扛实时钓鱼的因子
⑥ 推送配数字匹配          别用无脑"批准"，挡疲劳轰炸
⑦ 别用短信当唯一因子      SIM 劫持能整条绕过；短信是"聊胜于无"档
```

判断标准两句：OAuth——**"回调回来的东西，你验证它属于这一次授权了吗？"**；MFA——**"你选的因子，扛得住实时钓鱼吗？"**

## 六、这些防御的边界

**① OAuth 把身份验证外包，也把信任外包了。** IdP 被攻破、或 IdP 的账号本身被接管，你这边全盘失守。选 IdP 和选密码库一样是安全决定。

**② passkey 不是万能。** 它扛实时钓鱼，但设备丢失/恢复流程、账号找回通道往往成了新的软肋——攻击者绕过 passkey 去打"忘记了怎么办"。找回流程要和主认证同等强度。

**③ MFA 保护的是"登录这一步"，不保护"登录之后"。** 回到第 8 篇：会话令牌一旦被偷（XSS、Citrix Bleed 那类），MFA 已经在身后，拦不住重放。MFA 和会话保护是两道独立的关。

**关于时效**：OAuth 的这些必守项稳定。MFA 的**矩阵会随攻击手法演进**——今天"聊胜于无"的短信、"能扛钓鱼"的 passkey，其相对强弱可能因新的攻击/新的标准而变。矩阵表达的是"因子的本质决定它挡得住什么"这个方法，具体格子要按当年的威胁核对。

## 七、本篇小结

```
把外部接进认证，风险就搬到接缝处。OAuth 的缝在"回调那一下"，MFA 的缝在"选了哪种因子"。

⭐ OAuth：回来的 code 必须证明"属于本会话这一次授权" —— 缺 state = 登录 CSRF
   配套：redirect_uri 白名单 + PKCE + 验 IdP 令牌
⭐ MFA：开了 ≠ 安全。短信/TOTP/推送都挡不住【实时钓鱼】（可转发的信息）
   只有 passkey/FIDO2 能扛 —— 它把凭据绑定到源域，钓鱼站拿不到可用的东西
   推送还怕疲劳轰炸 => 配数字匹配

判断：OAuth 问"回调验证属于这次授权了吗"；MFA 问"这个因子扛得住实时钓鱼吗"。
边界：MFA 只保护登录这一步，令牌被偷之后靠第 8 篇。
```

### 思考题

1. §二 的 `state` 和 W4 将讲的 CSRF token，作用几乎一样。用第 8 篇/第 6 篇的共同主题（"信任外部回来的东西之前先确认归属"）说明它们是不是同一招。
2. 为什么 `redirect_uri` 必须是"确切地址白名单"而不能用前缀匹配？构造一个前缀匹配被绕过的思路。
3. §三 矩阵里，TOTP 挡住了 SIM 劫持但挡不住实时钓鱼，短信两个都挡不住。据此解释：为什么"短信 OTP 比 TOTP 弱"不只是"短信会被拦截"这一个原因。
4. passkey 扛实时钓鱼，靠的是"只对真域名签名"。如果攻击者不做中间人、而是攻破了 DNS 让钓鱼站点用上了真域名，passkey 还扛得住吗？（提示：想想证书/源绑定的完整链条。）
5. Uber 那次的因子是"推送批准"。如果换成"TOTP"，疲劳轰炸还成立吗？换成"passkey"呢？用矩阵逐格说明。
6. §六③ 说"MFA 只保护登录这一步"。把它和第 8 篇 Citrix Bleed 连起来：一次成功的、用了 passkey 的登录，事后令牌仍被内存泄露偷走——哪一道关失守了，另一道为什么帮不上？
7. 一个产品要在"安全"和"用户别嫌麻烦"之间平衡 MFA。基于矩阵，你会给"日常登录"和"改密码/大额转账"分别配什么因子？为什么不必所有操作都上最强因子？

> **相关**：[第 8 篇：会话与令牌]({{< ref "08-session-tokens.md" >}}) · [第 9 篇：JWT]({{< ref "09-jwt.md" >}}) · [Web 安全机制篇]({{< ref "/posts/security/web" >}}) · [事件分析]({{< ref "/posts/security/web/incidents" >}})
