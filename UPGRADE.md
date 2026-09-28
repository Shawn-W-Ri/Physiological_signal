# 上传这次升级后，怎样添加论文？

1. 解压 **biosignal-upgrade.zip**，把其中的文件/文件夹合并上传到 `Shawn-W-Ri/Physiological_signal` 仓库根目录。确认 `.github/workflows/daily.yml` 也上传了。不要再嵌套一层 biosignal-daily 目录。
2. 使用 Vercel 的话：GitHub → Settings → Secrets and variables → Actions → Variables，添加 `DEPLOY_TARGET=vercel`。
3. Vercel 项目 → Settings → Git → Deploy Hooks，创建 main 分支的 Hook；把 URL 放入 GitHub Actions Secret：`VERCEL_DEPLOY_HOOK`。详情见 README。
4. GitHub → Actions → **Update site and import papers** → **Run workflow**。
5. 在 `paper_links` 输入框粘贴 arXiv / PubMed / DOI 链接，多个以空格或换行分隔，点击运行。
6. 等待导入、提交完成，再到 Vercel Deployments 确认部署成功。
7. 网站 → 研究主题 → 对应信号 → 论文。未匹配主题的条目在“待分类”；失败原因在“添加论文”的处理记录中。

每个主题都有“论文 / 传感器 / 使用方法”。传感器和教程分别编辑 `public/data/sensors.json` 与 `public/data/methods.json`，用 tags 关联研究主题；无需为每个信号复制网页。

升级包保留已有归档与索引；如果没有配置 Vercel，则默认使用 GitHub Pages 工作流。确保 main 分支允许 Actions 保存数据。首次没有看到 Run workflow 时，检查工作流是否位于默认分支的 `.github/workflows` 中。

本次交付没有修改你的 GitHub 仓库或线上网站，升级需上传后生效。公开网页不直接写入 GitHub，避免在前端暴露令牌。
