---
title: "第 9 篇：JWT——签名是给谁看的"
date: 2026-09-01
weight: 9
tags: ["Web 安全"]
draft: false
summary: "JWT 把用户信息和一个签名装进令牌自己身上，服务端不用存。但它的坑几乎都出在'签名到底验没验、用什么验'上。这一篇手写 JWT，实测三个经典误用：接受 alg=none（无签名）、算法混淆、以及最常见的——直接读 payload 不验签。核心是一句：payload 是明文，谁都能改；唯一能拦住篡改的是签名，而签名只有在你正确验证时才有意义。"
showToc: true
tocOpen: false
---

| | |
|---|---|
| **失效的假设** | "JWT 是签名过的，所以里面的内容可信" |
| **所属组** | W2 · 认证与会话 |
| **前置** | [第 8 篇：会话与令牌]({{< ref "08-session-tokens.md" >}})。JWT 是那篇里"自包含令牌"的具体形态 |
| **复现环境** | Python 3 标准库，无外部依赖 |

## 一、JWT 是什么，以及它把信任放在了哪

你收到一个 JWT，把中间那段 base64 解开，看到 `{"user":"alice","role":"user"}`。

**这段内容，发这个请求的人也能解开，而且能改。** 他把 `user` 改成 `admin` 再发回来——你的代码会信吗？答案取决于你有没有做对一件事，而这一篇就是关于那一件事的。

上一篇讲了两种令牌：服务端存状态的、和自包含的。JWT 是后者的代表。一个 JWT 长这样，三段用点隔开：

```
header.payload.signature
  |      |         |
  算法   用户信息   对前两段的签名
```

前两段只是 **base64 编码的 JSON**——注意，是**编码**，不是加密。任何人都能解开来读，也能改。所以 JWT 的安全**完全**压在第三段签名上：服务端签发时用密钥算一个签名，验证时重算一遍比对，**对不上就说明有人动过前两段**。

### 打个比方

JWT 像一本**护照**。

护照上写的东西——名字、国籍、出生日期——你自己就能读，拿支笔也能改。**拦住你的从来不是那些字**，是纸张里的水印、芯片、防伪线。边检看的是防伪，不是字好不好看。

顺着这个比方，这一篇的三个误用就都有了名字：

```
alg=none      护照上多印了一行"本护照免检"，而边检照做了
算法混淆       边检拿着公开的样本去核防伪 —— 那样本谁都能拿到，谁都能照着做一本
根本没验签     边检压根没看防伪，只把名字念了一遍
```

⭐ 三个都不是"防伪技术被破解了"。**是查验流程出了问题。** 这也是 W2 一整组的主题：认证的失手大多不在算法，在流程。

说回代码：**payload 是明文、谁都能改；唯一拦住篡改的是签名。** 于是所有 JWT 漏洞都归结为同一个问题——**签名到底验没验、用什么验的。** 下面三个误用，都是这句话的反面。

## 二、误用①：接受 `alg=none`

JWT 的头部里有个 `alg` 字段，声明"我这个令牌用什么算法签的"。有些库会**信任这个字段去决定怎么验签**——包括信任一个特殊值 `none`（意思是"没有签名"）。

```python
import hmac, hashlib, base64, json

def b64(d): return base64.urlsafe_b64encode(d).rstrip(b"=").decode()
def make(header, payload, secret=b"server-secret"):
    h = b64(json.dumps(header).encode()); p = b64(json.dumps(payload).encode())
    signing_input = f"{h}.{p}".encode()
    sig = b64(hmac.new(secret, signing_input, hashlib.sha256).digest())
    return f"{h}.{p}.{sig}"

# 服务端签发的正常令牌：普通用户
token = make({"alg": "HS256", "typ": "JWT"}, {"user": "alice", "role": "user"})
print("正常令牌 role=user 已签发")

# —— 误用①：服务端信任令牌头里的 alg，且接受 alg=none（无签名）——
# 攻击者把 alg 改成 none、把 role 改成 admin、去掉签名
h = b64(json.dumps({"alg": "none", "typ": "JWT"}).encode())
p = b64(json.dumps({"user": "alice", "role": "admin"}).encode())
forged = f"{h}.{p}."                       # 第三段（签名）留空
def verify_broken(tok):
    hb, pb, sb = tok.split(".")
    header = json.loads(base64.urlsafe_b64decode(hb + "=="))
    if header["alg"] == "none":             # ← 致命：竟然接受 none
        return json.loads(base64.urlsafe_b64decode(pb + "=="))
    # ...（本应在这里验 HS256 签名）
print("alg=none 被接受，解析出的角色:", verify_broken(forged)["role"])
```

```
正常令牌 role=user 已签发
alg=none 被接受，解析出的角色: admin
```

攻击者做了三件事：把 `alg` 改成 `none`、把 `role` 从 `user` 改成 `admin`、把签名那段删空。服务端一看 `alg` 是 `none`，就**跳过了验签**，直接采信了 payload——于是普通用户变成了 admin。

⭐ 荒谬之处在于：**是令牌自己告诉服务端"你不用验我"，而服务端信了。** 这等于让嫌疑人自己决定要不要被搜身。根源是把"用什么算法验"这个**服务端该独断的决定**，交给了**攻击者能控制的字段**。

## 三、误用②：算法混淆（HS/RS）

有些系统用非对称算法 RS256：**私钥签名、公钥验签**，而公钥是公开的。攻击者利用"服务端信任 `alg` 字段"，把 `alg` 从 `RS256` 改成 `HS256`（对称，签名和验签用同一个密钥），然后**用那把公开的公钥当 HMAC 密钥去签名**。

```
服务端的验签代码（有洞）：alg 说 HS256，我就用 HS256 + 我手里的密钥验
   服务端手里的"密钥"在 RS256 语境下 = 公钥（公开的！）
   攻击者也有这把公钥 => 他能造出服务端认可的签名
```

⚠️ 这个坑比 `alg=none` 隐蔽：系统看起来用了"更安全的非对称加密"，却因为**验签时算法可被令牌操纵**，让公钥这个"本该公开"的东西变成了伪造密钥。它和误用①同源：**`alg` 字段不可信。**

⚠️ 这一节是本篇最绕的地方，值得慢慢看。绕在于要同时记住两件事：RS256 里那把用来**验**签的钥匙是公开的（这没问题，它本来就该公开）；HS256 里那把用来**验**签的钥匙同时也能用来**签**（这也没问题，对称算法本来就这样）。两件事各自都对，凑到一起就出事了——**攻击者把一把"只能用来验"的钥匙，塞进了一个"验签钥匙也能签"的算法里。** 如果一遍没读懂，只带走一句：让令牌决定用什么算法，就是让攻击者决定你手里那把钥匙的用途。

## 四、误用③：根本没验签

最常见、也最朴素的一个：图省事，直接 base64 解开 payload 就用，压根没验签这一步。

```python
import hmac, hashlib, base64, json

def b64(d): return base64.urlsafe_b64encode(d).rstrip(b"=").decode()
def ub64(s): return base64.urlsafe_b64decode(s + "==")
SECRET = b"server-secret"

def sign(payload):
    h = b64(json.dumps({"alg":"HS256","typ":"JWT"}).encode())
    p = b64(json.dumps(payload).encode())
    sig = b64(hmac.new(SECRET, f"{h}.{p}".encode(), hashlib.sha256).digest())
    return f"{h}.{p}.{sig}"

# 误用②：直接 base64 解 payload 就信，不验签名
def read_no_verify(tok):
    return json.loads(ub64(tok.split(".")[1]))

# 正确：先用固定算法 + 密钥重算签名并比对，通过了才信 payload
def read_verified(tok):
    h, p, sig = tok.split(".")
    expect = b64(hmac.new(SECRET, f"{h}.{p}".encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(sig, expect):
        raise ValueError("签名不匹配，拒绝")
    return json.loads(ub64(p))

token = sign({"user":"alice","role":"user"})
# 攻击者把 payload 里的 role 改成 admin（不动签名）
h,p,s = token.split(".")
tampered = f'{h}.{b64(json.dumps({"user":"alice","role":"admin"}).encode())}.{s}'

print("不验签就读，看到的 role:", read_no_verify(tampered)["role"], " <- 被篡改的值被采信")
try:
    read_verified(tampered)
except ValueError as e:
    print("验签后:", e, "<- 篡改被挡住")
```

```
不验签就读，看到的 role: admin  <- 被篡改的值被采信
验签后: 签名不匹配，拒绝 <- 篡改被挡住
```

攻击者只是把 payload 里的 `role` 改成 `admin`、**签名那段原样不动**。不验签的代码看到的就是 `admin`。而正确的验签——用**固定算法 + 服务端密钥**重算签名再比对——立刻发现签名对不上，拒绝。

⭐ 注意正确做法的两个要点，都在对付前几节的教训：

```
① 算法在服务端【写死】，不读令牌里的 alg   —— 堵住误用①②
② 用 compare_digest 做时序恒定比较         —— 呼应第 7 篇
```

## 五、它出现过的地方

JWT 的这些坑常年出现在各类库和实现里，展开在[事件分析]({{< ref "/posts/security/web/incidents" >}})里：

```
2015 起   多个 JWT 库的 alg=none / 算法混淆   同一个「信任 alg 字段」的错误，被不同语言的库反复踩中
```

⭐ 值得记住的是：这些几乎从不是"密码学被破解"，而是**验证流程的逻辑漏洞**——签名算法本身没问题，是"要不要验、用什么验"被搞错了。这正是 W2 的共同主题：认证的失手大多不在算法，在流程。

## 六、防御

```
① 服务端写死验签算法               绝不根据令牌的 alg 字段选算法；显式拒绝 none
② payload 当明文对待               不放敏感信息（它只是编码，不是加密）
③ 一定验签，再读内容               先 verify 通过，才信任 payload 里的任何字段
④ 校验标准声明（claims）            exp 过期、iss 签发方、aud 受众，都要验
⑤ 想清楚撤销（承接第 8 篇）        JWT 无状态 => 短过期 + refresh，或加吊销名单
```

判断标准：**你的验签代码，算法是从哪来的？** 从令牌里读的 → 有洞；在服务端写死的 → 对。

## 七、这些防御的边界

**① 验签正确 ≠ 令牌不会被偷。** 本篇解决的是"篡改"，不是"窃取"。一个签名完好的令牌被 XSS/泄露偷走后照样能重放——那是第 8 篇的传输保护和撤销问题。

**② `exp` 能限制重放窗口，但无法主动撤销。** 令牌在过期前一直有效，这是无状态的固有代价（第 8 篇 §四）。需要"立即失效"就得引入服务端状态。

**③ 别自己实现 JWT。** 上面手写只为演示机制。生产中用维护良好的库，并**显式配置**允许的算法（别用"自动检测"），把 §六① 交给库去强制。

**关于时效**：JWT 的结构和这些误用的机制稳定不变。会变的是**各库的默认行为**——是否默认拒绝 `none`、是否要求显式指定算法，不同库不同版本差别很大，选型时要查该库该版本的默认与配置。

## 八、本篇小结

```
JWT = header.payload.signature，前两段是 base64 明文（能读能改），
安全全压在签名上。所有 JWT 漏洞 = "签名到底验没验、用什么验"。

⭐ 误用①：接受 alg=none —— 令牌自己说"别验我"，服务端信了
⭐ 误用②：算法混淆(HS/RS) —— 服务端按令牌的 alg 选算法，公钥被当成 HMAC 密钥
⭐ 误用③：根本没验签 —— 直接读 payload，篡改的 role=admin 被采信

正确验签两要点：算法在服务端【写死】(堵住①②) + compare_digest 比对
判断标准：你的验签算法是从令牌里读的，还是服务端写死的？

补充：payload 不是加密的别放密码；验 exp/iss/aud；撤销靠短过期+refresh。
```

### 思考题

1. 三个误用（none / 算法混淆 / 不验签）有一个共同的根。用一句话说出这个根，并说明"算法在服务端写死"为什么能同时堵住前两个。
2. 为什么说"JWT 的 payload 里不能放敏感信息"？如果确实需要在令牌里携带敏感数据，该怎么做？（提示：编码 vs 加密。）
3. 算法混淆里，公钥"本该公开"却成了伪造密钥。这说明"公开的东西"和"能用来验签的东西"混在一起有多危险。据此解释为什么对称和非对称的密钥绝不能共用一个配置位。
4. `exp`（过期）能限制被盗令牌的重放窗口，却不能主动撤销。把这一条和第 8 篇"你能否 1 秒内让全部会话失效"对照，JWT 要满足那个标准得付出什么？
5. 有人用 JWT 存购物车（无害数据），觉得不验签也无所谓。这个判断在什么情况下会翻车？（提示：这个"无害"令牌会不会被同一套代码当认证用。）
6. §六 说"别自己实现 JWT，用库并显式配置算法"。为什么"显式配置算法"比"用库的自动检测"更重要——把它和误用①②联系起来。
7. 把 JWT 的"验签"和第 6 篇反序列化的"先验签再反序列化"放一起：两者都强调"验证要在信任之前"。它们防的是不是同一类攻击者能力？

> **相关**：[第 8 篇：会话与令牌]({{< ref "08-session-tokens.md" >}}) · [第 6 篇：不安全反序列化]({{< ref "06-insecure-deserialization.md" >}}) · [Web 安全机制篇]({{< ref "/posts/security/web" >}}) · [事件分析]({{< ref "/posts/security/web/incidents" >}})
