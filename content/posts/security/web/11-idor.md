---
title: "第 11 篇：横向越权（IDOR）——改个数字看别人的数据"
date: 2026-09-01
weight: 11
tags: ["Web 安全"]
draft: false
summary: "IDOR 是最不起眼也最常见的漏洞：接口按 id 取资源，却没检查这个 id 是不是当前用户的。把 URL 里的 1001 改成 1002，就看到了别人的订单。这一篇用十几行说清它的机制，以及为什么真正的修复不是'把 id 换成猜不到的 UUID'，而是'把归属校验写进每一次数据访问'。"
showToc: true
tocOpen: false
---

| | |
|---|---|
| **失效的假设** | "他手上没有别人的 id，所以看不到别人的数据" |
| **所属组** | W3 · 访问控制 |
| **别名** | IDOR（不安全的直接对象引用）、横向越权、BOLA（API 场景） |
| **复现环境** | Python 3 标准库，无外部依赖 |

## 一、一个改数字就能得手的漏洞

你登录后看自己的订单，地址栏是 `/orders/1001`。

你把 `1001` 改成 `1002`，回车。

前面十篇的漏洞多少都有点技术门槛。IDOR 没有——它可能是整份清单里最好利用的一个，一个能改 URL 的普通用户就能做。

场景：你登录后访问自己的订单，地址栏是 `/orders/1001`。你把 `1001` 改成 `1002`，回车。

```python
import sqlite3, threading, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer

db = sqlite3.connect(":memory:", check_same_thread=False)
db.executescript("""
CREATE TABLE orders(id INTEGER PRIMARY KEY, owner TEXT, total INT);
INSERT INTO orders VALUES (1001,'alice',42), (1002,'bob',999);
""")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 会话：谁在请求，由 cookie 决定（这里简化成 header）
        user = self.headers.get("X-User")
        oid  = self.path.rsplit("/", 1)[-1]
        if self.path.startswith("/vuln/"):
            row = db.execute("SELECT owner,total FROM orders WHERE id=?", (oid,)).fetchone()
        else:                                    # /safe/ ：归属是查询的一部分
            row = db.execute("SELECT owner,total FROM orders WHERE id=? AND owner=?",
                             (oid, user)).fetchone()
        if row is None:
            self.send_response(403); self.end_headers(); self.wfile.write(b"denied")
        else:
            self.send_response(200); self.end_headers()
            self.wfile.write(f"owner={row[0]} total={row[1]}".encode())
    def log_message(self, *a): pass

srv = HTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
port = srv.server_address[1]

def request(path):
    """alice 的浏览器发出的真实 HTTP 请求"""
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", headers={"X-User": "alice"})
    try:
        return f"200 {urllib.request.urlopen(req).read().decode()}"
    except urllib.error.HTTPError as e:
        return f"{e.code} {e.read().decode()}"

print("alice 访问自己的订单   /vuln/1001 ->", request("/vuln/1001"))
print("alice 把数字改成 1002  /vuln/1002 ->", request("/vuln/1002"))
print("同一个改动，加了归属校验 /safe/1002 ->", request("/safe/1002"))
print("她自己的那笔仍然正常    /safe/1001 ->", request("/safe/1001"))
srv.shutdown()
```

```
alice 访问自己的订单   /vuln/1001 -> 200 owner=alice total=42
alice 把数字改成 1002  /vuln/1002 -> 200 owner=bob total=999
同一个改动，加了归属校验 /safe/1002 -> 403 denied
她自己的那笔仍然正常    /safe/1001 -> 200 owner=alice total=42
```

`alice` 看到了 `bob` 的订单，**只因为她把地址栏里的数字加了一。**

这就是 IDOR（Insecure Direct Object Reference）：接口拿到一个指向对象的引用（订单号、用户 id、文件名），**直接就去取了那个对象，中间没有一步问"这个对象是不是该给这个人看"。**

它也叫**横向越权**——攻击者和受害者是**同级**用户（都是普通用户），攻击者横着移动去访问平级的别人的数据。（下一篇讲纵向越权：普通用户往上够管理员的权限。）

## 二、为什么它这么普遍

因为写出这个洞的代码，**读起来完全正常**：

```
order = db.query("SELECT * FROM orders WHERE id = ?", order_id)   # 参数化了！
return order
```

这段代码没有 SQL 注入（参数化做对了），没有任何"危险"的样子。它唯一缺的，是一句**"这个 order 属于当前用户吗"**。开发者的注意力都在"把数据取对"，而**访问控制是另一个维度的事**，很容易在写业务逻辑时整个地忘掉。

⭐ 根本原因是那条失效的假设：**以为"用户拿不到别人的 id"就等于安全。** 可 id 往往是顺序的、出现在 URL 里、出现在别人分享的链接里、能被枚举。**"猜不到"从来不是访问控制**——它顶多是让攻击慢一点。

### 打个比方

这就像一家银行的保管库，每个保险箱上写着编号，柜员按你报的号去取箱子——**但从不核对这个箱子是不是你的**。

发现问题后，把编号从"1001、1002"换成一串随机字符，并不能解决什么：柜员依然不核对。只要你说得出编号，他就把箱子递给你。

## 三、一个常见的假修复：把 id 换成 UUID

⚠️ 这一节的结论很多人第一次听会不服气——UUID 明明"更安全"了。它确实提高了成本，但请盯住一个区别：**它改变的是"攻击者要多久才能找到别人的 id"，没有改变"找到之后会发生什么"。** 前者是运气，后者才是权限。

发现 IDOR 后，一个很自然的反应是："那我把顺序的 `1001` 换成猜不到的 UUID，不就没法枚举了？"

这**治标不治本**，理由正是上一节那句话的延伸：

```
换 UUID 之后，攻击者还是能通过这些途径拿到别人的 id：
   · 别人分享的链接、转发的邮件、浏览器历史、日志
   · 一个接口返回的对象里嵌着另一个对象的 id
   · 引荐来源(Referer)泄露
一旦拿到，你的接口【照样】把不属于他的数据交出去 —— 因为洞根本不在 id 好不好猜。
```

⚠️ UUID 是好东西（能防枚举、减少信息泄露），但它是**纵深**，不是**修复**。把"难以猜测"当成访问控制，是 IDOR 反复出现的一个主因。真正的洞是"取数据时没校验归属"，那句校验不补上，id 再随机也没用。

## 四、真正的修复：把归属写进每一次访问

看回第一节的 `get_order_ok`：它把"归属"变成了取数据的**必要条件**——要么在查询里就带上 `WHERE owner = 当前用户`，要么取出后立刻校验归属，不匹配就拒绝。

```
错的心智模型                     对的心智模型
------------------------------------------------------
先按 id 取到对象，"应该没问题"     取对象时，"当前用户有权访问它"就是查询的一部分
                                默认拒绝：证明不了归属，就不返回
```

这和第 2 篇 SQL 那句"防护贴在拼接点上"是同构的：**访问控制必须贴在每一次数据访问上，而数据访问点很多，漏一个就是一个 IDOR。** 所以靠谱的做法不是"记得在每个接口加校验"，而是把校验**下沉到数据层**——让"取数据"这个动作本身天然带着"谁在取"。

```
可扩展的做法：
  · 查询层强制带租户/属主过滤（每个查询都自动 AND owner = 当前用户）
  · 或用统一的授权中间件：所有对象访问都过一遍"主体能否访问客体"的检查
  · 集中式策略，而不是每个 handler 各写各的 if
```

> 这一类没有单一的标志性公开事件，它以大量分散的个案存在；有技术细节的会收进[事件分析]({{< ref "/posts/security/web/incidents" >}})。

⭐ 值得注意的是它在 **API 时代更严重**：前后端分离后，每个数据对象几乎都有一个直接的 API 端点（`GET /api/users/{id}`），越权面比"页面时代"大得多。OWASP 专门把它列为 API 安全的头号问题（BOLA）。

## 五、防御

```
① 每一次对象访问都校验归属        取数据 = 取"这个用户有权取的数据"，默认拒绝
② 把校验下沉到数据/授权层         别指望每个 handler 记得写 if；集中强制
③ UUID / 随机 id 作为纵深         防枚举、减泄露，但【不替代】①
④ 写越权测试                     "用 A 的会话去访问 B 的资源，必须 403"，进 CI
```

判断标准：**把请求里的 id 换成别人的，你的接口会拒绝吗？** 这个测试该对每一个"按 id 取数据"的端点都跑一遍。

## 六、这些防御的边界

**① 归属不总是"owner 字段"那么简单。** 共享、团队、组织层级、被授权代理——现实的访问规则可能很复杂。越复杂，越要用集中式策略而不是散落的 if，否则一定漏。

**② 校验下沉到数据层，也要防"绕过数据层"的路径。** 批量导出、报表、后台任务、GraphQL 的嵌套解析，都可能绕开你精心设计的单对象校验。每一条数据出口都算访问点。

**③ IDOR 和纵向越权是两个维度，别混。** 这一篇解决"平级看平级"。就算归属校验做全了，"普通用户能不能调管理员接口"是**另一道**独立的检查——下一篇。

**关于时效**：IDOR 的机制不随技术变，是纯粹的逻辑漏洞。会变的是它的**高发位置**（从页面参数，到 REST API，到 GraphQL），但"取数据要校验归属"这条永远成立。

## 七、本篇小结

```
IDOR / 横向越权：接口按 id 取对象，却没问"这个对象该给这个人吗"。
改个数字就看到别人的数据 —— 攻击者和受害者是同级用户。

⭐ 失效的假设："用户拿不到别人的 id" = 安全
   真相：id 会从链接/日志/别的接口泄露，"猜不到"不是访问控制
⚠️ 假修复：把顺序 id 换成 UUID —— 那是纵深(防枚举)，不是修复；洞在"没校验归属"
⭐ 真修复：把归属校验写进【每一次】数据访问，默认拒绝，并下沉到数据/授权层
   （和"防护贴在拼接点上"同构：访问点很多，漏一个就是一个 IDOR）

判断标准：把请求里的 id 换成别人的，接口会拒绝吗？把这个做成 CI 里的越权测试。
```

### 思考题

1. §三 说"换 UUID 治标不治本"。给出至少三条"UUID 也会泄露给攻击者"的途径，说明为什么洞不在 id 好不好猜。
2. §二 那段有洞代码"读起来完全正常"，还参数化了。用第 2 篇的语言说明：SQL 注入和 IDOR 是两个正交的维度——一段代码可以没有注入却有 IDOR，反之亦然吗？
3. 为什么把归属校验"下沉到数据层"比"每个 handler 写 if"更可靠？和第 5 篇"用框架自动上下文编码"是不是同一个思路？
4. §七② 说批量导出/报表可能绕过单对象校验。设计一个场景：单个 `GET /order/{id}` 都校验了归属，但 `GET /orders/export` 泄露了全量。根因是什么？
5. IDOR 的 CI 测试是"用 A 的会话访问 B 的资源应 403"。为什么这个测试很少有人写？它和普通功能测试的思路差别在哪？（提示：功能测试验"该能做的能做"，越权测试验"不该能做的不能做"。）
6. GraphQL 里一次查询能嵌套取多层对象。为什么它让 IDOR 更难防？集中式授权在这里要检查到哪一层？
7. 把 IDOR 和下一篇的纵向越权预先对比：同样是"越权"，一个横一个纵，防御手段能不能用同一套集中式策略覆盖？各自校验的是"主体和客体"的什么关系？

> **相关**：[第 2 篇：SQL 注入]({{< ref "02-sql-injection.md" >}}) · [第 12 篇：纵向越权]({{< ref "12-privilege-escalation.md" >}}) · [Web 安全机制篇]({{< ref "/posts/security/web" >}}) · [事件分析]({{< ref "/posts/security/web/incidents" >}})
