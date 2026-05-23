---
title: "Homebrew 使用手册：macOS 软件包管理工具 brew 入门到常用维护"
date: 2026-05-23
tags: ["macOS", "Homebrew", "Terminal", "开发工具"]
draft: false
summary: "macOS 上 Homebrew 的完整使用指南，覆盖 Formula/Cask 安装、services 管理、Brewfile 备份恢复、Intel 到 Apple Silicon 迁移及常见问题排查。"
showToc: true
tocOpen: false
---

## 一、Homebrew 是什么？

Homebrew 是 macOS 上非常常用的软件包管理工具，也可以用于 Linux。

它的核心命令是：

```bash
brew
```

可以把它理解为 macOS 上的“软件安装与管理中心”。

使用 Homebrew 可以完成：

- 安装命令行工具，例如 `git`、`wget`、`node`、`go`
- 安装图形化应用，例如 `Google Chrome`、`OrbStack`、`Visual Studio Code`
- 升级软件
- 卸载软件
- 查看软件信息
- 管理后台服务，例如 `mysql`、`redis`、`postgresql`
- 备份和恢复软件清单

如果经常使用 macOS 做开发，`brew` 基本是必备工具。

---

## 二、安装 Homebrew

官方安装命令如下：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

复制到 macOS 终端执行即可。

安装过程中脚本会说明它准备做什么，并在真正执行前暂停确认。

---

## 三、Apple Silicon 与 Intel Mac 的安装路径

不同芯片架构下，Homebrew 默认安装路径不同。

| Mac 类型 | 默认路径 |
|---|---|
| Apple Silicon，例如 M1、M2、M3、M4、M5 | `/opt/homebrew` |
| Intel Mac | `/usr/local` |

可以用下面命令查看当前 Homebrew 路径：

```bash
brew --prefix
```

如果输出是：

```bash
/opt/homebrew
```

说明通常是 Apple Silicon 路径。

如果输出是：

```bash
/usr/local
```

说明通常是 Intel Mac 路径。

---

## 四、安装后配置环境变量

安装完成后，Homebrew 通常会提示你把下面内容加入 shell 配置文件。

Apple Silicon 常见写法：

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Intel Mac 常见写法：

```bash
echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/usr/local/bin/brew shellenv)"
```

也可以先查看 `brew` 在哪里：

```bash
which brew
```

查看 `brew` 是否正常：

```bash
brew --version
```

---

## 五、Homebrew 的几个核心概念

### 1. Formula

`Formula` 通常指命令行软件包，例如：

```bash
brew install git
brew install wget
brew install node
brew install go
```

这些工具一般安装后可以直接在终端使用。

---

### 2. Cask

`Cask` 通常指图形化应用，例如：

```bash
brew install --cask google-chrome
brew install --cask visual-studio-code
brew install --cask orbstack
```

这类应用通常会出现在 `/Applications` 目录中。

---

### 3. Tap

`Tap` 可以理解为第三方软件仓库。

查看当前 tap：

```bash
brew tap
```

添加 tap：

```bash
brew tap owner/repo
```

移除 tap：

```bash
brew untap owner/repo
```

一般情况下，新手不需要主动管理 tap，除非某些软件明确要求。

---

### 4. Cellar

`Cellar` 是 Homebrew 存放具体软件版本的目录。

例如 Apple Silicon 机器上常见位置是：

```bash
/opt/homebrew/Cellar
```

Homebrew 会把软件安装到自己的目录中，然后通过软链接暴露到 `bin` 目录。

这也是为什么很多命令会出现在：

```bash
/opt/homebrew/bin
```

---

### 5. Bottle

`Bottle` 是 Homebrew 预编译好的二进制包。

简单理解：

- 有 bottle：通常下载安装更快
- 没有 bottle：可能需要本地编译，安装会慢很多

日常使用不需要特别关心这个概念，但遇到安装很慢时，可以知道它可能是在源码编译。

---

## 六、最常用命令

### 1. 查看 brew 版本

```bash
brew --version
```

---

### 2. 更新 Homebrew 自身的软件索引

```bash
brew update
```

注意：`brew update` 更新的是 Homebrew 自己和软件索引，不是升级所有已安装软件。

---

### 3. 查看可升级的软件

```bash
brew outdated
```

---

### 4. 升级所有软件

```bash
brew upgrade
```

---

### 5. 升级指定软件

```bash
brew upgrade git
```

---

### 6. 安装软件

```bash
brew install git
```

---

### 7. 安装图形化应用

```bash
brew install --cask google-chrome
```

---

### 8. 卸载软件

```bash
brew uninstall git
```

---

### 9. 卸载图形化应用

```bash
brew uninstall --cask google-chrome
```

---

### 10. 查看已安装软件

查看 formula：

```bash
brew list
```

只查看命令行工具：

```bash
brew list --formula
```

只查看图形化应用：

```bash
brew list --cask
```

---

### 11. 查看软件信息

```bash
brew info git
```

查看 Cask 应用信息：

```bash
brew info --cask google-chrome
```

---

### 12. 搜索软件

```bash
brew search node
```

搜索图形化应用：

```bash
brew search --cask chrome
```

---

## 七、Formula 与 Cask 的区别

| 类型 | 安装命令 | 适合对象 | 示例 |
|---|---|---|---|
| Formula | `brew install xxx` | 命令行工具、开发库、服务组件 | `git`、`node`、`go`、`redis` |
| Cask | `brew install --cask xxx` | 图形界面应用 | `google-chrome`、`orbstack`、`visual-studio-code` |

例如：

```bash
brew install git
```

安装的是命令行工具。

```bash
brew install --cask visual-studio-code
```

安装的是图形化应用。

---

## 八、常用开发工具安装示例

### 1. Git

```bash
brew install git
```

查看版本：

```bash
git --version
```

---

### 2. Node.js

```bash
brew install node
```

查看版本：

```bash
node -v
npm -v
```

---

### 3. Go

```bash
brew install go
```

查看版本：

```bash
go version
```

---

### 4. Python

```bash
brew install python
```

查看版本：

```bash
python3 --version
pip3 --version
```

---

### 5. wget

```bash
brew install wget
```

---

### 6. tree

```bash
brew install tree
```

使用：

```bash
tree -L 2
```

---

### 7. ffmpeg

```bash
brew install ffmpeg
```

常用于音视频处理，例如把 `.aiff` 转成 `.mp3`：

```bash
ffmpeg -i input.aiff output.mp3
```

---

## 九、常用图形化应用安装示例

### 1. Google Chrome

```bash
brew install --cask google-chrome
```

---

### 2. Visual Studio Code

```bash
brew install --cask visual-studio-code
```

---

### 3. OrbStack

```bash
brew install --cask orbstack
```

---

### 4. iTerm2

```bash
brew install --cask iterm2
```

---

### 5. Docker Desktop

```bash
brew install --cask docker
```

如果已经使用 OrbStack，一般不需要再安装 Docker Desktop。

---

## 十、软件维护命令

### 1. 一键更新维护

日常可以使用：

```bash
brew update
brew outdated
brew upgrade
brew cleanup
brew doctor
```

含义分别是：

| 命令 | 含义 |
|---|---|
| `brew update` | 更新 Homebrew 和软件索引 |
| `brew outdated` | 查看有哪些软件可以升级 |
| `brew upgrade` | 升级已安装软件 |
| `brew cleanup` | 清理旧版本和缓存 |
| `brew doctor` | 检查 Homebrew 环境问题 |

---

### 2. 清理旧版本

```bash
brew cleanup
```

查看会清理什么，但不实际执行：

```bash
brew cleanup -n
```

---

### 3. 检查环境健康状态

```bash
brew doctor
```

如果输出：

```text
Your system is ready to brew.
```

一般说明状态正常。

如果有 Warning，可以根据提示逐条处理。

---

### 4. 查看配置

```bash
brew config
```

该命令会输出 Homebrew 版本、系统架构、macOS 版本、Ruby、Git 等信息。

---

## 十一、管理后台服务：brew services

Homebrew 可以管理一些后台服务，比如 Redis、MySQL、PostgreSQL。

### 1. 查看服务列表

```bash
brew services list
```

---

### 2. 启动服务

```bash
brew services start redis
```

启动后，服务会注册为开机或登录后自动启动。

---

### 3. 停止服务

```bash
brew services stop redis
```

---

### 4. 重启服务

```bash
brew services restart redis
```

---

### 5. 只运行一次，不注册开机启动

```bash
brew services run redis
```

`start` 和 `run` 的区别：

| 命令 | 含义 |
|---|---|
| `brew services start redis` | 启动并注册为登录后自动启动 |
| `brew services run redis` | 只运行，不注册自动启动 |

---

### 6. 查看服务详情

```bash
brew services info redis
```

---

## 十二、使用 Brewfile 备份和恢复软件

`Brewfile` 很适合迁移电脑或重装系统。

它可以把当前安装的软件整理成一个清单文件。

---

### 1. 导出当前软件清单

在当前目录生成 `Brewfile`：

```bash
brew bundle dump --force
```

生成全局 Brewfile：

```bash
brew bundle dump --global --force
```

---

### 2. 根据 Brewfile 安装软件

如果当前目录有 `Brewfile`：

```bash
brew bundle install
```

使用全局 Brewfile：

```bash
brew bundle install --global
```

---

### 3. 检查 Brewfile 中的软件是否都已安装

```bash
brew bundle check
```

如果想看缺少哪些：

```bash
brew bundle check --verbose
```

---

### 4. 示例 Brewfile

```ruby
tap "homebrew/bundle"

brew "git"
brew "go"
brew "node"
brew "tree"
brew "ffmpeg"

cask "google-chrome"
cask "visual-studio-code"
cask "orbstack"
```

有了这个文件后，新机器上只需要执行：

```bash
brew bundle install
```

就可以批量安装这些工具。

---

## 十三、从 Intel Mac 迁移到 Apple Silicon Mac

如果之前是 Intel Mac，现在换到 Apple Silicon Mac，不建议直接把旧的 `/usr/local/Homebrew` 整体复制过去。

更推荐做法：

### 1. 在旧电脑导出 Brewfile

```bash
brew bundle dump --global --force
```

通常会生成：

```bash
~/.Brewfile
```

---

### 2. 在新电脑安装 Homebrew

Apple Silicon 默认路径一般是：

```bash
/opt/homebrew
```

安装完成后配置环境变量：

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
```

---

### 3. 拷贝 Brewfile 到新电脑

例如拷贝到用户目录：

```bash
~/.Brewfile
```

---

### 4. 在新电脑执行恢复

```bash
brew bundle install --global
```

这样比直接复制旧目录更干净，也能避免 Intel 架构残留导致的问题。

---

## 十四、常见问题与排查

### 1. `brew: command not found`

说明系统找不到 `brew` 命令。

先确认是否安装：

```bash
ls /opt/homebrew/bin/brew
ls /usr/local/bin/brew
```

Apple Silicon 可以执行：

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Intel Mac 可以执行：

```bash
eval "$(/usr/local/bin/brew shellenv)"
```

然后再测试：

```bash
brew --version
```

如果恢复正常，需要把对应配置写入 `~/.zprofile`。

---

### 2. `Failed to connect to github.com port 443`

这种通常是网络、代理或 GitHub 连接问题。

可以先检查代理环境变量：

```bash
env | grep -i proxy
```

检查 Git 代理：

```bash
git config --global --get http.proxy
git config --global --get https.proxy
```

如果之前设置过错误代理，例如 `127.0.0.1:7890`，但代理软件没有启动，就可能导致连接失败。

可以临时清理 Git 代理：

```bash
git config --global --unset http.proxy
git config --global --unset https.proxy
```

再执行：

```bash
brew update
```

如果你确实需要代理，应确保代理软件正常运行，并且端口正确。

---

### 3. `Bad CPU type in executable`

这个问题常见于从 Intel Mac 迁移到 Apple Silicon 后，旧环境或旧 Homebrew 残留导致某些二进制不可用。

建议排查：

```bash
which brew
brew --prefix
uname -m
```

如果是 Apple Silicon，`uname -m` 通常输出：

```bash
arm64
```

Apple Silicon 上推荐使用：

```bash
/opt/homebrew
```

而不是继续沿用 Intel 时代的：

```bash
/usr/local/Homebrew
```

更稳妥的做法是使用 Brewfile 重新安装工具，而不是直接迁移旧的 Homebrew 目录。

---

### 4. `brew update` 很慢

可能原因包括：

- 网络连接 GitHub 较慢
- 代理配置异常
- DNS 解析慢
- Homebrew 本地仓库异常

可以先执行：

```bash
brew update --verbose
```

查看卡在哪一步。

也可以检查代理：

```bash
env | grep -i proxy
git config --global --get http.proxy
git config --global --get https.proxy
```

---

### 5. Cask 应用安装后打不开

可能原因：

- 应用不支持当前 macOS 版本
- 应用被系统安全策略拦截
- 应用来源被标记为 quarantine
- 应用自身损坏

可以先查看应用信息：

```bash
brew info --cask app-name
```

如果是 quarantine 问题，可以查看扩展属性：

```bash
xattr /Applications/AppName.app
```

谨慎移除 quarantine：

```bash
xattr -r -d com.apple.quarantine /Applications/AppName.app
```

只建议对自己确认可信的软件使用。

---

### 6. 如何彻底卸载 Cask 应用？

普通卸载：

```bash
brew uninstall --cask app-name
```

更彻底清理：

```bash
brew uninstall --cask --zap app-name
```

`--zap` 会尝试删除更多用户配置、缓存等文件。使用前建议确认数据是否需要保留。

---

### 7. 如何避免自动清理旧版本？

Homebrew 在升级软件后可能会自动清理旧版本。

如果确实想禁用自动清理，可以设置：

```bash
export HOMEBREW_NO_INSTALL_CLEANUP=1
```

如果只想指定某些 formula 不清理：

```bash
export HOMEBREW_NO_CLEANUP_FORMULAE=foo,bar
```

但一般不建议长期关闭清理，否则磁盘占用会越来越大。

---

## 十五、常用命令速查表

| 场景 | 命令 |
|---|---|
| 查看版本 | `brew --version` |
| 查看安装路径 | `brew --prefix` |
| 更新索引 | `brew update` |
| 查看可升级软件 | `brew outdated` |
| 升级全部软件 | `brew upgrade` |
| 安装命令行工具 | `brew install git` |
| 安装图形化应用 | `brew install --cask google-chrome` |
| 卸载软件 | `brew uninstall git` |
| 卸载图形化应用 | `brew uninstall --cask google-chrome` |
| 查看已安装软件 | `brew list` |
| 查看 Formula | `brew list --formula` |
| 查看 Cask | `brew list --cask` |
| 搜索软件 | `brew search node` |
| 查看软件信息 | `brew info node` |
| 清理旧版本 | `brew cleanup` |
| 预览清理内容 | `brew cleanup -n` |
| 检查环境 | `brew doctor` |
| 查看配置 | `brew config` |
| 查看服务 | `brew services list` |
| 启动服务 | `brew services start redis` |
| 停止服务 | `brew services stop redis` |
| 重启服务 | `brew services restart redis` |
| 导出 Brewfile | `brew bundle dump --force` |
| 根据 Brewfile 安装 | `brew bundle install` |

---

## 十六、推荐的日常使用流程

### 1. 安装软件前

```bash
brew search 软件名
brew info 软件名
```

确认是自己要安装的软件后，再执行：

```bash
brew install 软件名
```

如果是图形化应用：

```bash
brew install --cask 应用名
```

---

### 2. 每周维护一次

```bash
brew update
brew outdated
brew upgrade
brew cleanup
brew doctor
```

---

### 3. 换电脑前

```bash
brew bundle dump --global --force
```

保存好：

```bash
~/.Brewfile
```

新电脑安装 Homebrew 后执行：

```bash
brew bundle install --global
```

---

### 4. 遇到问题时

优先执行：

```bash
brew doctor
brew config
brew update --verbose
```

然后根据具体报错排查网络、代理、路径或架构问题。

---

## 十七、适合开发者安装的一组工具

下面是一组比较适合开发者的基础工具：

```bash
brew install git
brew install tree
brew install wget
brew install curl
brew install jq
brew install ripgrep
brew install fd
brew install fzf
brew install bat
brew install eza
brew install ffmpeg
```

图形化应用可以考虑：

```bash
brew install --cask google-chrome
brew install --cask visual-studio-code
brew install --cask orbstack
brew install --cask iterm2
```

说明：

| 工具 | 作用 |
|---|---|
| `git` | 版本管理 |
| `tree` | 目录树查看 |
| `wget` | 下载工具 |
| `jq` | JSON 处理 |
| `ripgrep` | 高性能文本搜索 |
| `fd` | 更好用的 find 替代工具 |
| `fzf` | 命令行模糊搜索 |
| `bat` | 更美观的 cat 替代工具 |
| `eza` | 更现代的 ls 替代工具 |
| `ffmpeg` | 音视频处理 |

---

## 十八、个人建议

如果只是日常开发，建议记住这几组命令就够了：

```bash
brew install xxx
brew install --cask xxx
brew update
brew outdated
brew upgrade
brew cleanup
brew doctor
brew services list
brew bundle dump --global --force
brew bundle install --global
```

其中最有价值的是 `Brewfile`。

因为它可以把一台电脑上的开发环境整理成一份清单。以后换电脑、重装系统、搭建新开发环境时，只需要用这份清单恢复即可。

---

## 参考资料

- Homebrew 官网：https://brew.sh/
- Homebrew 官方文档：https://docs.brew.sh/
- Homebrew Manual Page：https://docs.brew.sh/Manpage
- Homebrew Installation：https://docs.brew.sh/Installation
- Homebrew Bundle and Brewfile：https://docs.brew.sh/Brew-Bundle-and-Brewfile
- Homebrew Common Issues：https://docs.brew.sh/Common-Issues
- Homebrew FAQ：https://docs.brew.sh/FAQ
