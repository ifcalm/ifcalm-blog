---
title: "1273 个核心英语动词与句子模板"
date: 2026-05-29
tags: ["英语学习", "产品设计"]
draft: false
summary: "1273 个核心英语动词与句子模板"
showToc: true
tocOpen: false
---

这份文档适合用来训练“通过动词理解英语句子结构”的能力。

核心思路：

> 句子描述一个事件，动词是事件的核心。  
> 学动词时，不要只背中文意思，而要记住它需要几个参数，以及这些参数如何排列。

在下面的模板中：

```text
A = 动作发出者，通常是主语
B = 动作对象，通常是宾语
C = 补充结果、状态、目标或接收者
S = 一个完整小句，例如 that + 主语 + 动词
```

例如：

```text
A uses B.
I use Docker.

A sends B to C.
I sent the file to him.

A makes B C.
This change makes the system stable.
```

---

## 一、核心句子模板速查

| 模板 | 结构 | 含义 | 示例 |
|---|---|---|---|
| T1 | A + vi. | A 自己发生动作 | The server crashed. |
| T2 | A + vt. + B | A 对 B 做动作 | I fixed the bug. |
| T3 | A + vt. + B + to C | A 把 B 给/传到 C | I sent the file to him. |
| T4 | A + vt. + B + C | A 使 B 变成 C，或给 B 某物 | This made me happy. |
| T5 | A + link verb + C | A 是/变得/看起来 C | The service is stable. |
| T6 | A + verb + that S | A 认为/说明/确认某件事 | I think that it works. |
| T7 | A + verb + to do B | A 打算/需要/决定做某事 | We plan to deploy it. |
| T8 | A + verb + doing B | A 避免/喜欢/继续做某事 | Avoid storing secrets. |
| T9 | A + verb + prep + B | 动词与介词构成固定关系 | This depends on Redis. |
| T10 | A + phrasal verb + B | 短语动词整体表达动作 | We figured out the cause. |

---

## 二、1049 个核心动词主表（6 大场景分类）

> 以下按使用场景分为 6 组，每组内部按字母排序。短语动词独立成章。


### 一、核心基础：动作与状态

> 构成英语骨架的最高频动词：存在、运动、变化、感官、基本操作。（519 个）

| No. | Verb | 中文含义 | 核心句子模板 | 示例 | 中文例句 |
|---:|---|---|---|---|---|
| 1 | abandon | 放弃；抛弃 | `A abandons B.` | We abandoned the old pipeline in favor of GitHub Actions. | 我们放弃了旧的流水线，改用 GitHub Actions。 |
| 2 | absorb | 承受；缓冲（流量冲击） | `A absorbs B.` | The CDN absorbs the traffic spike without breaking. | CDN 在不崩溃的情况下吸收了流量高峰。 |
| 3 | acquire | 获得；收购 | `A acquires B.` | The service acquires a lock before writing. | 服务在写入前先获取锁。 |
| 4 | add | 添加 | `A adds B to C.` | Add this user to the group. | 把这个用户添加到组里。 |
| 5 | adjust | 调整；适应 | `A adjusts B.` | Adjust the heap size to reduce GC pauses. | 调整堆大小以减少 GC 暂停。 |
| 6 | adopt | 采纳；采用 | `A adopts B.` | The team adopted a new branching strategy. | 团队采用了新的分支策略。 |
| 7 | advance | 推进；提升 | `A advances B.` | Each commit advances the project incrementally. | 每次提交递增地推进项目。 |
| 8 | affect | 影响；作用于 | `A affects B.` | This config change affects all production instances. | 这个配置变更影响所有生产实例。 |
| 9 | afford | 负担得起；能... | `A can afford B. / A can afford to do B.` | We can't afford any downtime during peak hours. | 高峰时段我们承受不起任何宕机。 |
| 10 | aid | 辅助；帮助 | `A aids B in doing C.` | Static analysis aids developers in catching bugs early. | 静态分析帮助开发者早期捕获缺陷。 |
| 11 | allow | 允许 | `A allows B to do C.` | The policy allows users to upload files. | 策略允许用户上传文件。 |
| 12 | alter | 改变；修改 | `A alters B.` | The hotfix alters the database schema without downtime. | 热修复在不中断服务的情况下修改数据库模式。 |
| 13 | analyze | 分析 | `A analyzes B.` | We analyzed the logs. | 我们分析了日志。 |
| 14 | answer | 回答 | `A answers B.` | She answered the customer's question. | 她回答了客户的问题。 |
| 15 | anticipate | 预期；预料 | `A anticipates B. / A anticipates that S.` | We anticipate a traffic spike during the event. | 我们预期活动期间会有流量高峰。 |
| 16 | appear | 似乎；出现 | `A appears C. / A appears to do B.` | The error appears after deployment. | 这个错误在部署后出现。 |
| 17 | apply | 应用；申请 | `A applies B to C.` | Apply this patch to the server. | 把这个补丁应用到服务器。 |
| 18 | arise | 出现；产生 | `A arises. / A arises from B.` | Problems always arise during integration testing. | 集成测试阶段总会出现问题。 |
| 19 | arrive | 到达；抵达 | `A arrives. / A arrives at B.` | The response arrived within 200ms. | 响应在 200 毫秒内到达。 |
| 20 | ask | 询问；请求 | `A asks B. / A asks B to do C.` | I asked him to review the code. | 我请他评审代码。 |
| 21 | assist | 协助 | `A assists B with C.` | I assisted the team with testing. | 我协助团队测试。 |
| 22 | attempt | 尝试；企图 | `A attempts B. / A attempts to do B.` | The server attempts to reconnect every 5 seconds. | 服务器每 5 秒尝试重连一次。 |
| 23 | attract | 吸引 | `A attracts B.` | Good content attracts users. | 优质内容吸引用户。 |
| 24 | avoid | 避免 | `A avoids B. / A avoids doing B.` | Avoid storing secrets in code. | 避免把密钥存进代码。 |
| 25 | await | 等待（异步等待） | `A awaits B.` | The async function awaits the API response. | 异步函数等待 API 响应。 |
| 26 | balance | 平衡 | `A balances B.` | The load balancer balances traffic. | 负载均衡器平衡流量。 |
| 27 | ban | 封禁 | `A bans B.` | The firewall bans IPs after three failed attempts. | 防火墙在三次失败尝试后封禁 IP。 |
| 28 | be | 是；存在 | `A is B. / A is C.` | The service is unavailable. | 服务不可用。 |
| 29 | bear | 承受；忍受 | `A bears B.` | The index bears the load of heavy read traffic. | 索引承受着大量读流量的负载。 |
| 30 | beat | 打败；跳动；超越 | `A beats B.` | The new index beat the old one by 10x in benchmarks. | 新索引在基准测试中以 10 倍优势打败了旧的。 |
| 31 | become | 变成 | `A becomes C.` | The service became unstable. | 服务变得不稳定。 |
| 32 | begin | 开始 | `A begins. / A begins to do B.` | The task begins after approval. | 任务在审批后开始。 |
| 33 | behave | 行为；表现 | `A behaves. / A behaves like B.` | The service behaves differently under load. | 服务在负载下表现不同。 |
| 34 | belong | 属于 | `A belongs to B.` | This config belongs in the environment variables. | 这个配置属于环境变量。 |
| 35 | bend | 弯曲；改变规则 | `A bends B.` | Don't bend the coding standards just to ship faster. | 别为了赶发布而放宽编码规范。 |
| 36 | benefit | 受益；得益于 | `A benefits from B.` | The team benefits from pair programming. | 团队从结队编程中受益。 |
| 37 | bind | 绑定 | `A binds B to C.` | Bind the port to localhost. | 把端口绑定到本机。 |
| 38 | bite | 咬；反噬 | `A bites B. / A bites back.` | Tech debt always bites back at the worst time. | 技术债总在最糟的时候反咬一口。 |
| 39 | block | 阻止 | `A blocks B.` | The rule blocks unsafe requests. | 规则阻止不安全请求。 |
| 40 | blow | 吹；爆炸 | `A blows B. / A blows up.` | A typo in the config blew up the pipeline. | 配置里的一个拼写错误炸掉了流水线。 |
| 41 | boost | 提升；加速 | `A boosts B.` | Indexing boosted the query performance by 10x. | 索引将查询性能提升了 10 倍。 |
| 42 | borrow | 借入 | `A borrows B from C.` | The code borrows ideas from this library. | 这段代码借鉴了该库的思路。 |
| 43 | bow | 鞠躬；屈服；低头 | `A bows to B.` | The team bowed to pressure and cut scope. | 团队迫于压力砍了范围。 |
| 44 | brainstorm | 头脑风暴 | `A brainstorms B.` | The team brainstormed solutions for the latency issue. | 团队头脑风暴了延迟问题的解决方案。 |
| 45 | break | 破坏；中断 | `A breaks B.` | The change broke compatibility. | 这个改动破坏了兼容性。 |
| 46 | bring | 带来 | `A brings B to C.` | This change brings better performance. | 这个改动带来更好的性能。 |
| 47 | burn | 燃烧；烧毁；耗尽 | `A burns B. / A burns out.` | Don't burn yourself out before the launch. | 别在发布前把自己累垮。 |
| 48 | bury | 掩埋；隐藏；埋头于 | `A buries B in C.` | The critical alert was buried in a flood of warnings. | 关键告警被淹没在警告洪流中。 |
| 49 | buy | 购买 | `A buys B.` | The company bought new servers. | 公司购买了新服务器。 |
| 50 | calculate | 计算 | `A calculates B.` | The system calculates the total price. | 系统计算总价。 |
| 51 | call | 调用；打电话 | `A calls B.` | The client calls the API. | 客户端调用接口。 |
| 52 | capture | 捕获；捕捉 | `A captures B.` | The SDK captures all unhandled exceptions. | SDK 捕获所有未处理的异常。 |
| 53 | carry | 携带；承载 | `A carries B.` | The request carries a token. | 请求携带一个令牌。 |
| 54 | catch | 捕获；抓住 | `A catches B.` | The handler catches the exception. | 处理器捕获异常。 |
| 55 | cause | 导致；引起 | `A causes B. / A causes B to do C.` | The bug caused data loss. | 这个缺陷导致了数据丢失。 |
| 56 | cease | 停止；终止 | `A ceases. / A ceases to do B.` | The container ceased responding after OOM. | 容器在 OOM 后停止响应。 |
| 57 | challenge | 挑战；质疑 | `A challenges B.` | The edge case challenged our assumptions. | 这个边界情况挑战了我们的假设。 |
| 58 | change | 改变；更换 | `A changes B. / A changes.` | The plan changed after the meeting. | 会议后计划变了。 |
| 59 | chase | 追赶；追查 | `A chases B. / A chases down B.` | Chase down the root cause before it escalates. | 在升级之前追查到根因。 |
| 60 | cherry-pick | 挑选提交 | `A cherry-picks B.` | Cherry-pick the hotfix commit. | 挑选这个热修复提交。 |
| 61 | choose | 选择 | `A chooses B. / A chooses to do B.` | We chose the second option. | 我们选择了第二个方案。 |
| 62 | circulate | 传阅；分发 | `A circulates B.` | Circulate the meeting notes before the next session. | 下次会议前传阅会议纪要。 |
| 63 | classify | 分类；归类 | `A classifies B as C.` | The firewall classifies traffic as trusted or untrusted. | 防火墙将流量归类为可信或不可信。 |
| 64 | clean | 清理；清洁 | `A cleans B. / A cleans up B.` | Clean up unused dependencies. | 清理未使用的依赖。 |
| 65 | clear | 清除 | `A clears B.` | Clear the temporary files. | 清除临时文件。 |
| 66 | close | 关闭 | `A closes B.` | Close the old connection. | 关闭旧连接。 |
| 67 | collapse | 崩溃；倒塌 | `A collapses. / A collapses into B.` | The monolith collapsed under heavy load. | 单体在重负载下崩溃了。 |
| 68 | combine | 组合；合并 | `A combines B with C.` | Combine multiple API calls into a single batch request. | 将多个 API 调用合并为单个批量请求。 |
| 69 | come | 来；出现 | `A comes to B. / A comes from B.` | The error comes from the database. | 这个错误来自数据库。 |
| 70 | command | 命令；指挥 | `A commands B to do C.` | The CLI tool commands the daemon to restart. | CLI 工具命令守护进程重启。 |
| 71 | comment | 评论；发表意见 | `A comments on B. / A comments that S.` | Please comment on the PR before merging. | 合并前请对 PR 发表意见。 |
| 72 | compare | 比较 | `A compares B with C.` | Compare the two versions. | 比较两个版本。 |
| 73 | compromise | 妥协；折中 | `A compromises on B.` | Don't compromise on security for the sake of speed. | 不要为了速度在安全上妥协。 |
| 74 | concatenate | 拼接（字符串/数组） | `A concatenates B with C.` | Concatenate the path segments with a slash. | 用斜杠拼接路径段。 |
| 75 | concentrate | 集中；专注 | `A concentrates on B.` | Concentrate the business logic in the service layer. | 将业务逻辑集中在服务层。 |
| 76 | concern | 涉及；担忧 | `A concerns B. / A is concerned about B.` | This change concerns the authentication layer. | 这个改动涉及认证层。 |
| 77 | conduct | 进行；实施 | `A conducts B.` | We conducted a post-mortem after the outage. | 故障后我们进行了复盘。 |
| 78 | confront | 面对；对抗 | `A confronts B.` | The team confronted years of accumulated tech debt. | 团队面对多年累积的技术债。 |
| 79 | confuse | 混淆；困惑 | `A confuses B.` | Ambiguous error messages confuse users and developers alike. | 模糊的错误信息让用户和开发者都困惑。 |
| 80 | connect | 连接 | `A connects B to C.` | The client connects to the server. | 客户端连接到服务器。 |
| 81 | consolidate | 合并（报表）；整合 | `A consolidates B.` | Consolidate the three logging systems into one. | 将三个日志系统整合为一个。 |
| 82 | constitute | 构成；组成 | `A constitutes B.` | Three services constitute the core platform. | 三个服务构成核心平台。 |
| 83 | consult | 咨询；查阅 | `A consults B.` | Consult the docs before opening an issue. | 提 issue 前先查阅文档。 |
| 84 | contact | 联系；接触 | `A contacts B.` | Contact the on-call engineer if the alert persists. | 如果告警持续，联系值班工程师。 |
| 85 | contain | 包含 | `A contains B.` | The response contains user data. | 响应中包含用户数据。 |
| 86 | continue | 继续 | `A continues B. / A continues to do B.` | We continued the investigation. | 我们继续排查。 |
| 87 | contrast | 对比；形成对照 | `A contrasts B with C.` | Contrast the monolith's simplicity with microservices' flexibility. | 对比单体的简洁与微服务的灵活。 |
| 88 | convey | 传达；传递 | `A conveys B to C.` | A good commit message conveys the intent clearly. | 好的提交信息清晰地传达意图。 |
| 89 | cook | 烹饪；运行过热 | `A cooks B. / A cooks.` | Don't let the CPU cook at 100%. | 别让 CPU 烧到 100%。 |
| 90 | correct | 纠正；改正 | `A corrects B.` | The linter corrects common mistakes automatically. | Linter 自动纠正常见错误。 |
| 91 | correspond | 对应；通信 | `A corresponds to B.` | Each microservice corresponds to a bounded context. | 每个微服务对应一个限界上下文。 |
| 92 | cost | 花费 | `A costs B.` | The migration costs extra time. | 迁移需要额外时间。 |
| 93 | count | 数；计数 | `A counts B.` | The middleware counts API requests. | 中间件统计 API 请求次数。 |
| 94 | cover | 覆盖 | `A covers B.` | The tests cover this scenario. | 测试覆盖这个场景。 |
| 95 | craft | 精心制作 | `A crafts B.` | Craft a clear and concise API response. | 精心设计清晰简洁的 API 响应。 |
| 96 | crash | 崩溃 | `A crashes.` | The service crashed at midnight. | 服务在午夜崩溃。 |
| 97 | create | 创建 | `A creates B.` | The script creates a backup file. | 脚本会创建备份文件。 |
| 98 | cross | 穿过；交叉 | `A crosses B.` | The request crossed multiple data centers. | 请求跨越了多个数据中心。 |
| 99 | cry | 哭；叫 | `A cries. / A cries for B.` | Don't cry over a failed deploy. | 别为一次失败的部署懊恼。 |
| 100 | cure | 治愈；解决 | `A cures B.` | A rewrite won't cure a lack of tests. | 重写治不了缺少测试的病。 |
| 101 | customize | 定制 | `A customizes B.` | Users can customize the dashboard. | 用户可以定制仪表盘。 |
| 102 | cut | 切；削减 | `A cuts B.` | We cut the response time by half. | 我们把响应时间减半。 |
| 103 | damage | 损坏 | `A damages B.` | The failure damaged the data. | 故障损坏了数据。 |
| 104 | dance | 跳舞 | `A dances.` | The microservices dance around each other. | 微服务互相配合运转。 |
| 105 | dare | 敢；敢于 | `A dares to do B.` | Few developers dare to touch that legacy module. | 没几个开发者敢碰那个遗留模块。 |
| 106 | deadlock | 死锁 | `A deadlocks. / A deadlocks on B.` | The two transactions deadlocked on the same table. | 两个事务在同一张表上死锁了。 |
| 107 | decrease | 减少 | `A decreases B.` | Compression decreases file size. | 压缩减小文件大小。 |
| 108 | dedicate | 致力于 | `A dedicates B to C.` | Dedicate one thread per connection for simplicity. | 为简单起见，每个连接专用一个线程。 |
| 109 | default | 违约；默认 | `A defaults to B.` | The application defaults to port 8080 if not configured. | 如果未配置，应用默认使用 8080 端口。 |
| 110 | defeat | 打败；挫败 | `A defeats B.` | Don't let a single failure defeat the entire migration. | 别让单次失败挫败整个迁移。 |
| 111 | degrade | 降低；退化 | `A degrades B.` | Network issues degraded performance. | 网络问题降低了性能。 |
| 112 | demo | 演示 | `A demos B to C.` | Demo the new feature to stakeholders on Friday. | 周五向利益相关者演示新功能。 |
| 113 | dequeue | 出队 | `A dequeues B.` | The worker dequeues a message. | 工作线程取出一条消息。 |
| 114 | derive | 派生；源自 | `A derives B from C.` | The derived class inherits from the base class. | 派生类继承自基类。 |
| 115 | deserve | 值得 | `A deserves B.` | Every bug fix deserves a regression test. | 每个缺陷修复都值得一个回归测试。 |
| 116 | desire | 渴望；想要 | `A desires B. / A desires to do B.` | Every developer desires a fast CI pipeline. | 每个开发者都渴望快速的 CI 流水线。 |
| 117 | destroy | 销毁；破坏 | `A destroys B.` | Terraform destroyed the test environment. | Terraform 销毁了测试环境。 |
| 118 | dictate | 决定；支配 | `A dictates B.` | The SLA dictates the uptime requirements. | SLA 决定了正常运行时间要求。 |
| 119 | die | 死；停止 | `A dies.` | The process died unexpectedly. | 进程意外终止了。 |
| 120 | differ | 不同；有区别 | `A differs from B.` | Production behavior often differs from staging. | 生产环境行为常与预发布环境不同。 |
| 121 | dig | 挖；深入 | `A digs into B. / A digs B.` | Dig into the logs to find the root cause. | 深入日志找到根本原因。 |
| 122 | diminish | 减少；削弱 | `A diminishes B.` | Technical debt diminishes team velocity over time. | 技术债随时间削弱团队速度。 |
| 123 | disappear | 消失 | `A disappears.` | The alert disappeared after the instance restarted. | 实例重启后告警消失了。 |
| 124 | disconnect | 断开连接 | `A disconnects B from C.` | The proxy disconnected the client. | 代理断开了客户端连接。 |
| 125 | discover | 发现 | `A discovers B.` | We discovered a compatibility issue. | 我们发现了兼容性问题。 |
| 126 | dismiss | 驳回；解雇 | `A dismisses B.` | Don't dismiss the edge case — it will bite you. | 别忽略那个边界情况，它迟早会咬你。 |
| 127 | distinguish | 区分；辨别 | `A distinguishes B from C.` | Distinguish between transient and persistent errors. | 区分瞬时错误和持久错误。 |
| 128 | disturb | 打扰；干扰 | `A disturbs B.` | Don't disturb the deploy with concurrent config changes. | 别在部署时用并发配置变更干扰它。 |
| 129 | dive | 潜水；深入 | `A dives into B.` | Let's dive into the source code. | 让我们深入源代码看看。 |
| 130 | divide | 划分；分割 | `A divides B into C.` | Divide the monolith into loosely coupled modules. | 将单体划分为松耦合模块。 |
| 131 | do | 做；执行 | `A does B. / A does.` | The script does the heavy lifting. | 脚本承担了繁重的工作。 |
| 132 | dominate | 主导；支配 | `A dominates B.` | One slow query dominated the CPU profile. | 一个慢查询主导了 CPU 分析。 |
| 133 | downsize | 裁员；缩减规模 | `A downsizes B.` | The startup downsized the engineering team by 20%. | 创业公司将工程团队缩减了 20%。 |
| 134 | drag | 拖；拽 | `A drags B.` | The slow query dragged down the entire page. | 慢查询拖慢了整个页面。 |
| 135 | dress | 穿衣服；着装；处理 | `A dresses. / A dresses B.` | Dress the commit message properly before pushing. | 推送前把提交信息写规范。 |
| 136 | drink | 喝 | `A drinks B.` | The old server drinks power. | 旧服务器很耗电。 |
| 137 | drive | 驾驶；驱动 | `A drives B.` | User feedback drives the roadmap. | 用户反馈驱动产品路线图。 |
| 138 | drop | 掉落；下降 | `A drops B. / A drops.` | The connection dropped after the timeout. | 超时后连接断开了。 |
| 139 | dry | 变干；耗尽 | `A dries up. / A dries out B.` | The data stream dried up after the API change. | API 变更后数据流枯竭了。 |
| 140 | earn | 赚得；赢得 | `A earns B.` | Good support earns customer trust. | 良好支持赢得客户信任。 |
| 141 | ease | 缓解；减轻 | `A eases B.` | Async processing eases the load on the main thread. | 异步处理减轻主线程负载。 |
| 142 | eat | 吃；消耗 | `A eats B.` | This job eats a lot of memory. | 这个任务消耗大量内存。 |
| 143 | echo | 附和；回响 | `A echoes B.` | The team echoed the CTO's call for simpler systems. | 团队附和 CTO 对更简单系统的呼吁。 |
| 144 | eliminate | 消除；淘汰 | `A eliminates B.` | Caching eliminated the bottleneck entirely. | 缓存彻底消除了瓶颈。 |
| 145 | embrace | 拥抱；欣然接受 | `A embraces B.` | The team embraced pair programming after a trial week. | 试用一周后团队欣然接受了结队编程。 |
| 146 | emerge | 出现；浮现 | `A emerges. / A emerges from B.` | A pattern emerged from the incident data. | 故障数据中浮现出一个模式。 |
| 147 | emit | 发出；发射 | `A emits B.` | The service emits metrics to the monitoring system. | 服务向监控系统发出指标。 |
| 148 | employ | 使用；雇用 | `A employs B.` | The system employs a pub-sub pattern. | 系统采用了发布-订阅模式。 |
| 149 | empty | 清空；倒空 | `A empties B.` | Empty the log directory before the disk fills up. | 磁盘满之前清空日志目录。 |
| 150 | encounter | 遇到；遭遇 | `A encounters B.` | We encountered a race condition in production. | 我们在生产环境遇到了竞态条件。 |
| 151 | end | 结束 | `A ends. / A ends B.` | The meeting ended early. | 会议提前结束了。 |
| 152 | endure | 忍受；持续 | `A endures B.` | The legacy system endured years of feature creep. | 遗留系统忍受了多年的功能膨胀。 |
| 153 | enjoy | 享受；喜欢 | `A enjoys B. / A enjoys doing B.` | Users enjoy the fast response. | 用户喜欢快速响应。 |
| 154 | ensure | 确保 | `A ensures B. / A ensures that S.` | This check ensures data integrity. | 这个检查确保数据完整性。 |
| 155 | enter | 进入 | `A enters B.` | The product entered a new market. | 产品进入新市场。 |
| 156 | escape | 逃脱；避免 | `A escapes B. / A escapes.` | The null value escaped validation and crashed the server. | 空值逃过了校验，导致服务器崩溃。 |
| 157 | establish | 建立；设立 | `A establishes B.` | The client establishes a TLS connection first. | 客户端首先建立 TLS 连接。 |
| 158 | estimate | 估计 | `A estimates B.` | We estimated the cost. | 我们估算了成本。 |
| 159 | evolve | 演变；进化 | `A evolves. / A evolves into B.` | The architecture evolved from monolith to microservices. | 架构从单体演变为微服务。 |
| 160 | exceed | 超过；超出 | `A exceeds B.` | The request rate exceeded the rate limit. | 请求速率超过了限流阈值。 |
| 161 | exclude | 排除 | `A excludes B.` | The filter excludes invalid records. | 过滤器排除无效记录。 |
| 162 | exhaust | 耗尽 | `A exhausts B.` | The process exhausted memory. | 进程耗尽了内存。 |
| 163 | exhibit | 展示；表现出 | `A exhibits B.` | The system exhibits degraded performance under peak load. | 系统在峰值负载下表现出性能下降。 |
| 164 | exist | 存在 | `A exists.` | The file does not exist. | 文件不存在。 |
| 165 | exit | 退出 | `A exits B.` | The company exited the market. | 公司退出了市场。 |
| 166 | expand | 扩张 | `A expands B.` | The company expanded its market. | 公司扩大了市场。 |
| 167 | expect | 期望；预计 | `A expects B to do C.` | We expect the traffic to increase. | 我们预计流量会增加。 |
| 168 | explode | 爆炸；激增 | `A explodes. / A explodes to B.` | The error count exploded after the deploy. | 部署后错误数激增。 |
| 169 | extend | 扩展 | `A extends B.` | The class extends the base class. | 这个类继承了基类。 |
| 170 | face | 面对 | `A faces B.` | The team faces a tight deadline. | 团队面临紧张的截止时间。 |
| 171 | fade | 消退；褪色 | `A fades. / A fades away.` | The alert storm faded after the incident resolved. | 故障解决后告警风暴消退了。 |
| 172 | fail | 失败 | `A fails. / A fails to do B.` | The build failed. | 构建失败。 |
| 173 | fall | 落下；下降 | `A falls. / A falls to C.` | The request rate fell sharply. | 请求量急剧下降。 |
| 174 | favor | 偏爱；有利于 | `A favors B over C.` | Favor composition over inheritance in OOP design. | 在面向对象设计中，优先使用组合而非继承。 |
| 175 | feed | 喂；输入 | `A feeds B into C.` | Feed the log file into the analyzer. | 把日志文件输入分析器。 |
| 176 | feel | 感觉 | `A feels C. / A feels B.` | The interface feels slow. | 这个界面感觉很慢。 |
| 177 | fight | 战斗；对抗 | `A fights B. / A fights against B.` | The team fights tech debt each sprint. | 团队每个迭代对抗技术债。 |
| 178 | file | 提交；归档 | `A files B.` | File a detailed bug report with steps to reproduce. | 提交一份详细的缺陷报告并附上复现步骤。 |
| 179 | fill | 填满 | `A fills B with C.` | The script fills the database with test data. | 脚本用测试数据填充数据库。 |
| 180 | find | 找到；发现 | `A finds B C. / A finds that S.` | I found the solution useful. | 我发现这个方案很有用。 |
| 181 | finish | 完成 | `A finishes B. / A finishes doing B.` | I finished the report. | 我完成了报告。 |
| 182 | fit | 适合；符合；容纳 | `A fits into B. / A fits B.` | The new module fits cleanly into the existing architecture. | 新模块干净地融入现有架构。 |
| 183 | fix | 修复 | `A fixes B.` | The patch fixed the bug. | 补丁修复了缺陷。 |
| 184 | flow | 流动；流转 | `A flows through B. / A flows.` | Data flows from the producer to the consumer via Kafka. | 数据经由 Kafka 从生产者流向消费者。 |
| 185 | fly | 飞；快速移动 | `A flies. / A flies through B.` | The data flies through the pipeline. | 数据快速流经管道。 |
| 186 | focus | 专注 | `A focuses on B.` | The team focuses on stability. | 团队专注于稳定性。 |
| 187 | fold | 折叠；倒闭；合并 | `A folds B into C. / A folds.` | Fold the utility functions into the shared library. | 把工具函数合并到共享库中。 |
| 188 | force | 强制；强迫 | `A forces B to do C.` | Don't force push to main. | 不要强制推送到主分支。 |
| 189 | forecast | 预测 | `A forecasts B.` | The report forecasts higher demand. | 报告预测需求会增加。 |
| 190 | form | 形成；构成 | `A forms B. / A forms.` | These three services form the core platform. | 这三个服务构成核心平台。 |
| 191 | forward | 转发 | `A forwards B to C.` | The server forwards requests to the backend. | 服务器把请求转发给后端。 |
| 192 | foster | 培养；促进 | `A fosters B.` | Code review fosters a culture of shared ownership. | 代码评审培养共同拥有的文化。 |
| 193 | found | 创立；建立 | `A founds B.` | The team founded the project on solid principles. | 团队把项目建立在坚实的原则之上。 |
| 194 | fulfill | 满足；完成 | `A fulfills B.` | The API response fulfills the GraphQL query. | API 响应满足了 GraphQL 查询。 |
| 195 | gain | 获得 | `A gains B.` | The product gained more users. | 产品获得了更多用户。 |
| 196 | gather | 收集；聚集 | `A gathers B.` | The monitoring agent gathers metrics every minute. | 监控代理每分钟收集指标。 |
| 197 | generate | 生成 | `A generates B.` | The tool generates a report. | 工具生成报告。 |
| 198 | get | 得到；变得 | `A gets B. / A gets C.` | The system got slower. | 系统变慢了。 |
| 199 | give | 给 | `A gives B C. / A gives C to B.` | The manager gave us feedback. | 经理给了我们反馈。 |
| 200 | go | 去；变成 | `A goes to B. / A goes C.` | The request went through the proxy. | 请求经过了代理。 |
| 201 | grab | 抓住；获取；快速做 | `A grabs B.` | Grab a coffee and then grab the latest logs. | 拿杯咖啡然后抓取最新日志。 |
| 202 | grant | 授予；准予 | `A grants B to C.` | Grant read-only access to the auditor. | 授予审计员只读权限。 |
| 203 | grow | 增长；变得 | `A grows. / A grows C.` | The traffic grew quickly. | 流量增长很快。 |
| 204 | guarantee | 保证；担保 | `A guarantees B. / A guarantees that S.` | A mutex guarantees exclusive access. | 互斥锁保证独占访问。 |
| 205 | hang | 悬挂；挂起 | `A hangs. / A hangs B.` | The request hung until timeout. | 请求挂起直到超时。 |
| 206 | happen | 发生 | `A happens. / A happens to B.` | The problem happened again. | 问题再次发生。 |
| 207 | harm | 伤害；损害 | `A harms B.` | Hard-coded credentials harm the security posture. | 硬编码凭据损害安全态势。 |
| 208 | hate | 讨厌；恨 | `A hates B. / A hates doing B.` | Developers hate flaky tests. | 开发者讨厌不稳定的测试。 |
| 209 | have | 有；拥有 | `A has B.` | The project has three modules. | 这个项目有三个模块。 |
| 210 | hear | 听见 | `A hears B.` | I heard the alert. | 我听到了告警。 |
| 211 | heat | 加热；升温 | `A heats up B. / A heats up.` | The discussion heated up during the post-mortem. | 复盘期间讨论升温了。 |
| 212 | help | 帮助 | `A helps B do C.` | This tool helps us find bugs. | 这个工具帮助我们发现缺陷。 |
| 213 | hesitate | 犹豫 | `A hesitates to do B.` | Don't hesitate to escalate when the site is down. | 网站挂了就不要犹豫，立即升级。 |
| 214 | hint | 暗示；提示 | `A hints at B. / A hints that S.` | The log message hints at a connection pool issue. | 日志信息暗示连接池有问题。 |
| 215 | hit | 击中；达到；请求 | `A hits B.` | The cache hit rate reached 95%. | 缓存命中率达到 95%。 |
| 216 | hold | 持有；容纳 | `A holds B.` | The cache holds temporary data. | 缓存保存临时数据。 |
| 217 | hope | 希望 | `A hopes to do B. / A hopes that S.` | We hope to finish it today. | 我们希望今天完成。 |
| 218 | host | 主办；托管；承载 | `A hosts B.` | We host the API on a managed Kubernetes cluster. | 我们在托管 Kubernetes 集群上承载 API。 |
| 219 | hurry | 匆忙；赶紧 | `A hurries to do B.` | Don't hurry the deploy — double-check the config first. | 别急着部署，先仔细检查配置。 |
| 220 | hurt | 伤害；损害 | `A hurts B. / A hurts.` | Hasty refactors hurt the architecture. | 仓促的重构损害架构。 |
| 221 | ignore | 忽略 | `A ignores B.` | Do not ignore this warning. | 不要忽略这个警告。 |
| 222 | immerse | 沉浸 | `A immerses B in C.` | New hires immerse themselves in the codebase for a week. | 新人花一周时间沉浸在代码库中。 |
| 223 | impose | 强加；施加 | `A imposes B on C.` | Rate limiting imposes a cap on API calls. | 限流对 API 调用施加了上限。 |
| 224 | impress | 给...留下深刻印象 | `A impresses B with C.` | The intern impressed the team with a clean PR. | 实习生用一份干净的 PR 给团队留下深刻印象。 |
| 225 | improve | 改进 | `A improves B.` | This change improves performance. | 这个改动提升性能。 |
| 226 | include | 包含 | `A includes B.` | The package includes all dependencies. | 这个包包含所有依赖。 |
| 227 | incorporate | 纳入；合并 | `A incorporates B into C.` | Incorporate user feedback into the next sprint plan. | 将用户反馈纳入下一个迭代计划。 |
| 228 | increase | 增加 | `A increases B.` | Caching increases response speed. | 缓存提高响应速度。 |
| 229 | influence | 影响；左右 | `A influences B.` | User feedback directly influences the roadmap. | 用户反馈直接影响产品路线图。 |
| 230 | injure | 伤害；损害 | `A injures B.` | A hasty hotfix can injure the system's stability. | 仓促的热修复会损害系统稳定性。 |
| 231 | intend | 打算 | `A intends to do B.` | We intend to release it tomorrow. | 我们打算明天发布。 |
| 232 | interest | 使感兴趣 | `A interests B.` | DevOps practices interest more engineers every year. | DevOps 实践每年吸引更多工程师的兴趣。 |
| 233 | interfere | 干涉；干扰 | `A interferes with B.` | Background tasks should not interfere with user requests. | 后台任务不应干扰用户请求。 |
| 234 | intervene | 干预；介入 | `A intervenes. / A intervenes in B.` | The on-call intervened when the alert fired. | 告警触发时值班介入了。 |
| 235 | invent | 发明；创造 | `A invents B.` | Don't invent a new protocol when HTTP suffices. | HTTP 够用就别发明新协议。 |
| 236 | invert | 反转；倒置 | `A inverts B.` | Invert the if-condition to reduce nesting. | 反转 if 条件以减少嵌套。 |
| 237 | invite | 邀请 | `A invites B to C. / A invites B to do C.` | I invited him to the meeting. | 我邀请他参加会议。 |
| 238 | involve | 涉及；包含 | `A involves B. / A involves doing B.` | The fix involves updating three microservices. | 这个修复涉及更新三个微服务。 |
| 239 | isolate | 隔离；孤立 | `A isolates B from C.` | Docker isolates the application from the host OS. | Docker 将应用与宿主机操作系统隔离开。 |
| 240 | jump | 跳；快速跳转 | `A jumps. / A jumps to B.` | The latency jumped from 50ms to 500ms. | 延迟从 50ms 跳到了 500ms。 |
| 241 | justify | 证明...合理 | `A justifies B.` | The performance gain justifies the added complexity. | 性能提升证明了增加复杂度的合理性。 |
| 242 | keep | 保持；保留 | `A keeps B C.` | Keep the connection alive. | 保持连接存活。 |
| 243 | kill | 杀死；终止 | `A kills B.` | Kill the stuck process. | 终止卡住的进程。 |
| 244 | kiss | 亲吻；轻触 | `A kisses B.` | Keep it simple, stupid — the KISS principle. | 保持简单——KISS 原则。 |
| 245 | knock | 敲；击倒 | `A knocks B. / A knocks B out.` | A bad config knocked the service offline. | 一个错误配置把服务打下线了。 |
| 246 | lack | 缺乏；缺少 | `A lacks B.` | The legacy system lacks proper error handling. | 遗留系统缺乏恰当的错误处理。 |
| 247 | lag | 滞后 | `A lags behind B.` | The replica lagged behind the primary by 200 transactions. | 副本落后主库 200 个事务。 |
| 248 | land | 着陆；获得；落地 | `A lands B. / A lands.` | The PR finally landed on main after three reviews. | PR 经过三次评审后终于合入主分支。 |
| 249 | lapse | 失效；流逝 | `A lapses. / A lapses after B.` | The API token lapsed after 90 days of no rotation. | API 令牌在 90 天未轮换后失效。 |
| 250 | last | 持续；维持 | `A lasts. / A lasts for B.` | The access token lasts for one hour after issue. | 访问令牌签发后持续一小时。 |
| 251 | laugh | 笑 | `A laughs. / A laughs at B.` | Don't laugh at legacy code — it pays the bills. | 别嘲笑遗留代码，是它在养家。 |
| 252 | leave | 离开；留下 | `A leaves B C. / A leaves B.` | This change leaves the old logic unchanged. | 这个改动让旧逻辑保持不变。 |
| 253 | lend | 借出 | `A lends B to C.` | The service lends resources to workers. | 服务把资源借给工作线程。 |
| 254 | let | 让；允许 | `A lets B do C.` | Let the pipeline finish before merging. | 等流水线完成再合并。 |
| 255 | lie | 躺；位于 | `A lies in B.` | The real problem lies in the data layer. | 真正的问题在数据层。 |
| 256 | lift | 举起；解除；提升 | `A lifts B.` | The team lifted the deploy freeze after the audit passed. | 审计通过后团队解除了部署冻结。 |
| 257 | like | 喜欢；像 | `A likes B. / A likes doing B.` | I like this implementation. | 我喜欢这个实现。 |
| 258 | link | 连接；关联 | `A links B to C.` | Link the shared library at compile time. | 编译时链接共享库。 |
| 259 | listen | 监听 | `A listens on B.` | The server listens on port 8080. | 服务器监听 8080 端口。 |
| 260 | live | 生活；居住 | `A lives in B. / A lives.` | The service lives in this namespace. | 该服务位于这个命名空间中。 |
| 261 | livelock | 活锁 | `A livelocks.` | The retry loop livelocked without making progress. | 重试循环陷入活锁，毫无进展。 |
| 262 | locate | 找到；定位 | `A locates B.` | The profiler locates the exact bottleneck in seconds. | 分析器几秒内定位到确切的瓶颈。 |
| 263 | lock | 锁定 | `A locks B.` | The transaction locks the row. | 事务锁定该行。 |
| 264 | look | 看起来；看 | `A looks C. / A looks at B.` | The design looks good. | 这个设计看起来不错。 |
| 265 | loop | 循环 | `A loops through B.` | The event loop processes messages from the queue. | 事件循环处理队列中的消息。 |
| 266 | lose | 失去；丢失 | `A loses B.` | The system lost some data. | 系统丢失了一些数据。 |
| 267 | love | 爱；喜欢 | `A loves B. / A loves doing B.` | Developers love clean APIs. | 开发者喜欢干净的接口。 |
| 268 | make | 做；使；制造 | `A makes B. / A makes B C.` | This change makes the system stable. | 这个改动让系统变得稳定。 |
| 269 | manipulate | 操纵；控制 | `A manipulates B.` | The script manipulates the DOM after the page loads. | 脚本在页面加载后操纵 DOM。 |
| 270 | manufacture | 制造；生产 | `A manufactures B.` | The factory manufactures custom server racks. | 工厂制造定制服务器机架。 |
| 271 | matter | 重要；有关系 | `A matters. / It matters that S.` | Consistency matters more than cleverness in a codebase. | 在代码库中，一致性比聪明更重要。 |
| 272 | mean | 意思是；意味着 | `A means B. / A means that S.` | A 503 error means the service is down. | 503 错误意味着服务挂了。 |
| 273 | measure | 测量 | `A measures B.` | The tool measures response time. | 工具测量响应时间。 |
| 274 | meet | 满足；会面 | `A meets B.` | The design meets the requirements. | 设计满足需求。 |
| 275 | mind | 介意 | `A minds B. / A minds doing B.` | Do you mind reviewing this PR? | 你介意评审这个 PR 吗？ |
| 276 | mislead | 误导 | `A misleads B.` | Misleading log messages misled the investigation. | 误导性的日志信息误导了排查。 |
| 277 | miss | 错过；遗漏 | `A misses B.` | We missed one edge case. | 我们遗漏了一个边界场景。 |
| 278 | misunderstand | 误解 | `A misunderstands B.` | The client misunderstood the API contract. | 客户端误解了 API 契约。 |
| 279 | mitigate | 缓解 | `A mitigates B.` | Rate limiting mitigates the attack. | 限流缓解攻击。 |
| 280 | modify | 修改；变更 | `A modifies B.` | The script modifies the database schema. | 脚本修改数据库模式。 |
| 281 | move | 移动 | `A moves B to C.` | Move the file to the backup folder. | 把文件移动到备份目录。 |
| 282 | name | 命名；取名 | `A names B C.` | Name the variable descriptively, not just x or tmp. | 给变量起描述性的名字，别只用 x 或 tmp。 |
| 283 | need | 需要 | `A needs B. / A needs to do B.` | We need more logs. | 我们需要更多日志。 |
| 284 | neglect | 忽视；忽略 | `A neglects B.` | Neglecting error handling leads to silent failures. | 忽视错误处理会导致静默失败。 |
| 285 | nest | 嵌套 | `A nests B inside C.` | Nest the callback inside a try-catch for safety. | 将回调嵌套在 try-catch 中以保安全。 |
| 286 | nudge | 轻推；提醒 | `A nudges B to do C.` | The bot nudges reviewers when a PR sits idle for a day. | PR 闲置一天后，机器人提醒评审者。 |
| 287 | obey | 遵守 | `A obeys B.` | The client must obey the rate limit headers. | 客户端必须遵守限流头部。 |
| 288 | observe | 观察到 | `A observes B.` | The monitor observed high latency. | 监控观察到高延迟。 |
| 289 | obtain | 获得；获取 | `A obtains B from C.` | Obtain an API key from the dashboard. | 从仪表盘获取 API 密钥。 |
| 290 | occur | 发生 | `A occurs. / A occurs in B.` | The timeout occurs in production. | 超时发生在生产环境。 |
| 291 | offer | 提供 | `A offers B to C.` | The platform offers cloud storage. | 该平台提供云存储。 |
| 292 | offset | 抵消；偏移 | `A offsets B.` | Caching offsets the increased load on the database. | 缓存抵消了数据库增加的压力。 |
| 293 | omit | 省略 | `A omits B.` | Omit sensitive fields from the log output. | 日志输出中省略敏感字段。 |
| 294 | open | 打开；开放 | `A opens B.` | Please open the configuration file. | 请打开配置文件。 |
| 295 | overcome | 克服；战胜 | `A overcomes B.` | We overcame the rate limit with batching. | 我们用批量处理克服了速率限制。 |
| 296 | overflow | 溢出 | `A overflows B. / A overflows.` | The buffer overflowed and corrupted adjacent memory. | 缓冲区溢出损坏了相邻内存。 |
| 297 | overwhelm | 压垮；淹没 | `A overwhelms B.` | The traffic spike overwhelmed the connection pool. | 流量高峰压垮了连接池。 |
| 298 | owe | 欠；归功于 | `A owes B to C.` | The project owes its stability to thorough testing. | 这个项目的稳定性归功于充分测试。 |
| 299 | own | 拥有 | `A owns B.` | The team owns this service. | 这个团队负责这个服务。 |
| 300 | pad | 填充（padding） | `A pads B with C.` | Pad the buffer with zeros before hashing. | 哈希前用零填充缓冲区。 |
| 301 | participate | 参与；参加 | `A participates in B.` | Everyone participates in the daily stand-up. | 每个人都参与每日站会。 |
| 302 | pass | 传递；通过 | `A passes B to C.` | Pass the parameter to the function. | 把参数传给函数。 |
| 303 | pause | 暂停 | `A pauses B.` | We paused the deployment. | 我们暂停了部署。 |
| 304 | pay | 支付 | `A pays B for C.` | We pay for additional storage. | 我们为额外存储付费。 |
| 305 | peek | 偷看；预览 | `A peeks at B.` | Peek at the first message in the queue without dequeuing. | 偷看队列中第一条消息但不出队。 |
| 306 | permit | 允许 | `A permits B.` | The license permits commercial use. | 许可证允许商业使用。 |
| 307 | persist | 坚持；持续存在 | `A persists. / A persists in B.` | The connection pool persists across requests. | 连接池在请求间持续存在。 |
| 308 | pick | 挑选 | `A picks B.` | Pick a stable version. | 选择一个稳定版本。 |
| 309 | pivot | 旋转；转型 | `A pivots to B.` | The startup pivoted from B2C to B2B. | 这家创业公司从 B2C 转型到 B2B。 |
| 310 | place | 放置；下（单） | `A places B in/on C.` | Place a callback on the event queue. | 将回调放入事件队列。 |
| 311 | play | 玩；播放；扮演 | `A plays B. / A plays with B.` | This component plays a key role. | 这个组件起着关键作用。 |
| 312 | pledge | 承诺；保证 | `A pledges to do B. / A pledges B.` | The company pledged to fix all critical bugs within 24 hours. | 公司承诺在 24 小时内修复所有严重缺陷。 |
| 313 | plummet | 骤降 | `A plummets.` | The response time plummeted after the optimization. | 优化后响应时间骤降。 |
| 314 | polish | 打磨；润色 | `A polishes B.` | Polish the UI before the demo. | 演示前打磨 UI。 |
| 315 | pose | 提出；造成 | `A poses B.` | Unvalidated input poses a security risk. | 未校验的输入构成安全风险。 |
| 316 | practise | 练习；实践 | `A practises B.` | Practise test-driven development until it becomes habit. | 练习 TDD 直到它变成习惯。 |
| 317 | predict | 预测 | `A predicts B.` | The model predicts user behavior. | 模型预测用户行为。 |
| 318 | prefer | 更喜欢 | `A prefers B to C. / A prefers to do B.` | We prefer a simple design. | 我们更喜欢简单的设计。 |
| 319 | pretend | 假装 | `A pretends to do B. / A pretends that S.` | Don't pretend the bug doesn't exist. | 别假装这个缺陷不存在。 |
| 320 | prevent | 防止 | `A prevents B from doing C.` | Validation prevents invalid input. | 校验防止无效输入。 |
| 321 | prime | 准备；预热 | `A primes B.` | Prime the cache before the traffic spike hits. | 在流量高峰到来前预热缓存。 |
| 322 | proceed | 继续；进行 | `A proceeds with B. / A proceeds to do B.` | The pipeline proceeds to the deploy stage. | 流水线进入部署阶段。 |
| 323 | produce | 产生；生产 | `A produces B.` | The service produces events. | 服务产生事件。 |
| 324 | prompt | 提示；促使 | `A prompts B to do C.` | The error prompted us to re-examine the logic. | 这个错误促使我们重新检查逻辑。 |
| 325 | provide | 提供 | `A provides B for C.` | The API provides user information. | 这个接口提供用户信息。 |
| 326 | proxy | 代理 | `A proxies B to C.` | Nginx proxies traffic to the app. | Nginx 把流量代理到应用。 |
| 327 | pull | 拉取 | `A pulls B from C.` | Pull the latest image. | 拉取最新镜像。 |
| 328 | pursue | 追求；从事 | `A pursues B.` | We're pursuing a microservices migration. | 我们在推动微服务迁移。 |
| 329 | push | 推送；推动 | `A pushes B to C.` | Push the commit to GitHub. | 把提交推送到 GitHub。 |
| 330 | put | 放；放置 | `A puts B in/on C.` | Put the config file in this directory. | 把配置文件放在这个目录下。 |
| 331 | qualify | 使合格；限定；有资格 | `A qualifies B. / A qualifies for B.` | Three candidates qualified for the final interview round. | 三位候选人取得了终面资格。 |
| 332 | quit | 退出；停止 | `A quits B. / A quits.` | Quit the process gracefully with a SIGTERM. | 用 SIGTERM 优雅退出进程。 |
| 333 | race | 竞态 | `A races with B. / A races.` | Two writes raced and corrupted the counter. | 两次写入发生竞态，损坏了计数器。 |
| 334 | rain | 下雨；如雨般落下 | `It rains B.` | It rains alerts during Black Friday. | 黑五期间告警如雨下。 |
| 335 | raise | 举起；提高；提出 | `A raises B.` | She raised a valid concern. | 她提出了一个合理的担忧。 |
| 336 | reach | 达到；到达 | `A reaches B.` | The CPU usage reached 90%. | CPU 使用率达到 90%。 |
| 337 | react | 反应；回应 | `A reacts to B.` | The circuit breaker reacts to consecutive failures. | 断路器对连续失败做出反应。 |
| 338 | rebalance | 再平衡 | `A rebalances B.` | Kafka rebalances partitions when a consumer joins. | 消费者加入时 Kafka 再平衡分区。 |
| 339 | receive | 接收 | `A receives B from C.` | The server received the request. | 服务器收到了请求。 |
| 340 | record | 记录；录制 | `A records B.` | The middleware records every request for auditing. | 中间件记录每个请求用于审计。 |
| 341 | redirect | 重定向 | `A redirects B to C.` | The site redirects HTTP to HTTPS. | 网站把 HTTP 重定向到 HTTPS。 |
| 342 | reduce | 减少；归约 | `A reduces B.` | The cache reduces database load. | 缓存减少数据库负载。 |
| 343 | refine | 精炼；改进 | `A refines B.` | Refine the search algorithm based on user feedback. | 基于用户反馈改进搜索算法。 |
| 344 | reflect | 反映；反思 | `A reflects B. / A reflects on B.` | The dashboard reflects real-time metrics. | 仪表盘反映实时指标。 |
| 345 | regard | 认为；看待 | `A regards B as C.` | We regard code review as essential, not optional. | 我们认为代码评审是必需的，不是可选的。 |
| 346 | reinforce | 加强；强化 | `A reinforces B.` | The incident reinforced the importance of testing. | 这次事故强化了测试的重要性。 |
| 347 | reiterate | 重申 | `A reiterates B. / A reiterates that S.` | The post-mortem reiterates the importance of testing. | 复盘重申了测试的重要性。 |
| 348 | relieve | 缓解；减轻 | `A relieves B.` | Horizontal scaling relieves the pressure on a single node. | 水平扩展缓解了单节点压力。 |
| 349 | rely | 依赖；依靠 | `A relies on B.` | The feature relies on a third-party API. | 这个功能依赖第三方 API。 |
| 350 | remain | 保持 | `A remains C.` | The risk remains high. | 风险仍然很高。 |
| 351 | remove | 移除 | `A removes B from C.` | Remove the unused dependency. | 移除未使用的依赖。 |
| 352 | renew | 续订 | `A renews B.` | The customer renewed the contract. | 客户续签了合同。 |
| 353 | repair | 修理 | `A repairs B.` | The script repaired the damaged file. | 脚本修复了损坏文件。 |
| 354 | repeat | 重复；重做 | `A repeats B. / A repeats.` | The bug repeats on every cold start. | 这个缺陷在每次冷启动时重现。 |
| 355 | replace | 替换 | `A replaces B with C.` | We replaced the old library with a new one. | 我们用新库替换了旧库。 |
| 356 | represent | 代表；表示 | `A represents B.` | Each node in the graph represents a server instance. | 图中每个节点代表一个服务器实例。 |
| 357 | research | 研究 | `A researches B.` | We researched local regulations. | 我们研究了本地法规。 |
| 358 | resist | 抵抗；抵制 | `A resists B.` | The team resisted the urge to rewrite from scratch. | 团队抵制了从零重写的冲动。 |
| 359 | rest | 休息 | `A rests. / A rests on B.` | Let the server rest between stress tests. | 压力测试之间让服务器休息一下。 |
| 360 | restrict | 限制；约束 | `A restricts B to C.` | Restrict API access to internal IPs only. | 将 API 访问限制为内网 IP。 |
| 361 | resume | 恢复；继续 | `A resumes B.` | The job resumed after the restart. | 任务在重启后恢复。 |
| 362 | retain | 留住 | `A retains B.` | Good service retains customers. | 良好服务留住客户。 |
| 363 | retry | 重试 | `A retries B.` | The client retries the request. | 客户端重试请求。 |
| 364 | return | 返回；归还 | `A returns B.` | The function returns an error. | 这个函数返回一个错误。 |
| 365 | reuse | 复用 | `A reuses B.` | The module reuses existing logic. | 该模块复用现有逻辑。 |
| 366 | reverse | 逆转；反转 | `A reverses B.` | The rollback reversed the breaking change. | 回滚逆转了那个破坏性变更。 |
| 367 | rid | 摆脱 | `A rids B of C.` | Rid the codebase of unused dependencies. | 清除代码库中未使用的依赖。 |
| 368 | ride | 骑；乘；经受 | `A rides B. / A rides out B.` | The service rode out the traffic spike. | 服务扛过了流量高峰。 |
| 369 | ring | 响铃；打电话 | `A rings. / A rings B.` | The alert rings at 3 AM. | 告警在凌晨 3 点响起。 |
| 370 | rise | 上升；增加 | `A rises. / A rises to C.` | CPU usage rose to 95%. | CPU 使用率上升到 95%。 |
| 371 | risk | 冒险；冒...的风险 | `A risks B. / A risks doing B.` | Deploying on Friday risks ruining the weekend. | 周五部署冒险毁掉周末。 |
| 372 | rotate | 轮换；旋转 | `A rotates B.` | Rotate the API keys every 90 days. | 每 90 天轮换一次 API 密钥。 |
| 373 | route | 路由 | `A routes B to C.` | The gateway routes requests to services. | 网关把请求路由到服务。 |
| 374 | ruin | 毁坏 | `A ruins B.` | A single bad deploy ruined the weekend for the on-call. | 一次糟糕的部署毁了值班的周末。 |
| 375 | rule | 统治；裁决 | `A rules out B. / A rules that S.` | We ruled out a network issue after the ping test. | ping 测试后我们排除了网络问题。 |
| 376 | run | 运行；跑 | `A runs B. / A runs on C.` | The app runs on Docker. | 应用运行在 Docker 上。 |
| 377 | rush | 匆忙；仓促 | `A rushes B. / A rushes to do B.` | Don't rush the migration — plan each step carefully. | 别仓促迁移，每一步都要仔细规划。 |
| 378 | sacrifice | 牺牲 | `A sacrifices B for C.` | We sacrificed some latency for stronger consistency. | 我们牺牲了一些延迟以换取更强的一致性。 |
| 379 | save | 保存；节省 | `A saves B.` | This cache saves response time. | 这个缓存节省响应时间。 |
| 380 | say | 说 | `A says B. / A says that S.` | He said the issue was fixed. | 他说问题已经修复。 |
| 381 | scale | 扩缩容 | `A scales B.` | Scale the service to ten instances. | 把服务扩容到十个实例。 |
| 382 | scatter | 分散；散开 | `A scatters B across C.` | The log files scattered across three different servers. | 日志文件分散在三台不同的服务器上。 |
| 383 | score | 得分；评分；赢得 | `A scores B. / A scores.` | The new release scored high marks in the performance audit. | 新版本在性能审计中得了高分。 |
| 384 | scream | 尖叫 | `A screams. / A screams for B.` | The CPU fan screams during a full build. | 全量构建时 CPU 风扇尖啸。 |
| 385 | see | 看见；理解 | `A sees B. / A sees that S.` | I see the problem now. | 我现在明白问题了。 |
| 386 | seek | 寻找；寻求 | `A seeks B. / A seeks to do B.` | We're seeking a simpler solution. | 我们正在寻找更简单的方案。 |
| 387 | seem | 似乎 | `A seems C. / A seems to do B.` | The solution seems reasonable. | 这个方案看起来合理。 |
| 388 | segment | 细分 | `A segments B.` | We segmented customers by usage. | 我们按使用量细分客户。 |
| 389 | seize | 抓住；把握 | `A seizes B.` | Seize the opportunity to refactor during the migration. | 趁迁移之机把握重构的机会。 |
| 390 | select | 选择 | `A selects B.` | Select the correct environment. | 选择正确的环境。 |
| 391 | sell | 销售 | `A sells B to C.` | The vendor sells cloud services. | 供应商销售云服务。 |
| 392 | send | 发送 | `A sends B to C. / A sends C B.` | I sent the document to him. | 我把文档发给了他。 |
| 393 | sense | 感知；察觉 | `A senses B.` | The circuit breaker senses failures and opens automatically. | 断路器感知故障并自动断开。 |
| 394 | separate | 分离；分开 | `A separates B from C.` | Separate the config from the code. | 把配置和代码分离。 |
| 395 | serve | 服务 | `A serves B.` | The platform serves enterprise customers. | 平台服务企业客户。 |
| 396 | set | 设置；设定；放置 | `A sets B. / A sets B to C.` | Set the timeout to 30 seconds. | 把超时设为 30 秒。 |
| 397 | sever | 切断 | `A severs B.` | The load balancer severs idle connections after 60 seconds. | 负载均衡器在 60 秒后切断空闲连接。 |
| 398 | shake | 摇晃；震动 | `A shakes B. / A shakes.` | The outage shook the team's confidence. | 这次故障动摇了团队的信心。 |
| 399 | shape | 塑造；影响 | `A shapes B.` | Senior engineers shape the technical direction of the team. | 高级工程师塑造团队的技术方向。 |
| 400 | share | 分享；共享 | `A shares B with C.` | Please share the link with the team. | 请把链接分享给团队。 |
| 401 | shed | 去除；阐明 | `A sheds B. / A sheds light on B.` | The investigation shed light on the root cause. | 调查阐明了根本原因。 |
| 402 | shift | 转移；转变 | `A shifts B to C.` | We shifted traffic to the backup cluster. | 我们把流量转移到备用集群。 |
| 403 | shoot | 射击；快速发送 | `A shoots B to C.` | Shoot me a message on Slack. | 在 Slack 上给我发个消息。 |
| 404 | signal | 发信号；表明 | `A signals B. / A signals that S.` | The health endpoint signals whether the service is ready. | 健康端点表明服务是否就绪。 |
| 405 | sing | 唱 | `A sings B. / A sings.` | The team sang his praises at the demo. | 团队在演示中对他赞不绝口。 |
| 406 | sit | 坐；位于 | `A sits in B. / A sits between B and C.` | The proxy sits between client and server. | 代理位于客户端和服务器之间。 |
| 407 | skip | 跳过 | `A skips B.` | Skip invalid records. | 跳过无效记录。 |
| 408 | sleep | 睡觉；休眠 | `A sleeps.` | The process sleeps for 5 seconds. | 进程休眠 5 秒。 |
| 409 | slide | 滑动；滑入 | `A slides into B.` | The feature toggled and traffic slid from v1 to v2. | 功能切换后流量从 v1 滑入 v2。 |
| 410 | slip | 滑；溜走；错过 | `A slips. / A slips through B.` | The bug slipped through code review into production. | 这个缺陷溜过了代码评审进了生产环境。 |
| 411 | smell | 闻；察觉 | `A smells B. / A smells of B.` | This approach smells of over-engineering. | 这个方案有过度设计的味道。 |
| 412 | smile | 微笑 | `A smiles. / A smiles at B.` | The client smiled at the demo. | 客户看到演示笑了。 |
| 413 | soar | 飙升 | `A soars.` | The error rate soared after the deploy and triggered alerts. | 部署后错误率飙升并触发告警。 |
| 414 | solidify | 巩固 | `A solidifies B.` | Solidify the API contract with integration tests. | 用集成测试巩固 API 契约。 |
| 415 | solve | 解决 | `A solves B.` | This patch solves the problem. | 这个补丁解决了问题。 |
| 416 | sound | 听起来 | `A sounds C.` | Your plan sounds practical. | 你的计划听起来很实用。 |
| 417 | span | 跨越；涵盖 | `A spans B.` | A single trace spans five microservices. | 一次追踪跨越五个微服务。 |
| 418 | spawn | 产生；衍生 | `A spawns B.` | The process spawns a child thread for each request. | 进程为每个请求衍生一个子线程。 |
| 419 | speak | 说话；发言 | `A speaks to B about C.` | She spoke about the project status. | 她谈了项目状态。 |
| 420 | spend | 花费 | `A spends B on C. / A spends B doing C.` | We spent two hours fixing the bug. | 我们花了两个小时修复缺陷。 |
| 421 | spike | 猛增 | `A spikes.` | CPU usage spiked to 99% during the batch job. | 批量任务期间 CPU 使用率猛增到 99%。 |
| 422 | spill | 溢出；泄露 | `A spills into B.` | The log spill overfilled the disk. | 日志溢出填满了磁盘。 |
| 423 | spot | 发现；认出 | `A spots B.` | Spot the regression before the canary goes to 100%. | 在金丝雀 100% 铺开前发现回归。 |
| 424 | spread | 传播；扩散 | `A spreads B across C.` | The CDN spreads content across edge locations worldwide. | CDN 将内容传播到全球边缘节点。 |
| 425 | stack | 堆叠 | `A stacks B on top of C.` | The tech stack layers React on top of Node.js. | 技术栈将 React 叠在 Node.js 上。 |
| 426 | stand | 站立；承受 | `A stands. / A stands for B.` | The system can stand high traffic. | 系统能承受高流量。 |
| 427 | start | 开始 | `A starts. / A starts B. / A starts to do B.` | The service starts automatically. | 服务会自动启动。 |
| 428 | stay | 保持；停留 | `A stays C. / A stays in B.` | The process stayed active. | 这个进程保持活跃。 |
| 429 | steal | 偷；窃取 | `A steals B from C.` | An attacker stole session tokens. | 攻击者窃取了会话令牌。 |
| 430 | stimulate | 刺激；激发 | `A stimulates B.` | The outage stimulated interest in chaos engineering. | 故障激发了混沌工程的兴趣。 |
| 431 | stop | 停止 | `A stops. / A stops B. / A stops doing B.` | The container stopped unexpectedly. | 容器意外停止了。 |
| 432 | strengthen | 加强；强化 | `A strengthens B.` | Type checking strengthens the codebase against bugs. | 类型检查强化代码库以抵御缺陷。 |
| 433 | strike | 打击；罢工 | `A strikes B. / A strikes.` | The outage struck at midnight during peak traffic. | 故障在午夜流量高峰时袭来。 |
| 434 | strip | 剥离 | `A strips B from C.` | Strip sensitive data from the logs before shipping. | 传输前从日志中剥离敏感数据。 |
| 435 | strive | 努力；奋斗 | `A strives to do B. / A strives for B.` | We strive for 99.9% uptime. | 我们努力达成 99.9% 的正常运行时间。 |
| 436 | struggle | 挣扎；奋斗 | `A struggles with B. / A struggles to do B.` | The team struggled with flaky integration tests. | 团队与不稳定的集成测试作斗争。 |
| 437 | stun | 使震惊 | `A stuns B.` | The sudden traffic drop stunned the operations team. | 流量的突然下降震惊了运维团队。 |
| 438 | submit | 提交 | `A submits B to C.` | Submit the PR for review. | 提交 PR 等待评审。 |
| 439 | substitute | 替代 | `A substitutes B for C.` | Substitute environment variables in the config template. | 在配置模板中替换环境变量。 |
| 440 | succeed | 成功 | `A succeeds. / A succeeds in doing B.` | The deployment succeeded. | 部署成功。 |
| 441 | suffer | 遭受；受苦 | `A suffers from B.` | The service suffers from high latency at peak. | 服务在高峰期遭受高延迟。 |
| 442 | suffice | 足够 | `A suffices. / A suffices to do B.` | A simple retry loop suffices for transient errors. | 简单的重试循环足以应对瞬时错误。 |
| 443 | suit | 适合；满足 | `A suits B.` | Choose the database that suits your access pattern. | 选择适合你访问模式的数据库。 |
| 444 | supply | 供应 | `A supplies B to C.` | The vendor supplies the hardware. | 供应商提供硬件。 |
| 445 | suppress | 压制 | `A suppresses B.` | Suppress duplicate alerts during a known incident. | 在已知故障期间压制重复告警。 |
| 446 | surge | 激增 | `A surges.` | Traffic surges during the holiday shopping season. | 假日购物季流量激增。 |
| 447 | surround | 包围；围绕 | `A surrounds B.` | The debate surrounded the choice of database. | 讨论围绕着数据库的选择。 |
| 448 | survey | 调查 | `A surveys B.` | We surveyed enterprise users. | 我们调研了企业用户。 |
| 449 | survive | 幸存；存活 | `A survives B. / A survives.` | The system survived the DDoS attack. | 系统在 DDoS 攻击中存活下来。 |
| 450 | suspect | 怀疑；觉得 | `A suspects B. / A suspects that S.` | I suspect a memory leak in the new build. | 我怀疑新构建有内存泄漏。 |
| 451 | suspend | 暂停；中止 | `A suspends B.` | The OS suspended the process due to OOM. | 操作系统因内存不足中止了进程。 |
| 452 | sustain | 维持 | `A sustains B.` | The system cannot sustain 10,000 writes per second. | 系统无法维持每秒 10000 次写入。 |
| 453 | swarm | 集群；蜂群 | `A swarms. / A swarms around B.` | The containers swarm around the orchestrator. | 容器围绕编排器形成集群。 |
| 454 | swell | 膨胀；增加 | `A swells.` | The message queue swelled during the outage. | 故障期间消息队列膨胀。 |
| 455 | swim | 游泳 | `A swims. / A swims through B.` | The team swam through a sea of bugs. | 团队在缺陷海洋中挣扎前行。 |
| 456 | synthesize | 合成 | `A synthesizes B from C.` | The monitoring system synthesizes a health score from multiple signals. | 监控系统从多个信号合成健康评分。 |
| 457 | tailor | 定制 | `A tailors B to C.` | Tailor the error message to the user's context. | 根据用户上下文定制错误信息。 |
| 458 | take | 拿；采取；花费 | `A takes B. / A takes time to do B.` | This task takes two days. | 这个任务需要两天。 |
| 459 | talk | 谈话 | `A talks to B about C.` | I talked to him about the plan. | 我和他谈了这个计划。 |
| 460 | target | 瞄准 | `A targets B.` | The campaign targets young users. | 活动面向年轻用户。 |
| 461 | taste | 品尝；体验 | `A tastes B. / A has a taste of B.` | The new hire got a taste of on-call life. | 新人体验了值班的滋味。 |
| 462 | tear | 撕裂；撕破 | `A tears B. / A tears B down.` | Tear down the test environment after validation. | 验证后拆除测试环境。 |
| 463 | tell | 告诉 | `A tells B C. / A tells B that S.` | Please tell me the result. | 请告诉我结果。 |
| 464 | tend | 倾向于；照顾 | `A tends to do B.` | Microservices tend to increase operational complexity. | 微服务倾向于增加运维复杂度。 |
| 465 | terminate | 终止；结束 | `A terminates B.` | The load balancer terminates idle connections. | 负载均衡器终止空闲连接。 |
| 466 | threaten | 威胁；危及 | `A threatens B.` | The memory leak threatened the system's stability. | 内存泄漏威胁到系统的稳定性。 |
| 467 | thrive | 繁荣；兴旺 | `A thrives.` | Open source projects thrive on community contributions. | 开源项目因社区贡献而繁荣。 |
| 468 | throw | 抛出 | `A throws B.` | The method throws an exception. | 这个方法抛出异常。 |
| 469 | timeout | 超时 | `A times out.` | The request timed out. | 请求超时了。 |
| 470 | tolerate | 容忍；忍受 | `A tolerates B.` | The system tolerates up to two node failures. | 系统容忍最多两个节点故障。 |
| 471 | touch | 触碰；涉及 | `A touches B.` | This PR touches three modules. | 这个 PR 涉及三个模块。 |
| 472 | transport | 传输；运输 | `A transports B to C.` | The protocol transports binary data over a WebSocket. | 该协议通过 WebSocket 传输二进制数据。 |
| 473 | trap | 困住；捕获 | `A traps B. / A is trapped in B.` | The team felt trapped in the legacy monolith. | 团队感觉被困在遗留单体中。 |
| 474 | travel | 旅行；传播 | `A travels. / A travels through B.` | Data travels through three proxies. | 数据经过三层代理传输。 |
| 475 | traverse | 遍历 | `A traverses B.` | The algorithm traverses the graph in O(n) time. | 算法以 O(n) 时间遍历图。 |
| 476 | trim | 修剪；削减 | `A trims B.` | Trim the Docker image to reduce its size by 60%. | 修剪 Docker 镜像将其体积减少 60%。 |
| 477 | trust | 信任 | `A trusts B. / A trusts B to do C.` | Don't trust user input without validation. | 不要信任未经校验的用户输入。 |
| 478 | try | 尝试；试图 | `A tries B. / A tries to do B.` | Try a different approach. | 尝试另一种方法。 |
| 479 | turn | 变成；转向 | `A turns C. / A turns to B.` | The status turned red. | 状态变成了红色。 |
| 480 | twist | 扭曲；扭转；缠绕 | `A twists B.` | Don't twist the requirement — implement what the spec says. | 别曲解需求，按规格说明实现。 |
| 481 | type | 打字；分类 | `A types B. / A types B as C.` | TypeScript types every variable at compile time. | TypeScript 在编译时对每个变量进行类型标注。 |
| 482 | uncover | 发现；揭露 | `A uncovers B.` | Fuzz testing uncovered a critical buffer overflow. | 模糊测试发现了一个严重的缓冲区溢出。 |
| 483 | undergo | 经历；经受 | `A undergoes B.` | The database undergoes a major version upgrade. | 数据库经历了一次主版本升级。 |
| 484 | undermine | 削弱；破坏 | `A undermines B.` | Skipping tests undermines the team's confidence. | 跳过测试削弱团队的信心。 |
| 485 | undertake | 承担；从事 | `A undertakes B.` | The team undertook a major refactoring effort. | 团队承担了一次重大重构工作。 |
| 486 | unify | 统一 | `A unifies B.` | Unify the logging format across all services. | 统一所有服务的日志格式。 |
| 487 | unlock | 解锁 | `A unlocks B.` | The process unlocks the file. | 进程解锁文件。 |
| 488 | unveil | 公布；揭晓 | `A unveils B.` | The team unveiled the new architecture at the all-hands. | 团队在全员大会上公布了新架构。 |
| 489 | upset | 打乱；使不安 | `A upsets B.` | A late requirement change upset the sprint plan. | 迟来的需求变更打乱了迭代计划。 |
| 490 | use | 使用 | `A uses B to do C.` | We use Redis to cache data. | 我们使用 Redis 缓存数据。 |
| 491 | utilize | 使用；利用 | `A utilizes B.` | The cache utilizes Redis for in-memory storage. | 缓存利用 Redis 做内存存储。 |
| 492 | vanish | 消失 | `A vanishes.` | The race condition vanished after adding a mutex. | 添加互斥锁后，竞态条件消失了。 |
| 493 | vary | 变化；不同 | `A varies. / A varies from B.` | Response times vary depending on the query complexity. | 响应时间因查询复杂度而不同。 |
| 494 | venture | 冒险；敢于 | `A ventures into B.` | The startup ventured into the developer tools space. | 这家创业公司冒险进入了开发者工具领域。 |
| 495 | vest | 归属（期权） | `A vests. / A vests B.` | Your stock options vest over a four-year period. | 你的股票期权分四年归属。 |
| 496 | view | 查看 | `A views B.` | View the container logs. | 查看容器日志。 |
| 497 | visualize | 可视化 | `A visualizes B.` | The dashboard visualizes latency percentiles over time. | 仪表盘将随时间变化的延迟百分位可视化。 |
| 498 | void | 使无效 | `A voids B.` | A failed payment voids the access token. | 支付失败使访问令牌无效。 |
| 499 | wage | 进行 | `A wages B.` | The team wages a constant battle against technical debt. | 团队与技术债进行持续的斗争。 |
| 500 | wait | 等待 | `A waits for B.` | The client waits for a response. | 客户端等待响应。 |
| 501 | wake | 醒来；唤醒 | `A wakes. / A wakes B up.` | The on-call woke up to 50 alerts. | 值班被 50 条告警叫醒。 |
| 502 | walk | 走；遍历 | `A walks through B.` | Let's walk through the deployment steps. | 我们走一遍部署步骤。 |
| 503 | wane | 减弱；衰退 | `A wanes.` | Enthusiasm for the framework waned after performance issues. | 性能问题后对该框架的热情衰退了。 |
| 504 | want | 想要 | `A wants B. / A wants to do B.` | The customer wants a faster solution. | 客户想要更快的方案。 |
| 505 | warp | 扭曲 | `A warps B.` | High load warped the latency measurements. | 高负载扭曲了延迟测量。 |
| 506 | wash | 洗；清洗 | `A washes B.` | The CI pipeline washes stale build artifacts. | CI 流水线清洗过期的构建产物。 |
| 507 | waste | 浪费 | `A wastes B.` | Repeated builds waste time. | 重复构建浪费时间。 |
| 508 | watch | 观察；观看 | `A watches B.` | Watch the service metrics. | 观察服务指标。 |
| 509 | wave | 挥手；波动 | `A waves B. / A waves at B.` | Wave away the flaky test and investigate later. | 先挥手放过这个不稳定测试，稍后排查。 |
| 510 | wear | 穿；磨损 | `A wears B.` | Heavy traffic wears the disk. | 高流量磨损磁盘。 |
| 511 | weigh | 称重；权衡 | `A weighs B against C.` | Weigh the cost of refactoring against the benefits. | 权衡重构的成本与收益。 |
| 512 | win | 赢得 | `A wins B.` | The team won the contract. | 团队赢得了合同。 |
| 513 | wind | 缠绕 | `A winds B.` | Wind down the old service after the migration. | 迁移后逐步停掉旧服务。 |
| 514 | wish | 希望 | `A wishes to do B.` | I wish to improve my English. | 我希望提升英语。 |
| 515 | withstand | 承受；经受住 | `A withstands B.` | The system withstood the Black Friday traffic spike. | 系统经受住了黑五流量高峰。 |
| 516 | witness | 见证；目击 | `A witnesses B.` | We witnessed a 10x traffic increase after launch. | 发布后我们见证了 10 倍流量增长。 |
| 517 | wreck | 毁坏 | `A wrecks B.` | A bad migration wrecked the data integrity. | 一次糟糕的迁移毁坏了数据完整性。 |
| 518 | yield | 产出；让步 | `A yields B.` | The benchmark yielded surprising performance insights. | 基准测试产出了令人意外的性能洞察。 |
| 519 | zero | 归零；聚焦 | `A zeros in on B.` | The debugger zeroed in on the exact failing line. | 调试器聚焦到了确切失败的那一行。 |

### 二、思维与沟通

> 思考、表达、交流、学习、说服——一切围绕信息的输入与输出。（134 个）

| No. | Verb | 中文含义 | 核心句子模板 | 示例 | 中文例句 |
|---:|---|---|---|---|---|
| 520 | accept | 接受 | `A accepts B.` | The system accepts valid tokens. | 系统接受有效令牌。 |
| 521 | acknowledge | 确认收到；承认 | `A acknowledges B. / A acknowledges that S.` | The server acknowledges every request with an ACK. | 服务器用 ACK 确认每个请求。 |
| 522 | address | 处理；解决；向...讲话 | `A addresses B.` | The patch addresses three security issues. | 这个补丁解决了三个安全问题。 |
| 523 | admit | 承认；接纳 | `A admits B. / A admits that S.` | The team admitted the timeline was unrealistic. | 团队承认时间线不切实际。 |
| 524 | advise | 建议 | `A advises B to do C.` | The expert advised us to upgrade. | 专家建议我们升级。 |
| 525 | agree | 同意 | `A agrees with B. / A agrees to do C.` | We agreed to postpone the release. | 我们同意推迟发布。 |
| 526 | announce | 宣布 | `A announces B.` | The team announced a new release. | 团队宣布了新版本。 |
| 527 | apologize | 道歉 | `A apologizes to B for C.` | We apologized for the delay. | 我们为延迟道歉。 |
| 528 | appreciate | 感激；欣赏；理解 | `A appreciates B.` | I appreciate the detailed code review. | 感谢细致的代码评审。 |
| 529 | approve | 批准 | `A approves B.` | The manager approved the plan. | 经理批准了方案。 |
| 530 | argue | 争论；论证 | `A argues that S. / A argues for B.` | She argued for a simpler architecture. | 她论证了更简单的架构。 |
| 531 | assert | 断言 | `A asserts that S.` | The test asserts that the result is valid. | 测试断言结果有效。 |
| 532 | assume | 假设 | `A assumes that S.` | The function assumes the input is valid. | 函数假设输入是有效的。 |
| 533 | assure | 确保；使确信 | `A assures B. / A assures that S.` | The health check assures the service is alive. | 健康检查确保服务是活的。 |
| 534 | believe | 相信 | `A believes that S.` | We believe the issue is resolved. | 我们相信问题已经解决。 |
| 535 | blame | 责备；归咎于 | `A blames B for C.` | Don't blame the tool — check the config first. | 别怪工具，先检查配置。 |
| 536 | brief | 简要汇报 | `A briefs B on C.` | Brief the manager on the deployment status before the stand-up. | 站会前向经理简要汇报部署状态。 |
| 537 | chat | 聊天；闲聊 | `A chats with B about C.` | We chatted about the new architecture over coffee. | 我们喝咖啡时聊了新架构。 |
| 538 | cite | 引用；举例 | `A cites B.` | The report cited three major outages last quarter. | 报告引用了上季度三次重大故障。 |
| 539 | claim | 声称 | `A claims that S.` | The vendor claims the issue is resolved. | 供应商声称问题已解决。 |
| 540 | clarify | 澄清 | `A clarifies B.` | The document clarifies the requirements. | 文档澄清了需求。 |
| 541 | communicate | 沟通；传达 | `A communicates B to C.` | Communicate the outage status clearly to stakeholders. | 向利益相关者清晰传达故障状态。 |
| 542 | complain | 抱怨；投诉 | `A complains about B.` | Users complained about slow responses. | 用户抱怨响应很慢。 |
| 543 | compose | 撰写；组成 | `A composes B.` | The developer composes a detailed commit message. | 开发者撰写详细的提交信息。 |
| 544 | conclude | 得出结论 | `A concludes that S.` | We concluded that the cache caused the issue. | 我们得出结论：缓存导致了问题。 |
| 545 | confirm | 确认 | `A confirms B. / A confirms that S.` | Please confirm the deployment time. | 请确认部署时间。 |
| 546 | congratulate | 祝贺 | `A congratulates B on C.` | The lead congratulated the team on the smooth launch. | 负责人祝贺团队顺利上线。 |
| 547 | consider | 考虑；认为 | `A considers B C. / A considers doing B.` | We considered using Docker. | 我们考虑使用 Docker。 |
| 548 | contend | 竞争（锁/资源） | `A contends for B.` | Multiple goroutines contend for the mutex. | 多个 goroutine 竞争互斥锁。 |
| 549 | convince | 使相信；说服 | `A convinces B that S.` | The data convinced us that the fix worked. | 数据让我们相信修复有效。 |
| 550 | criticize | 批评；评论 | `A criticizes B for C.` | Don't criticize the code without offering a solution. | 不要只批评代码而不给出解决方案。 |
| 551 | debate | 辩论；讨论 | `A debates B. / A debates whether S.` | The team debated whether to adopt a monorepo. | 团队就是否采用 monorepo 进行了辩论。 |
| 552 | debrief | 复盘汇报 | `A debriefs B on C.` | We debriefed the outage with the entire engineering org. | 我们向整个工程团队复盘了故障。 |
| 553 | decide | 决定 | `A decides B. / A decides to do B.` | We decided to upgrade the service. | 我们决定升级服务。 |
| 554 | declare | 声明 | `A declares B.` | The function declares a variable. | 函数声明了一个变量。 |
| 555 | decline | 下降；拒绝 | `A declines. / A declines B.` | The request rate declined after the cache warmed up. | 缓存预热后请求速率下降了。 |
| 556 | define | 定义 | `A defines B as C.` | The spec defines the field as optional. | 规范把该字段定义为可选。 |
| 557 | demand | 要求 | `A demands B.` | The customer demanded a quick fix. | 客户要求快速修复。 |
| 558 | demonstrate | 证明；演示 | `A demonstrates B.` | The demo demonstrates the feature. | 演示展示了该功能。 |
| 559 | deny | 否认；拒绝 | `A denies B.` | The API denied access. | 接口拒绝访问。 |
| 560 | describe | 描述 | `A describes B.` | The document describes the process. | 文档描述了流程。 |
| 561 | determine | 确定 | `A determines B.` | The config determines the behavior. | 配置决定行为。 |
| 562 | disagree | 不同意 | `A disagrees with B.` | I disagree with this approach. | 我不同意这个方法。 |
| 563 | discuss | 讨论 | `A discusses B with C.` | We discussed the risk with the team. | 我们和团队讨论了风险。 |
| 564 | doubt | 怀疑 | `A doubts B. / A doubts that S.` | I doubt the result is correct. | 我怀疑结果是否正确。 |
| 565 | draft | 起草；草拟 | `A drafts B.` | Draft the API spec before coding. | 编码前先起草 API 规范。 |
| 566 | edit | 编辑；修改 | `A edits B.` | Edit the config file to change the timeout. | 编辑配置文件修改超时时间。 |
| 567 | educate | 教育；培训 | `A educates B about C.` | Educate the team about secure coding practices. | 对团队进行安全编码实践培训。 |
| 568 | elaborate | 详细说明 | `A elaborates on B.` | Elaborate on the design decision in the RFC. | 在 RFC 中详细说明设计决策。 |
| 569 | emphasize | 强调；着重 | `A emphasizes B. / A emphasizes that S.` | The post-mortem emphasized the need for better monitoring. | 复盘强调了加强监控的必要性。 |
| 570 | explain | 解释 | `A explains B to C.` | He explained the design to us. | 他向我们解释了设计。 |
| 571 | express | 表达；表示 | `A expresses B.` | The log format expresses events in structured JSON. | 日志格式用结构化 JSON 表达事件。 |
| 572 | float | 漂浮；提出（想法） | `A floats B.` | Float the proposal in the next architecture review. | 在下次架构评审中提出这个提案。 |
| 573 | forget | 忘记 | `A forgets B. / A forgets to do B.` | Don't forget to restart the service. | 不要忘记重启服务。 |
| 574 | forgive | 原谅 | `A forgives B for doing C.` | Forgive the late reply. | 请见谅回复晚了。 |
| 575 | grasp | 理解；抓住 | `A grasps B.` | New hires quickly grasped the deployment flow. | 新人很快掌握了部署流程。 |
| 576 | greet | 问候；迎接 | `A greets B with C.` | The API greets new users with a welcome email. | API 用欢迎邮件迎接新用户。 |
| 577 | guess | 猜测 | `A guesses that S.` | I guess the network is unstable. | 我猜网络不稳定。 |
| 578 | highlight | 突出；强调 | `A highlights B.` | The error log highlights the exact line of failure. | 错误日志高亮了确切的失败行。 |
| 579 | illustrate | 说明；举例说明 | `A illustrates B. / A illustrates how S.` | The diagram illustrates the data flow. | 这张图说明了数据流转。 |
| 580 | imagine | 想象；设想 | `A imagines B. / A imagines that S.` | Imagine the system under peak load. | 想象系统在峰值负载下的情况。 |
| 581 | imply | 暗示；意味着 | `A implies B. / A implies that S.` | A 500 error implies the server crashed. | 500 错误意味着服务器崩溃了。 |
| 582 | indicate | 表明；显示；指示 | `A indicates B. / A indicates that S.` | The logs indicate a memory leak. | 日志表明存在内存泄漏。 |
| 583 | infer | 推断 | `A infers B from C.` | We inferred the cause from the logs. | 我们从日志推断原因。 |
| 584 | inform | 通知 | `A informs B of C. / A informs B that S.` | Please inform the users of the change. | 请通知用户这个变更。 |
| 585 | insist | 坚持；强调 | `A insists on B. / A insists that S.` | The lead insisted on writing tests first. | 负责人坚持先写测试。 |
| 586 | interact | 互动；交流 | `A interacts with B.` | The frontend interacts with the backend via REST APIs. | 前端通过 REST API 与后端交互。 |
| 587 | interrupt | 打断；中断 | `A interrupts B. / A interrupts.` | The signal interrupted the graceful shutdown. | 信号中断了优雅关闭。 |
| 588 | introduce | 介绍；引入 | `A introduces B to C.` | The document introduces the new API. | 文档介绍了新接口。 |
| 589 | joke | 开玩笑 | `A jokes about B. / A jokes that S.` | We joked that the bug was a feature, not a defect. | 我们开玩笑说那个 bug 是特性，不是缺陷。 |
| 590 | judge | 判断 | `A judges B by C.` | We judged the solution by its result. | 我们根据结果判断方案。 |
| 591 | know | 知道 | `A knows B. / A knows that S.` | I know the root cause. | 我知道根因。 |
| 592 | learn | 学习；得知 | `A learns B. / A learns to do B.` | I learned a new debugging method. | 我学到了新的调试方法。 |
| 593 | mention | 提到 | `A mentions B.` | He mentioned a possible risk. | 他提到了一个可能的风险。 |
| 594 | negotiate | 协商 | `A negotiates B with C.` | We negotiated the deadline with the client. | 我们与客户协商截止时间。 |
| 595 | note | 注意；记录；指出 | `A notes B. / A notes that S.` | Note that the API key expires in 30 days. | 注意 API 密钥 30 天后过期。 |
| 596 | notice | 注意到 | `A notices B. / A notices that S.` | I noticed a strange log entry. | 我注意到一条奇怪日志。 |
| 597 | notify | 通知 | `A notifies B about C.` | The system notified the admin. | 系统通知了管理员。 |
| 598 | object | 反对 | `A objects to B.` | The reviewer objected to the tight coupling. | 评审者反对这种紧耦合。 |
| 599 | outline | 概述；勾画轮廓 | `A outlines B.` | The RFC outlines the new architecture. | RFC 概述了新架构。 |
| 600 | perceive | 感知；认为 | `A perceives B as C.` | Users perceive latency above 200ms as slow. | 用户将 200ms 以上的延迟感知为慢。 |
| 601 | persuade | 说服 | `A persuades B to do C.` | He persuaded the team to simplify the design. | 他说服团队简化设计。 |
| 602 | pitch | 推介；推销（想法） | `A pitches B to C.` | The developer pitched the refactoring idea to the tech lead. | 开发者向技术负责人推介了重构想法。 |
| 603 | practice | 练习 | `A practices B. / A practices doing B.` | Practice writing short sentences. | 练习写短句。 |
| 604 | praise | 赞美；表扬 | `A praises B for C.` | The tech lead praised the clean error handling. | 技术负责人表扬了清晰的错误处理。 |
| 605 | present | 展示；呈现 | `A presents B to C.` | She presented the proposal to the team. | 她向团队展示了方案。 |
| 606 | promise | 承诺 | `A promises to do B.` | We promised to deliver it this week. | 我们承诺本周交付。 |
| 607 | pronounce | 发音；宣称 | `A pronounces B.` | Can you pronounce the name of this library correctly? | 你能正确念出这个库的名字吗？ |
| 608 | propose | 提出 | `A proposes B.` | We proposed a new architecture. | 我们提出了新架构。 |
| 609 | prove | 证明 | `A proves B. / A proves that S.` | The result proves the fix works. | 结果证明修复有效。 |
| 610 | question | 质疑；询问 | `A questions B.` | The auditor questioned the access control design. | 审计员质疑了访问控制设计。 |
| 611 | quote | 引用 | `A quotes B.` | The report quoted customer feedback. | 报告引用了客户反馈。 |
| 612 | read | 阅读 | `A reads B.` | Read the error message carefully. | 仔细阅读错误信息。 |
| 613 | realize | 意识到 | `A realizes that S.` | I realized the config was wrong. | 我意识到配置错了。 |
| 614 | recall | 回忆；回想 | `A recalls B. / A recalls that S.` | I can't recall the exact error message. | 我记不清确切的错误信息了。 |
| 615 | recap | 概括；回顾 | `A recaps B.` | Recap the key decisions at the end of the meeting. | 会议结束时回顾关键决策。 |
| 616 | reckon | 认为；估计 | `A reckons that S. / A reckons B.` | I reckon the fix will take two hours. | 我估计这个修复要花两小时。 |
| 617 | recognize | 识别；认可 | `A recognizes B.` | The system recognizes the pattern. | 系统识别出这个模式。 |
| 618 | recommend | 推荐 | `A recommends B to C.` | The architect recommended this framework. | 架构师推荐了这个框架。 |
| 619 | refuse | 拒绝 | `A refuses B. / A refuses to do B.` | The server refused the connection due to an invalid cert. | 服务器因证书无效拒绝了连接。 |
| 620 | reject | 拒绝 | `A rejects B.` | The server rejected the request. | 服务器拒绝了请求。 |
| 621 | remember | 记住 | `A remembers B. / A remembers to do B.` | Remember to update the config. | 记得更新配置。 |
| 622 | remind | 提醒 | `A reminds B to do C.` | Remind me to check the logs. | 提醒我检查日志。 |
| 623 | reply | 回复 | `A replies to B.` | I replied to the email. | 我回复了邮件。 |
| 624 | report | 报告 | `A reports B to C.` | The agent reports errors to the server. | 代理向服务器报告错误。 |
| 625 | request | 请求 | `A requests B from C.` | The client requested more resources. | 客户端请求更多资源。 |
| 626 | require | 要求；需要 | `A requires B to do C.` | This feature requires user permission. | 这个功能需要用户权限。 |
| 627 | resolve | 解决 | `A resolves B.` | We resolved the conflict. | 我们解决了冲突。 |
| 628 | respond | 回应 | `A responds to B.` | The server responded quickly. | 服务器响应很快。 |
| 629 | shout | 喊叫；大声说 | `A shouts. / A shouts about B.` | The error logs are shouting at us. | 错误日志在对我们喊叫。 |
| 630 | show | 显示；展示 | `A shows B. / A shows that S.` | The logs show a timeout. | 日志显示发生了超时。 |
| 631 | specify | 指定；明确说明 | `A specifies B.` | Specify the port number in the config file. | 在配置文件中指定端口号。 |
| 632 | spell | 拼写；意味着 | `A spells B. / A spells out B.` | A missing semicolon spells trouble. | 遗漏一个分号意味着麻烦。 |
| 633 | state | 陈述 | `A states that S.` | The report states that the system is stable. | 报告称系统是稳定的。 |
| 634 | study | 学习；研究 | `A studies B.` | We studied the root cause for hours. | 我们研究了数小时根因。 |
| 635 | suggest | 建议 | `A suggests B. / A suggests doing B.` | I suggest using a simple solution. | 我建议使用简单方案。 |
| 636 | summarize | 总结 | `A summarizes B.` | Please summarize the meeting notes. | 请总结会议纪要。 |
| 637 | suppose | 假设；认为 | `A supposes that S.` | Suppose the cache is empty. | 假设缓存为空。 |
| 638 | swear | 发誓；咒骂 | `A swears by B. / A swears that S.` | The SRE team swears by infrastructure as code. | SRE 团队坚信基础设施即代码。 |
| 639 | teach | 教 | `A teaches B C. / A teaches C to B.` | He taught us a useful pattern. | 他教了我们一个有用的模式。 |
| 640 | thank | 感谢 | `A thanks B for C.` | Thank you for your support. | 感谢你的支持。 |
| 641 | think | 认为；思考 | `A thinks that S. / A thinks about B.` | I think this design is better. | 我认为这个设计更好。 |
| 642 | train | 训练 | `A trains B to do C.` | The team trained the model. | 团队训练了模型。 |
| 643 | translate | 翻译 | `A translates B into C.` | Translate this sentence into English. | 把这个句子翻译成英文。 |
| 644 | underline | 强调；在...下划线 | `A underlines B.` | This incident underlines the need for better monitoring. | 这次故障强调了加强监控的必要性。 |
| 645 | understand | 理解 | `A understands B.` | We understand the customer's concern. | 我们理解客户的担忧。 |
| 646 | urge | 催促；强烈建议 | `A urges B to do C.` | The security audit urged the team to patch immediately. | 安全审计催促团队立即打补丁。 |
| 647 | voice | 表达；说出 | `A voices B.` | She voiced her concerns about the timeline. | 她表达了对时间表的担忧。 |
| 648 | warn | 警告 | `A warns B about C.` | The tool warned us about vulnerabilities. | 工具警告我们存在漏洞。 |
| 649 | welcome | 欢迎 | `A welcomes B.` | We welcome contributions to the project. | 我们欢迎对项目的贡献。 |
| 650 | whisper | 轻声说；耳语 | `A whispers B to C.` | The debug log whispers hints about the memory leak. | 调试日志轻声透露了内存泄漏的线索。 |
| 651 | wonder | 想知道；好奇 | `A wonders whether S. / A wonders about B.` | I wonder if the fix worked. | 我想知道修复是否生效了。 |
| 652 | write | 写 | `A writes B.` | I wrote the deployment guide. | 我写了部署指南。 |
| 653 | yell | 大喊；叫嚷 | `A yells at B. / A yells.` | The error logs are yelling at us to fix the config. | 错误日志在对我们大喊快修配置。 |

### 三、工程与技术

> 编码、测试、部署、运维、调试——软件工程师的日常工具箱。（127 个）

| No. | Verb | 中文含义 | 核心句子模板 | 示例 | 中文例句 |
|---:|---|---|---|---|---|
| 654 | access | 访问；获取 | `A accesses B.` | The app accesses the camera after permission is granted. | 应用在获得权限后访问摄像头。 |
| 655 | activate | 激活 | `A activates B.` | The license activates the feature. | 许可证会激活这个功能。 |
| 656 | adapt | 适应；改编 | `A adapts to B. / A adapts B.` | The system adapts to changing traffic patterns. | 系统适应不断变化的流量模式。 |
| 657 | architect | 设计架构 | `A architects B.` | She architected the new platform. | 她设计了新平台架构。 |
| 658 | archive | 归档 | `A archives B.` | Archive old logs monthly. | 每月归档旧日志。 |
| 659 | attach | 附上；连接；附加 | `A attaches B to C.` | Attach the debugger to the running process. | 将调试器附加到运行中的进程。 |
| 660 | audit | 审计 | `A audits B.` | The team audited the access logs. | 团队审计了访问日志。 |
| 661 | automate | 自动化 | `A automates B.` | Automate the entire CI/CD pipeline to save time. | 自动化整条 CI/CD 流水线以节省时间。 |
| 662 | back | 支持；回退 | `A backs B. / A backs up B.` | Always back up the database before migration. | 迁移前务必备份数据库。 |
| 663 | benchmark | 基准测试 | `A benchmarks B.` | We benchmarked the new implementation. | 我们对新实现做了基准测试。 |
| 664 | boot | 启动 | `A boots B.` | The system boots quickly. | 系统启动很快。 |
| 665 | bootstrap | 引导启动；初始化 | `A bootstraps B.` | The script bootstraps the development environment. | 脚本引导启动开发环境。 |
| 666 | branch | 创建分支 | `A branches from B.` | Create a branch from main. | 从主分支创建一个分支。 |
| 667 | browse | 浏览；翻阅 | `A browses B.` | Browse the API documentation before opening a ticket. | 开工单前先浏览 API 文档。 |
| 668 | build | 构建 | `A builds B.` | The pipeline builds the image. | 流水线构建镜像。 |
| 669 | checkout | 检出 | `A checks out B.` | Check out the feature branch. | 检出功能分支。 |
| 670 | click | 点击 | `A clicks B. / A clicks on B.` | Click the deploy button and monitor the logs. | 点击部署按钮并监控日志。 |
| 671 | clone | 克隆 | `A clones B.` | Clone the repository. | 克隆仓库。 |
| 672 | code | 编码 | `A codes B.` | He coded the core logic. | 他编写了核心逻辑。 |
| 673 | commit | 提交 | `A commits B.` | Commit the code changes. | 提交代码改动。 |
| 674 | compile | 编译 | `A compiles B.` | The compiler compiles the source code. | 编译器编译源代码。 |
| 675 | compress | 压缩 | `A compresses B.` | Compress the log files. | 压缩日志文件。 |
| 676 | configure | 配置 | `A configures B.` | Configure the database connection. | 配置数据库连接。 |
| 677 | construct | 构建；构造 | `A constructs B.` | The builder pattern constructs complex objects step by step. | 建造者模式逐步构造复杂对象。 |
| 678 | control | 控制；管理 | `A controls B.` | This feature flag controls the rollout. | 这个功能标志控制灰度发布。 |
| 679 | cope | 应对；处理 | `A copes with B.` | The thread pool helps the server cope with bursts. | 线程池帮助服务器应对突发流量。 |
| 680 | deactivate | 停用 | `A deactivates B.` | The admin deactivated the account. | 管理员停用了该账号。 |
| 681 | debug | 调试 | `A debugs B.` | We debugged the payment issue. | 我们调试了支付问题。 |
| 682 | decompress | 解压 | `A decompresses B.` | The script decompresses the archive. | 脚本解压归档文件。 |
| 683 | deploy | 部署 | `A deploys B to C.` | We deployed the app to production. | 我们把应用部署到生产环境。 |
| 684 | deprecate | 弃用（旧 API/方法） | `A deprecates B.` | The team deprecated the v1 endpoint in favor of v2. | 团队弃用了 v1 端点，改用 v2。 |
| 685 | deserialize | 反序列化 | `A deserializes B.` | The server deserializes the request body. | 服务器反序列化请求体。 |
| 686 | design | 设计 | `A designs B.` | We designed a simple API. | 我们设计了一个简单接口。 |
| 687 | develop | 开发 | `A develops B.` | The team developed a new module. | 团队开发了一个新模块。 |
| 688 | diagnose | 诊断 | `A diagnoses B.` | The tool diagnosed a DNS issue. | 工具诊断出 DNS 问题。 |
| 689 | disable | 禁用 | `A disables B.` | We disabled the old API. | 我们禁用了旧接口。 |
| 690 | display | 显示；展示 | `A displays B.` | The dashboard displays real-time latency metrics. | 仪表盘显示实时延迟指标。 |
| 691 | downgrade | 降级 | `A downgrades B to C.` | We downgraded the dependency. | 我们降级了依赖。 |
| 692 | download | 下载 | `A downloads B from C.` | Download the package from the mirror. | 从镜像站下载包。 |
| 693 | enable | 启用 | `A enables B.` | This option enables debug mode. | 这个选项启用调试模式。 |
| 694 | enhance | 增强 | `A enhances B.` | The patch enhances security. | 补丁增强了安全性。 |
| 695 | execute | 执行 | `A executes B.` | The script executes the command. | 脚本执行命令。 |
| 696 | fork | 派生 | `A forks B.` | Fork the open-source project. | 派生这个开源项目。 |
| 697 | frame | 设计；表述 | `A frames B as C.` | Frame the proposal in terms of business value. | 从业务价值的角度表述这个提案。 |
| 698 | generalize | 概括；泛化 | `A generalizes B.` | Generalize the helper function to handle all edge cases. | 泛化辅助函数以处理所有边界情况。 |
| 699 | handle | 处理 | `A handles B.` | The service handles user requests. | 服务处理用户请求。 |
| 700 | ignite | 点燃；启动 | `A ignites B.` | A single tweet ignited a debate about REST vs GraphQL. | 一条推特点燃了 REST vs GraphQL 的争论。 |
| 701 | implement | 实现 | `A implements B.` | We implemented the login feature. | 我们实现了登录功能。 |
| 702 | initialize | 初始化 | `A initializes B.` | The app initializes the cache. | 应用初始化缓存。 |
| 703 | inject | 注入 | `A injects B into C.` | Dependency injection injects the logger into the service. | 依赖注入将日志器注入到服务中。 |
| 704 | install | 安装 | `A installs B.` | Install the latest SDK. | 安装最新 SDK。 |
| 705 | instantiate | 实例化 | `A instantiates B.` | The code instantiates a new object. | 代码实例化一个新对象。 |
| 706 | integrate | 集成 | `A integrates B with C.` | We integrated the app with OAuth. | 我们把应用与 OAuth 集成。 |
| 707 | intercept | 拦截（请求） | `A intercepts B.` | The middleware intercepts every incoming request. | 中间件拦截每个传入请求。 |
| 708 | interpret | 解释；解读 | `A interprets B as C.` | The parser interprets JSON into a data structure. | 解析器将 JSON 解读为数据结构。 |
| 709 | investigate | 调查；排查 | `A investigates B.` | We investigated the timeout. | 我们排查了超时问题。 |
| 710 | invoke | 调用 | `A invokes B.` | The handler invokes the service. | 处理器调用服务。 |
| 711 | kick | 踢；启动 | `A kicks B. / A kicks off B.` | The cron job kicks off every hour. | 定时任务每小时启动一次。 |
| 712 | launch | 上线；启动 | `A launches B.` | We launched the new feature. | 我们上线了新功能。 |
| 713 | login | 登录 | `A logins to B.` | Login to the server via SSH with your key. | 用你的密钥通过 SSH 登录服务器。 |
| 714 | logout | 登出 | `A logouts of B.` | Logout of the admin panel when you're done. | 完成后从管理面板登出。 |
| 715 | maintain | 维护 | `A maintains B.` | The team maintains this service. | 团队维护这个服务。 |
| 716 | marshall | 编组（数据） | `A marshalls B into C.` | Marshall the struct into JSON before sending. | 发送前将结构体编组为 JSON。 |
| 717 | merge | 合并 | `A merges B into C.` | Merge the branch into main. | 把分支合并到主干。 |
| 718 | migrate | 迁移 | `A migrates B from C to D.` | We migrated data to the new database. | 我们把数据迁移到新数据库。 |
| 719 | mock | 模拟 | `A mocks B.` | The test mocks the database. | 测试模拟数据库。 |
| 720 | mount | 安装；挂载；增加 | `A mounts B.` | Mount the persistent volume before starting the pod. | 启动 pod 前挂载持久卷。 |
| 721 | navigate | 导航；浏览 | `A navigates B.` | The CLI helps users navigate the configuration options. | CLI 帮助用户浏览配置选项。 |
| 722 | offload | 卸载；分流 | `A offloads B to C.` | Offload CPU-intensive tasks to a worker queue. | 将 CPU 密集型任务分流到工作队列。 |
| 723 | operate | 操作；运营 | `A operates B.` | The team operates the platform. | 团队运营这个平台。 |
| 724 | optimize | 优化 | `A optimizes B.` | We optimized the query. | 我们优化了查询。 |
| 725 | orchestrate | 编排（容器/服务） | `A orchestrates B.` | Kubernetes orchestrates hundreds of containers. | Kubernetes 编排数百个容器。 |
| 726 | override | 覆盖；重写 | `A overrides B.` | The subclass overrides the default validation logic. | 子类覆盖了默认校验逻辑。 |
| 727 | package | 打包 | `A packages B.` | The script packages the application. | 脚本打包应用。 |
| 728 | parse | 解析 | `A parses B.` | The parser parses the JSON file. | 解析器解析 JSON 文件。 |
| 729 | patch | 打补丁 | `A patches B.` | Patch the vulnerable library. | 给有漏洞的库打补丁。 |
| 730 | perform | 执行；表现 | `A performs B.` | The system performs a security check. | 系统执行安全检查。 |
| 731 | pin | 固定；锁定版本 | `A pins B to C.` | Pin the dependency to a specific version for reproducibility. | 将依赖锁定到特定版本以确保可复现性。 |
| 732 | port | 移植（代码） | `A ports B to C.` | Port the Python script to Go for better performance. | 将 Python 脚本移植到 Go 以获得更好性能。 |
| 733 | power | 供电；驱动；快速启动 | `A powers B. / A powers up B.` | This one config file powers the entire service mesh. | 这一个配置文件驱动着整个服务网格。 |
| 734 | preserve | 保留；维护 | `A preserves B.` | Preserve the original error context when re-throwing. | 重新抛出时保留原始错误上下文。 |
| 735 | probe | 探测；探查 | `A probes B.` | The readiness probe checks if the container is alive. | 就绪探针检查容器是否存活。 |
| 736 | process | 处理 | `A processes B.` | The worker processes messages. | 工作线程处理消息。 |
| 737 | profile | 性能分析 | `A profiles B.` | The tool profiles CPU usage. | 工具分析 CPU 使用。 |
| 738 | program | 编程 | `A programs B.` | The robot is programmed to stop. | 机器人被编程为停止。 |
| 739 | provision | 配置/供给（基础设施） | `A provisions B.` | Terraform provisions the cloud infrastructure. | Terraform 配置云基础设施。 |
| 740 | publish | 发布 | `A publishes B to C.` | The service publishes events to Kafka. | 服务向 Kafka 发布事件。 |
| 741 | rebase | 变基 | `A rebases B onto C.` | Rebase your branch onto main. | 把你的分支变基到主分支。 |
| 742 | refactor | 重构 | `A refactors B.` | We refactored the old module. | 我们重构了旧模块。 |
| 743 | refresh | 刷新；更新 | `A refreshes B.` | Refresh the access token before it expires. | 令牌过期前刷新访问令牌。 |
| 744 | release | 发布 | `A releases B.` | The team released version 2.0. | 团队发布了 2.0 版本。 |
| 745 | render | 渲染；使成为 | `A renders B. / A renders B C.` | The browser renders the page in milliseconds. | 浏览器在毫秒内渲染页面。 |
| 746 | reproduce | 复现 | `A reproduces B.` | I reproduced the bug locally. | 我在本地复现了缺陷。 |
| 747 | reset | 重置 | `A resets B.` | Reset the password. | 重置密码。 |
| 748 | restart | 重启 | `A restarts B.` | Restart the service. | 重启服务。 |
| 749 | restructure | 重组；重构 | `A restructures B.` | Restructure the monolith into domain-driven modules. | 将单体重构为领域驱动的模块。 |
| 750 | retire | 退休；淘汰；停用 | `A retires B.` | Retire the legacy API after all clients migrate to v2. | 所有客户端迁移到 v2 后停用旧 API。 |
| 751 | revert | 恢复；回退 | `A reverts B.` | Revert the breaking commit before it reaches production. | 在到达生产环境前回退这个破坏性提交。 |
| 752 | rollback | 回滚 | `A rolls back B to C.` | We rolled back the release. | 我们回滚了发布。 |
| 753 | scan | 扫描 | `A scans B for C.` | The scanner scans images for vulnerabilities. | 扫描器扫描镜像漏洞。 |
| 754 | scroll | 滚动；翻阅 | `A scrolls through B.` | Scroll through the logs to find the first error. | 翻阅日志找到第一个错误。 |
| 755 | serialize | 序列化 | `A serializes B.` | The library serializes the object. | 库将对象序列化。 |
| 756 | shutdown | 关闭 | `A shuts down B.` | Shut down the server safely. | 安全关闭服务器。 |
| 757 | simplify | 简化 | `A simplifies B.` | We simplified the workflow. | 我们简化了流程。 |
| 758 | simulate | 模拟 | `A simulates B.` | Simulate 10,000 concurrent users with a load test. | 用负载测试模拟 10000 并发用户。 |
| 759 | stash | 储藏（git stash） | `A stashes B.` | Stash your uncommitted changes before pulling. | 拉取前储藏未提交的改动。 |
| 760 | stub | 打桩 | `A stubs B.` | The unit test stubs the external API. | 单元测试为外部接口打桩。 |
| 761 | subscribe | 订阅 | `A subscribes to B.` | The client subscribes to the topic. | 客户端订阅该主题。 |
| 762 | support | 支持 | `A supports B.` | The API supports pagination. | 接口支持分页。 |
| 763 | tackle | 处理；解决 | `A tackles B.` | The sprint tackled three performance issues. | 这个迭代处理了三个性能问题。 |
| 764 | tag | 打标签 | `A tags B as C.` | Tag the release as v1.0. | 把发布标记为 v1.0。 |
| 765 | test | 测试 | `A tests B.` | We tested the API. | 我们测试了接口。 |
| 766 | throttle | 节流；限速 | `A throttles B.` | The API gateway throttles requests above 1000 per second. | API 网关对超过每秒 1000 次的请求限速。 |
| 767 | time | 计时；安排时间 | `A times B.` | Time the API call to see if the optimization worked. | 给 API 调用计时看优化是否生效。 |
| 768 | trace | 追踪 | `A traces B.` | The tool traces slow requests. | 工具追踪慢请求。 |
| 769 | treat | 对待；处理 | `A treats B as C.` | Treat all input as untrusted. | 将所有输入视为不可信。 |
| 770 | trigger | 触发 | `A triggers B.` | The button triggers a request. | 按钮触发请求。 |
| 771 | troubleshoot | 排查故障 | `A troubleshoots B.` | The on-call engineer troubleshoots the production issue. | 值班工程师排查生产问题。 |
| 772 | tune | 调优 | `A tunes B.` | Tune the garbage collector for low-latency workloads. | 为低延迟工作负载调优垃圾回收器。 |
| 773 | undo | 撤销 | `A undoes B.` | The transaction can undo all changes on failure. | 事务可以在失败时撤销所有更改。 |
| 774 | uninstall | 卸载 | `A uninstalls B.` | Uninstall the old plugin. | 卸载旧插件。 |
| 775 | unload | 卸载；取消加载 | `A unloads B.` | The system unloaded the module. | 系统卸载了该模块。 |
| 776 | unmarshall | 解组（数据） | `A unmarshalls B into C.` | Unmarshall the JSON response into a typed struct. | 将 JSON 响应解组为类型化结构体。 |
| 777 | unmount | 卸载（挂载点） | `A unmounts B.` | Unmount the persistent volume before detaching the disk. | 分离磁盘前先卸载持久卷。 |
| 778 | upgrade | 升级 | `A upgrades B to C.` | Upgrade the database to version 8. | 把数据库升级到 8 版本。 |
| 779 | upload | 上传 | `A uploads B to C.` | Upload the image to the bucket. | 把图片上传到桶。 |
| 780 | work | 工作；运行 | `A works. / A works on B.` | The new version works well. | 新版本运行良好。 |

### 四、数据与安全

> 数据的全生命周期：存取、转换、加密、备份、监控与防护。（99 个）

| No. | Verb | 中文含义 | 核心句子模板 | 示例 | 中文例句 |
|---:|---|---|---|---|---|
| 781 | aggregate | 聚合 | `A aggregates B.` | The report aggregates daily data. | 报告聚合每日数据。 |
| 782 | attack | 攻击 | `A attacks B.` | Bots attacked the login endpoint. | 机器人攻击登录接口。 |
| 783 | authenticate | 认证 | `A authenticates B.` | The system authenticates the user. | 系统认证用户。 |
| 784 | authorize | 授权 | `A authorizes B to do C.` | The admin authorized him to access the database. | 管理员授权他访问数据库。 |
| 785 | backup | 备份 | `A backs up B.` | Back up the database before release. | 发布前备份数据库。 |
| 786 | batch | 批量处理 | `A batches B.` | Batch the INSERT statements for better performance. | 批量执行 INSERT 语句以获得更好性能。 |
| 787 | bypass | 绕过 | `A bypasses B.` | The attacker bypassed the check. | 攻击者绕过了检查。 |
| 788 | cache | 缓存 | `A caches B.` | The browser caches static files. | 浏览器缓存静态文件。 |
| 789 | certify | 认证；证明 | `A certifies B.` | The authority certifies the certificate. | 机构认证证书。 |
| 790 | check | 检查 | `A checks B.` | Check the configuration. | 检查配置。 |
| 791 | coalesce | 合并（请求/事件） | `A coalesces B into C.` | The middleware coalesces multiple requests into one. | 中间件将多个请求合并为一个。 |
| 792 | convert | 转换 | `A converts B into C.` | Convert the file into JSON. | 把文件转换为 JSON。 |
| 793 | copy | 复制 | `A copies B to C.` | Copy the file to the server. | 把文件复制到服务器。 |
| 794 | corrupt | 损坏 | `A corrupts B.` | The crash corrupted the file. | 崩溃损坏了文件。 |
| 795 | decode | 解码 | `A decodes B.` | The server decodes the token. | 服务器解码令牌。 |
| 796 | decrypt | 解密 | `A decrypts B.` | The app decrypts the message. | 应用解密消息。 |
| 797 | deduplicate | 去重 | `A deduplicates B.` | The pipeline deduplicates events before processing. | 流水线在处理前去重事件。 |
| 798 | defend | 防御 | `A defends B against C.` | The firewall defends the system against attacks. | 防火墙保护系统免受攻击。 |
| 799 | delete | 删除 | `A deletes B.` | The cleanup job deletes old logs. | 清理任务会删除旧日志。 |
| 800 | detect | 检测到 | `A detects B.` | The scanner detected a vulnerability. | 扫描器检测到一个漏洞。 |
| 801 | document | 记录；写文档 | `A documents B.` | Document the new API. | 为新接口写文档。 |
| 802 | drain | 排空（连接/队列） | `A drains B.` | Drain the connection pool before restarting. | 重启前排空连接池。 |
| 803 | duplicate | 复制；重复 | `A duplicates B.` | Duplicate the staging environment for load testing. | 复制预发布环境用于负载测试。 |
| 804 | encode | 编码 | `A encodes B.` | The client encodes the URL. | 客户端编码 URL。 |
| 805 | encrypt | 加密 | `A encrypts B.` | The service encrypts sensitive data. | 服务加密敏感数据。 |
| 806 | evict | 逐出（缓存） | `A evicts B from C.` | Redis evicts the least recently used keys first. | Redis 优先逐出最近最少使用的键。 |
| 807 | expire | 过期（TTL/会话） | `A expires. / A expires after B.` | The session expires after 30 minutes of inactivity. | 会话在 30 分钟无活动后过期。 |
| 808 | exploit | 利用 | `A exploits B.` | The attacker exploited a vulnerability. | 攻击者利用了漏洞。 |
| 809 | export | 导出 | `A exports B to C.` | Export the dashboard as a shareable JSON file. | 将仪表盘导出为可共享的 JSON 文件。 |
| 810 | expose | 暴露 | `A exposes B.` | The container exposes port 80. | 容器暴露 80 端口。 |
| 811 | extract | 提取；抽取 | `A extracts B from C.` | Extract the shared logic into a utility module. | 把共享逻辑提取到工具模块。 |
| 812 | fetch | 获取 | `A fetches B from C.` | The client fetches data from the API. | 客户端从接口获取数据。 |
| 813 | filter | 过滤 | `A filters B.` | The query filters invalid records. | 查询过滤无效记录。 |
| 814 | flush | 刷新；清空 | `A flushes B.` | Flush the Redis cache. | 清空 Redis 缓存。 |
| 815 | format | 格式化 | `A formats B.` | The tool formats the code. | 工具格式化代码。 |
| 816 | guard | 守卫；防范 | `A guards against B. / A guards B.` | Input validation guards against injection attacks. | 输入校验防范注入攻击。 |
| 817 | hash | 哈希 | `A hashes B.` | The system hashes the password. | 系统对密码做哈希。 |
| 818 | hide | 隐藏 | `A hides B.` | The UI hides advanced options. | 界面隐藏高级选项。 |
| 819 | hydrate | 填充（缓存/对象） | `A hydrates B with C.` | Hydrate the user object with data from the database. | 用数据库中的数据填充用户对象。 |
| 820 | identify | 识别；确定 | `A identifies B.` | We identified the root cause. | 我们确定了根因。 |
| 821 | import | 导入；输入 | `A imports B into C.` | Import the CSV data into the analytics database. | 将 CSV 数据导入分析数据库。 |
| 822 | index | 索引 | `A indexes B.` | The engine indexes documents. | 引擎索引文档。 |
| 823 | insert | 插入 | `A inserts B into C.` | Insert the record into the table. | 把记录插入表中。 |
| 824 | instrument | 插桩（代码/监控） | `A instruments B.` | Instrument the code with OpenTelemetry traces. | 用 OpenTelemetry 追踪插桩代码。 |
| 825 | invalidate | 使失效（缓存） | `A invalidates B.` | Invalidate the cache after updating the record. | 更新记录后使缓存失效。 |
| 826 | join | 连接；加入 | `A joins B with C.` | The query joins two tables. | 查询连接两个表。 |
| 827 | leak | 泄露 | `A leaks B.` | The bug leaked memory. | 这个缺陷导致内存泄漏。 |
| 828 | load | 加载 | `A loads B.` | The app loads the config at startup. | 应用启动时加载配置。 |
| 829 | log | 记录日志 | `A logs B.` | The service logs every request. | 服务记录每个请求。 |
| 830 | map | 映射 | `A maps B to C.` | The function maps IDs to names. | 函数把 ID 映射到名称。 |
| 831 | mask | 遮蔽；脱敏 | `A masks B.` | The system masks sensitive fields. | 系统对敏感字段脱敏。 |
| 832 | match | 匹配；相符 | `A matches B.` | The test output must match the expected snapshot. | 测试输出必须匹配预期快照。 |
| 833 | mine | 挖掘（数据/日志） | `A mines B for C.` | Mine the logs for patterns before the outage. | 挖掘日志中以找出故障前的模式。 |
| 834 | monitor | 监控 | `A monitors B.` | The platform monitors service health. | 平台监控服务健康状态。 |
| 835 | normalize | 规范化 | `A normalizes B.` | Normalize the input before saving. | 保存前规范化输入。 |
| 836 | partition | 分区 | `A partitions B by C.` | Partition the table by date for faster queries. | 按日期对表分区以加快查询。 |
| 837 | paste | 粘贴 | `A pastes B into C.` | Paste the token into the config. | 把令牌粘贴到配置中。 |
| 838 | poll | 轮询；拉取 | `A polls B.` | The client polls the server every 5 seconds for updates. | 客户端每 5 秒轮询服务器获取更新。 |
| 839 | populate | 填充；写入数据 | `A populates B with C.` | The migration populates the new column with default values. | 迁移用默认值填充新列。 |
| 840 | prefetch | 预取 | `A prefetches B.` | The CPU prefetches data into the cache before it's needed. | CPU 在需要之前将数据预取到缓存中。 |
| 841 | preload | 预加载 | `A preloads B.` | Preload the critical CSS to speed up rendering. | 预加载关键 CSS 以加速渲染。 |
| 842 | print | 打印；输出 | `A prints B.` | The program prints the result. | 程序输出结果。 |
| 843 | propagate | 传播（上下文/追踪） | `A propagates B to C.` | Propagate the trace context across service boundaries. | 跨服务边界传播追踪上下文。 |
| 844 | protect | 保护 | `A protects B from C.` | Encryption protects data from leakage. | 加密保护数据不泄露。 |
| 845 | purge | 清除（数据/队列） | `A purges B.` | Purge the dead-letter queue after investigating. | 调查后清除死信队列。 |
| 846 | query | 查询 | `A queries B.` | The service queries the database. | 服务查询数据库。 |
| 847 | queue | 排队 | `A queues B.` | The system queues requests. | 系统将请求排队。 |
| 848 | replicate | 复制；同步副本 | `A replicates B to C.` | The database replicates data to replicas. | 数据库向副本复制数据。 |
| 849 | reshard | 重新分片 | `A reshards B.` | The database reshards data across new nodes. | 数据库跨新节点重新分片数据。 |
| 850 | restore | 恢复 | `A restores B.` | Restore the data from backup. | 从备份恢复数据。 |
| 851 | retrieve | 检索；获取 | `A retrieves B from C.` | Retrieve the user profile from the cache first. | 首先从缓存中检索用户资料。 |
| 852 | reveal | 揭示；透露；显示 | `A reveals B. / A reveals that S.` | The flame graph revealed the CPU bottleneck instantly. | 火焰图立刻揭示了 CPU 瓶颈。 |
| 853 | safeguard | 保护 | `A safeguards B from C.` | Circuit breakers safeguard the system from cascading failures. | 断路器保护系统免受级联故障。 |
| 854 | sample | 抽样；采样 | `A samples B.` | The profiler samples CPU usage every 10ms. | 分析器每 10ms 采样一次 CPU 使用。 |
| 855 | sanitize | 净化；清理 | `A sanitizes B.` | Sanitize user input. | 清理用户输入。 |
| 856 | scrape | 爬取（web scraping） | `A scrapes B.` | The crawler scrapes product data from e-commerce sites. | 爬虫从电商网站爬取商品数据。 |
| 857 | search | 搜索 | `A searches B for C.` | The app searches the database for users. | 应用在数据库中搜索用户。 |
| 858 | secure | 保护；使安全 | `A secures B.` | Use HTTPS to secure traffic. | 使用 HTTPS 保护流量。 |
| 859 | seed | 播种（数据库初始数据） | `A seeds B with C.` | Seed the database with test fixtures before integration tests. | 集成测试前用测试夹具填充数据库。 |
| 860 | shard | 分片 | `A shards B across C.` | Shard the user data across three database instances. | 将用户数据分片到三个数据库实例。 |
| 861 | shield | 屏蔽；防护 | `A shields B from C.` | A rate limiter shields the backend from abuse. | 限流器屏蔽后端免遭滥用。 |
| 862 | sign | 签名 | `A signs B.` | The client signs the request. | 客户端对请求签名。 |
| 863 | sort | 排序 | `A sorts B.` | The system sorts results by time. | 系统按时间排序结果。 |
| 864 | split | 拆分 | `A splits B into C.` | Split the file into smaller parts. | 把文件拆成更小的部分。 |
| 865 | stale | 变陈旧（数据/缓存） | `A stales. / A becomes stale.` | The cached token went stale after one hour. | 缓存令牌一小时后变陈旧。 |
| 866 | store | 存储 | `A stores B in C.` | The app stores tokens in memory. | 应用将令牌存在内存中。 |
| 867 | stream | 流式传输 | `A streams B to C.` | The server streams logs to the monitoring dashboard. | 服务器将日志流式传输到监控仪表盘。 |
| 868 | sweep | 扫；清理 | `A sweeps B.` | The garbage collector sweeps unreachable objects. | 垃圾回收器清理不可达对象。 |
| 869 | sync | 同步 | `A syncs B with C.` | Sync local files with the server. | 同步本地文件和服务器。 |
| 870 | track | 跟踪 | `A tracks B.` | We track progress every day. | 我们每天跟踪进展。 |
| 871 | transfer | 转移；传输 | `A transfers B to C.` | Transfer the file to the remote server via SCP. | 通过 SCP 将文件传输到远程服务器。 |
| 872 | transform | 转换 | `A transforms B into C.` | The job transforms raw data into reports. | 任务把原始数据转换成报告。 |
| 873 | truncate | 截断（字符串/表） | `A truncates B.` | The log output truncates long messages at 200 characters. | 日志输出将长消息截断为 200 字符。 |
| 874 | update | 更新 | `A updates B.` | The job updates user status. | 任务更新用户状态。 |
| 875 | vacuum | 清理（数据库） | `A vacuums B.` | PostgreSQL vacuums dead tuples to reclaim space. | PostgreSQL 清理死元组以回收空间。 |
| 876 | validate | 校验 | `A validates B.` | The server validates the token. | 服务器校验令牌。 |
| 877 | verify | 验证 | `A verifies B.` | The test verifies the fix. | 测试验证了修复。 |
| 878 | violate | 违反 | `A violates B.` | The request violates the rule. | 请求违反了规则。 |
| 879 | zip | 压缩 | `A zips B.` | Zip the log files before archiving them. | 归档前压缩日志文件。 |

### 五、协作与管理

> 项目推进与团队协作：计划、分配、评审、领导、交付。（79 个）

| No. | Verb | 中文含义 | 核心句子模板 | 示例 | 中文例句 |
|---:|---|---|---|---|---|
| 880 | accomplish | 完成；达成 | `A accomplishes B.` | The refactoring accomplished two goals at once. | 重构一次达成了两个目标。 |
| 881 | achieve | 达成 | `A achieves B.` | The team achieved the target. | 团队达成了目标。 |
| 882 | advocate | 倡导；主张 | `A advocates B. / A advocates for B.` | She advocates for test-driven development. | 她倡导测试驱动开发。 |
| 883 | align | 对齐 | `A aligns B with C.` | We aligned the plan with customer needs. | 我们让计划与客户需求对齐。 |
| 884 | allocate | 分配 | `A allocates B to C.` | The system allocates memory to the process. | 系统给进程分配内存。 |
| 885 | appraise | 评估（绩效） | `A appraises B.` | The manager appraises each engineer's contribution per quarter. | 经理每季度评估每位工程师的贡献。 |
| 886 | arrange | 安排 | `A arranges B.` | Please arrange the deployment window. | 请安排部署窗口。 |
| 887 | assess | 评估 | `A assesses B.` | The team assessed the risk. | 团队评估了风险。 |
| 888 | assign | 分配 | `A assigns B to C.` | The lead assigned the task to me. | 负责人把任务分配给我。 |
| 889 | attend | 参加；出席 | `A attends B.` | I attended the sprint review. | 我参加了迭代评审会。 |
| 890 | budget | 预算 | `A budgets B for C.` | We budgeted more money for security. | 我们为安全预算了更多资金。 |
| 891 | cancel | 取消 | `A cancels B.` | The team canceled the old plan. | 团队取消了旧计划。 |
| 892 | chair | 主持（会议） | `A chairs B.` | The tech lead chairs the weekly architecture review. | 技术负责人主持每周架构评审。 |
| 893 | collaborate | 协作；合作 | `A collaborates with B on C.` | The frontend team collaborates closely with the API team. | 前端团队与 API 团队紧密协作。 |
| 894 | compensate | 补偿；弥补 | `A compensates for B.` | Retries compensate for transient network failures. | 重试弥补瞬时网络故障。 |
| 895 | complete | 完成 | `A completes B.` | We completed the migration. | 我们完成了迁移。 |
| 896 | comply | 遵守 | `A complies with B.` | The system complies with the policy. | 系统符合该策略。 |
| 897 | cooperate | 合作 | `A cooperates with B.` | We cooperate with local partners. | 我们与本地伙伴合作。 |
| 898 | coordinate | 协调 | `A coordinates B with C.` | I coordinated the test with QA. | 我和测试团队协调测试。 |
| 899 | delay | 延迟 | `A delays B.` | The dependency delayed the release. | 依赖问题延迟了发布。 |
| 900 | delegate | 委派 | `A delegates B to C.` | The manager delegated the task to the team. | 经理把任务委派给团队。 |
| 901 | deliver | 交付；传送 | `A delivers B to C.` | We delivered the feature on time. | 我们按时交付了这个功能。 |
| 902 | demote | 降职；降级 | `A demotes B.` | The admin demoted the user to read-only access. | 管理员将用户降级为只读权限。 |
| 903 | direct | 指导；引导 | `A directs B to C.` | The load balancer directs traffic to healthy nodes. | 负载均衡器将流量导向健康节点。 |
| 904 | distribute | 分发；分配 | `A distributes B to C.` | The CDN distributes content to edge nodes globally. | CDN 向全球边缘节点分发内容。 |
| 905 | encourage | 鼓励 | `A encourages B to do C.` | We encourage code review. | 我们鼓励代码评审。 |
| 906 | endorse | 背书；签署 | `A endorses B.` | The architecture review board endorsed the proposal. | 架构评审委员会背书了这个提案。 |
| 907 | enforce | 强制执行 | `A enforces B.` | The gateway enforces authentication. | 网关强制认证。 |
| 908 | engage | 吸引参与 | `A engages B.` | The campaign engages new users. | 活动吸引新用户参与。 |
| 909 | evaluate | 评估 | `A evaluates B.` | We evaluated the new framework. | 我们评估了新框架。 |
| 910 | examine | 检查；审查 | `A examines B.` | The profiler examines every function call for hotspots. | 分析器检查每个函数调用以找热点。 |
| 911 | expedite | 加快；加速 | `A expedites B.` | We expedited the security patch after the CVE was published. | CVE 发布后我们加快了安全补丁的发布。 |
| 912 | facilitate | 促进；推动 | `A facilitates B.` | The API gateway facilitates service discovery. | API 网关促进了服务发现。 |
| 913 | fire | 解雇；触发 | `A fires B. / A fires off B.` | Never fire someone over a single production bug. | 永远不要因为一个生产 bug 就解雇人。 |
| 914 | follow | 跟随；遵循 | `A follows B.` | Follow the deployment guide. | 遵循部署指南。 |
| 915 | fund | 资助 | `A funds B.` | The program funds new projects. | 该计划资助新项目。 |
| 916 | govern | 治理；决定 | `A governs B.` | The IAM policy governs who can access the bucket. | IAM 策略治理谁能访问存储桶。 |
| 917 | guide | 指导 | `A guides B through C.` | The document guides users through setup. | 文档指导用户完成设置。 |
| 918 | head | 领导；前往 | `A heads B. / A heads to B.` | The VP of Engineering heads the technical strategy. | 工程 VP 领导技术战略。 |
| 919 | hire | 雇用；租用 | `A hires B.` | Hire for curiosity and adaptability, not just years of experience. | 招聘看重好奇心和适应力，而不仅仅是工作年限。 |
| 920 | inspect | 检查 | `A inspects B.` | The tool inspects the image. | 工具检查镜像。 |
| 921 | inspire | 激励；启发 | `A inspires B to do C.` | The outage inspired a complete monitoring overhaul. | 那次故障启发了一次彻底的监控改造。 |
| 922 | interview | 访谈 | `A interviews B.` | The team interviewed key customers. | 团队访谈了关键客户。 |
| 923 | lead | 领导；引导 | `A leads B.` | He leads the development team. | 他领导开发团队。 |
| 924 | liaise | 联络；对接 | `A liaises with B.` | The PM liaises between engineering and marketing. | 产品经理在工程和市场之间联络对接。 |
| 925 | manage | 管理 | `A manages B.` | She manages the project. | 她管理这个项目。 |
| 926 | mentor | 指导；辅导 | `A mentors B.` | Senior engineers mentor new hires during their first sprint. | 高级工程师在第一个迭代指导新人。 |
| 927 | motivate | 激励；驱使 | `A motivates B to do C.` | The outage motivated us to improve monitoring. | 那次故障促使我们改进监控。 |
| 928 | organize | 组织 | `A organizes B.` | We organized a review meeting. | 我们组织了一次评审会议。 |
| 929 | oversee | 监督 | `A oversees B.` | The SRE team oversees the production infrastructure. | SRE 团队监督生产基础设施。 |
| 930 | partner | 合作 | `A partners with B.` | The company partnered with an operator. | 公司与运营商合作。 |
| 931 | pilot | 试点 | `A pilots B.` | We piloted the service in one city. | 我们在一个城市试点服务。 |
| 932 | plan | 计划 | `A plans B. / A plans to do B.` | We plan to refactor the module. | 我们计划重构模块。 |
| 933 | postpone | 推迟 | `A postpones B.` | We postponed the meeting. | 我们推迟了会议。 |
| 934 | prepare | 准备 | `A prepares B.` | Prepare the release notes. | 准备发布说明。 |
| 935 | prioritize | 确定优先级 | `A prioritizes B.` | We prioritized critical bugs. | 我们优先处理严重缺陷。 |
| 936 | promote | 推广；促进 | `A promotes B.` | We promoted the new feature. | 我们推广了新功能。 |
| 937 | rank | 排序；排名 | `A ranks B by C.` | The system ranks results by relevance. | 系统按相关性排序结果。 |
| 938 | rate | 评估；评级 | `A rates B.` | Users rate the search results for relevance. | 用户对搜索结果的相关性进行评级。 |
| 939 | reconcile | 对账；调和；使一致 | `A reconciles B with C.` | Reconcile the local branch with the remote before pushing. | 推送前将本地分支与远程保持一致。 |
| 940 | recruit | 招聘 | `A recruits B.` | We're recruiting senior backend engineers. | 我们在招聘资深后端工程师。 |
| 941 | regulate | 监管；调节 | `A regulates B.` | Rate limiting regulates the flow of incoming requests. | 速率限制调节入站请求的流量。 |
| 942 | resign | 辞职 | `A resigns from B.` | The CTO resigned after three years at the company. | CTO 在公司工作三年后辞职了。 |
| 943 | review | 评审；回顾 | `A reviews B.` | Please review the code. | 请评审代码。 |
| 944 | reward | 奖励；回报 | `A rewards B with C.` | Clean interfaces reward you with easier maintenance. | 清晰的接口用更易维护来回报你。 |
| 945 | satisfy | 满足 | `A satisfies B.` | The feature satisfies user needs. | 功能满足用户需求。 |
| 946 | saturate | 饱和（带宽/资源） | `A saturates B.` | The backup job saturated the network link. | 备份任务使网络链路饱和。 |
| 947 | schedule | 安排 | `A schedules B.` | I scheduled a meeting. | 我安排了一个会议。 |
| 948 | screen | 筛选；审查 | `A screens B.` | Screen all third-party dependencies for vulnerabilities. | 筛查所有第三方依赖的漏洞。 |
| 949 | scrutinize | 仔细审查 | `A scrutinizes B.` | The security team scrutinized every line of the patch. | 安全团队仔细审查了补丁的每一行。 |
| 950 | settle | 解决；定居 | `A settles B. / A settles on B.` | The team settled on a hybrid approach. | 团队最终确定了混合方案。 |
| 951 | sponsor | 赞助；发起 | `A sponsors B.` | The company sponsors several open-source projects. | 公司赞助了多个开源项目。 |
| 952 | starve | 饿死（线程/资源饥饿） | `A starves B. / A is starved of B.` | A low-priority task can be starved of CPU time. | 低优先级任务可能被饿死 CPU 时间。 |
| 953 | streamline | 精简；提高效率 | `A streamlines B.` | Automate the deploy pipeline to streamline releases. | 自动化部署流水线以精简发布。 |
| 954 | supervise | 监督；管理 | `A supervises B.` | The orchestrator supervises all running containers. | 编排器管理所有运行中的容器。 |
| 955 | synchronize | 同步 | `A synchronizes B with C.` | Synchronize the local state with the server. | 将本地状态与服务器同步。 |
| 956 | value | 重视；评估 | `A values B.` | The team values code simplicity over cleverness. | 团队重视代码简洁胜过聪明。 |
| 957 | vet | 审查；考察 | `A vets B.` | Vet every third-party dependency before adding it. | 添加前审查每个第三方依赖。 |
| 958 | vote | 投票；表决 | `A votes on B. / A votes to do B.` | The team voted to adopt a four-day work week trial. | 团队投票通过了四天工作周试行。 |

### 六、商务与生活

> 商务交易与日常生活：市场、财务、旅行、饮食、健康。（91 个）

| No. | Verb | 中文含义 | 核心句子模板 | 示例 | 中文例句 |
|---:|---|---|---|---|---|
| 959 | accrue | 累积；产生（利息） | `A accrues B.` | Technical debt accrues silently sprint after sprint. | 技术债一个迭代一个迭代地默默累积。 |
| 960 | admire | 钦佩；欣赏 | `A admires B for C.` | I admire the team's dedication to code quality. | 我钦佩团队对代码质量的执着。 |
| 961 | advertise | 广告宣传 | `A advertises B.` | The brand advertised its new product. | 品牌宣传了新产品。 |
| 962 | amaze | 使惊讶；使惊叹 | `A amazes B.` | The performance gain amazed the entire team. | 性能提升让整个团队惊讶。 |
| 963 | annoy | 使烦恼；惹恼 | `A annoys B.` | Flaky tests annoy developers more than anything else. | 不稳定的测试最让开发者恼火。 |
| 964 | bake | 烘焙；内置 | `A bakes B into C.` | Security is baked into the development process, not added later. | 安全内置在开发流程中，不是事后添加。 |
| 965 | bet | 打赌；确信 | `A bets on B. / A bets that S.` | I bet the bug is in the caching layer. | 我打赌这个 bug 在缓存层。 |
| 966 | bid | 投标；出价 | `A bids on B. / A bids for B.` | Three vendors bid on the cloud infrastructure contract. | 三家供应商对云基础设施合同投标。 |
| 967 | bill | 计费 | `A bills B for C.` | The system bills customers monthly. | 系统按月向客户计费。 |
| 968 | bother | 打扰；费心 | `A bothers B. / A bothers to do B.` | Don't bother with manual testing — automate it. | 别费心手动测试了，自动化吧。 |
| 969 | brand | 塑造品牌 | `A brands B as C.` | They branded the app as a super app. | 他们把应用塑造成超级应用。 |
| 970 | calm | 使平静；镇定 | `A calms B down.` | The runbook calms everyone down during an incident. | 故障期间的 runbook 让所有人镇定下来。 |
| 971 | capitalize | 资本化；利用 | `A capitalizes on B.` | Capitalize on the migration window to upgrade dependencies. | 利用迁移窗口升级依赖。 |
| 972 | celebrate | 庆祝；赞美 | `A celebrates B.` | The team celebrated the launch with a demo day. | 团队用演示日庆祝上线。 |
| 973 | charge | 收费 | `A charges B for C.` | The platform charges users for storage. | 平台向用户收取存储费用。 |
| 974 | climb | 爬；攀升 | `A climbs. / A climbs to B.` | The error rate climbed to 5%. | 错误率攀升到 5%。 |
| 975 | collect | 收集 | `A collects B from C.` | The agent collects metrics every minute. | 代理每分钟收集指标。 |
| 976 | comfort | 安慰；使舒适 | `A comforts B.` | A familiar tech stack comforts the onboarding engineer. | 熟悉的技术栈让入职工程师感到舒适。 |
| 977 | compete | 竞争 | `A competes with B.` | The product competes with local platforms. | 产品与本地平台竞争。 |
| 978 | consume | 消费；消耗 | `A consumes B.` | The worker consumes messages. | 工作线程消费消息。 |
| 979 | contract | 订约 | `A contracts with B.` | The vendor contracted with the operator. | 供应商与运营商签约。 |
| 980 | contribute | 贡献；有助于 | `A contributes to B.` | Heavy logging contributed to the slowdown. | 大量日志导致了变慢。 |
| 981 | cross-sell | 交叉销售 | `A cross-sells B to C.` | The platform cross-sells monitoring tools to existing customers. | 平台向现有客户交叉销售监控工具。 |
| 982 | delight | 使高兴；取悦 | `A delights B.` | A fast CI pipeline delights the entire engineering team. | 快速的 CI 流水线让整个工程团队高兴。 |
| 983 | depreciate | 贬值；折旧 | `A depreciates B. / A depreciates.` | Server hardware depreciates by 30% per year. | 服务器硬件每年折旧 30%。 |
| 984 | differentiate | 区分；差异化 | `A differentiates B from C.` | This feature differentiates us from competitors. | 这个功能让我们区别于竞争对手。 |
| 985 | disappoint | 使失望 | `A disappoints B.` | The v2 API disappointed users with its complexity. | v2 API 的复杂性让用户失望。 |
| 986 | disburse | 支付；支出 | `A disburses B to C.` | Finance disburses the cloud credits to each team quarterly. | 财务每季度向各团队发放云额度。 |
| 987 | draw | 画；绘制；得出 | `A draws B. / A draws B from C.` | Draw a conclusion from the metrics. | 从指标中得出结论。 |
| 988 | dream | 梦想；做梦 | `A dreams of B.` | We dream of zero-downtime deploys. | 我们梦想零宕机部署。 |
| 989 | email | 发邮件 | `A emails B about C.` | Email the security team before making firewall changes. | 修改防火墙规则前给安全团队发邮件。 |
| 990 | embarrass | 使尴尬 | `A embarrasses B.` | A production outage embarrassed the engineering team. | 生产故障让工程团队尴尬。 |
| 991 | entertain | 娱乐；招待；考虑 | `A entertains B.` | We can't entertain every feature request. | 我们无法考虑每个功能请求。 |
| 992 | excite | 使兴奋；激发 | `A excites B about C.` | The new tech stack excited the engineering team. | 新技术栈让工程团队兴奋起来。 |
| 993 | exercise | 行使；运用 | `A exercises B.` | The tests exercise every code path. | 测试覆盖了每条代码路径。 |
| 994 | explore | 探索 | `A explores B.` | We explored several solutions. | 我们探索了几种方案。 |
| 995 | fear | 害怕；担心 | `A fears B. / A fears that S.` | The team feared a data loss incident. | 团队担心数据丢失事件。 |
| 996 | finance | 融资；资助 | `A finances B.` | The bank financed the project. | 银行为项目融资。 |
| 997 | freeze | 冻结；凝固 | `A freezes. / A freezes B.` | The UI froze after the API call. | API 调用后界面冻结了。 |
| 998 | frighten | 使害怕；吓唬 | `A frightens B.` | The complexity of the legacy code frightens new hires. | 遗留代码的复杂性吓到了新人。 |
| 999 | fry | 油炸；烧毁 | `A fries B. / A fries.` | A power surge fried the server's motherboard. | 电涌烧毁了服务器的主板。 |
| 1000 | heal | 自愈；修复 | `A heals B.` | The platform heals failed instances. | 平台修复失败实例。 |
| 1001 | hedge | 对冲 | `A hedges against B.` | Multi-cloud deployment hedges against a single vendor failure. | 多云部署对冲单一供应商故障的风险。 |
| 1002 | hunt | 狩猎；搜寻 | `A hunts for B. / A hunts down B.` | Hunt down the memory leak with a heap profiler. | 用堆分析器追踪内存泄漏。 |
| 1003 | insure | 投保；确保 | `A insures B against C.` | Regular backups insure the data against accidental deletion. | 定期备份确保数据免遭意外删除。 |
| 1004 | invest | 投资 | `A invests B in C.` | The company invested money in AI. | 公司投资 AI。 |
| 1005 | invoice | 开票 | `A invoices B.` | The vendor invoiced the customer. | 供应商给客户开票。 |
| 1006 | liquidate | 清算；变现 | `A liquidates B.` | The startup liquidated its assets after the shutdown. | 创业公司关闭后清算了资产。 |
| 1007 | market | 营销 | `A markets B to C.` | The company markets services to operators. | 公司向运营商营销服务。 |
| 1008 | marry | 结婚；结合 | `A marries B with C.` | Marry the legacy system with the new platform via an adapter. | 通过适配器将遗留系统与新平台结合。 |
| 1009 | message | 发消息 | `A messages B about C.` | Message the on-call engineer if the alert persists. | 如果告警持续，给值班工程师发消息。 |
| 1010 | offend | 冒犯；得罪 | `A offends B.` | A harsh code review can offend junior developers. | 苛刻的代码评审会冒犯初级开发者。 |
| 1011 | order | 命令；排序；订购 | `A orders B. / A orders B to do C.` | Order the search results by relevance descending. | 按相关性降序排列搜索结果。 |
| 1012 | outsource | 外包 | `A outsources B to C.` | Outsource the email delivery to a third-party service. | 将邮件发送外包给第三方服务。 |
| 1013 | pack | 打包；包装 | `A packs B into C.` | Webpack packs all modules into a single bundle. | Webpack 把所有模块打包成一个 bundle。 |
| 1014 | paint | 画；描绘；涂漆 | `A paints B. / A paints a picture of B.` | The dashboard paints a clear picture of system health. | 仪表盘描绘了系统健康状况的清晰画面。 |
| 1015 | panic | 恐慌；惊慌 | `A panics. / A panics about B.` | Don't panic when the error rate spikes — follow the runbook. | 错误率飙升时别恐慌，照着 runbook 来。 |
| 1016 | park | 停放；搁置 | `A parks B in C.` | Park this task in the backlog for now. | 先把这任务搁在待办列表里。 |
| 1017 | phone | 打电话 | `A phones B.` | Phone the on-call if the incident severity escalates. | 如果故障严重性升级，给值班打电话。 |
| 1018 | please | 使高兴；请 | `A pleases B.` | The fix pleased the users who had been waiting for weeks. | 这个修复让等了几周的用户高兴。 |
| 1019 | position | 定位 | `A positions B as C.` | We positioned the product as a cloud portal. | 我们把产品定位为云门户。 |
| 1020 | post | 发布；张贴 | `A posts B to C.` | Post a summary of the incident to the team channel. | 在团队频道发布故障总结。 |
| 1021 | pour | 倾倒；大量投入 | `A pours B into C.` | The team poured weeks of effort into the refactor. | 团队把数周精力倾注到了重构中。 |
| 1022 | procure | 采购；获得 | `A procures B.` | Procure the necessary cloud resources before the migration. | 迁移前采购必要的云资源。 |
| 1023 | purchase | 采购 | `A purchases B.` | The team purchased cloud resources. | 团队采购云资源。 |
| 1024 | recover | 恢复 | `A recovers from B.` | The service recovered from the failure. | 服务从故障中恢复。 |
| 1025 | refund | 退款 | `A refunds B to C.` | The platform refunded the fee to the user. | 平台把费用退给用户。 |
| 1026 | register | 注册；登记 | `A registers B. / A registers for B.` | The service registers itself with the gateway. | 服务向网关注册自己。 |
| 1027 | regret | 后悔；遗憾 | `A regrets B. / A regrets doing B.` | The team regretted skipping integration tests. | 团队后悔跳过了集成测试。 |
| 1028 | reimburse | 报销；偿还 | `A reimburses B for C.` | The company reimburses employees for conference tickets. | 公司报销员工的会议门票费用。 |
| 1029 | relax | 放松 | `A relaxes B. / A relaxes.` | Relax the rate limit for internal services. | 对内部服务放宽速率限制。 |
| 1030 | rent | 租用；出租 | `A rents B from C.` | Rent cloud instances instead of buying physical servers. | 租用云实例而不是买物理服务器。 |
| 1031 | reserve | 保留 | `A reserves B.` | The system reserves memory for the kernel. | 系统为内核保留内存。 |
| 1032 | scare | 吓唬；使害怕 | `A scares B.` | A sudden traffic spike scared the on-call team at 3 AM. | 凌晨三点的突增流量吓到了值班团队。 |
| 1033 | shock | 使震惊 | `A shocks B.` | The sudden 10x traffic surge shocked the on-call team. | 突如其来的 10 倍流量震惊了值班团队。 |
| 1034 | shop | 购物；选购 | `A shops for B.` | Shop around for the best cloud provider before committing. | 承诺使用之前货比三家选云服务商。 |
| 1035 | socialize | 社交；分享推广 | `A socializes B with C.` | Socialize the proposal with stakeholders before the meeting. | 会前先和利益相关者沟通这个提案。 |
| 1036 | stretch | 拉伸；延伸；超出 | `A stretches B.` | Don't stretch the sprint beyond its capacity. | 别让迭代超出容量。 |
| 1037 | sue | 起诉 | `A sues B for C.` | A competitor sued the startup for patent infringement. | 竞争对手以专利侵权起诉了这家创业公司。 |
| 1038 | surprise | 使吃惊；惊讶 | `A surprises B. / A is surprised by B.` | Don't be surprised if the deploy fails on a Friday. | 如果周五部署失败了，别惊讶。 |
| 1039 | text | 发短信；文本 | `A texts B about C.` | Text the team when the deploy is complete. | 部署完成后给团队发消息。 |
| 1040 | tip | 倾斜；给小费；提示 | `A tips B. / A tips the balance.` | A single bottleneck tipped the entire system over. | 单个瓶颈就让整个系统翻了。 |
| 1041 | unpack | 拆包；解析 | `A unpacks B.` | The function unpacks the tuple into named variables. | 函数将元组解包为命名变量。 |
| 1042 | upsell | 向上销售 | `A upsells B to C.` | The sales team upsells premium support to enterprise clients. | 销售团队向企业客户向上销售高级支持。 |
| 1043 | visit | 访问；拜访 | `A visits B.` | The crawler visits the homepage first. | 爬虫首先访问首页。 |
| 1044 | volunteer | 自愿；主动 | `A volunteers to do B.` | One developer volunteered to lead the migration. | 一位开发者主动请缨主导迁移。 |
| 1045 | wander | 漫游；走神 | `A wanders. / A wanders through B.` | The discussion wandered into architecture territory. | 讨论跑题到了架构领域。 |
| 1046 | warrant | 保证；需要；授权 | `A warrants B. / A warrants doing B.` | The severity of the bug warrants an immediate hotfix. | 这个缺陷的严重性需要立即热修复。 |
| 1047 | withdraw | 撤回；提取 | `A withdraws B.` | The team withdrew the deprecated endpoint. | 团队撤回了已弃用的端点。 |
| 1048 | wither | 衰退 | `A withers.` | Legacy systems wither without maintenance. | 遗留系统不维护就会衰退。 |
| 1049 | worry | 担心 | `A worries about B. / A worries that S.` | Don't worry about the traffic spike, it's expected. | 别担心流量峰值，这是预期的。 |
## 三、224 个短语动词速查

> 短语动词（phrasal verb）由动词 + 介词/副词构成，整体表达一个动作。以下按字母顺序排列。

| No. | Phrasal Verb | 中文含义 | 核心句子模板 | 示例 | 中文例句 |
|---:|---|---|---|---|---|
| 1 | aim at | 瞄准；针对 | `A aims at B. / A is aimed at B.` | This optimization aims at reducing cold start time. | 这项优化旨在减少冷启动时间。 |
| 2 | back off | 退避（重试策略） | `A backs off. / A backs off from B.` | The client backs off exponentially after repeated failures. | 客户端在反复失败后指数退避。 |
| 3 | back up | 备份；支持 | `A backs up B.` | Back up the database before running the migration. | 运行迁移前备份数据库。 |
| 4 | belong to | 属于 | `A belongs to B.` | This repository belongs to our team. | 这个仓库属于我们团队。 |
| 5 | block out | 屏蔽；划出（时间） | `A blocks out B.` | Block out two hours of focus time on the calendar. | 在日历上划出两小时的专注时间。 |
| 6 | blow over | 平息；过去 | `A blows over.` | The incident will blow over after the post-mortem. | 复盘之后故障风波会平息的。 |
| 7 | blow up | 爆炸；炸毁；放大 | `A blows up. / A blows B up.` | The monolith finally blew up under the traffic spike. | 单体终于在流量高峰下炸了。 |
| 8 | boil down | 归结为 | `A boils down to B.` | The performance issue boils down to a missing index. | 这个性能问题归结为一个缺失的索引。 |
| 9 | bottom out | 触底；停止恶化 | `A bottoms out.` | The latency spike bottomed out after the rollback. | 回滚后延迟尖峰触底停止恶化。 |
| 10 | branch out | 拓展（新领域） | `A branches out into B.` | The platform branched out from payments into lending. | 该平台从支付拓展到借贷领域。 |
| 11 | break down | 分解；出故障 | `A breaks down B. / A breaks down.` | Break down the epic into smaller user stories. | 将史诗分解为更小的用户故事。 |
| 12 | break into | 闯入；打入；开始从事 | `A breaks into B.` | It's hard to break into the developer tools market. | 打入开发者工具市场很难。 |
| 13 | break out | 爆发；分离出 | `A breaks out of B. / A breaks out B.` | Break out the shared logic into a separate library. | 将共享逻辑分离到独立的库中。 |
| 14 | bring up | 提出 | `A brings up B.` | She brought up a security concern. | 她提出了一个安全担忧。 |
| 15 | bubble up | 向上浮现 | `A bubbles up to B.` | Unhandled errors bubble up to the global error handler. | 未处理的错误向上冒泡到全局错误处理器。 |
| 16 | build up | 积累；建立；堆积 | `A builds up B. / A builds up.` | Technical debt builds up silently sprint after sprint. | 技术债一个迭代一个迭代地悄悄积累。 |
| 17 | burn down | 烧毁；燃尽 | `A burns down B. / A burns down.` | The team burned down the entire backlog in one sprint. | 团队一个迭代就燃尽了整个待办列表。 |
| 18 | burn out | 耗尽；过度疲劳 | `A burns out. / A burns B out.` | On-call rotations help prevent engineers from burning out. | 值班轮换有助于防止工程师过度疲劳。 |
| 19 | call in | 叫来；召集；来电 | `A calls in B.` | Call in the SRE expert when the incident escalates. | 故障升级时把 SRE 专家叫来。 |
| 20 | call off | 取消 | `A calls off B.` | The team called off the deploy due to the storm. | 团队因风暴取消了部署。 |
| 21 | call on | 调用；呼吁；拜访 | `A calls on B.` | The plugin calls on the core API for authentication. | 插件调用核心 API 做认证。 |
| 22 | call up | 调出；召集；打电话 | `A calls up B.` | Call up the cached data instead of querying the database. | 调出缓存数据而不查询数据库。 |
| 23 | calm down | 冷静下来；平息 | `A calms down. / A calms B down.` | The alert storm calmed down after the fix deployed. | 修复部署后告警风暴平息了。 |
| 24 | care about | 关心 | `A cares about B.` | Customers care about stability. | 客户关心稳定性。 |
| 25 | carry on | 继续 | `A carries on with B.` | The pipeline carries on despite warnings. | 流水线虽有警告但继续运行。 |
| 26 | carry out | 执行 | `A carries out B.` | Carry out the test plan. | 执行测试计划。 |
| 27 | carry over | 延续；结转 | `A carries over B to C.` | Carry over the unused budget to the next quarter. | 将未使用的预算结转到下个季度。 |
| 28 | cash in | 兑现；获利 | `A cashes in on B.` | The competitor cashed in on our outage with a blog post. | 竞争对手趁我们故障发博文获利。 |
| 29 | catch on | 流行；理解；跟上 | `A catches on. / A catches on to B.` | GraphQL caught on quickly among frontend developers. | GraphQL 在前端开发者中迅速流行起来。 |
| 30 | catch up | 赶上；追上 | `A catches up with B.` | The replica caught up with the primary after the lag. | 延迟后副本追上了主库。 |
| 31 | check off | 勾选；完成 | `A checks off B.` | Check off each item on the deployment checklist. | 逐项勾选部署检查清单上的内容。 |
| 32 | check on | 检查；查看；确认 | `A checks on B.` | Check on the deploy status before leaving for the day. | 下班前检查一下部署状态。 |
| 33 | check out | 检出（代码）；调查 | `A checks out B.` | Check out the feature branch before making changes. | 做改动前先检出功能分支。 |
| 34 | churn out | 大量产出；快速生产 | `A churns out B.` | The team churned out three features in one sprint. | 团队一个迭代就产出了三个功能。 |
| 35 | clean up | 清理 | `A cleans up B.` | Clean up temporary files. | 清理临时文件。 |
| 36 | clear out | 清空；清理 | `A clears out B.` | Clear out the stale feature flags after the release. | 发布后清理过时的功能标志。 |
| 37 | clear up | 清理；澄清；放晴 | `A clears up B. / A clears up.` | Clear up the ambiguity in the acceptance criteria. | 澄清验收标准中的模糊之处。 |
| 38 | clock in | 打卡上班 | `A clocks in.` | Remote workers clock in by joining the daily stand-up. | 远程员工通过加入每日站会打卡上班。 |
| 39 | clock out | 打卡下班 | `A clocks out.` | Encourage the team to clock out on time during crunch weeks. | 赶工周鼓励团队按时下班。 |
| 40 | come about | 发生；产生 | `A comes about.` | How did this race condition come about in the first place? | 这个竞态条件最初是怎么产生的？ |
| 41 | come around | 到来；改变主意 | `A comes around to B.` | The team eventually came around to the microservices approach. | 团队最终接受了微服务方案。 |
| 42 | come from | 来自 | `A comes from B.` | The problem comes from the network. | 问题来自网络。 |
| 43 | come to | 得出；达到；苏醒 | `A comes to B.` | After hours of debugging, we finally came to the root cause. | 调试数小时后，我们终于找到了根因。 |
| 44 | come up | 出现；提出 | `A comes up. / A comes up with B.` | The team came up with a clever workaround. | 团队想出了一个巧妙的工作方案。 |
| 45 | come with | 附带 | `A comes with B.` | The SDK comes with examples. | SDK 附带示例。 |
| 46 | consist of | 由……组成 | `A consists of B.` | The system consists of three services. | 系统由三个服务组成。 |
| 47 | cook up | 想出；捏造 | `A cooks up B.` | The team cooked up a quick prototype over the weekend. | 团队周末赶出了一个快速原型。 |
| 48 | count on | 指望；依靠 | `A counts on B.` | The team counts on the CI pipeline to catch regressions. | 团队指望 CI 流水线捕获回归。 |
| 49 | cover for | 代替；掩护；为...打掩护 | `A covers for B.` | Cover for your teammate during their vacation. | 同事休假时替他顶一下。 |
| 50 | crack down | 严厉打击；镇压 | `A cracks down on B.` | GitHub cracked down on abuse of GitHub Actions minutes. | GitHub 严厉打击滥用 Actions 分钟数的行为。 |
| 51 | cut back | 削减；缩减 | `A cuts back on B.` | We cut back on third-party dependencies to reduce risk. | 我们削减了第三方依赖以减少风险。 |
| 52 | cut in | 插嘴；切入；加塞 | `A cuts in. / A cuts in on B.` | A breaking change cut in right before the release deadline. | 一个破坏性变更在发布截止前插了进来。 |
| 53 | cut off | 切断；中断 | `A cuts off B.` | The firewall cut off the malicious connection. | 防火墙切断了恶意连接。 |
| 54 | cut over | 切换（迁移的最后一步） | `A cuts over from B to C.` | The team cut over from the old database to the new one at midnight. | 团队在凌晨从旧数据库切换到新数据库。 |
| 55 | deal with | 处理 | `A deals with B.` | We need to deal with this risk. | 我们需要处理这个风险。 |
| 56 | depend on | 依赖 | `A depends on B.` | This feature depends on Redis. | 这个功能依赖 Redis。 |
| 57 | drag on | 拖延；拖很久 | `A drags on. / A drags on B.` | The migration dragged on for six months. | 迁移拖了六个月。 |
| 58 | draw up | 起草；拟定 | `A draws up B.` | Draw up a rollback plan before the deploy. | 部署前拟定回滚方案。 |
| 59 | drill down | 深入钻取（数据） | `A drills down into B.` | Drill down into the trace to find the slowest span. | 深入钻取追踪以找到最慢的 span。 |
| 60 | drop off | 下降；减少；掉线 | `A drops off. / A drops off B.` | Traffic dropped off sharply after the event ended. | 活动结束后流量急剧下降。 |
| 61 | drop out | 退出；掉线 | `A drops out. / A drops out of B.` | The node dropped out of the cluster after a network split. | 网络分裂后该节点退出了集群。 |
| 62 | end up | 最终；以...告终 | `A ends up doing B. / A ends up C.` | Without monitoring, small issues end up as outages. | 没有监控，小问题最终会变成宕机。 |
| 63 | factor in | 考虑进去 | `A factors in B.` | Factor in the network latency when setting timeouts. | 设置超时时要考虑网络延迟。 |
| 64 | fall back | 降级/回退（兜底方案） | `A falls back to B.` | Fall back to the default config if the file is missing. | 如果文件缺失，回退到默认配置。 |
| 65 | fan out | 扇出 | `A fans out B to C.` | The message queue fans out events to multiple consumers. | 消息队列将事件扇出到多个消费者。 |
| 66 | figure out | 弄清楚 | `A figures out B.` | We figured out the root cause. | 我们弄清楚了根因。 |
| 67 | fill in | 填写 | `A fills in B.` | Fill in the required fields. | 填写必填字段。 |
| 68 | fill out | 填写（表格） | `A fills out B.` | Fill out the incident report within 24 hours. | 在 24 小时内填写故障报告。 |
| 69 | filter out | 过滤掉 | `A filters out B.` | Filter out the bot traffic from the analytics. | 从分析中过滤掉机器人流量。 |
| 70 | flesh out | 充实；完善 | `A fleshes out B.` | Flesh out the user story with acceptance criteria. | 用验收标准充实用户故事。 |
| 71 | flip through | 快速翻阅 | `A flips through B.` | Flip through the logs to spot the anomaly. | 快速翻阅日志以找出异常。 |
| 72 | follow through | 坚持到底；执行到底 | `A follows through on B.` | The team followed through on every action item. | 团队对每个行动项都执行到底。 |
| 73 | follow up | 跟进 | `A follows up on B.` | I will follow up on this issue. | 我会跟进这个问题。 |
| 74 | get across | 传达清楚；使理解 | `A gets B across to C.` | It's hard to get the urgency across in a Slack message. | Slack 消息很难把紧急性传达清楚。 |
| 75 | get around | 规避；绕过 | `A gets around B.` | A clever hack got around the API rate limit. | 一个巧妙的方法绕过了 API 速率限制。 |
| 76 | get back | 回来；回复 | `A gets back to B.` | I'll get back to you after investigating the error log. | 调查完错误日志后回复你。 |
| 77 | get out | 出去；发布；逃离 | `A gets out of B. / A gets B out.` | Get the hotfix out before the peak traffic window. | 在流量高峰窗口前把热修复发出去。 |
| 78 | get through | 完成；熬过；接通 | `A gets through B.` | We got through the entire agenda in 30 minutes. | 我们 30 分钟内完成了全部议程。 |
| 79 | give up | 放弃 | `A gives up B.` | Do not give up learning English. | 不要放弃学习英语。 |
| 80 | go down | 下降；宕机；载入史册 | `A goes down.` | The site went down for 15 minutes during the deploy. | 部署期间网站宕了 15 分钟。 |
| 81 | go through | 经历；仔细检查 | `A goes through B.` | Go through the entire PR before approving. | 批准前仔细检查整个 PR。 |
| 82 | hand in | 提交；上交 | `A hands in B.` | Hand in the security review before the release. | 发布前提交安全审查。 |
| 83 | hand over | 移交；交出 | `A hands over B to C.` | Hand over the on-call duties to the next shift. | 将值班职责移交给下一个班次。 |
| 84 | hang out | 挂起；逗留 | `A hangs out. / A hangs out in B.` | The request hung out in the pending state for too long. | 请求在等待状态挂起太久了。 |
| 85 | hold back | 保留；抑制 | `A holds back B.` | Don't hold back feedback during the code review. | 代码评审时不要保留反馈。 |
| 86 | hold off | 暂缓；推迟 | `A holds off on B.` | Hold off on the deploy until the traffic spike passes. | 等流量高峰过去再部署。 |
| 87 | hold up | 支撑；延迟 | `A holds up B. / A holds up.` | The index holds up well under heavy read traffic. / Don't let a review hold up the deploy. | 索引在大量读流量下支撑得很好。/ 别让评审延误部署。 |
| 88 | hone in | 瞄准；集中 | `A hones in on B.` | The profiler honed in on the memory leak. | 分析器瞄准了内存泄漏。 |
| 89 | iron out | 解决（细节问题） | `A irons out B.` | Iron out the edge cases before the release. | 发布前解决边界情况。 |
| 90 | keep up | 跟上；保持 | `A keeps up with B.` | The system keeps up with 10,000 requests per second. | 系统跟上了每秒 10000 次请求。 |
| 91 | key in | 键入；输入 | `A keys in B.` | Key in the verification code to complete the login. | 输入验证码完成登录。 |
| 92 | lay out | 布置；阐述 | `A lays out B.` | The RFC lays out the migration plan in detail. | RFC 详细阐述了迁移计划。 |
| 93 | lead to | 导致 | `A leads to B.` | High latency leads to bad user experience. | 高延迟导致糟糕的用户体验。 |
| 94 | lean into | 拥抱；积极面对 | `A leans into B.` | Lean into the discomfort of learning a new paradigm. | 积极面对学习新范式的阵痛。 |
| 95 | let go | 放手；解雇 | `A lets B go.` | The company let go of 10% of the workforce. | 公司解雇了 10% 的员工。 |
| 96 | light up | 亮起；点亮 | `A lights up B. / A lights up.` | The monitoring dashboard lit up with red alerts. | 监控仪表盘亮起红色告警。 |
| 97 | line up | 排队；安排 | `A lines up B.` | Line up the dependencies before starting the sprint. | 开始迭代前排好依赖关系。 |
| 98 | lock down | 锁定；封锁 | `A locks down B.` | Lock down the production environment after the breach. | 入侵后封锁生产环境。 |
| 99 | log in | 登录 | `A logs in to B.` | The user logs in to the system. | 用户登录系统。 |
| 100 | log out | 退出登录 | `A logs out of B.` | The user logged out of the portal. | 用户退出门户。 |
| 101 | look for | 寻找 | `A looks for B.` | Look for errors in the logs. | 在日志中查找错误。 |
| 102 | look into | 调查 | `A looks into B.` | We will look into this issue. | 我们会调查这个问题。 |
| 103 | look up | 查阅；查找 | `A looks up B.` | Look up the error code in the documentation. | 在文档中查阅错误码。 |
| 104 | make up | 弥补；组成 | `A makes up B. / A makes up for B.` | Microservices make up the core platform. / Speed makes up for lack of features. | 微服务构成核心平台。/ 速度弥补功能不足。 |
| 105 | map out | 规划；详细安排 | `A maps out B.` | Map out the migration path from monolith to microservices. | 规划从单体到微服务的迁移路径。 |
| 106 | mark down | 减价；记下 | `A marks down B.` | The team marked down the action items during the retro. | 团队在回顾会上记下了行动项。 |
| 107 | measure up | 达标；符合标准 | `A measures up to B.` | The new hire's first PR measured up to the team's standards. | 新人第一个 PR 就达到了团队标准。 |
| 108 | miss out | 错过；遗漏 | `A misses out on B.` | Don't miss out on the early-bird discount for the conference. | 别错过会议的早鸟折扣。 |
| 109 | mix up | 混淆；混合 | `A mixes up B with C.` | I always mix up the staging and production URLs. | 我总把预发布和生产 URL 搞混。 |
| 110 | mock up | 打样；做模型 | `A mocks up B.` | Mock up the new UI before writing a single line of code. | 写代码前先把新 UI 做个模型出来。 |
| 111 | move on | 继续前进；翻篇 | `A moves on from B.` | After the post-mortem, the team moved on quickly. | 复盘后团队迅速翻篇继续前进。 |
| 112 | move up | 提前；上升 | `A moves up B. / A moves up.` | Move up the deployment to Tuesday to catch the window. | 将部署提前到周二以赶上窗口。 |
| 113 | narrow down | 缩小范围 | `A narrows down B to C.` | Narrow down the root cause to a single commit. | 将根因缩小范围到一次提交。 |
| 114 | open up | 打开；开放 | `A opens up B.` | Open up the internal API to trusted partners. | 向可信伙伴开放内部 API。 |
| 115 | opt in | 选择加入 | `A opts in to B.` | Users must opt in to the beta program. | 用户必须选择加入 Beta 计划。 |
| 116 | opt out | 选择退出 | `A opts out of B.` | Users can opt out of data collection in settings. | 用户可以在设置中选择退出数据收集。 |
| 117 | own up | 承认；坦白 | `A owns up to B.` | The engineer owned up to the misconfiguration immediately. | 那位工程师立即承认了配置错误。 |
| 118 | pan out | 结果；成功 | `A pans out.` | The microservices migration didn't pan out as expected. | 微服务迁移的结果不如预期。 |
| 119 | pass on | 传递；转发 | `A passes on B to C.` | Pass on the context to the downstream service. | 将上下文传递到下游服务。 |
| 120 | pay off | 回报；还清 | `A pays off. / A pays off B.` | The investment in testing paid off during the migration. | 测试上的投入在迁移期间得到了回报。 |
| 121 | pencil in | 暂定；临时安排 | `A pencils in B.` | Pencil in the architecture review for Wednesday afternoon. | 暂定周三下午做架构评审。 |
| 122 | phase out | 逐步淘汰 | `A phases out B.` | Phase out the deprecated API over three releases. | 用三个版本逐步淘汰弃用的 API。 |
| 123 | pick out | 挑选；辨认出 | `A picks out B from C.` | Pick out the critical alerts from the noise. | 从噪音中挑出关键告警。 |
| 124 | pick up | 拿起；学会；接人 | `A picks up B.` | New hires pick up the codebase quickly with pair programming. | 新人通过结队编程快速上手代码库。 |
| 125 | pile up | 堆积；累积 | `A piles up.` | Unread Slack messages pile up during the weekend. | 周末未读的 Slack 消息堆积起来。 |
| 126 | pin down | 确定；明确 | `A pins down B.` | Pin down the exact commit that introduced the bug. | 确定引入缺陷的确切提交。 |
| 127 | pitch in | 出力；出钱 | `A pitches in.` | Everyone pitched in to resolve the production incident. | 每个人都在出力解决生产故障。 |
| 128 | play down | 淡化；轻描淡写 | `A plays down B.` | Don't play down the severity of a data loss bug. | 别淡化数据丢失缺陷的严重性。 |
| 129 | plug in | 插入；接通 | `A plugs in B.` | Plug in your API key to start using the service. | 插入你的 API 密钥即可开始使用服务。 |
| 130 | point out | 指出 | `A points out B.` | He pointed out a design flaw. | 他指出了一个设计缺陷。 |
| 131 | power down | 关机；断电 | `A powers down B.` | Power down the staging environment over the weekend. | 周末关掉预发布环境。 |
| 132 | press on | 继续；坚持 | `A presses on with B.` | Despite the setbacks, the team pressed on with the launch. | 尽管遇到挫折，团队坚持推进上线。 |
| 133 | pull off | 完成（困难的事） | `A pulls off B.` | The team pulled off a zero-downtime migration. | 团队完成了零宕机迁移。 |
| 134 | pull out | 抽出；退出 | `A pulls out B from C. / A pulls out of B.` | Pull out the shared components into a design system. | 将共享组件抽出到设计系统中。 |
| 135 | push back | 推后；反对 | `A pushes back on B.` | The engineer pushed back on the unrealistic deadline. | 工程师反对不切实际的截止日期。 |
| 136 | put off | 推迟 | `A puts off B.` | Don't put off the security patch until next sprint. | 别把安全补丁推迟到下个迭代。 |
| 137 | put together | 组合；拼凑 | `A puts together B.` | Put together a quick prototype before the pitch meeting. | 推介会前快速拼一个原型出来。 |
| 138 | queue up | 排队；入队 | `A queues up B.` | The scheduler queues up jobs based on priority. | 调度器按优先级将作业入队。 |
| 139 | ramp down | 逐步减少 | `A ramps down B.` | Ramp down the old service as traffic shifts to the new one. | 随着流量转移到新服务，逐步减少旧服务。 |
| 140 | ramp up | 逐步增加（流量/负载） | `A ramps up B.` | Ramp up the canary traffic from 5% to 50% gradually. | 将金丝雀流量从 5% 逐步增加到 50%。 |
| 141 | reach out | 联系；主动接触 | `A reaches out to B.` | Reach out to the platform team before building your own solution. | 在自建方案前先联系平台团队。 |
| 142 | refer to | 指的是；参考 | `A refers to B.` | This field refers to user ID. | 这个字段指用户 ID。 |
| 143 | rein in | 控制；收紧 | `A reins in B.` | Rein in the scope creep before the sprint derails. | 在迭代脱轨前收紧范围蔓延。 |
| 144 | relate to | 与……相关 | `A relates to B.` | This error relates to authentication. | 这个错误与认证有关。 |
| 145 | rely on | 依靠 | `A relies on B.` | The app relies on the database. | 应用依赖数据库。 |
| 146 | result in | 导致 | `A results in B.` | Invalid input results in an error. | 无效输入导致错误。 |
| 147 | roll back | 回退 | `A rolls back B.` | Roll back the deploy if the error rate spikes. | 如果错误率飙升就回退部署。 |
| 148 | roll out | 推出（新功能/版本） | `A rolls out B.` | Roll out the new feature to 10% of users initially. | 初步向 10% 用户推出新功能。 |
| 149 | rough out | 草拟；粗略画出 | `A roughs out B.` | Rough out the API contract before the integration meeting. | 集成会议前草拟 API 契约。 |
| 150 | rule out | 排除（可能性） | `A rules out B.` | The ping test ruled out a network issue. | ping 测试排除了网络问题。 |
| 151 | run by | 过一遍；给...看看 | `A runs B by C.` | Run the architecture proposal by the tech lead first. | 先把架构提案给技术负责人过一遍。 |
| 152 | run out | 耗尽 | `A runs out of B.` | The server ran out of disk space during the backup. | 备份期间服务器耗尽磁盘空间。 |
| 153 | run through | 快速过一遍；彩排 | `A runs through B.` | Run through the demo script once before the client call. | 客户电话前快速过一遍演示脚本。 |
| 154 | scale back | 缩减规模 | `A scales back B.` | We scaled back the feature scope to meet the deadline. | 我们缩减了功能范围以赶上截止日期。 |
| 155 | scope out | 考察；评估 | `A scopes out B.` | Scope out the third-party API before committing to it. | 承诺使用之前先评估第三方 API。 |
| 156 | search for | 搜索 | `A searches for B.` | Search for the keyword. | 搜索关键词。 |
| 157 | set up | 搭建；设置 | `A sets up B.` | Set up the local environment. | 搭建本地环境。 |
| 158 | settle on | 决定；选定 | `A settles on B.` | After much debate, the team settled on PostgreSQL. | 经过大量讨论，团队选定了 PostgreSQL。 |
| 159 | sew up | 缝合；搞定 | `A sews up B.` | Sew up the remaining edge cases before the release. | 发布前搞定剩余的边界情况。 |
| 160 | shake out | 抖出；淘汰出 | `A shakes out B.` | Load testing shakes out the hidden performance issues. | 负载测试抖出隐藏的性能问题。 |
| 161 | shore up | 支撑；加强 | `A shores up B.` | The team shored up the monitoring before Black Friday. | 黑五前团队加强了监控。 |
| 162 | show up | 出现；露面 | `A shows up. / A shows up in B.` | The error only shows up under high concurrency. | 这个错误只在高并发下出现。 |
| 163 | shut down | 关闭 | `A shuts down B.` | Shut down unused containers. | 关闭未使用的容器。 |
| 164 | sign up | 注册 | `A signs up for B.` | Users sign up for the service. | 用户注册该服务。 |
| 165 | smooth out | 抚平；解决问题 | `A smooths out B.` | The hotfix smoothed out the latency spikes. | 热修复抚平了延迟尖峰。 |
| 166 | sort out | 整理；解决 | `A sorts out B.` | Sort out the merge conflicts before the end of the day. | 今天之内解决合并冲突。 |
| 167 | spin down | 关闭（实例/容器） | `A spins down B.` | Spin down the staging instances over the weekend to save cost. | 周末关闭预发布实例以节省成本。 |
| 168 | spin up | 启动（实例/容器） | `A spins up B.` | The autoscaler spins up new pods when CPU exceeds 80%. | CPU 超过 80% 时自动扩缩器启动新 Pod。 |
| 169 | square away | 处理妥当 | `A squares away B.` | Square away the legal review before the launch date. | 上线日前把法务审查处理妥当。 |
| 170 | stamp out | 消灭；杜绝 | `A stamps out B.` | Stamp out flaky tests before they erode team trust. | 在不稳定测试侵蚀团队信任之前消灭它们。 |
| 171 | stand out | 突出；显著 | `A stands out. / A stands out from B.` | The latency spike stood out on the dashboard. | 延迟尖峰在仪表盘上格外突出。 |
| 172 | start over | 重新开始 | `A starts over.` | If the rebase goes wrong, start over from a clean branch. | 如果 rebase 出错，从干净分支重新开始。 |
| 173 | step up | 加大；站出来 | `A steps up B. / A steps up to do B.` | Step up the retry frequency after the third failure. | 第三次失败后加大重试频率。 |
| 174 | stick to | 坚持；遵守 | `A sticks to B.` | Stick to the coding standards even under time pressure. | 即使时间紧张也要遵守编码规范。 |
| 175 | stock up | 囤积；备货 | `A stocks up on B.` | Stock up on snacks before the hackathon. | 黑客马拉松前囤好零食。 |
| 176 | stumble upon | 偶然发现 | `A stumbles upon B.` | The developer stumbled upon a critical security flaw. | 开发者偶然发现了一个严重安全漏洞。 |
| 177 | sum up | 总结；概括 | `A sums up B.` | Sum up the key takeaways in three bullet points. | 用三个要点总结关键结论。 |
| 178 | swap out | 替换掉 | `A swaps out B for C.` | Swap out the old library for the new one in one PR. | 在一个 PR 里把旧库替换成新库。 |
| 179 | switch off | 关掉；停止思考 | `A switches off B.` | Switch off the feature flag after the canary succeeds. | 金丝雀验证成功后关掉功能标志。 |
| 180 | switch over | 切换过去 | `A switches over to B.` | Switch over to the backup data center during the outage. | 故障期间切换到备用数据中心。 |
| 181 | take apart | 拆开；剖析 | `A takes apart B.` | Take apart the monolithic service into independent modules. | 把单体服务拆分为独立模块。 |
| 182 | take back | 收回；撤回 | `A takes back B.` | The developer took back the commit after noticing the bug. | 开发者注意到 bug 后撤回了提交。 |
| 183 | take down | 记下；拆除 | `A takes down B.` | Take down the production notes during the incident call. | 故障电话期间记下处理记录。 |
| 184 | take on | 承担；雇佣 | `A takes on B.` | The team took on three new projects this quarter. | 团队本季度承担了三个新项目。 |
| 185 | take over | 接管；接手 | `A takes over B.` | The backup server takes over when the primary fails. | 主服务器故障时备份服务器接管。 |
| 186 | take up | 占用；开始做 | `A takes up B.` | The batch job takes up too much CPU during peak hours. | 批处理任务在高峰期占用太多 CPU。 |
| 187 | talk over | 讨论；商量 | `A talks over B with C.` | Talk over the API design before writing the spec. | 写规范之前先讨论 API 设计。 |
| 188 | talk up | 赞扬；吹捧 | `A talks up B.` | Talk up the team's achievements during the sprint review. | 迭代评审时赞扬团队的成果。 |
| 189 | tap into | 利用；接入 | `A taps into B.` | Tap into the existing auth system instead of building a new one. | 接入现有认证系统而不是新建一个。 |
| 190 | taper off | 逐渐减少 | `A tapers off.` | The alert noise tapered off after the fix deployed. | 修复部署后告警噪音逐渐减少了。 |
| 191 | tear down | 拆除（环境/资源） | `A tears down B.` | Tear down the test environment after the CI run finishes. | CI 运行结束后拆除测试环境。 |
| 192 | think over | 仔细考虑 | `A thinks over B.` | Think over the trade-offs before migrating to a new framework. | 迁移到新框架前仔细考虑取舍。 |
| 193 | think through | 想透彻；全面考虑 | `A thinks through B.` | Think through all the edge cases before coding. | 编码前全面考虑所有边界情况。 |
| 194 | throw away | 扔掉；浪费 | `A throws away B.` | Don't throw away the prototype — it might become a feature. | 别扔掉原型，它可能变成功能。 |
| 195 | throw out | 扔掉；否决 | `A throws out B.` | The committee threw out the proposal due to security concerns. | 委员会因安全隐患否决了该提案。 |
| 196 | tie up | 占用；绑住 | `A ties up B.` | The long-running transaction tied up the database connection. | 长事务占用了数据库连接。 |
| 197 | top up | 补足；充值 | `A tops up B.` | Top up the cloud credits before the end of the quarter. | 季度末前充值云额度。 |
| 198 | touch base | 沟通一下；碰个头 | `A touches base with B.` | Touch base with the security team before deploying. | 部署前和安全团队碰个头。 |
| 199 | trade off | 权衡；取舍 | `A trades off B for C.` | We traded off some latency for stronger consistency. | 我们为更强的一致性牺牲了一些延迟。 |
| 200 | trickle down | 渗透/下传 | `A trickles down to B.` | Architecture decisions trickle down to every line of code. | 架构决策渗透到每一行代码。 |
| 201 | trip over | 绊倒；遇到困难 | `A trips over B.` | The team tripped over an undocumented API behavior. | 团队遇到了一个未文档化的 API 行为。 |
| 202 | try out | 试用；尝试 | `A tries out B.` | Try out the new IDE plugin before the team adopts it. | 团队采用前先试用新的 IDE 插件。 |
| 203 | turn around | 扭转；转好 | `A turns around B.` | The new SRE practices turned the reliability around. | 新的 SRE 实践扭转了可靠性。 |
| 204 | turn down | 拒绝；关小 | `A turns down B.` | The team turned down the feature request due to scope creep. | 团队因范围蔓延拒绝了该功能请求。 |
| 205 | turn off | 关闭 | `A turns off B.` | Turn off the old switch. | 关闭旧开关。 |
| 206 | turn on | 打开 | `A turns on B.` | Turn on debug mode. | 打开调试模式。 |
| 207 | turn over | 移交；翻转 | `A turns over B to C.` | Turn over the on-call duties to the next shift. | 将值班职责移交给下一班。 |
| 208 | turn up | 出现；调大 | `A turns up.` | The bug only turned up under very specific conditions. | 这个 bug 只在非常特定的条件下出现。 |
| 209 | type out | 打出；完整输入 | `A types out B.` | Type out the full error message in the bug report. | 在缺陷报告中打出完整错误信息。 |
| 210 | use up | 用完；耗尽 | `A uses up B.` | The build job used up all the available disk space. | 构建任务用完了所有可用磁盘空间。 |
| 211 | wait for | 等待 | `A waits for B.` | Wait for the build to finish. | 等待构建完成。 |
| 212 | walk away | 离开；放弃 | `A walks away from B.` | Don't walk away from a failing build — fix it immediately. | 别对失败的构建置之不理，立即修复。 |
| 213 | walk through | 逐步演示；走查 | `A walks through B.` | Walk through the deployment steps with the new hire. | 带新人逐步走一遍部署步骤。 |
| 214 | warm up | 预热（缓存/连接池） | `A warms up B.` | Warm up the cache before putting the instance into rotation. | 将实例加入轮换前预热缓存。 |
| 215 | weed out | 淘汰；清除 | `A weeds out B.` | Code review weeds out subtle bugs before they reach production. | 代码评审在 bug 到生产前就淘汰掉它们。 |
| 216 | weigh in | 发表意见；参与讨论 | `A weighs in on B.` | The architect weighed in on the database design discussion. | 架构师参与了数据库设计的讨论。 |
| 217 | wind down | 逐步减少；放松 | `A winds down B. / A winds down.` | Wind down the old API gradually over six months. | 用六个月逐步停掉旧 API。 |
| 218 | wind up | 结束；最终 | `A winds up doing B.` | We wound up rewriting the module from scratch. | 我们最终从零重写了那个模块。 |
| 219 | work on | 从事；处理 | `A works on B.` | I am working on the bug. | 我正在处理这个缺陷。 |
| 220 | work out | 解决；锻炼；算出来 | `A works out B. / A works out.` | We worked out a compromise between the two approaches. | 我们找到了两种方案之间的折中。 |
| 221 | work with | 与……合作 | `A works with B.` | We work with the QA team. | 我们与测试团队合作。 |
| 222 | wrap up | 总结；完成 | `A wraps up B.` | Wrap up the sprint with a demo and a retro. | 以演示和回顾结束迭代。 |
| 223 | zero in | 聚焦；瞄准 | `A zeros in on B.` | The investigation zeroed in on the caching layer. | 调查聚焦在了缓存层。 |
| 224 | zip through | 快速完成 | `A zips through B.` | The script zips through 10,000 records in seconds. | 脚本在数秒内快速处理完 10000 条记录。 |## 四、如何真正掌握这些动词？

### 1. 按“参数”记动词

不要只记：

```text
send = 发送
```

要记：

```text
A sends B to C.
A 把 B 发送给 C。
```

这样你会自然知道句子怎么造。

### 2. 每个动词至少造两个工作句

例如：

```text
We deployed the app to production.
我们把应用部署到生产环境。

The pipeline deploys the service automatically.
流水线自动部署服务。
```

### 3. 读长句时先找动词

看到长句时，优先问自己三个问题：

```text
1. 这个句子的核心动词是什么？
2. 这个动词需要几个参数？
3. 哪些部分只是修饰成分？
```

例如：

```text
I sometimes eat fresh Fuji apples from a nearby grocery store.
```

核心主干是：

```text
I eat apples.
```

其他内容只是修饰：

```text
sometimes
fresh
Fuji
from a nearby grocery store
```

### 4. 不要沉迷语法术语

你不一定要记住“宾补、表语、双宾语”等术语。  
更重要的是知道：

```text
make 可以有 A make B C
tell 可以有 A tell B C
send 可以有 A send B to C
depend 必须常和 on 搭配
```

这比死记语法术语更接近真实语言能力。

---

## 四、如何真正掌握这些动词？

### 1. 按“参数”记动词

不要只记：

```text
send = 发送
```

要记：

```text
A sends B to C.
A 把 B 发送给 C。
```

这样你会自然知道句子怎么造。

### 2. 每个动词至少造两个工作句

例如：

```text
We deployed the app to production.
我们把应用部署到生产环境。

The pipeline deploys the service automatically.
流水线自动部署服务。
```

### 3. 读长句时先找动词

看到长句时，优先问自己三个问题：

```text
1. 这个句子的核心动词是什么？
2. 这个动词需要几个参数？
3. 哪些部分只是修饰成分？
```

例如：

```text
I sometimes eat fresh Fuji apples from a nearby grocery store.
```

核心主干是：

```text
I eat apples.
```

其他内容只是修饰：

```text
sometimes
fresh
Fuji
from a nearby grocery store
```

### 4. 不要沉迷语法术语

你不一定要记住“宾补、表语、双宾语”等术语。  
更重要的是知道：

```text
make 可以有 A make B C
tell 可以有 A tell B C
send 可以有 A send B to C
depend 必须常和 on 搭配
```

这比死记语法术语更接近真实语言能力。

---


| 阶段 | 数量 | 目标 |
|---|---:|---|
| 第1阶段 | 1～100 | 掌握最基础的系动词、存在和发生动词 |
| 第2阶段 | 101～200 | 掌握启动、停止、开关类操作动词 |
| 第3阶段 | 201～300 | 掌握创建、删除、增删改查动词 |
| 第4阶段 | 301～400 | 掌握通信、表达、理解和认知动词 |
| 第5阶段 | 401～500 | 掌握项目管理、工作流和交付动词 |
| 第6阶段 | 501～600 | 掌握数据、网络、运维、安全动词 |
| 第7阶段 | 601～700 | 掌握商务、产品和营销动词 |
| 第8阶段 | 701～800 | 掌握系统设计、优化和架构动词 |
| 第9阶段 | 801～900 | 补充日常交流、商务和职场场景动词 |
| 第10阶段 | 901～1000 | 巩固剩余高频和专项场景动词 |
| 第11阶段 | 1001～1019 | 继续扩展动词覆盖范围 |

---


英语句子的核心不是名词，也不是形容词，而是动词。  
动词决定了一个句子可以放几个参数，也决定了句子的基本骨架。

真正有效的学习方式是：

```text
动词 + 参数模板 + 场景例句 + 反复仿写
```

当你熟悉这 1272 个核心动词之后，再去阅读技术文档、邮件、会议纪要和英文文章，会更容易抓住句子的主干。


## 五、推荐学习节奏

| 阶段 | 数量 | 目标 |
|---|---:|---|
| 第1阶段 | 1～100 | 掌握最基础的系动词、存在和发生动词 |
| 第2阶段 | 101～200 | 掌握启动、停止、开关类操作动词 |
| 第3阶段 | 201～300 | 掌握创建、删除、增删改查动词 |
| 第4阶段 | 301～400 | 掌握通信、表达、理解和认知动词 |
| 第5阶段 | 401～500 | 掌握项目管理、工作流和交付动词 |
| 第6阶段 | 501～600 | 掌握数据、网络、运维、安全动词 |
| 第7阶段 | 601～700 | 掌握商务、产品和营销动词 |
| 第8阶段 | 701～800 | 掌握系统设计、优化和架构动词 |
| 第9阶段 | 801～900 | 补充日常交流、商务和职场场景动词 |
| 第10阶段 | 901～1000 | 巩固剩余高频和专项场景动词 |
| 第11阶段 | 1001～1019 | 继续扩展动词覆盖范围 |

---

## 六、总结

英语句子的核心不是名词，也不是形容词，而是动词。  
动词决定了一个句子可以放几个参数，也决定了句子的基本骨架。

真正有效的学习方式是：

```text
动词 + 参数模板 + 场景例句 + 反复仿写
```

当你熟悉这 1273 个核心动词之后，再去阅读技术文档、邮件、会议纪要和英文文章，会更容易抓住句子的主干。

---

## 附录：高频动词补充

> 以下是查漏补缺项，暂不并入前文 1273 个核心动词编号。

### A. 情态与助动词

| Verb | 中文含义 | 核心句子模板 | 示例 | 中文例句 |
|---|---|---|---|---|
| can | 能；可以 | `A can do B.` | This tool can generate a report automatically. | 这个工具可以自动生成报告。 |
| could | 能够；可能；可以（委婉） | `A could do B.` | We could cache the response to reduce latency. | 我们可以缓存响应来降低延迟。 |
| will | 将会；愿意 | `A will do B.` | The service will restart after the deploy. | 服务会在部署后重启。 |
| would | 会；愿意；将会（假设或委婉） | `A would do B.` | A retry would solve most transient failures. | 一次重试会解决大多数瞬时故障。 |
| should | 应该 | `A should do B.` | You should validate input before saving it. | 保存前应该验证输入。 |
| may | 可能；可以 | `A may do B.` | The request may fail if the token expires. | 如果令牌过期，请求可能会失败。 |
| might | 可能 | `A might do B.` | This change might affect older clients. | 这个改动可能影响旧客户端。 |
| must | 必须 | `A must do B.` | Users must confirm their email before login. | 用户登录前必须确认邮箱。 |
| shall | 应当；将要（正式/规范） | `A shall do B.` | The system shall reject invalid signatures. | 系统应当拒绝无效签名。 |

### B. 基础动词补充

| Verb | 中文含义 | 核心句子模板 | 示例 | 中文例句 |
|---|---|---|---|---|
| act | 行动；充当 | `A acts. / A acts as B. / A acts on B.` | The gateway acts as a reverse proxy. | 网关充当反向代理。 |
| base | 以……为基础 | `A bases B on C. / B is based on C.` | We based the estimate on historical data. | 我们基于历史数据做了估算。 |
| care | 关心；在意 | `A cares. / A cares about B.` | Customers care about reliability more than features. | 客户比起功能更关心可靠性。 |
| consist | 由……组成 | `A consists of B.` | The platform consists of three core services. | 这个平台由三个核心服务组成。 |
| deal | 处理；应对 | `A deals with B.` | The handler deals with expired sessions. | 处理器应对过期会话。 |
| depend | 依赖；取决于 | `A depends on B.` | The release depends on the security review. | 发布取决于安全评审。 |
| lay | 放置；铺设；提出 | `A lays B. / A lays out B.` | Lay out the migration plan before coding. | 编码前先列出迁移计划。 |
| point | 指向；指出 | `A points to B. / A points out B.` | The metric points to a database bottleneck. | 这个指标指向数据库瓶颈。 |
| press | 按；压；催促 | `A presses B. / A presses on with B.` | Press Enter to continue the installation. | 按回车继续安装。 |
| refer | 指的是；参考 | `A refers to B.` | This field refers to the user's primary email. | 这个字段指用户的主邮箱。 |
| relate | 相关；联系 | `A relates to B.` | This bug relates to the cache invalidation logic. | 这个缺陷和缓存失效逻辑有关。 |
| result | 导致；结果是 | `A results in B.` | Invalid input results in a validation error. | 无效输入会导致校验错误。 |
| shut | 关闭；合上 | `A shuts B. / A shuts down B.` | Shut the connection before releasing the resource. | 释放资源前关闭连接。 |
| touch | 触碰；涉及；接触 | `A touches B. / A touches base with B.` | This patch touches the authentication module. | 这个补丁涉及认证模块。 |
