# AI 项目日报

每天整理最近一周值得关注的 AI 开源项目与实用工具，重点关注 AI 编程、Agent、MCP、Skill、自动化测试和创作。

- 网站：https://LuckyE1120.github.io/ai-project-daily/
- GitHub：https://github.com/LuckyE1120/ai-project-daily（公开仓库）
- 日报原文：[`reports/`](reports/)
- 每日任务：北京时间 10:15 开始，生成结束后同步源码和网站；完成时间取决于检索与部署。

## 本地使用

仅需 Python 3 与 Node.js（Node 用于语法检查，网站运行本身无第三方依赖）。

```bash
python3 build.py
python3 -m unittest discover -s tests
node --check web/app.js
python3 -m http.server 8767 --directory dist
```

打开 http://localhost:8767 。支持日期归档、全文关键词搜索、项目仓库跳转和 Markdown 下载。日期直达链接使用 `#date=2026-10-14`。搜索会筛选左侧归档和项目卡片；正文保留当前所选日期。

## 新增日报

1. 在 `reports/` 新建 `AI项目日报-YYYY-MM-DD.md`，每个日期一篇。
2. 首张 Markdown 表格按“项目（GitHub 链接）｜用途｜热度信号｜体验前提｜建议”排列，自动生成项目卡片。
3. 执行上述构建和检查；`dist/` 是完整静态网站，随源码一起版本管理。
4. 提交并推送 GitHub；GitHub Actions 自动构建并部署到 GitHub Pages。详细流程见 [`UPDATE.md`](UPDATE.md)。

所有热度统计注明来源和日期；区分第三方统计、官方事实、作者宣称与编辑判断。资料调研不等于安装实测，滚动周增不能相减当作单日增长。

## 目录

| 位置 | 内容 |
|---|---|
| `reports/` | 可独立阅读的 Markdown 日报 |
| `web/` | 网站模板、样式和交互 |
| `build.py` | 无第三方依赖的静态生成器 |
| `dist/` | 可直接部署的生成结果及 Markdown 下载 |
| `.github/workflows/pages.yml` | 推送后检查、构建、部署 GitHub Pages |
| `UPDATE.md` | 每日更新和失败恢复流程 |

不保存账户凭据；定时任务使用当前客户端的 GitHub 登录，Actions 使用 GitHub 提供的短期凭据。
