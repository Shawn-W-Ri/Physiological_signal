# Signal Daily · 生理信号资讯与科研论文日报

一个可部署到 **GitHub Pages** 的轻量静态项目。前端使用 Vite + 原生 JavaScript / CSS，采集任务使用 Python 标准库；无需数据库、服务器或付费 API。默认语言中文。

## 已实现

- 首页两个板块：行业 / 科研新闻、最新科研论文。
- ECG/心电、EEG/脑电、EMG/肌电、PPG、EDA/皮电、呼吸、睡眠、可穿戴设备八个主题筛选。
- 按北京时间首次收录日归档，另列原文发表日期；日期与主题写入 URL hash，可复制当前视图链接。
- RSS / Atom、公开 HTML 列表页、arXiv API、PubMed E-utilities 数据源。
- 每日采集、跨日期去重、来源失败隔离、超时重试、保留历史内容。
- 可选中文标题 / 摘要接口；无密钥或接口失败时显示原文摘录。
- GitHub Actions 每天采集、提交 JSON、构建、部署 Pages；首次 push 只构建，可手动触发立即采集。
- 响应式布局、键盘操作、来源链接、明确的示例 / 空内容 / 加载失败提示。

## 1. 本地运行

需要 Node.js **22.12+**（含 npm）、Python **3.11+**，推荐 3.12。

```sh
npm ci
npm run dev
```

在终端提示的本地地址打开网站。不要直接双击 index.html；模块和 JSON 需要 HTTP 服务。

```sh
python scripts/update.py       # 采集真实来源，需联网
python -m unittest discover -s tests -v
npm run build                 # 生成 dist/
npm run preview               # 查看生产构建
```

`npm run update` 和 `npm test` 分别是前两个 Python 命令的快捷方式。若系统使用 `python3`，直接使用 `python3 scripts/update.py`。本地修改数据后刷新页面即可。

项目可能带有明确标注的示例归档，用于离线查看界面。**示例条目不是实际新闻或论文**。任何来源首次成功采集后，程序会删除示例归档，即使当日没有匹配条目。空日报表示没有新收录，不表示源站没有发布。已有真实归档不会被采集失败清空。

## 2. 数据源配置

编辑 `config/sources.json`：

| 字段 | 说明 |
| --- | --- |
| timezone | 默认 Asia/Shanghai；Windows 缺少时区数据时对北京时间自动使用 UTC+8 |
| lookbackDays | 默认回看 7 天；arXiv 按提交时间，PubMed 按入库时间；RSS 按原文日期 |
| maxItemsPerSource | 每来源最多收录 30 条；API 每次也只查询这个数量，MVP 不分页 |
| translationLimit | 每次最多尝试翻译的新条目数，默认 20；超出保留原文 |
| sources[].enabled | 启用 / 停用来源 |
| id / name / kind | 唯一来源 ID / 展示名称 / news 或 paper |
| type | rss、web、arxiv、pubmed |
| url | RSS feed 或公开 HTML 页面地址 |
| query | arXiv / PubMed 各自的检索语法 |
| tags | 该来源附加的主题标签，必须使用上述八种名称 |
| filterByTopics | 为 true 时，只收录匹配关键词或固定 tags 的条目 |
| linkPattern | web 类型使用的链接 URL 正则表达式 |

RSS / Atom 示例：

```json
{"id":"my-rss","name":"研究机构","type":"rss","kind":"news","enabled":true,"url":"https://your-source.example/feed.xml","filterByTopics":true}
```

网页源示例（将地址和规则换成实际来源后启用）：

```json
{"id":"my-web","name":"研究所新闻","type":"web","kind":"news","enabled":true,"url":"https://your-source.example/news","linkPattern":"/news/20[0-9]{2}/","tags":["EEG/脑电"]}
```

网页适配器读取普通 HTML 中匹配 URL 的链接文字；不执行 JavaScript、不抓取文章全文。它不猜测发布日期，无日期的内容会显示“日期未知”，回看过滤不适用于这类条目。动态渲染网站需另写适配器。RSS 没有发布日期时也保留日期未知。选择允许聚合的公开源，保留署名和原文链接，并按源站规则调整采集频率。默认只保存短摘录，最多 700 个字符。

`scripts/update.py` 的 `TOPICS` 是透明的关键词规则，可按研究方向调整。短缩写可能有歧义；自动归类不等同人工筛选。默认 MIT 可穿戴专题可能长期没有新内容，这是正常空结果。arXiv 条目明确标注预印本；PubMed 是索引平台，并不保证所有收录内容均经过同行评审。

## 3. GitHub Pages 部署

1. 在 GitHub 创建仓库，将**本目录内所有文件**放入仓库根目录，包含隐藏目录 `.github`。默认分支使用 `main`。
2. 提交并推送。`package-lock.json` 必须一起提交；不要上传 `node_modules`、`.env` 或密钥。
3. 仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。
4. **Settings → Actions → General** 确认允许运行工作流，并允许工作流对仓库写入。组织策略可能覆盖仓库权限。
5. 如果 `main` 启用了必须通过 PR / 禁止机器人直推的保护规则，需要为采集提交提供允许的策略，或改为机器人 PR 流程。当前方案使用 `GITHUB_TOKEN` 提交 `public/data`，不需要个人访问令牌。
6. 打开 **Actions → Daily digest and GitHub Pages → Run workflow**，从 main 执行首次采集并部署。
7. 部署地址见工作流的 `github-pages` environment，通常为 `https://用户名.github.io/仓库名/`。

`vite.config.js` 使用 `base: './'`，资源与数据路径均为相对路径，支持仓库子目录、个人主页与自定义域名；归档使用 hash，不会因刷新子路由导致 404。自定义域名按 GitHub Pages 文档配置。首次运行若 Pages 尚未启用，请先完成第 3 步并重跑。

仓库为私有时需确认你的 GitHub 计划支持 Pages。这个项目交付不自动创建远端仓库，也不自动开启 Pages。

## 4. 每日定时与失败处理

工作流文件：`.github/workflows/daily.yml`。

```yaml
schedule:
  - cron: '17 23 * * *'
```

对应每天 **UTC 23:17 / 次日北京时间 07:17**。GitHub 的 cron 使用 UTC，可能排队延迟，不保证准点；定时工作流只在默认分支运行。公开仓库长时间无活动可能被 GitHub 停用定时任务，可在 Actions 中重新启用。参考 [GitHub schedule 文档](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)。

- `push main`：测试、构建、部署已有数据，不发起采集。
- 定时 / 手动：先测试，再采集、提交归档，然后在**同一个工作流**构建并部署，避免机器人提交不触发下一次工作流的问题。
- 部分源失败：继续使用其余来源，页面显示提示，Actions 摘要列出源状态。
- 全部源失败：采集命令返回非零；工作流仍部署已有内容并给出 warning。工作流整体可能成功，**不等于采集全部成功**，请查看 Collection status。
- 同日重跑不会重复收录；跨日重复链接和标准化相同标题也不再收录。arXiv 同一论文的版本更新目前不产生新条目。
- 使用 DOI（有则优先）、规范化链接及标题去重。不同库标题变化且缺少相同 DOI 时，仍可能存在重复，可人工编辑归档。
- 重叠工作流排队处理；若采集时有人工推送导致非快进冲突，保存步骤会失败，不会强制覆盖。重跑工作流即可重新从 main 采集。
- 归档按天无限保留。当前首页索引含所有历史内容，适合第一版；增长较大时改为按天懒加载。

## 5. 可选中文标题与摘要

默认无需 API key。翻译只在 Python 采集端执行，浏览器不会接触密钥。`translate()` 预留兼容 **chat/completions** JSON 接口，不绑定任何供应商。配置以下三个环境变量或同名 Actions Secrets：

| 名称 | 值 |
| --- | --- |
| TRANSLATE_API_URL | 完整 HTTPS endpoint，包括 /chat/completions 等实际路径 |
| TRANSLATE_API_KEY | 供应商密钥 |
| TRANSLATE_MODEL | 供应商支持的模型名 |

接口应接受 `model`、`messages`、`temperature`，返回 `choices[0].message.content`，其中内容为 JSON 字符串：`{"titleZh":"中文标题","summaryZh":"简短中文摘要"}`。不支持此格式时替换 `translate()`。超时、解析失败或没有配置时保留原文，不影响采集。当前仅翻译新条目，不自动回填旧归档。翻译失败不改变来源采集状态，但会在日志中记录 fallback；AI 生成结果在页面明确标注。

本地用 shell 设置变量；`.env.example` 只是模板，**Python 不自动加载 .env**。例如 PowerShell：

```powershell
$env:TRANSLATE_API_URL = 'https://your-provider.example/v1/chat/completions'
$env:TRANSLATE_API_KEY = 'your-key'
$env:TRANSLATE_MODEL = 'your-model'
python scripts/update.py
```

不要使用 `VITE_` 前缀放密钥，也不要写进 JSON / 前端文件。`NCBI_API_KEY`、`NCBI_EMAIL` 同样可选，供 PubMed 请求使用。默认请求之间留有间隔，不需要 NCBI key。

## 6. 文件结构与维护

```text
.github/workflows/daily.yml    每日采集 + Pages 部署
config/sources.json            数据源、窗口、数量配置
scripts/update.py              采集、解析、去重、翻译接口
tests/test_update.py           离线回归测试
public/data/archive/*.json     每日内容（持久化主数据）
public/data/index.json         前端聚合索引与最近采集状态
public/favicon.svg            网站图标
src/main.js                   页面渲染、主题与日期筛选
src/style.css                 响应式样式
index.html                    入口
vite.config.js                相对部署路径
```

归档结构：`{"date":"YYYY-MM-DD","items":[...]}`。条目含 `id`、`kind`、`source`、`sourceId`、`title`、`summary`、`url`、`doi`、`published`、`collected`、`tags`；中文内容使用可选 `titleZh` / `summaryZh`。`published` 可为年、年月、完整日期或空字符串，避免伪造日期。索引包含 `schemaVersion`、`lastRun`、`status`、`sources` 和 `days`。

人工修改时先编辑对应 archive 文件，下次采集会重建 index；需要立即更新展示时，同步修改 index 或执行采集。不要只修改 index 后期待永久保留。

后续扩展：增加 Crossref / Europe PMC 适配器；分页与限额告警；术语表辅助翻译；论文 DOI 多来源合并；人工审核发布；按天加载索引；生成 RSS；迁移 Astro 构建静态文章详情以改善搜索引擎收录。当前 MVP 不包含用户账号、上传表单、邮件订阅或医学建议功能。

## 官方参考

- [Vite 静态部署](https://vite.dev/guide/static-deploy)
- [GitHub Pages 自定义工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [arXiv API](https://info.arxiv.org/help/api/user-manual.html)
- [PubMed E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25499/)
- [NCBI 使用声明](https://www.ncbi.nlm.nih.gov/About/disclaimer.html)
- [ScienceDaily RSS 说明](https://www.sciencedaily.com/newsfeeds.htm)
