# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# 本地开发服务器（带草稿）
hugo server -D

# 构建生产站点（输出到 public/）
hugo

# 创建新文章（交互式选择 content 子目录）
hugo new content content/posts/<category>/<slug>.md
```

## Architecture

- **Hugo v0.161+ (extended)** 静态博客，部署于 `blog.ifcalm.org`
- **主题**: PaperMod（vendored in `themes/paperMod/`，非 git submodule）
- **语言**: 中文（`zh-cn`），单语言站点，无 `/zh/` 子路径
- **评论系统**: Giscus，关联 repo `ifcalm/ifcalm-blog-comments`

### 内容结构

所有文章在 `content/posts/` 下按分类分子目录：

| 目录 | 菜单名称 | 内容类型 |
|------|---------|---------|
| `web3/` | web3 | 区块链技术文章 |
| `books/` | 读书&技术 | 编程语言/技术学习笔记 |
| `essay/` | 随笔&感悟 | 个人随笔 |
| `notes/` | 日记&笔记 | 日记、开发笔记、AI 工具、读书笔记 |

分类目录对应的菜单层级关系见 `hugo.toml` 中的 `[menu]` 配置。

### 首页模式

当前使用 `profileMode`（`hugo.toml:52`），显示头像、副标题和导航按钮。与 `homeInfoParams` 互斥，二者只启用一个。

### 文章 Front Matter

使用 YAML 格式（`---`），常用字段：

```yaml
title: "文章标题"
date: 2023-06-18
tags: ["区块链", "web3"]
draft: false
summary: "文章摘要"
showToc: false       # 是否显示目录
tocOpen: false       # 是否默认展开目录
```

### 无自定义模板

`layouts/` 目录为空，所有布局依赖 PaperMod 主题内置模板，无需维护自定义覆盖。
