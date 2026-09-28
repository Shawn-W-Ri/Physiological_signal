# 交付验证记录

验证日期：2026-09-28。

- 生产构建：通过（Vite 7.3.6，版本已由 package-lock.json 锁定）。
- Python 回归测试：5 组通过，覆盖 RSS/Atom、HTML 链接、PubMed XML、标签、稳定 ID、跨日去重、重复运行、失败保留归档、示例清理、翻译成功与降级。
- 浏览器：页面加载、日期归档选择器、URL 主题链接、键盘筛选、空结果、重置已验证。
- 响应式：检查了桌面与 390px 手机视口；手机视口文档宽度 375px，无横向溢出。
- 实际联网：MIT News RSS、ScienceDaily RSS 成功；当前七天窗口收录 4 条 ScienceDaily 新闻，MIT 源本窗口无新条目。
- 实际联网：arXiv 和 PubMed 在本机 Python 中因 `CERTIFICATE_VERIFY_FAILED` 失败（本地证书链不受信任）。未关闭 TLS 验证。论文解析通过离线测试，但论文 API 的完整在线采集尚未验证。可在 GitHub Actions 的干净运行环境中手动运行确认，不能保证源站始终可用。
- GitHub Pages：部署工作流与源码已提供，尚未创建或推送远端仓库，实际部署尚未执行。
- 翻译：未使用真实 API key；验证了接口格式与失败降级，实际供应商调用需配置后确认。

遇到证书错误时，应修复本机或组织代理的受信任证书配置，或在标准 GitHub-hosted runner 中测试，不要通过关闭证书校验绕过错误。
