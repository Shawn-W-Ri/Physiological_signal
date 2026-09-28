# Signal Daily · 生理信号研究与实践（第二版）

以信号为研究主题，每个主题下统一提供 **论文 / 传感器 / 使用方法** 三个分类。继续保留每日新闻和日期归档。Vite + 原生 JavaScript + Python 标准库，无数据库，无需翻译 API key 即可运行。

## 使用结构

```text
研究主题
├─ ECG/心电
│  ├─ 论文（所有收录日期）
│  ├─ 传感器
│  └─ 使用方法
├─ EEG/脑电、EMG/肌电、PPG、EDA/皮电、呼吸、睡眠、可穿戴设备
│  └─ 同样的三个分类
└─ 待分类（没有匹配关键词的论文）
每日资讯 → 日期归档 → 新闻 / 论文
添加论文 → GitHub 导入入口与逐条处理结果
```

一条资料可以有多个主题标签，只保存一份，在相关主题中同时显示。主题页面不受每日归档日期限制。侧边数字在研究主题中表示论文数，在每日资讯中表示当日新闻与论文的条目数；传感器与方法有独立计数。

## 1. 从第一版升级

优先使用 `biosignal-upgrade.zip`：解压后，把**里面的文件和目录直接合并到 GitHub 仓库根目录**，不要再包一层文件夹。升级包不包含你的历史归档、聚合索引、来源配置、论文链接清单和导入日志，因此不会用本地样例覆盖线上内容。

必须上传隐藏目录 `.github`。旧的 `src/main.js` 可以保留但不再使用，新入口是 `src/library.js`。不要上传 `node_modules`、`node_modules_1` 或 `dist`。完整项目压缩包适合新建仓库；已有内容的仓库请用升级包。

首次部署后首页显示研究主题。若仍是旧页面，检查 Vercel/Pages 是否部署了最新提交并刷新页面。

## 2. 批量添加论文链接（推荐）

1. GitHub 仓库打开 **Actions → Update site and import papers → Run workflow**。
2. 分支选 `main`，在 `paper_links` 中粘贴链接，多个用**空格或换行**分隔。
3. 只添加指定论文时，无需勾选 `collect_news`；勾选则同时采集新闻及自动检索论文。
4. 点击 **Run workflow**，等待导入和部署完成。
5. 网站 → 研究主题 → 对应信号 → **论文**。进入“添加论文”可查看每条链接的处理结果。

支持：

| 类型 | 接受的形式 |
| --- | --- |
| arXiv | `https://arxiv.org/abs/论文编号`，或 `/pdf/论文编号.pdf` |
| PubMed | `https://pubmed.ncbi.nlm.nih.gov/PMID/` |
| DOI | `https://doi.org/10.xxxx/实际编号`，或直接填写 `10.xxxx/实际编号` |

上述是格式说明，不是真实待导入条目。DOI 元数据由 Crossref 读取，不是所有 DOI 都注册在 Crossref；找不到元数据会显示失败。出版社网页、ResearchGate 和普通 PDF 下载链接目前不直接解析，请复制页面上的 DOI。不要用逗号分隔链接，因为 DOI 本身可能带逗号。

导入流程：链接识别 → 公开 API 元数据 → 标题/摘要关键词分类 → 去重 → 可选翻译 → JSON 归档 → 构建与部署。成功识别多个主题时会同时归类，不能识别时进入“待分类”。自动标签是初筛，不保证语义完全准确。没有摘要的论文只根据标题分类，不捏造摘要或日期。

**另一种方式**：直接在 `config/papers.txt` 中每行加一个链接，提交到 main 后，工作流会处理。Actions 表单提交的链接也会保存到此文件，便于失败重试。每次最多尝试 40 条，新链接与排队链接优先；历史成功链接不重复请求。失败记录请查看 `public/data/imports.json` 或网页“添加论文”。永久失效链接可从 papers.txt 删除，下一次运行会移除对应处理记录。

GitHub Actions 表单仅限有仓库权限的成员。静态网站“添加论文”按钮会打开 GitHub，不在公开前端保存写入令牌。更换仓库时修改 `public/data/site.json` 的 `repository`。

## 3. Vercel 部署与自动更新

本项目可以继续使用你已经连接 GitHub 的 Vercel 项目：

1. Vercel 构建配置：Framework Preset 选 **Vite**，Build Command 为 `npm run build`，Output Directory 为 `dist`，Node.js 22.12+。Root Directory 是包含 package.json 的目录。
2. GitHub 仓库 → **Settings → Secrets and variables → Actions → Variables**，新增 `DEPLOY_TARGET`，值为 `vercel`。这会跳过 GitHub Pages 部署。
3. Vercel 项目 → **Settings → Git → Deploy Hooks**，创建一个指向 `main` 的 Hook。
4. 将完整 Hook URL 保存到 GitHub 同一页面的 **Secrets**，名称为 `VERCEL_DEPLOY_HOOK`，不要写进公开代码或网页。
5. 确认 GitHub Actions 允许写入内容。自动导入将先提交归档到 main，再调用 Hook，让 Vercel 构建最新内容。

普通代码推送也可由 Vercel 的 Git 集成自动部署；Hook 用于明确触发机器人更新后的部署。Hook 返回成功只表示任务已提交，最终上线状态仍以 Vercel **Deployments** 为准。若 Vercel 对机器人提交的作者有权限限制，需按该账号/团队的 Git 部署权限配置处理，Hook 不绕过平台权限。

参考：[Vercel Deploy Hooks](https://vercel.com/docs/deploy-hooks)。

## 4. GitHub Pages 部署（另一种选择）

不设置 `DEPLOY_TARGET`（或设为 `pages`）时默认部署 GitHub Pages。

1. 仓库默认分支设为 main，上传项目文件，含 `.github` 与 package-lock.json。
2. **Settings → Pages → Source** 选择 **GitHub Actions**。
3. 确认 Actions 可以对仓库写入。若 main 的保护规则禁止机器人直推，需提供相应规则或改为 PR 流程；当前不自动创建 PR。
4. Actions 手动运行本工作流，部署地址在 `github-pages` environment 中。

Vite 使用相对资源路径，支持 `用户名.github.io/仓库名/`。主题和分类采用 hash 路由，可分享并刷新，不需要服务器路由重写。

参考：[GitHub Pages 自定义工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。

## 5. 本地运行

需要 Node.js **22.12+**（含 npm）、Python **3.11+**，推荐 Python 3.12。

```sh
npm ci
npm run dev
```

打开终端显示的 HTTP 地址。不要双击 index.html。

```sh
python scripts/import_papers.py   # 处理 config/papers.txt
python scripts/update.py          # 自动采集新闻与论文
python -m unittest discover -s tests -v
npm run build                    # 生成 dist/
npm run preview                  # 查看构建结果
```

也可通过环境变量 `PAPER_LINKS` 给导入器传入多条链接；它会追加保存到 papers.txt。不支持 PowerShell 的系统可换用相应 shell 语法：

```powershell
$env:PAPER_LINKS = '这里替换成真实论文链接，多个以空格分隔'
python scripts/import_papers.py
```

示例文本本身不可导入。Python 不自动读取 `.env`。

## 6. 每日任务与异常处理

`.github/workflows/daily.yml` 每天 UTC 23:17 / 次日北京时间 07:17 运行；GitHub 定时任务可能排队延迟，不保证准点。

- **push main**：运行测试、处理链接清单、保存数据、构建与部署；不自动检索 RSS/arXiv/PubMed。
- **schedule**：自动检索并处理待导入/失败链接，再保存和部署。
- **workflow_dispatch**：处理表单及清单；勾选 collect_news 才执行自动检索。
- 采集状态与手动导入状态分别保存；部分失败不影响已成功收录的内容。
- 全部源失败时仍保留归档；失败导入在日志中标记，不生成假论文。
- 采集/导入步骤允许继续部署并输出 warning，因此工作流整体成功不等于所有来源都成功。逐条导入结果见 imports.json；来源状态见 index.json。
- 多次导入按稳定 ID、规范化链接、标准化标题去重；跨库标题不同且缺少相同标识时仍可能重复。arXiv 版本更新不新增论文。
- 同一工作流完成提交与部署，不依赖 GITHUB_TOKEN 的提交再次触发 Actions。并发工作流排队；遇到人工推送造成非快进冲突时不会强制覆盖，重跑即可。

GitHub 定时事件运行于默认分支，公开仓库长期无活动可能停用计划任务。参考 [schedule 文档](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)。

## 7. 扩展主题、传感器、使用方法

| 文件 | 负责内容 |
| --- | --- |
| public/data/topics.json | 研究主题的 id、名称、简介 |
| public/data/sensors.json | 传感器介绍、接口、注意事项、官方链接 |
| public/data/methods.json | 使用流程、步骤、说明、关联设备 |
| public/data/site.json | GitHub 仓库地址 |
| public/data/archive/*.json | 按首次收录日保存的新闻与论文主数据 |
| public/data/index.json | 聚合索引与采集状态 |
| public/data/imports.json | 每个输入链接的处理结果 |
| config/papers.txt | 待导入及已导入的链接清单 |
| config/sources.json | 自动检索的数据源和窗口 |
| scripts/update.py | 来源采集、TOPICS 关键词、翻译接口 |
| scripts/import_papers.py | 指定论文链接解析、分类与归档 |
| src/library.js | 主题/分类路由与渲染 |

新增传感器，在 sensors.json 数组中添加一条：

```json
{
  "id": "unique-sensor-id",
  "name": "设备名称",
  "tags": ["ECG/心电"],
  "summary": "设备用途",
  "interface": "采集接口",
  "considerations": "使用前需要确认的条件",
  "source": "厂家官方文档",
  "url": "https://实际官方文档地址"
}
```

新增方法，在 methods.json 数组中添加 `id`、`title`、`tags`、`sensorIds`、`summary`、`steps`（字符串数组）、`note`、`source`、`url`。sensorIds 引用设备 id；tags 引用主题名称，页面会自动关联。初始 6 个设备与 6 篇方法均附厂商来源，流程是入门提纲，具体接线/参数应依所用硬件版本手册，不等同临床操作规程。

新增信号主题时，在 topics.json 添加展示信息，同时在 update.py 的 `TOPICS` 中增加关键词规则；自动导入与每日采集共用此规则。增加新的内容类型（如数据集、算法）时，可沿用 JSON 数组及 tags，并在 library.js 增加分类与对应卡片渲染函数。

修正已收录论文的标签：编辑 archive 对应条目的 tags，并同步编辑 index，或运行一次勾选 collect_news 的任务由采集器重建索引。若所有外部来源失败，本版采集器保留原索引，请手动同步；只修改 index 的内容会在未来重建时被 archive 覆盖。

## 8. 自动数据源与中文翻译

sources.json 的 type 支持 `rss` / `web` / `arxiv` / `pubmed`；`enabled` 控制开关，`query` 配置检索式，`url` 配置 RSS/HTML，`linkPattern` 配置 HTML 链接正则。`tags` 可为来源附加标签，`filterByTopics` 决定是否过滤无关内容。

默认回看 7 天、每源最多 30 条，不分页；高产出时需增加限额或扩展分页。PubMed 按入库时间检索、arXiv 按提交时间、RSS 按发布日期过滤。网页适配器只读静态 HTML 链接，不执行 JavaScript，也不猜测日期。无日期的资料保留“日期未知”。

可选中文接口在 `update.py → translate()`。通过环境变量或 Actions Secrets 配置：

- `TRANSLATE_API_URL`：完整 HTTPS chat/completions endpoint。
- `TRANSLATE_API_KEY`、`TRANSLATE_MODEL`：供应商密钥与模型名。
- `NCBI_API_KEY`、`NCBI_EMAIL`：可选 PubMed 请求参数。

接口应接受 model/messages/temperature，返回 choices[0].message.content，其中内容是 JSON 字符串，含 titleZh 与 summaryZh。缺少配置、超时或解析失败时保留原文。仅对新条目翻译，不自动回填旧条目。密钥只供采集端使用，不要写入 VITE_* 或公开 JSON。

前端只展示来源提供的简短摘录；不爬取全文或绕过付费访问。arXiv 标注预印本，PubMed 仅作为索引来源，自动分类与翻译请以原文为准。

## 验证与限制

见 VALIDATION.md。当前本机对论文 API 的 TLS 信任链存在限制，新导入器使用离线 API 响应测试，不代表真实 API 已在线验证。GitHub Actions 与远端部署需上传后确认。历史数据量增大后，可把完整 index 改为分主题/按天加载；本版无数据库与公共写入后端。
