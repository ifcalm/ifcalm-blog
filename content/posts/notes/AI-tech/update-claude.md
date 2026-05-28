---
title: "解决 Homebrew 安装 Claude Code 失败：downloads.claude.ai 连接超时"
date: 2026-05-28
tags: ["Homebrew", "Claude Code", "Proxy"]
draft: false
summary: "解决 Homebrew 安装 Claude Code 失败：downloads.claude.ai 连接超时"
showToc: true
tocOpen: false
---

# 解决 Homebrew 安装 Claude Code 失败：downloads.claude.ai 连接超时

最近在 macOS 上使用 Homebrew 安装 Claude Code 时，遇到了下载失败的问题。错误信息如下：

```bash
✘ Cask claude-code (2.1.144)
Error: Download failed on Cask 'claude-code' with message: Download failed: https://downloads.claude.ai/claude-code-releases/2.1.144/darwin-arm64/claude
curl: (28) Failed to connect to downloads.claude.ai port 443 after 75051 ms: Couldn't connect to server
```

从报错信息来看，问题并不是 Homebrew 本身安装命令错误，而是 `curl` 在下载 Claude Code 二进制文件时，无法连接到：

```bash
https://downloads.claude.ai/
```

也就是说，真正的问题是：**终端环境没有正确走代理，导致 brew / curl 无法访问 Claude Code 的下载地址。**

---

## 一、问题现象

执行安装命令：

```bash
brew install --cask claude-code
```

或升级命令：

```bash
brew upgrade --cask claude-code
```

出现如下错误：

```bash
curl: (28) Failed to connect to downloads.claude.ai port 443 after 75051 ms: Couldn't connect to server
```

其中重点是：

```bash
Failed to connect to downloads.claude.ai port 443
```

这说明当前终端访问 Claude Code 下载服务器失败。

---

## 二、排查思路

这个问题通常和以下几个原因有关：

1. 当前网络无法直接访问 `downloads.claude.ai`
2. macOS 系统代理已开启，但终端没有走代理
3. Homebrew / curl / git 没有配置代理环境变量
4. DNS 或 IPv6 路由存在问题
5. Homebrew 下载缓存中存在失败的残留文件

本次问题的核心原因是：**macOS 系统代理已开启，但终端环境变量中没有代理配置。**

---

## 三、查看终端是否配置代理

先执行：

```bash
env | grep -i proxy
```

如果没有任何输出，例如：

```bash
lishuaishuai@MacBook-Air ~ % env | grep -i proxy
lishuaishuai@MacBook-Air ~ %
```

说明当前终端没有配置代理环境变量。

这时即使 macOS 系统代理已经开启，`brew`、`curl`、`git` 等命令行工具也可能不会自动走代理。

---

## 四、查看 macOS 系统代理

继续执行：

```bash
scutil --proxy
```

输出如下：

```bash
<dictionary> {
  ExceptionsList : <array> {
    0 : 127.0.0.1
    1 : 192.168.0.0/16
    2 : 10.0.0.0/8
    3 : 172.16.0.0/12
    4 : localhost
    5 : *.local
    6 : *.crashlytics.com
    7 : <local>
  }
  FTPPassive : 1
  HTTPEnable : 1
  HTTPPort : 7897
  HTTPProxy : 127.0.0.1
  HTTPSEnable : 1
  HTTPSPort : 7897
  HTTPSProxy : 127.0.0.1
  ProxyAutoConfigEnable : 0
  SOCKSEnable : 1
  SOCKSPort : 7897
  SOCKSProxy : 127.0.0.1
```

从这里可以看到，系统代理已经开启：

```bash
HTTPEnable : 1
HTTPProxy  : 127.0.0.1
HTTPPort   : 7897

HTTPSEnable : 1
HTTPSProxy  : 127.0.0.1
HTTPSPort   : 7897

SOCKSEnable : 1
SOCKSProxy  : 127.0.0.1
SOCKSPort   : 7897
```

也就是说，当前系统代理地址是：

```bash
127.0.0.1:7897
```

---

## 五、临时为终端配置代理

既然系统代理端口是 `7897`，可以在当前终端中执行：

```bash
export HTTP_PROXY=http://127.0.0.1:7897
export HTTPS_PROXY=http://127.0.0.1:7897
export ALL_PROXY=socks5h://127.0.0.1:7897

export http_proxy=http://127.0.0.1:7897
export https_proxy=http://127.0.0.1:7897
export all_proxy=socks5h://127.0.0.1:7897
```

这里同时配置了大写和小写形式，是为了兼容不同命令行工具。

很多工具会读取：

```bash
HTTP_PROXY
HTTPS_PROXY
ALL_PROXY
```

也有一些工具会读取：

```bash
http_proxy
https_proxy
all_proxy
```

为了减少兼容性问题，建议两组都配置。

---

## 六、验证代理是否生效

配置完成后，再执行：

```bash
env | grep -i proxy
```

正常应该看到类似输出：

```bash
HTTP_PROXY=http://127.0.0.1:7897
HTTPS_PROXY=http://127.0.0.1:7897
ALL_PROXY=socks5h://127.0.0.1:7897
http_proxy=http://127.0.0.1:7897
https_proxy=http://127.0.0.1:7897
all_proxy=socks5h://127.0.0.1:7897
```

然后测试 Claude Code 下载域名：

```bash
curl -Iv --connect-timeout 10 https://downloads.claude.ai/
```

只要不再出现连接超时，就说明终端代理已经生效。

即使返回的是 `403`、`404` 之类的状态，也不一定是问题。关键是能连上服务器，说明网络链路已经打通。

---

## 七、重新安装 Claude Code

代理配置生效后，重新执行：

```bash
brew install --cask claude-code
```

如果之前安装失败过，可以先清理缓存：

```bash
brew cleanup claude-code
rm -rf "$(brew --cache)/downloads/"*claude*
brew install --cask claude-code
```

安装完成后，检查版本：

```bash
claude --version
```

---

## 八、推荐做成终端代理开关

临时执行 `export` 只对当前终端窗口有效。关闭终端后，下次还需要重新设置。

更推荐的方式是把代理配置封装成开关函数，写入 `~/.zshrc`。

执行：

```bash
cat >> ~/.zshrc <<'EOF'

proxy_on() {
  export HTTP_PROXY=http://127.0.0.1:7897
  export HTTPS_PROXY=http://127.0.0.1:7897
  export ALL_PROXY=socks5h://127.0.0.1:7897
  export http_proxy=http://127.0.0.1:7897
  export https_proxy=http://127.0.0.1:7897
  export all_proxy=socks5h://127.0.0.1:7897
  echo "Terminal proxy enabled: 127.0.0.1:7897"
}

proxy_off() {
  unset HTTP_PROXY HTTPS_PROXY ALL_PROXY
  unset http_proxy https_proxy all_proxy
  echo "Terminal proxy disabled"
}
EOF

source ~/.zshrc
```

之后需要开启终端代理时执行：

```bash
proxy_on
```

关闭终端代理时执行：

```bash
proxy_off
```

查看当前代理状态：

```bash
env | grep -i proxy
```

---

## 九、常用排查命令汇总

### 1. 查看终端代理

```bash
env | grep -i proxy
```

### 2. 查看 macOS 系统代理

```bash
scutil --proxy
```

### 3. 测试 Claude Code 下载地址

```bash
curl -Iv --connect-timeout 10 https://downloads.claude.ai/
```

### 4. 测试 GitHub 访问

```bash
curl -Iv --connect-timeout 10 https://github.com/
```

### 5. 清理 Homebrew 下载缓存

```bash
brew cleanup claude-code
rm -rf "$(brew --cache)/downloads/"*claude*
```

### 6. 重新安装 Claude Code

```bash
brew install --cask claude-code
```

---

## 十、总结

这次问题的本质是：

> macOS 系统代理已经开启，但终端环境没有配置代理变量，导致 brew / curl 访问 `downloads.claude.ai` 超时。

解决方式是：

1. 使用 `scutil --proxy` 查看系统代理端口
2. 使用 `env | grep -i proxy` 检查终端代理环境变量
3. 根据系统代理端口，为终端配置 `HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY`
4. 使用 `curl` 验证下载域名是否能连通
5. 清理 Homebrew 缓存并重新安装 Claude Code

这类问题并不只会影响 Claude Code，也可能影响：

```bash
brew install
brew update
git clone
git push
curl
npm install
go mod tidy
```

所以在 macOS 上做开发时，建议给终端配置一个 `proxy_on` / `proxy_off` 开关。这样既能解决海外资源下载超时问题，也不会长期污染终端环境。
