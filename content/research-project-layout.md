---
{
  "slug": "research-project-layout",
  "title": "给研究项目一个清晰的目录结构",
  "category": "code",
  "date": "2026-09-03",
  "summary": "把数据、脚本、配置与结果分开放置，减少“这个文件到底是哪一次运行的”困扰。",
  "tags": [
    "Python",
    "项目管理"
  ],
  "pinned": true,
  "featured": false,
  "draft": false
}
---

## 先区分文件的角色

一个小型研究项目也可以区分原始输入、处理脚本、配置和输出。目录结构没有唯一标准，但命名应该让未来的自己看得懂。

```text
project/
  README.md
  data/raw/
  data/processed/
  scripts/
  configs/
  results/
  notes/
```

## 给每次运行留下身份

建议使用可读的运行标识，并在结果目录中记录参数文件的版本。不要仅用“最终版”“最终版2”来区分结果。

## 不覆盖原始输入

处理结果单独保存。在运行之前说明脚本将读取和写入哪些路径，避免把人工修改混入原始数据。

## 写一份最小 README

写清项目目的、目录含义、运行命令和已知限制。一个能被另一位同事理解的小项目，比一组只有作者记得用途的文件更容易交接。
