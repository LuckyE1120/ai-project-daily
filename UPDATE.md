# 每日更新流程

本仓库是日报归档的持久来源。原定时任务 `ai` 每天北京时间 10:15 开始，在原聊天推送摘要，同时更新本仓库。GitHub Actions 在每次主分支推送后自动部署网站。

工作目录：`/Users/lvliangbin/Documents/Codex/2026-10-12/https-github-com-bbylw-rea-cn/outputs/ai-project-daily`。

GitHub 远程 `origin`：`https://github.com/LuckyE1120/ai-project-daily.git`，主分支 `main`。

网站：`https://LuckyE1120.github.io/ai-project-daily/`。

## 内容与检查

1. 检查工作树，执行 `git fetch origin`。干净时可快进到 `origin/main`；若有并发修改，保留并合并，禁止强制推送。
2. 阅读 `reports/` 最近几期，优先选择首次收录项目与已核实的重要更新。
3. 用互联网检索、项目官方仓库和发布说明核对事实；记录检索日期、热度窗口、来源链接、安装前提。区分第三方统计与官方事实，不把当前 README 功能表述成当日新发布。
4. 把当天 Markdown 同时保存到原聊天的 `outputs/AI项目日报-YYYY-MM-DD.md` 及本仓库 `reports/`，同一天重跑更新同一文件。每期的首张表格用于自动生成项目卡片；列顺序为项目、用途、热度、体验前提、建议。
5. 执行 `python3 build.py`、`python3 -m unittest discover -s tests`、`node --check web/app.js`。失败时修复再发布。

## 同步与发布

1. 检查改动，只提交日报与网站相关文件（包含生成的 `dist/`）。提交说明建议 `docs: add AI daily YYYY-MM-DD`。没有内容变化时无需空提交。
2. 正常推送 `git push origin main`，核对远程主分支 SHA 与本地提交一致。
3. 用 `gh run list --repo LuckyE1120/ai-project-daily --workflow pages.yml --limit 5` 找到本次提交对应的运行。检查这次运行的结果，不以旧运行成功替代本次验证。
4. 等待 GitHub Actions 构建部署；短间隔查询状态，避免长时间阻塞。失败时查看失败日志、修复可修复问题；保留原始日报和已推送提交。不要删除或重新创建仓库。
5. 发布成功后，在原聊天推送简明摘要、重点项目、日报文件链接、网站和 GitHub 链接。即使无显著变化也说明检查结果；遇到失败，明确报告哪个环节未完成，并保留已成功部分供重试。

资料搜集由原聊天的本机定时任务执行，客户端需要能运行任务且 GitHub 认证有效。GitHub Actions 负责构建与部署，不能独立搜集并撰写日报。任务 10:15 开始，线上完成时间取决于检索、推送和 Actions 队列。

仓库与网站均已按用户要求公开；只保存日报、网站代码与更新说明，不加入本聊天的其他项目或账户凭据。
