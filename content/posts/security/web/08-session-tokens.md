---
title: "第 8 篇：会话与令牌——签发、存储、撤销的一整条命"
date: 2026-09-01
weight: 8
tags: ["Web 安全"]
draft: false
summary: "登录只是把'你是谁'换成一个令牌，之后每个请求都靠它。这一篇顺着令牌的一生走：生成要不可预测（random 和 secrets 的天壤之别）、登录后必须换新令牌（会话固定）、以及存储与撤销的取舍。核心是把'认证'和'会话'分开看——密码对不对是一瞬间的事，令牌有没有被人接管是往后每一个请求的事。"
showToc: true
tocOpen: false
---

| | |
|---|---|
| **失效的假设** | "登录验过密码了，后面这个会话就是安全的" |
| **所属组** | W2 · 认证与会话 |
| **一句话主线** | 认证是一瞬间，会话是一整段。令牌的生成/传输/存储/撤销，每一环都能单独失手 |
| **复现环境** | Python 3 标准库，无外部依赖 |

## 一、登录之后，你靠的是一张纸条

你输完密码，点了登录。页面跳转，右上角出现你的名字。

接下来你点了十几个页面，一次都没再输过密码。

**服务器凭什么知道后面这十几个请求还是你？**

它不知道。HTTP 不记得任何人——每个请求到达时，服务器都是第一次见它。所以"登录"这件事的真相是：你出示一次密码，服务器发给你一张**纸条**（会话令牌 / cookie），此后每个请求你都递上这张纸条，**服务器认纸条不认人**。

这句话有个让人不安的推论：**验密码只发生一次，之后所有的安全都压在那张纸条上。** 于是攻击者的目标从"猜密码"变成了更省事的"搞到那张纸条"——偷、猜、或者事先塞给你一张他也有副本的。

### 打个比方

这就像**演唱会的手环**。

进场时保安查你的身份证、核对购票记录，认认真真验一次——然后给你戴一个手环。之后你出去买瓶水再进来，保安只看手环，**再也不看你的脸**。

于是想混进去的人有了一个比"伪造身份证"省事得多的思路：**他不需要变成你，只需要弄到一个手环。** 偷一个、仿一个、或者干脆在你进场前就把一个他也有同款的手环套到你手上。

⭐ 这三条路，正好就是这一篇的三节：偷（传输保护）、仿（生成要不可预测）、事先塞给你一个（会话固定）。

⚠️ 第三条是最反直觉的，因为它**不需要攻击者拿到任何本来属于你的东西**。第三节专门讲它。

## 二、生成：纸条必须"猜不出来"

如果令牌能被预测，攻击者连偷都不用偷，直接算出来。而"可预测"最常见的来源，是用错了随机数：

```python
import random, secrets

# 会话 token 若用"可预测"的随机源，攻击者能重建它。
# random 是伪随机：知道种子（现实里常是时间戳等可猜的值）就能预测后续。
random.seed(1337)
server_tokens = [random.randint(10**9, 10**10) for _ in range(3)]

random.seed(1337)                                  # 攻击者用同样的种子
attacker = [random.randint(10**9, 10**10) for _ in range(3)]
print("服务端发的 token :", server_tokens)
print("攻击者复现的序列 :", attacker)
print("完全一致（可预测）:", server_tokens == attacker)

# 正确做法：CSPRNG，不可预测、无种子可复现
a, b = secrets.token_hex(16), secrets.token_hex(16)
print("secrets 两次生成是否不同:", a != b, "| 每个 token 位数:", len(a) * 4)
```

```
服务端发的 token : [8835625582, 8686328573, 6616242630]
攻击者复现的序列 : [8835625582, 8686328573, 6616242630]
完全一致（可预测）: True
secrets 两次生成是否不同: True | 每个 token 位数: 128
```

`random` 是**伪随机数**：它为"统计上均匀"设计，不为"不可预测"设计。它由一个种子推导出整个序列——攻击者只要拿到或猜到种子（现实里种子常是启动时间戳这类可猜的值），就能**复现你发出的每一个令牌**。上面攻击者用同样的种子，一字不差地重建了序列。

⭐ 会话令牌必须来自 **CSPRNG**（密码学安全随机数，Python 里是 `secrets`）——它不可预测、没有"种子"能让人复现。规则很干脆：**任何和安全有关的随机值（会话令牌、密码重置码、CSRF token）都用 `secrets`，绝不用 `random`。**

令牌还得**够长**：128 位以上，让暴力猜解在概率上不可行。上面 `secrets.token_hex(16)` 是 128 位。

## 三、签发：登录成功的那一刻，必须换新纸条

这是个特别隐蔽的坑，因为它和"令牌生成得好不好"**无关**——就算你的令牌完美地不可预测，还是可能栽。

攻击者的做法是：先给你一张纸条，等你拿着它去登录。

下面这段起了一个真实的 HTTP 服务器，用标准库的 `http.cookiejar` 当受害者的浏览器——**cookie 怎么带、什么时候被换掉，全由它按浏览器的规则决定，不是我说了算**：

```python
import threading, urllib.request, http.cookiejar, secrets
from http.server import BaseHTTPRequestHandler, HTTPServer

sessions = {}          # sid -> 已登录的用户名

class App(BaseHTTPRequestHandler):
    def do_GET(self):
        sid = ""
        for kv in self.headers.get("Cookie", "").split(";"):
            if kv.strip().startswith("sid="): sid = kv.strip()[4:]
        self.send_response(200)
        if self.path.startswith("/login"):
            if self.path.startswith("/login/vuln"):
                sessions[sid] = "victim"                    # 有洞：沿用登录前那个 sid
            else:
                sessions.pop(sid, None)                     # 修复：作废旧的，发一张新的
                new = secrets.token_hex(4); sessions[new] = "victim"
                self.send_header("Set-Cookie", f"sid={new}; Path=/")
        self.end_headers()
        self.wfile.write(f"当前这张纸条属于: {sessions.get(sid) or '（未登录）'}".encode())
    def log_message(self, *a): pass

srv = HTTPServer(("127.0.0.1", 0), App)
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"

def victim_logs_in(path):
    """受害者点开了攻击者发来的链接，浏览器带着攻击者预置的 sid 去登录"""
    jar = http.cookiejar.CookieJar()
    br = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    c = http.cookiejar.Cookie(0,"sid","ATTACKER-PLANTED",None,False,"127.0.0.1",False,False,
                              "/",True,False,None,False,None,None,None)
    jar.set_cookie(c)                                   # 攻击者预先塞进去的那张纸条
    br.open(base + path).read()

def attacker_tries(sid):
    """攻击者拿着自己那张 ATTACKER-PLANTED 去访问"""
    r = urllib.request.Request(base + "/me", headers={"Cookie": f"sid={sid}"})
    return urllib.request.urlopen(r).read().decode()

sessions.clear(); victim_logs_in("/login/vuln")
print("有洞版 —— 攻击者拿着预置的那张纸条:", attacker_tries("ATTACKER-PLANTED"))
sessions.clear(); victim_logs_in("/login/safe")
print("修复版 —— 攻击者拿着预置的那张纸条:", attacker_tries("ATTACKER-PLANTED"))
print("修复版里受害者的真实会话         :", list(sessions.values()))
srv.shutdown()
```

```
有洞版 —— 攻击者拿着预置的那张纸条: 当前这张纸条属于: victim
修复版 —— 攻击者拿着预置的那张纸条: 当前这张纸条属于: （未登录）
修复版里受害者的真实会话         : ['victim']
```

**看第一行。** 攻击者拿的是他**自己预先造出来的**那串 `ATTACKER-PLANTED`——他从来没偷过任何东西。可服务器告诉他：这张纸条属于 victim。他现在就是 victim。

过程是这样的：攻击者先想办法让受害者带着 `ATTACKER-PLANTED` 这个 sid 访问站点（一个带 `?sid=...` 的链接、一次子域上的 cookie 注入都行）。受害者输入自己的账号密码、**登录成功**——可服务器**沿用了那个旧 sid**，只是给它盖了个"已登录"的章。于是攻击者手里那份副本，跟着一起升级成了受害者的会话。

这叫**会话固定（session fixation）**。注意漏洞在哪：**不在令牌怎么生成**（这个 sid 是攻击者定的，谈不上生成质量），而在**登录前后是不是同一个令牌**。

第二行是修复：登录时作废旧 sid、发一张全新的。攻击者手里那份立刻变成废纸，而受害者的会话好好的（第三行）。

⭐ 回到手环那个比方：会话固定就是**有人在你进场前，先给你套了一个他也有同款的手环**。你验完票、进了场，那只手环变成了"已入场"——而他手上那只一模一样。

修复因此只有一句话：**验完票之后，剪掉旧手环，换一只新的。** 换成代码就是——登录成功（以及任何权限变化）后，作废旧令牌，发一个全新的。 这和第 2 篇"修复点在拼接处"、第 6 篇"先验签再反序列化"是同一类思维——**在关键状态变化的那一刻，重置信任**。

## 四、存储与撤销：无状态的代价

令牌存哪、怎么作废，是一组连在一起的取舍：

```
服务端有状态（session store）      令牌只是一个随机 ID，真实数据在服务端
   撤销：删掉那条记录即可，立刻生效
   代价：每个请求要查一次存储

无状态（自包含令牌，如 JWT）        用户信息 + 签名直接装在令牌里
   优点：服务端不用存、不用查，天然横向扩展
   ⚠️ 撤销难：令牌自己就是凭证，服务端"不认识"它，
      没法简单地"删掉"——它在过期前一直有效
```

⚠️ 这个取舍是 W2 里最容易踩的：团队为了"无状态、好扩展"选了自包含令牌，却没意识到**自己交出了"立即登出/立即封号"的能力**。下一篇（JWT）会专门讲这一类令牌自己的坑；这里先记住这个权衡的存在。

传输环节的三件套（都属于"别让纸条在路上被捡走"）：

```
Secure     只在 HTTPS 上发送，别在明文 HTTP 里裸奔
HttpOnly   JS 读不到它，削弱 XSS 偷 cookie（呼应第 5 篇）
SameSite   限制跨站自动携带，和 CSRF 一起防（见 W4）
```

> 这一类没有单一的标志性公开事件，它以大量分散的个案存在；有技术细节的会收进[事件分析]({{< ref "/posts/security/web/incidents" >}})。

⭐ Citrix Bleed 这类的教训精准踩在本篇主线上：**攻击者要的从来不是你的密码，是你那张登录后的纸条。** 拿到有效会话令牌，密码和 MFA 都被绕过了——因为那两样只在签发纸条时查过一次。

## 五、防御

```
① 令牌用 CSPRNG，≥128 位          secrets，绝不用 random
② 登录/提权后立即轮换令牌          根治会话固定
③ 传输三件套                      Secure + HttpOnly + SameSite
④ 想清楚撤销怎么做                 需要"立即登出/封号" => 别用纯无状态令牌，
                                 或加一层服务端吊销名单
⑤ 设过期 + 空闲超时               纸条不该永久有效；高危操作要求重新认证
```

判断标准：**你能不能在 1 秒内让某一个用户的所有会话立刻失效？** 答不出来，说明撤销这一环没设计。

## 六、这些防御的边界

**① 令牌轮换防固定，不防"登录后被偷"。** 会话固定是"登录前就被塞了令牌"，轮换能解。但登录**之后**令牌通过 XSS、日志、内存泄露被偷走，轮换救不了——那要靠 HttpOnly、绑定设备指纹、异常检测。

**② 无状态令牌的撤销没有银弹。** 加吊销名单就等于又变回"有状态"，牺牲了当初选它的理由。常见折中是"短过期 + refresh token"，但这会把复杂度转移到 refresh 流程上（见下一篇）。

**③ SameSite 不是 CSRF 的完整答案。** 它挡住大部分跨站自动携带，但有例外场景和历史绕过。W4 会展开，别把它当唯一防线。

**关于时效**：机制（不可预测、登录轮换、传输保护）稳定。会变的是 **cookie 属性的浏览器默认值**（SameSite 默认策略已经改过一次）和推荐的令牌长度/过期时长，涉及具体默认值要按当年的浏览器行为核实。

## 七、本篇小结

```
登录 = 用一次密码换一张纸条，之后服务器认纸条不认人。
=> 攻击者的目标从"猜密码"变成"搞到纸条"。

⭐ 生成：令牌必须不可预测。random 是伪随机、可被复现；用 secrets（CSPRNG）+ ≥128 位
⭐ 签发：登录/提权后必须换新令牌，否则会话固定 —— 攻击者预置的旧纸条会指向受害者
   撤销：无状态令牌好扩展，但交出了"立即失效"的能力，是最常被忽略的取舍
   传输：Secure + HttpOnly + SameSite

核心判断：你能不能在 1 秒内让一个用户的全部会话立刻失效？
真实教训（Citrix Bleed 类）：拿到有效会话令牌 = 绕过密码和 MFA，
   因为那两样只在发纸条时查过一次。
```

### 思考题

1. §二 里 `random` 被同一个种子一字不差地复现。为什么"把种子换成更大的数"或"多调用几次再用"都不是解法，而必须换成 `secrets`？（提示：伪随机的确定性不因序列长短改变。）
2. 会话固定（§三）和会话劫持（登录后偷令牌）都让攻击者拿到受害者的会话。两者的**时间点**不同——据此说明为什么"登录后轮换令牌"能解前者、不能解后者。
3. §四 说自包含令牌"交出了立即撤销的能力"。设计一个方案，在保留大部分无状态优点的同时，能做到"封某个用户号后 5 分钟内其令牌失效"。你付出了什么代价？
4. 为什么 `HttpOnly` 能削弱"XSS 偷 cookie"，却对"会话固定"毫无帮助？把这两个漏洞按"攻击者在哪一步动手"归类。
5. §四 末尾说 Citrix Bleed 里"拿到令牌就绕过了 MFA"。这对"MFA 是万能的"这种想法意味着什么？MFA 保护的是哪一步、不保护哪一步？
6. 一个 API 用 JWT 做无状态认证，产品要加"异地登录时踢掉其他设备"。这个需求和 JWT 的无状态本质冲突在哪？你会怎么折中？
7. "你能否 1 秒内让一个用户全部会话失效"这个判断标准，对有状态 session 和无状态 JWT 分别意味着要预先准备什么？

> **相关**：[第 7 篇：密码存储]({{< ref "07-password-storage.md" >}}) · [第 5 篇：XSS]({{< ref "05-xss.md" >}}) · [Web 安全机制篇]({{< ref "/posts/security/web" >}}) · [事件分析]({{< ref "/posts/security/web/incidents" >}})
