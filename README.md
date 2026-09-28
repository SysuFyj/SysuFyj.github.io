# Ringo 的博客

本仓库是 Hexo 7.3.0 / NexT 8.21.0 生成的静态站点。当前 main 与历史 master 分支均未包含 Hexo 原始 Markdown、主题源码或构建配置。

2026-09-28 整理：保留 12 篇文章的原地址、发布日期、更新日期、章节锚点与代码示例；新增主题归档、恢复标签及论文目录，并整理显示问题。

- [完整归档总目](docs/博客归档总目.md)
- [显示问题与处理记录](docs/页面检查报告.md)
- [逐篇元数据与原始图片引用](content/catalog.json)
- [恢复的 Markdown 阅读副本](content/posts/)

## 本地查看

在仓库目录运行 `python3 -m http.server 8765 --bind 127.0.0.1`，访问 <http://127.0.0.1:8765/library/>。不要直接双击 HTML，原站使用以 `/` 开头的资源路径，需要通过本地服务器查看。

## 后续维护

HTML 是当前网页正文的维护入口；`content/posts/` 是自动生成的阅读副本，并非 Hexo 原稿，也不会被 Hexo 自动发布。手工修改阅读副本后重新运行整理脚本会覆盖该副本。

使用 Python 3.9 或更新版本：

```sh
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt
.venv/bin/python scripts/maintain.py
.venv/bin/python scripts/verify.py
```

`scripts/catalog-data.json` 保存逐篇主题、摘要、关键词和整理备注。脚本以现有 12 篇文章为此次整理范围，生成主题页、论文页、标签页、首页摘要、搜索索引、归档总目和 Markdown 副本。校验脚本检查原文地址、代码块、配图数量、目录锚点、站内引用及资源完整性。新增文章时需扩展该维护流程和预期数量。

**如果找回原 Hexo 工程，应将这些修改迁移到源配置和模板中，再恢复 Hexo 发布流程。直接从旧工程部署会覆盖本次静态网页修复。**

整理后的静态站点已合并到 `main` 并发布到 GitHub Pages；新增文章已加入正式归档。
