---
title: "第 18 篇：依赖投毒——你装的包，不一定是作者写的包"
date: 2026-09-01
weight: 18
tags: ["Web 安全"]
draft: false
summary: "W6 开篇。你的代码里，自己写的可能只占几个百分点，其余全是依赖——而每一个依赖都是一条你没审过的代码进入你系统的通道。这一篇讲攻击者往这条通道里塞东西的几条路：抢注、依赖混淆、账号接管、维护者移交。其中依赖混淆用真实的 pip 复现：两个源里放同名包，pip 自己跳过内网源选走了公共源那个高版本。"
showToc: true
tocOpen: false
---

| | |
|---|---|
| **失效的假设** | "我 import 的这个包，就是那个作者写的、我以为的那个包" |
| **所属组** | W6 · 供应链 |
| **视角转变** | 前 17 篇防"别人攻击你的代码"；W6 防"你信任的代码本身有毒" |
| **复现环境** | Python 3 标准库，无外部依赖 |

## 一、你的代码里，自己写的是少数

昨晚你的 CI 跑了一次 `npm install`，和过去三百次没有任何不同：没人改配置，没人加依赖，流水线全绿。

今天早上，你们的部署密钥出现在了一个陌生的服务器上。

打开这个项目的依赖树，你会看到几百上千个包。你亲手写的代码，可能只占最终跑起来的一小部分，其余全是**别人写的、你没读过、却拥有和你代码同等权限**的东西。

这就是供应链安全的前提，也是它和前面 17 篇的根本区别：

```
W1–W5   攻击者从【外部】攻击你的代码（注入、越权、解析）
W6      攻击者让【你信任并引入的代码本身】带毒
        —— 它一旦装进来，就在你的进程里，权限和你自己的代码一样大
```

⭐ 关键的心理转变：**一次 `npm install` / `pip install`，是在往你的系统里引入一批你没审过的代码，并授予它完全的运行权限。** 攻击者要做的，不是攻破你，是让你**自愿装上**他的东西。下面是他常走的几条路。

## 二、路径一：名字上做手脚

最省事的攻击，是让你**装错包**——你以为装的是 A，实际装的是攻击者的 A'。

```
抢注(typosquatting)   注册一个和热门包只差一个字母的名字（reqeusts vs requests）
                      你手一抖打错，就装了它
依赖混淆(confusion)   你的私有包名，被攻击者在【公共源】上抢注，且版本号更高
```

依赖混淆特别隐蔽，因为你**没打错任何字**——是装包器自己选错了源。这件事可以用**真的 pip** 演一遍：造两个本地"源"，各放一个同名包，然后让 pip 自己挑。

```python
import subprocess, tempfile, os, zipfile, sys

def make_wheel(dirpath, name, version, marker):
    """造一个最小的 wheel 放进某个'源'目录"""
    d = f"{name.replace('-','_')}-{version}"
    p = os.path.join(dirpath, f"{d}-py3-none-any.whl")
    with zipfile.ZipFile(p, "w") as z:
        z.writestr(f"{d}.dist-info/METADATA",
                   f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n")
        z.writestr(f"{d}.dist-info/WHEEL",
                   "Wheel-Version: 1.0\nGenerator: demo\nRoot-Is-Purelib: true\nTag: py3-none-any\n")
        z.writestr(f"{d}.dist-info/RECORD", "")
        z.writestr(f"{name.replace('-','_')}/__init__.py", f"WHO = {marker!r}\n")

root = tempfile.mkdtemp()
internal = os.path.join(root, "internal"); os.makedirs(internal)
public   = os.path.join(root, "public");   os.makedirs(public)
make_wheel(internal, "demo-internal-utils", "1.2.0",  "内网源上你自己的包")
make_wheel(public,   "demo-internal-utils", "99.0.0", "公共源上攻击者抢注的同名包")

out = os.path.join(root, "out")
subprocess.run([sys.executable, "-m", "pip", "download", "--no-deps", "-q",
                "--no-index", "-f", internal, "-f", public, "-d", out,
                "demo-internal-utils"], check=True)
print("你要装的是内网那个 1.2.0；pip 同时能看到两个源。")
print("pip 实际选走的是   :", os.listdir(out)[0])
```

```
你要装的是内网那个 1.2.0；pip 同时能看到两个源。
pip 实际选走的是   : demo_internal_utils-99.0.0-py3-none-any.whl
```

**跳过内网源、选走公共源那个 99.0.0 的，不是我写的代码，是 pip 自己。** 它没做错任何事：它的默认策略就是"从我能看到的所有源里，挑版本号最高的那个"——这在正常场景下完全合理，甚至是你想要的。

```
你的私有包            demo-internal-utils  1.2.0    只发布在内网源
攻击者在公共源抢注     demo-internal-utils  99.0.0   同名，版本号更高
装包器的默认策略      "所有源里挑版本号最高的"  =>  装了攻击者那个
```

攻击者怎么知道 `demo-internal-utils` 这个名字？它可能出现在你泄露的 `package.json`、一段报错栈、一个前端打包产物、一份公开的招聘 JD 里。**私有包名不是秘密**，而这套攻击只需要名字。

⭐ 根因是那条失效的假设：**"包名 = 我想要的那个包"。** 名字不是身份——一个名字可以对应多个源、多个发布者，而默认解析规则里**根本没有"哪个源更可信"这个概念，只有"哪个版本号更大"**。

修复是把私有包**锁定到可信源**（私有作用域/命名空间、或显式指定索引且禁止回落到公共源），不再跨源比版本——这又是"默认拒绝 + 白名单"（第 12/14 篇）在依赖解析上的化身。

## 三、路径二：占住名字之后，动里面的代码

就算你装的是"对的包"，它也可能在某次更新后变了：

```
账号接管       维护者的账号被撞库/钓鱼攻破，攻击者发布一个带后门的新版本
维护者移交     维护者把仓库转给"热心接手的人"，对方几个月后投毒
               （event-stream 2018 就是这样：热心贡献者接手后植入了窃密代码）
构建产物替换   源码干净，但发布到源上的【构建产物】被替换（源码和产物不一致）
```

这些的共同点是：**你信任的是"这个包"，但"这个包"背后的人和字节会变**，而你的信任是一次性给出、长期有效的。

### 打个比方

`npm install` 像是给一群素未谋面的人发了你家钥匙，并且说"进来吧，冰箱随便开"。你审过其中三五个人，剩下几百个是他们各自带来的朋友。

而"锁文件"是给每把钥匙拍了张照：下次开门的人长得不一样，门就不开。

## 四、为什么"装个包"本身就危险

很多人以为"装了但没 `import`、没调用，就没事"。**错。** 装包这个动作本身，在多数生态里就会执行包带来的代码。

下面这段用真的 pip 装一个包。这个包**没有任何恶意函数**、你也**一次都不会 import 它**——它只是自带了一个"构建后端"，而 pip 装包时会 import 并调用那个后端：

```python
import subprocess, tempfile, os, sys, textwrap

pkg = tempfile.mkdtemp()
proof = os.path.join(tempfile.mkdtemp(), "attacker-was-here.txt")

# 这个包的"构建后端"就是包自己带的一个 .py。装它的时候，pip 会 import
# 这个文件并调用里面的函数 —— 模块顶层那一行，就是后门站的位置。
open(os.path.join(pkg, "evil_backend.py"), "w").write(textwrap.dedent(f"""
    import os, zipfile
    open({proof!r}, "w").write("装包过程执行了我的代码")     # <- 后门在这里

    def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
        n = "harmless_looking-1.0-py3-none-any.whl"
        with zipfile.ZipFile(os.path.join(wheel_directory, n), "w") as z:
            d = "harmless_looking-1.0.dist-info"
            z.writestr(d + "/METADATA",
                       "Metadata-Version: 2.1\\nName: harmless-looking\\nVersion: 1.0\\n")
            z.writestr(d + "/WHEEL",
                       "Wheel-Version: 1.0\\nGenerator: x\\nRoot-Is-Purelib: true\\nTag: py3-none-any\\n")
            z.writestr(d + "/RECORD", "")
            z.writestr("harmless_looking/__init__.py", "")
        return n

    def build_sdist(sdist_directory, config_settings=None): raise NotImplementedError
    def get_requires_for_build_wheel(config_settings=None): return []
"""))
open(os.path.join(pkg, "pyproject.toml"), "w").write(
    '[build-system]\nrequires = []\nbackend-path = ["."]\nbuild-backend = "evil_backend"\n')

print("装之前，那个文件存在吗:", os.path.exists(proof))
r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--no-index",
                    "--target", tempfile.mkdtemp(), pkg], capture_output=True, text=True)
print("pip 装完了吗          :", r.returncode == 0)
print("装之后，那个文件存在吗:", os.path.exists(proof))
print("文件内容              :", open(proof).read().strip())
print("我 import 过这个包吗   :", False)
```

```
装之前，那个文件存在吗: False
pip 装完了吗          : True
装之后，那个文件存在吗: True
文件内容              : 装包过程执行了我的代码
我 import 过这个包吗   : False
```

最后两行是重点：**磁盘上多出了一个文件，而我从头到尾没有 import 过这个包。** 写这个文件的是 pip——它按规范 import 了包自带的构建后端并调用它，包作者的代码就在那一刻跑了起来，用的是**你的权限**：在你的开发机上是你，在 CI 上是那台机器的全部凭据。

⚠️ 这里那行后门写在**模块顶层**，也就是说它在 `import` 那一瞬间就执行了，`build_wheel` 有没有被调用都无所谓。把这个包改成"装到一半失败"，文件照样会出现——**"装失败了应该没事吧"这个安慰是不成立的。**

各生态的入口不同，性质一样：

```
Python   PEP 517 构建后端 / sdist 里的 setup.py
Node     package.json 的 preinstall / install / postinstall 脚本
Ruby     gem 的 extconf.rb 扩展构建
```

⚠️ 如果你的第一反应是"这也太夸张了，装个包而已"——那正是这一节要拆掉的直觉。装包在你脑子里是**下载**（一个读操作），而在包管理器那里是**下载 + 在你机器上跑一段作者提供的代码**。这两件事的风险差着数量级，而命令行上看起来一模一样。

⭐ "安装 = 执行"这件事，和第 6 篇"反序列化 = 执行"是**同一台机器**：**一个你以为无害的动作（装包 / 还原对象），其实携带并触发了代码。** 所以恶意包不需要你调用它的任何函数——`install` 那一下就得手了。

防线是**锁文件（lockfile）：把每个包的哈希钉死**。下次安装时哈希对不上——不管是源被投毒还是传输被篡改——直接拒绝。这和第 16 篇"用事实核验声称"、第 9 篇"验签再信任"是同一招：**用一个钉死的哈希，证明"这次装的字节 = 上次审过的字节"。**

⚠️ 但注意锁文件挡的是**字节变了**这一种情况。第一次就把毒锁进来，或者你主动升级到了投毒版本，哈希只会忠实地锁住那个毒——见 §七①。

## 五、它出现过的地方

展开在[事件分析]({{< ref "/posts/security/web/incidents" >}})里：

```
2018      event-stream                 维护者把仓库移交后，接手者植入窃密代码
2024.03   xz-utils / CVE-2024-3094     长期社会工程取得信任，后门只出现在发布包里
```

## 六、防御

```
① 锁文件 + 哈希校验           钉死每个依赖的确切版本和哈希，装的必须和审过的一致
② 私有包锁定到可信源          防依赖混淆：私有作用域/命名空间，绝不跨源比版本
③ 关掉/审计安装脚本           CI 里禁用 postinstall，或只允许白名单（装 ≠ 让它随便跑）
④ 依赖最小化 + 定期审计       每个依赖都是攻击面；能不加就不加，加了要盯着
⑤ 更新要看 diff，不盲目升级    版本跳变尤其是维护者变更后，看变更再升
```

判断标准：**你现在装的这个包的字节，和你上次审过的是同一份吗？谁能证明？** 答案是"锁文件里的哈希"——没有它，你无法回答。

## 七、这些防御的边界

**① 锁文件保证"一致"，不保证"干净"。** 它确保你每次装的都是同一份字节，但如果你**第一次**锁进来的就是投毒版本，哈希只会忠实地锁住那个毒。锁文件防篡改和源投毒，不替代"引入时的审查"。

**② 哈希校验挡不住"合法发布的恶意更新"。** 维护者账号被接管后发布的新版本，有正当的签名和新哈希——你主动升级并更新锁文件时，毒就进来了。所以 §六⑤"更新看 diff"和锁文件是互补的两道。

**③ 传递依赖是盲区。** 你直接依赖 10 个包，它们可能拉进来上千个间接依赖。你审得过来直接的，审不过来全部。这需要工具化的依赖扫描和 SBOM（软件物料清单），而不是人眼。

**关于时效**：供应链攻击的路径（抢注、混淆、接管、移交）稳定。会变的是**各生态的默认防护**——是否默认校验哈希、是否默认执行安装脚本、私有源的默认优先级，不同包管理器不同版本差别很大，落地要查你用的那个工具的当前默认。

## 八、本篇小结

```
你的代码里自己写的是少数，其余是依赖 —— 每个依赖都拥有和你代码同等的权限。
W6 的视角：攻击者不攻破你，而是让你【自愿装上】他的东西。

攻击路径：
   名字层  抢注(typosquatting) / 依赖混淆(私有名被公共源抢发高版本)
   代码层  账号接管 / 维护者移交(event-stream) / 构建产物替换
⭐ 失效的假设："包名 = 我想要的那个包" —— 名字不是身份
⭐ "装个包" = "执行代码"（很多生态装包即跑 postinstall）
   和第 6 篇"反序列化=执行"同构：无害动作携带并触发了代码

防御：锁文件+哈希(装的=审过的) · 私有包锁定可信源 · 关安装脚本 · 依赖最小化 · 升级看 diff
边界：锁文件保证"一致"不保证"干净"；传递依赖是人眼盯不住的盲区。
```

### 思考题

1. 依赖混淆里"你一个字都没打错"，为什么还是装错了包？和 typosquatting 的"打错字"相比，哪个更难靠"小心一点"避免？
2. §四 说"安装 = 执行"和第 6 篇"反序列化 = 执行"同构。把第 6 篇的"换成纯数据格式"这个根治思路，类比到依赖安装上，对应什么做法？
3. 锁文件"保证一致不保证干净"（§七①）。举一个"锁文件忠实地锁住了毒"的场景。这说明锁文件应该配合哪一道防御才完整？
4. 为什么"CI 里禁用 postinstall"是高价值的防御？把它和第 3 篇/第 16 篇"关掉用不到的功能"这个反复出现的主题联系起来。
5. §七③ 说传递依赖是盲区。你直接审查了所有直接依赖，一个间接依赖仍被投毒。这在防御上要求什么工具化能力？为什么人眼不够？
6. 维护者账号被接管后发的恶意版本"有正当签名和新哈希"。这对"签名/哈希能证明什么"意味着什么？它证明了"字节没被中途篡改"，但没证明什么？
7. 把 W6 的"你信任的代码本身有毒"和 W1–W5"外部攻击你的代码"对比：防御的着力点有什么根本不同？为什么说供应链是"信任的传递"问题而不是"输入校验"问题？

> **相关**：[第 6 篇：不安全反序列化]({{< ref "06-insecure-deserialization.md" >}}) · [第 19 篇：构建与 CI]({{< ref "19-build-ci.md" >}}) · [Web 安全机制篇]({{< ref "/posts/security/web" >}}) · [事件分析]({{< ref "/posts/security/web/incidents" >}})
