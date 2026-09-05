# 知行手记 · KF-Money

AI 工具、科研实践与技术记录。由 Python 标准库生成的静态博客，发布到 GitHub Pages。

网站地址：https://kf-money.github.io/

## 内容与结构

`site.json` 是站名、作者、简介、联系方式、分类和域名配置；`content/*.md` 是文章源文件；`assets/` 是前端样式与交互；`build.py` 生成 `site/`；`editor.py` 提供只监听本机的内容工作台；`.github/workflows/deploy.yml` 负责构建、测试与发布。

首发版本包含 12 篇原创演示文章、4 个专题、6 个在浏览器本地处理的工具。演示文章用于展示版式，不代表站长已完成的项目或研究成果。`demo: true` 会保留演示说明及 noindex；它不是密码保护。

## 在 GitHub 网页上更新

进入 `content/` 选择文章，点击编辑并提交到 `master`，或新建 Markdown 文件。更新 `site.json` 可修改站点信息。提交后，在仓库 Actions 查看本次构建、测试和部署结果，不要将提交成功等同于部署成功。

文件名必须与 `slug` 一致，使用小写英文字母、数字和短横线。文章开头是 JSON，而不是 YAML：

```markdown
---
{
  "slug": "my-first-note",
  "title": "我的第一篇笔记",
  "category": "research",
  "date": "2026-09-05",
  "summary": "一句话介绍。",
  "tags": ["科研笔记"],
  "pinned": false,
  "featured": false,
  "draft": false
}
---

## 从一个问题开始

这里写正文。
```

当前分类 id 为 `ai`、`research`、`code`、`thoughts`；分类可以在 `site.json` 中调整。正文支持标题、段落、列表、引用、链接、代码块及简单表格，不是完整 CommonMark，也没有内置 LaTeX 公式渲染。

## 本地可视化写作

需要 Python 3.10 或以上，无需安装 Python 第三方依赖。

```bash
git clone https://github.com/KF-Money/KF-Money.GitHub.io.git
cd KF-Money.GitHub.io
python editor.py
```

Windows 也可双击 `START-WINDOWS.bat`。浏览器打开本机 `http://127.0.0.1:8765/`，支持新建、修改、预览、草稿和站点设置。仅本地保存不会更新线上站点，检查后提交源文件：

```bash
git add content site.json
git diff --cached
git commit -m "更新博客内容"
git push origin master
```

不要开放本地管理端口，不要把 Python 编辑器部署到 GitHub Pages。

## 构建与测试

```bash
python build.py
python -m unittest discover -s tests -p "test_*.py" -v
python -m http.server 8000 --directory site --bind 127.0.0.1
```

构建先写临时目录，校验失败不会替换上一次本地输出。`site/` 是构建产物，不需要提交。GitHub Actions 只上传此目录，不上传编辑器、源码和配置。

## GitHub Pages 首次设置与排错

仓库 Settings → Pages → Build and deployment → Source 应为 **GitHub Actions**。工作流对 `master` 的 push 自动构建发布，对 PR 只构建测试，支持手动 Run workflow。

如果部署日志要求修改 Pages 发布来源，由仓库管理员在上述位置选择 GitHub Actions，然后在 Actions 重新运行失败任务。若出现环境审批，检查 `github-pages` 环境的部署规则；不要删除已有保护规则来绕过审核。

工作流使用 GitHub 提供的短期 `GITHUB_TOKEN` 与 OIDC，仅给予构建读取代码、部署 Pages 所需权限，不需要把个人 Token、密码或私钥放入仓库。构建成功但 deploy 失败时，网站尚未完成本次更新。

## 自定义域名

当前使用 GitHub 默认域名，没有添加 CNAME，也没有改动 DNS。启用自己的域名时，先按 GitHub 文档验证域名所有权，在 Settings → Pages 设置 Custom domain，再修改 DNS 与 `site.json` 的 `domain`，提交后检查 HTTPS。

使用 Actions 发布时，单独提交 CNAME 文件不能代替 Pages 的 Custom domain 设置。详情：https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site

## 正式文章与隐私

替换或删除全部示例文章、核对作者简介，再将 `site.json` 中 `demo` 改为 `false` 并提交。不要填写不存在的备案号。邮箱和微信保持留空，直到决定公开这些信息。

**这是公开仓库。`draft: true` 只阻止文章进入生成网页和站内搜索；已提交的草稿仍能从公开仓库及 Git 历史读取。不要提交尚未公开的论文、保密数据、密码、API Key、个人令牌或私钥。删除最新文件也不会自动清除 Git 历史。**

## 回退

旧主页已保留在 `backup-before-zhinote-20260905` 分支；初始提交为 `c9ed1fe03162b684fe7834fc2636bdee17970671`。不要删除备份分支。恢复近期新版内容可 revert 相应提交并重新发布；恢复旧版 Jekyll 站点还需要匹配旧版 Pages 分支发布设置，不要仅把旧源码交给新 Python 工作流。

## 实现说明

页面使用本地 CSS、JavaScript 和 SVG，无需外部图片或字体 CDN。前端工具不上传输入内容。搜索索引包含所有已发布文章的正文。网站结构参考导航型技术博客；实现、文案与演示文章独立编写，未使用参考站的作者身份、文章、联系方式或备案信息。

GitHub 官方部署说明：https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
