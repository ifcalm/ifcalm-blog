# 我在栀南镇的日子

[![Hugo](https://img.shields.io/badge/Hugo-v0.161%2B-FF4088?logo=hugo)](https://gohugo.io/)
[![Theme](https://img.shields.io/badge/Theme-PaperMod-4a6da7)](https://github.com/adityatelange/hugo-PaperMod)

基于 [Hugo](https://gohugo.io/) 构建的个人博客，使用 PaperMod 主题，部署于 [blog.ifcalm.org](https://blog.ifcalm.org)。

## 技术栈

- **静态生成**: Hugo v0.161+ (extended)
- **主题**: PaperMod（vendored in `themes/paperMod/`）
- **评论**: [Giscus](https://giscus.app/)
- **语言**: 中文 (`zh-cn`)，单语言站点
- **部署**: GitHub Pages / 静态托管

## 本地开发

```bash
# 克隆仓库
git clone https://github.com/ifcalm/ifcalm-blog.git
cd ifcalm-blog

# 启动开发服务器（包含草稿）
hugo server -D

# 构建生产站点
hugo
```

浏览器打开 `http://localhost:1313` 即可预览。

## 内容结构

所有文章位于 `content/posts/`，按主题分子目录：

| 目录 | 名称 | 内容 |
|------|------|------|
| `web3/` | web3 | 区块链技术 |
| `books/` | 读书&技术 | 编程语言、技术学习笔记 |
| `essay/` | 随笔&感悟 | 个人随笔 |
| `notes/` | 日记&笔记 | 日记、开发笔记、AI 工具 |

## 新建文章

```bash
hugo new content content/posts/<category>/<slug>.md
```

### Front Matter 模板

```yaml
---
title: "文章标题"
date: 2026-05-24
tags: ["标签1", "标签2"]
draft: false
summary: "文章摘要"
showToc: true
tocOpen: false
---
```

## 功能

- **profileMode 首页** — 显示头像、简介和导航按钮
- **Giscus 评论** — 基于 GitHub Discussions
- **代码高亮 + 复制按钮**
- **面包屑导航**
- **文章目录（TOC）**
- **暗色/亮色主题**
- **PWA 支持**

## 许可证

博客内容版权归作者所有。代码部分使用 [MIT License](LICENSE)（如有）。
